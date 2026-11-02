"""Registro Federal de las Organizaciones de la Sociedad Civil (CLUNI), Secretaría de Bienestar.

Listados semestrales publicados por la Comisión de Fomento de las Actividades de las OSC
(corresponsabilidad.gob.mx, "Guía para consultar el listado de OSC"), como hojas de Google. El archivo
"OSC activas" contiene en realidad todas las OSC inscritas con su ESTATUS OSC (ACTIVA, ACTIVA
CONDICIONADA, INACTIVA, DISOLUCION). Se cuentan CLUNI únicos por entidad y estatus.
Cortes: 31 de diciembre de 2024 y 31 de diciembre de 2025.
"""

from __future__ import annotations

import unicodedata
from pathlib import Path

import pandas as pd

from ..rutas import ENTIDADES

G = "https://docs.google.com/spreadsheets/d/{}/export?format=xlsx"
ARCHIVOS = [
    (G.format("1agyghq8vjzklXDs45GPD32zWnaD3xLlw"), "osc_estatus_2024-12-31.xlsx"),
    (G.format("1j3m6OM6ab5D-D6plvCz_AbCLAHoq_G5z"), "osc_estatus_2025-12-31.xlsx"),
]
INDICADORES = {"osc_activas": {"ACTIVA"}, "osc_activas_y_condicionadas": {"ACTIVA", "ACTIVA CONDICIONADA"}}


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower().strip()
    return " ".join(s.split())


CLAVES = {_norm(n): c for c, n in ENTIDADES.items()} | {
    "coahuila": "05", "michoacan": "16", "veracruz": "30", "estado de mexico": "15", "distrito federal": "09"}


def procesar(copia: Path) -> pd.DataFrame:
    filas = []
    for _, nombre in ARCHIVOS:
        anio = int(nombre.split("_")[-1][:4])
        df = pd.read_excel(copia / nombre, sheet_name=0, usecols=["CLUNI", "ENTIDAD", "ESTATUS OSC"], dtype=str)
        df = df.drop_duplicates("CLUNI")
        df["estatus"] = df["ESTATUS OSC"].str.strip().str.upper()
        df["unidad"] = df["ENTIDAD"].map(lambda s: CLAVES.get(_norm(s)))
        if df["unidad"].isna().any():
            raise ValueError(f"OSC {anio}: entidades no reconocidas {df.loc[df.unidad.isna(), 'ENTIDAD'].unique()}")
        for ind, estatus in INDICADORES.items():
            sel = df[df["estatus"].isin(estatus)]
            g = sel.groupby("unidad").size().reindex(sorted(ENTIDADES), fill_value=0)
            filas += [{"nivel": "estatal", "unidad": u, "anio": anio, "indicador": ind, "valor": v} for u, v in g.items()]
            filas.append({"nivel": "nacional", "unidad": "MEX", "anio": anio, "indicador": ind, "valor": len(sel)})
    return pd.DataFrame(filas)
