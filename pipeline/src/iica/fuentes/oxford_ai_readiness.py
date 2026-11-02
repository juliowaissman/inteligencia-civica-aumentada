"""Oxford Insights, Government AI Readiness Index 2025.

Los informes y el archivo de datos se entregan tras un formulario, pero los puntajes por país
(total, seis pilares y catorce dimensiones) vienen incrustados como JSON en la página pública
del índice. Se descarga esa página y se leen tal cual.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd

from ..descargar import bajar
from ._paises import bajar_geonames, iso2_a_iso3

URL = "https://oxfordinsights.com/ai-readiness/government-ai-readiness-index-2025/"
ANIO = 2025
CAMPOS = {
    "oxf_total": "total",
    "oxf_capacidad_politica": "policy_capacity",
    "oxf_infraestructura": "ai_infrastructure",
    "oxf_gobernanza": "governance",
    "oxf_adopcion_sector_publico": "public_sector_adoption",
    "oxf_desarrollo_difusion": "development_diffusion",
    "oxf_resiliencia": "resilience",
}


def descargar(destino: Path) -> None:
    bajar(URL, destino / "government-ai-readiness-index-2025.html")
    bajar_geonames(destino)


def procesar(copia: Path) -> pd.DataFrame:
    html = (copia / "government-ai-readiness-index-2025.html").read_text(encoding="utf-8")
    iso3 = iso2_a_iso3(copia)
    dec = json.JSONDecoder()
    paises: dict[str, dict] = {}
    for m in re.finditer(r'\{"id":\d+,"name":', html):
        try:
            o, _ = dec.raw_decode(html, m.start())
        except json.JSONDecodeError:
            continue
        if "total" in o and o.get("code"):
            paises[o["code"]] = o
    if len(paises) < 150:
        raise ValueError(f"oxford_ai_readiness: solo {len(paises)} países; revisar el formato de la página")
    filas = []
    for iso2, o in paises.items():
        u = iso3.get(iso2)
        if u is None:
            raise ValueError(f"oxford_ai_readiness: código ISO2 sin equivalencia: {iso2}")
        for ind, campo in CAMPOS.items():
            filas.append({"nivel": "internacional", "unidad": u, "anio": ANIO, "indicador": ind, "valor": o.get(campo)})
    return pd.DataFrame(filas)
