"""World Justice Project: Rule of Law Index, archivo de datos históricos (2012–2026).

Se usa la hoja "Historical Data" del archivo oficial, que trae una fila por
país-edición con códigos de columna (f_3, f_3_1, ...). Las ediciones bienales
"2012-2013" y "2017-2018" se asignan al último año del periodo (2013 y 2018).
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

ARCHIVOS = [
    (
        "https://worldjusticeproject.org/rule-of-law-index/downloads/2026_wjp_rule_of_law_index_HISTORICAL_DATA_FILE.xlsx",
        "2026_wjp_rule_of_law_index_HISTORICAL_DATA_FILE.xlsx",
    ),
]

# id del indicador en el catálogo -> código de columna de WJP
CODIGOS = {
    "wjp_gob_abierto": "f_3",
    "wjp_leyes_datos": "f_3_1",
    "wjp_derecho_info": "f_3_2",
    "wjp_participacion": "f_3_3",
    "wjp_quejas": "f_3_4",
}


def procesar(copia: Path) -> pd.DataFrame:
    crudo = pd.read_excel(copia / ARCHIVOS[0][1], sheet_name="Historical Data", header=None)
    codigos = crudo.iloc[0].tolist()
    etiquetas = crudo.iloc[1].tolist()
    df = crudo.iloc[2:].copy()
    df.columns = [c if isinstance(c, str) else e for c, e in zip(codigos, etiquetas)]
    df = df.dropna(subset=["Country Code"])
    anio = df["Year"].astype(str).str.split("-").str[-1].astype(int)
    filas = []
    for ind, cod in CODIGOS.items():
        filas.append(pd.DataFrame({
            "nivel": "internacional",
            "unidad": df["Country Code"].astype(str).str.strip(),
            "anio": anio,
            "indicador": ind,
            "valor": pd.to_numeric(df[cod], errors="coerce"),
        }))
    return pd.concat(filas, ignore_index=True).dropna(subset=["valor"])
