"""UIT: personas con habilidades TIC por tipo de habilidad (ODS 4.4.1, serie SE_ADT_ACTS).

El ITU DataHub (datahub.itu.int y api.datahub.itu.int) responde 403 a clientes automáticos, así
que la serie se baja de la Base de Datos Global de Indicadores ODS de la ONU (UN DESA), que
redistribuye los datos de la UIT como agencia custodia del indicador 4.4.1.
"""

from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlencode

import pandas as pd

from ..descargar import bajar
from ._paises import bajar_geonames, numerico_a_iso3

TIPOS = {"itu_copiar_pegar": "COPA", "itu_formula_hoja": "ARSP", "itu_programar": "PCPR"}
FILTRO = [
    {"name": "Type of skill", "values": list(TIPOS.values())},
    {"name": "Sex", "values": ["BOTHSEX"]},
    {"name": "Age", "values": ["ALLAGE"]},
]
URL = "https://unstats.un.org/sdgapi/v1/sdg/Series/Data?" + urlencode(
    {"seriesCode": "SE_ADT_ACTS", "dimensions": json.dumps(FILTRO), "pageSize": 100000}
)
ARCHIVO = "SE_ADT_ACTS.json"


def descargar(destino: Path) -> None:
    bajar(URL, destino / ARCHIVO)
    bajar_geonames(destino)


def procesar(copia: Path) -> pd.DataFrame:
    d = json.loads((copia / ARCHIVO).read_text(encoding="utf-8"))
    if d["totalElements"] > len(d["data"]):
        raise ValueError("itu: respuesta paginada incompleta; aumentar pageSize")
    iso3 = numerico_a_iso3(copia)
    inv = {v: k for k, v in TIPOS.items()}
    filas = []
    for x in d["data"]:
        dim = x["dimensions"]
        u = iso3.get(str(x["geoAreaCode"]))
        if u is None or dim.get("Reporting Type") != "G" or dim.get("Location", "ALLAREA") != "ALLAREA":
            continue  # agregados regionales (M49), otras series de reporte o desgloses urbano/rural
        filas.append({"nivel": "internacional", "unidad": u, "anio": int(x["timePeriodStart"]),
                      "indicador": inv[dim["Type of skill"]], "valor": float(x["value"])})
    df = pd.DataFrame(filas)
    if df.duplicated(["unidad", "anio", "indicador"]).any():
        raise ValueError("itu: más de un valor por país, año e indicador")
    return df
