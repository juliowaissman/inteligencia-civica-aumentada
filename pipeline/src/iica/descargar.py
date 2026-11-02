"""Descarga de fuentes con copia fechada y metadatos de procedencia.

Cada fuente tiene un módulo `iica.fuentes.<id>` con:
  - ARCHIVOS: lista de (url, nombre_archivo) para descarga directa, o
  - descargar(destino: Path) -> None para casos especiales.
La copia queda en datos/crudos/<id>/<AAAA-MM-DD>/ junto con `procedencia.json`.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import importlib
import json
from pathlib import Path

import requests

from .catalogo import Fuente
from .rutas import CRUDOS

AGENTE = "iica-pipeline/0.1 (investigacion academica; Universidad de Sonora)"


def _sha256(ruta: Path) -> str:
    h = hashlib.sha256()
    with ruta.open("rb") as fh:
        for bloque in iter(lambda: fh.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


def bajar(url: str, destino: Path, **kw) -> Path:
    destino.parent.mkdir(parents=True, exist_ok=True)
    with requests.get(url, headers={"User-Agent": AGENTE}, stream=True, timeout=120, **kw) as r:
        r.raise_for_status()
        with destino.open("wb") as fh:
            for bloque in r.iter_content(1 << 20):
                fh.write(bloque)
    return destino


def ultima_copia(fuente_id: str) -> Path | None:
    base = CRUDOS / fuente_id
    if not base.exists():
        return None
    fechas = sorted(p for p in base.iterdir() if p.is_dir())
    return fechas[-1] if fechas else None


def descargar(fuente: Fuente) -> Path:
    if fuente.descarga == "manual":
        copia = ultima_copia(fuente.id)
        if copia is None:
            raise RuntimeError(
                f"{fuente.id}: requiere descarga manual. {fuente.instrucciones}\n"
                f"Guarda los archivos en {CRUDOS / fuente.id / 'AAAA-MM-DD'}/"
            )
        return copia
    mod = importlib.import_module(f"iica.fuentes.{fuente.id}")
    hoy = dt.date.today().isoformat()
    destino = CRUDOS / fuente.id / hoy
    destino.mkdir(parents=True, exist_ok=True)
    if hasattr(mod, "descargar"):
        mod.descargar(destino)
    else:
        for url, nombre in mod.ARCHIVOS:
            bajar(url, destino / nombre)
    archivos = {
        p.name: _sha256(p) for p in sorted(destino.iterdir()) if p.is_file() and p.name != "procedencia.json"
    }
    (destino / "procedencia.json").write_text(
        json.dumps(
            {
                "fuente": fuente.id,
                "nombre": fuente.nombre,
                "url": fuente.url,
                "licencia": fuente.licencia,
                "fecha_acceso": hoy,
                "sha256": archivos,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return destino
