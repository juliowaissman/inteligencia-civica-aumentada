"""Banco Mundial: World Development Indicators y Worldwide Governance Indicators (API v2)."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from ..descargar import bajar

# id del indicador en el catálogo -> código en la API del Banco Mundial
CODIGOS = {
    "wb_internet": "IT.NET.USER.ZS",
    "wb_terciaria": "SE.TER.ENRR",
    "wgi_voz": "GOV_WGI_VA.EST",
    "wgi_efectividad": "GOV_WGI_GE.EST",
    "wgi_corrupcion": "GOV_WGI_CC.EST",
}
API = "https://api.worldbank.org/v2/country/all/indicator/{codigo}?format=json&per_page=20000&date=2000:2026"


PAISES = "https://api.worldbank.org/v2/country?format=json&per_page=400"
POBLACION = "https://api.worldbank.org/v2/country/all/indicator/SP.POP.TOTL?format=json&per_page=20000&date=2000:2026"


def descargar(destino: Path) -> None:
    for ind, codigo in CODIGOS.items():
        bajar(API.format(codigo=codigo), destino / f"{ind}.json")
    # Metadatos de países (nombre, región, si es agregado) y población, para filtros y tasas.
    bajar(PAISES, destino / "paises.json")
    bajar(POBLACION, destino / "poblacion.json")


def paises(copia: Path) -> pd.DataFrame:
    """Países reales (sin agregados regionales) con nombre y región del Banco Mundial."""
    _, datos = json.loads((copia / "paises.json").read_text())
    filas = [
        {"unidad": d["id"], "nombre": d["name"], "region": d["region"]["value"]}
        for d in datos
        if d["region"]["value"] != "Aggregates"
    ]
    return pd.DataFrame(filas)


def poblacion(copia: Path) -> pd.DataFrame:
    _, datos = json.loads((copia / "poblacion.json").read_text())
    return pd.DataFrame(
        [{"unidad": d["countryiso3code"], "anio": int(d["date"]), "poblacion": d["value"]}
         for d in datos if d["value"] is not None and d.get("countryiso3code")]
    )


def procesar(copia: Path) -> pd.DataFrame:
    filas = []
    for ind in CODIGOS:
        meta, datos = json.loads((copia / f"{ind}.json").read_text())
        for d in datos or []:
            iso = d.get("countryiso3code")
            if iso and len(iso) == 3 and d["value"] is not None:
                filas.append({"nivel": "internacional", "unidad": iso, "anio": int(d["date"]),
                              "indicador": ind, "valor": d["value"]})
    return pd.DataFrame(filas)
