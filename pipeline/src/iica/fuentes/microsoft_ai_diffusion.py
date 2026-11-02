"""Microsoft AI Economy Institute: AI Diffusion (proporción de personas que usan IA generativa)."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from ..descargar import bajar
from ._paises import bajar_geonames, nombre_a_iso3

NOMBRE = "AI_Diffusion_Q22026_Update.csv"
URL = f"https://raw.githubusercontent.com/microsoft/ai-diffusion-report/main/data/{NOMBRE}"
# Columna del periodo más reciente (2.º trimestre de 2026).
COLUMNA = "Q2 2026 AI Diffusion"
ANIO = 2026
# Nombres del archivo de Microsoft que no coinciden con GeoNames.
ALIAS = {
    "Netherlands": "NLD",
    "Czech Republic": "CZE",
    "Bosnia And Herzegovina": "BIH",
    "Türkiye": "TUR",
    "Cote D'Ivoire": "CIV",
    "Congo": "COG",
    "Congo (DRC)": "COD",
}


def descargar(destino: Path) -> None:
    bajar(URL, destino / NOMBRE)
    bajar_geonames(destino)


def procesar(copia: Path) -> pd.DataFrame:
    # El CSV viene codificado en Mac Roman (p. ej. "T\x9frkiye").
    d = pd.read_csv(copia / NOMBRE, encoding="mac_roman")
    iso3 = nombre_a_iso3(copia, ALIAS)
    faltan = set(d["Economy"]) - set(iso3)
    if faltan:
        raise ValueError(f"microsoft_ai_diffusion: economías sin código ISO3: {faltan}")
    valor = d[COLUMNA].astype(str).str.rstrip("%").astype(float)
    return pd.DataFrame({"nivel": "internacional", "unidad": d["Economy"].map(iso3), "anio": ANIO,
                         "indicador": "ms_difusion_ia", "valor": valor})
