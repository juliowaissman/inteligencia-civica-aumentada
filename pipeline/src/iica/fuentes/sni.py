"""SECIHTI: Sistema Nacional de Investigadoras e Investigadores (SNII), padrón vigente, programa S191.

Se descarga el padrón del 2.º semestre de 2025 desde el almacén de datos (datastore) de datos.gob.mx,
solo con las columnas necesarias (sin nombres de personas). El archivo original del editor está en
repodatos.atdt.gob.mx, que rechaza descargas automatizadas (HTTP 403); la exportación del datastore de
CKAN contiene los mismos registros.

Conteo absoluto por entidad de acreditación/comisión. Las tasas por habitante se calculan después con
`conapo_poblacion`.
"""

from __future__ import annotations

import unicodedata
from pathlib import Path

import pandas as pd

from ..rutas import ENTIDADES

RECURSO = "5aa363f1-ae6c-420f-8904-86c8c0662432"  # s191_snii_2s_2025.csv
ANIO = 2025
ARCHIVOS = [
    (f"https://www.datos.gob.mx/datastore/dump/{RECURSO}?format=csv"
     "&fields=cvu,nivel,area_conocimiento,entidad_acreditacion_comision",
     "s191_snii_2s_2025.csv"),
]


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower().strip()
    return " ".join(s.split())


CLAVES = {_norm(n): c for c, n in ENTIDADES.items()} | {"mexico": "15", "estado de mexico": "15"}


def procesar(copia: Path) -> pd.DataFrame:
    df = pd.read_csv(copia / ARCHIVOS[0][1], dtype=str)
    if df["cvu"].duplicated().any():
        raise ValueError("SNII: CVU duplicados en el padrón")
    clave = df["entidad_acreditacion_comision"].map(lambda s: CLAVES.get(_norm(s)))
    sin = df.loc[clave.isna(), "entidad_acreditacion_comision"].unique()
    if set(sin) - {"Sin Entidad de Acreditacion"}:
        raise ValueError(f"SNII: entidades no reconocidas {sin}")
    filas = [{"nivel": "nacional", "unidad": "MEX", "anio": ANIO, "indicador": "sni_investigadores",
              "valor": len(df)}]
    for c, n in clave.value_counts().items():
        filas.append({"nivel": "estatal", "unidad": c, "anio": ANIO, "indicador": "sni_investigadores", "valor": n})
    return pd.DataFrame(filas)
