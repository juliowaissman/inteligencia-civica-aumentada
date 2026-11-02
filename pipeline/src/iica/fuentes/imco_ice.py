"""IMCO: Índice de Competitividad Estatal (ICE), base de datos de la edición 2022 (serie 2003-2022).

IMCO no publica base de datos para las ediciones 2023-2026 (solo PDF con posiciones, sin puntajes en
texto). La última base descargable es la de la edición 2022, enlazada desde
https://indices.imco.org.mx/competitividad-estatal (archivo en Google Drive). La hoja "Puntajes"
tiene bloques "ICE 2003" ... "ICE 2022" (misma metodología), con un renglón por entidad.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

ARCHIVOS = [
    ("https://drive.google.com/uc?export=download&id=1E0ZnOJRhXwxYmk6aHBWgPfzjJ3LsCaLK", "ICE_2022_base_de_datos.xlsx"),
]
COLUMNAS = {"Político": "imco_politico", "Gobierno": "imco_gobierno", "Economía": "imco_economia",
            "Innovación": "imco_innovacion", "GENERAL": "imco_general"}


def procesar(copia: Path) -> pd.DataFrame:
    p = pd.read_excel(copia / ARCHIVOS[0][1], sheet_name="Puntajes", header=None, dtype=object)
    filas = []
    inicios = [i for i, v in p[1].items() if isinstance(v, str) and v.startswith("ICE ")]
    for i in inicios:
        anio = int(p.at[i, 1].split()[1])
        cab = [str(c).strip() for c in p.loc[i + 1, 1:13]]
        bloque = p.loc[i + 2:i + 33, 1:13]
        bloque.columns = cab
        if len(bloque) != 32 or bloque["Clave Inegi"].isna().any():
            raise ValueError(f"IMCO ICE {anio}: bloque incompleto")
        for _, r in bloque.iterrows():
            clave = f"{int(r['Clave Inegi']):02d}"
            for col, ind in COLUMNAS.items():
                filas.append({"nivel": "estatal", "unidad": clave, "anio": anio, "indicador": ind, "valor": float(r[col])})
    return pd.DataFrame(filas)
