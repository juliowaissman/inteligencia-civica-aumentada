"""GitHub Innovation Graph: desarrolladores y colaboración entre economías (CSV trimestrales, CC0)."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from ..descargar import bajar
from ._paises import bajar_geonames, iso2_a_iso3

BASE = "https://raw.githubusercontent.com/github/innovationgraph/main/data/{}"
ARCHIVOS_FUENTE = ["developers.csv", "economy_collaborators.csv"]
# Agregado regional publicado por GitHub que no es un país.
NO_PAISES = {"EU"}


def descargar(destino: Path) -> None:
    for nombre in ARCHIVOS_FUENTE:
        bajar(BASE.format(nombre), destino / nombre)
    bajar_geonames(destino)


def procesar(copia: Path) -> pd.DataFrame:
    iso3 = iso2_a_iso3(copia)
    # keep_default_na=False: "NA" es Namibia, no un valor faltante.
    dev = pd.read_csv(copia / "developers.csv", keep_default_na=False)
    col = pd.read_csv(copia / "economy_collaborators.csv", keep_default_na=False)

    # Años completos (con los cuatro trimestres publicados).
    completos = dev.groupby("year")["quarter"].nunique()
    completos = set(completos[completos == 4].index)

    # Desarrolladores: cuentas acumuladas al cierre del 4.º trimestre de cada año.
    d = dev[(dev["quarter"] == 4) & dev["year"].isin(completos)]
    d = d.assign(indicador="gh_desarrolladores", valor=d["developers"])

    # Colaboración transfronteriza: suma anual (4 trimestres) del peso enviado por la
    # economía a repositorios de OTRAS economías; se excluye el agregado "EU" como destino
    # para no contar dos veces a sus miembros.
    c = col[(col["source"] != col["destination"]) & ~col["destination"].isin(NO_PAISES)]
    c = c[c["year"].isin(completos)]
    c = c.groupby(["source", "year"], as_index=False)["weight"].sum()
    c = c.rename(columns={"source": "iso2_code"}).assign(indicador="gh_colaboracion_externa", valor=c["weight"])

    out = pd.concat([d, c], ignore_index=True)
    out = out[~out["iso2_code"].isin(NO_PAISES)]
    out["unidad"] = out["iso2_code"].map(iso3)
    out = out.dropna(subset=["unidad"])
    return pd.DataFrame({"nivel": "internacional", "unidad": out["unidad"], "anio": out["year"],
                         "indicador": out["indicador"], "valor": out["valor"]})
