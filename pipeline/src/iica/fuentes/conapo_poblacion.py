"""CONAPO: Proyecciones de la Población de México y de las Entidades Federativas (datos.gob.mx).

Solo se usa como denominador (población a mitad de año) para tasas por habitante.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

ARCHIVOS = [
    (
        "https://www.datos.gob.mx/dataset/f2b9b220-3ef7-4e3a-bde6-87e1dac78c6a/resource/"
        "b4fe49a8-c86a-4c32-8450-8f3c4cc83125/download/05_indicadores_demograficos_proyecciones.csv",
        "05_indicadores_demograficos_proyecciones.csv",
    ),
]


def procesar(copia: Path) -> pd.DataFrame:
    df = pd.read_csv(copia / ARCHIVOS[0][1], usecols=["ANIO", "CVE_GEO", "POB_MIT_ANIO"])
    cve = df["CVE_GEO"].astype(int)
    return pd.DataFrame({
        "nivel": cve.map(lambda c: "nacional" if c == 0 else "estatal"),
        "unidad": cve.map(lambda c: "MEX" if c == 0 else f"{c:02d}"),
        "anio": df["ANIO"].astype(int),
        "indicador": "poblacion_total",
        "valor": df["POB_MIT_ANIO"],
    })
