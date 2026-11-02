"""IMPI en cifras: solicitudes de invenciones de mexicanos por entidad federativa (1993-2025).

Hoja "Inv 3" del capítulo de invenciones de "IMPI en cifras" (hoja de Google enlazada desde
https://www.gob.mx/impi/documentos/instituto-mexicano-de-la-propiedad-industrial-en-cifras-impi-en-cifras).
Por cada año hay columnas Patentes | Diseños industriales | Modelos de utilidad | Trazados de CI | Total.
Se usan solo los años completos (se omiten las columnas trimestrales preliminares "nT AAAAP").
"-" significa 0. El total nacional es el renglón "Total / Total" (incluye a los mexicanos que radican
en el extranjero, por lo que es algo mayor que la suma de las entidades).
"""

from __future__ import annotations

import unicodedata
from pathlib import Path

import pandas as pd

from ..rutas import ENTIDADES

ARCHIVOS = [
    ("https://docs.google.com/spreadsheets/d/1htTdMGQaJkr988ro7oGwBwm-nfHnbkRk/export?format=xlsx",
     "impi_en_cifras_invenciones.xlsx"),
]
COLUMNAS = {"Patentes": "impi_solicitudes_patente", "Total": "impi_solicitudes_invenciones"}


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower().strip()
    return " ".join(s.split())


CLAVES = {_norm(n): c for c, n in ENTIDADES.items()} | {
    "coahuila": "05", "michoacan": "16", "veracruz": "30", "estado de mexico": "15", "distrito federal": "09"}


def procesar(copia: Path) -> pd.DataFrame:
    d = pd.read_excel(copia / ARCHIVOS[0][1], sheet_name="Inv 3", header=None, dtype=object)
    i_anio = next(i for i in range(10) if str(d.iat[i, 1]).startswith("Entidad"))
    anios = d.iloc[i_anio].ffill()
    tipos = d.iloc[i_anio + 1].astype(str).str.split("/").str[0].str.strip()
    filas = []
    for i in range(i_anio + 2, len(d)):
        nombre = str(d.iat[i, 1]).strip()
        if nombre.startswith("Total"):
            nivel, unidad = "nacional", "MEX"
        elif _norm(nombre) in CLAVES:
            nivel, unidad = "estatal", CLAVES[_norm(nombre)]
        else:
            continue
        for j in range(2, d.shape[1]):
            a = str(anios.iat[j]).strip()
            if not a.replace(".0", "").isdigit() or tipos.iat[j] not in COLUMNAS:
                continue
            v = d.iat[i, j]
            v = 0 if str(v).strip() == "-" else v
            filas.append({"nivel": nivel, "unidad": unidad, "anio": int(float(a)),
                          "indicador": COLUMNAS[tipos.iat[j]], "valor": float(v)})
    df = pd.DataFrame(filas)
    if df[df.nivel == "estatal"].unidad.nunique() != 32:
        raise ValueError("IMPI: no se encontraron las 32 entidades")
    return df
