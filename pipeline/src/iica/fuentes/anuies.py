"""ANUIES: Anuario Estadístico de Educación Superior (anuario.anuies.mx).

El anuario se consulta en una aplicación web; aquí se reproduce la misma consulta que hace la página
(POST con action=consulta) y se guarda la respuesta JSON tal cual: matrícula total por entidad y campo
amplio de formación (CINE-F), todos los niveles (TSU, licenciatura, normal y posgrado) y modalidades.
"""

from __future__ import annotations

import json
import unicodedata
from pathlib import Path

import pandas as pd
import requests

from ..descargar import AGENTE
from ..rutas import ENTIDADES

URL = "https://anuario.anuies.mx/"
CICLOS = ["2020-2021", "2021-2022", "2022-2023", "2023-2024", "2024-2025", "2025-2026"]
TIC = "Tecnologías de la información y la comunicación"


def _consulta(ciclo: str) -> dict:
    datos = {
        "action": "consulta", "ciclo": ciclo, "vars[]": "MATRÍCULA",
        "desagSexo": "0", "desagDiscapacidad": "0", "desagEdad": "0", "desagHLI": "0",
        "desagProcedencia": "0", "niProcedencia[]": "",
        "includeEnts": "1", "entMode": "all", "includeMuns": "0", "munMode": "all",
        "includeSos": "0", "includeSub": "0", "subMode": "all", "includeAnuies": "0",
        "includeInstitucion": "0", "includeEscuela": "0", "includeNivel": "0", "includeModalidad": "0",
        "includePrograma": "0", "includeStem": "0", "includeCampoAmplio": "1",
        "includeCampoEspecifico": "0", "includeCampoDetallado": "0", "includeCampoUnitario": "0",
        "pageSize": "5000", "page": "1", "maxRows": "5000",
    }
    r = requests.post(URL, data=datos, headers={"User-Agent": AGENTE}, timeout=300)
    r.raise_for_status()
    d = r.json()
    if not d.get("ok") or d.get("meta", {}).get("hasMore"):
        raise RuntimeError(f"ANUIES {ciclo}: respuesta incompleta {d.get('error') or d.get('meta')}")
    return d


def descargar(destino: Path) -> None:
    for ciclo in CICLOS:
        (destino / f"matricula_entidad_campo_{ciclo}.json").write_text(
            json.dumps(_consulta(ciclo), ensure_ascii=False), encoding="utf-8")


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower().strip()
    return " ".join(s.split())


CLAVES = {_norm(n): c for c, n in ENTIDADES.items()} | {
    "coahuila": "05", "michoacan": "16", "veracruz": "30"}


def procesar(copia: Path) -> pd.DataFrame:
    filas = []
    for ciclo in CICLOS:
        d = json.loads((copia / f"matricula_entidad_campo_{ciclo}.json").read_text(encoding="utf-8"))
        df = pd.DataFrame(d["rows"])
        df["valor"] = pd.to_numeric(df["MAT_TOTAL"])
        df["unidad"] = df["ENTIDAD"].map(lambda s: CLAVES.get(_norm(s)))
        if df["unidad"].isna().any():
            raise ValueError(f"ANUIES {ciclo}: entidades no reconocidas {df.loc[df.unidad.isna(), 'ENTIDAD'].unique()}")
        anio = int(ciclo[:4])  # año de inicio del ciclo escolar
        tic = df[df["CAMPO_AMPLIO"] == TIC]
        for ind, t in (("anuies_matricula_superior", df), ("anuies_matricula_tic", tic)):
            g = t.groupby("unidad")["valor"].sum()
            filas += [{"nivel": "estatal", "unidad": u, "anio": anio, "indicador": ind, "valor": v} for u, v in g.items()]
            filas.append({"nivel": "nacional", "unidad": "MEX", "anio": anio, "indicador": ind, "valor": g.sum()})
    return pd.DataFrame(filas)
