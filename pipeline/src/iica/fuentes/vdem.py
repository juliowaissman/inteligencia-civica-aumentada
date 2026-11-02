"""V-Dem (Varieties of Democracy), Country-Year dataset v16.

El sitio de V-Dem entrega el CSV detrás de un formulario (correo, aviso de privacidad
y campo anti-bots), así que no se automatiza. La descarga automática usa el archivo
`vdem.RData` que el propio V-Dem Institute publica en su paquete oficial de R
`vdemdata` (GitHub vdeminstitute/vdemdata, commit "v16 release"), que contiene el
conjunto completo Country-Year v16 (incluye todas las variables del Core).

Leer .RData requiere `pyreadr` (no es dependencia del proyecto todavía):
    uv run --with pyreadr iica cobertura --fuente vdem
Alternativa sin pyreadr: descargar a mano el CSV del Country-Year Core v16 y colocar
el .zip o el .csv en la carpeta de la copia; `procesar` lo usa si existe.
"""

from __future__ import annotations

import zipfile
from pathlib import Path

import pandas as pd

# Commit "v16 release" (2026-03-17) del repositorio oficial vdeminstitute/vdemdata.
COMMIT = "f4dd26922e658442524dfd954bf14f7ebe622d5d"
ARCHIVOS = [
    (f"https://raw.githubusercontent.com/vdeminstitute/vdemdata/{COMMIT}/data/vdem.RData", "vdem.RData"),
]

# id del indicador en el catálogo -> variable de V-Dem (estimación puntual)
VARIABLES = {
    "vdem_partip": "v2x_partip",
    "vdem_delib": "v2xdl_delib",
    "vdem_cspart": "v2x_cspart",
    "vdem_egal": "v2x_egal",
}
COLS = ["country_text_id", "year", *VARIABLES.values()]


def _leer(copia: Path) -> pd.DataFrame:
    csvs = sorted(copia.glob("V-Dem-CY-Core*.csv"))
    if csvs:
        return pd.read_csv(csvs[0], usecols=COLS, low_memory=False)
    zips = sorted(copia.glob("V-Dem-CY-Core*.zip"))
    if zips:
        with zipfile.ZipFile(zips[0]) as z:
            nombre = next(n for n in z.namelist() if n.lower().endswith(".csv") and "core" in n.lower())
            with z.open(nombre) as fh:
                return pd.read_csv(fh, usecols=COLS, low_memory=False)
    try:
        import pyreadr
    except ImportError as e:
        raise RuntimeError(
            "vdem: leer vdem.RData requiere pyreadr. Usa `uv run --with pyreadr iica ...` "
            "o coloca el CSV Country-Year Core v16 en la copia."
        ) from e
    df = next(iter(pyreadr.read_r(copia / "vdem.RData").values()))
    return df[COLS]


def procesar(copia: Path) -> pd.DataFrame:
    df = _leer(copia)
    largo = df.melt(id_vars=["country_text_id", "year"], var_name="var", value_name="valor").dropna()
    inv = {v: k for k, v in VARIABLES.items()}
    return pd.DataFrame({
        "nivel": "internacional",
        "unidad": largo["country_text_id"].astype(str),
        "anio": largo["year"].astype(int),
        "indicador": largo["var"].map(inv),
        "valor": largo["valor"],
    })
