"""Global Index on Responsible AI (GIRAI) 2026: puntaje global y cinco dimensiones.

El conjunto completo de datos del GIRAI se entrega tras llenar un formulario. Los puntajes por
país, sin embargo, vienen incrustados (JSON de Next.js) en la página pública del índice, que es
lo que se descarga y se lee aquí.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd

from ..descargar import bajar

URL = "https://www.global-index.ai/"
ANIO = 2026  # edición del índice
DIMENSIONES = {
    "girai_inclusion": "inclusion-diversity",
    "girai_etica": "ethics-sustainability",
    "girai_trabajo": "labour-skills",
    "girai_confianza": "trust-safety",
    "girai_sector_publico": "ai-use-public-service",
}


def descargar(destino: Path) -> None:
    bajar(URL, destino / "global-index-ai.html")


def _paises(html: str) -> dict[str, dict]:
    trozos = re.findall(r'self\.__next_f\.push\(\[1,(".*?")\]\)</script>', html, flags=re.S)
    flujo = "".join(json.loads(t) for t in trozos)
    dec = json.JSONDecoder()
    out: dict[str, dict] = {}
    for m in re.finditer(r'\{"iso3":', flujo):
        try:
            obj, _ = dec.raw_decode(flujo, m.start())
        except json.JSONDecodeError:
            continue
        if "girai" in obj and "dimensionScores" in obj:
            out[obj["iso3"]] = obj
    return out


def procesar(copia: Path) -> pd.DataFrame:
    paises = _paises((copia / "global-index-ai.html").read_text(encoding="utf-8"))
    if len(paises) < 100:
        raise ValueError(f"girai: solo se encontraron {len(paises)} países; revisar el formato de la página")
    filas = []
    for iso3, o in paises.items():
        filas.append(("girai_total", iso3, o["girai"]))
        for ind, clave in DIMENSIONES.items():
            filas.append((ind, iso3, o["dimensionScores"].get(clave)))
    df = pd.DataFrame(filas, columns=["indicador", "unidad", "valor"])
    return df.assign(nivel="internacional", anio=ANIO)
