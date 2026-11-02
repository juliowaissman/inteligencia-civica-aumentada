"""INEGI DENUE: establecimientos de servicios de TI por entidad (descarga masiva por sector, CSV).

Se usan los archivos nacionales de los sectores 54 (incluye la rama SCIAN 5415, servicios de diseño de
sistemas de cómputo y servicios relacionados) y 51 (incluye 5182, procesamiento electrónico de
información, hospedaje y otros servicios relacionados). Se descargan dos cortes: el vigente
(sin sufijo de versión en el servidor) y el de mayo de 2025. El año se toma del campo `Temporal` de
los metadatos de cada archivo.
"""

from __future__ import annotations

import io
import re
import zipfile
from pathlib import Path

import pandas as pd

from ..rutas import ENTIDADES

BASE = "https://www.inegi.org.mx/contenidos/masiva/denue/"
ARCHIVOS = [
    (BASE + "denue_00_54_csv.zip", "denue_00_54_csv.zip"),
    (BASE + "denue_00_51_csv.zip", "denue_00_51_csv.zip"),
    (BASE + "2025_05/denue_00_54_0525_csv.zip", "denue_00_54_0525_csv.zip"),
    (BASE + "2025_05/denue_00_51_0525_csv.zip", "denue_00_51_0525_csv.zip"),
]
RAMAS = {"54": ("5415", "denue_5415"), "51": ("5182", "denue_5182")}


def _leer(ruta: Path) -> tuple[int, pd.DataFrame]:
    with zipfile.ZipFile(ruta) as z:
        meta = next(n for n in z.namelist() if n.endswith("metadatos_denue.txt"))
        texto = z.read(meta).decode("utf-8-sig", errors="replace")
        anio = int(re.search(r"Temporal:\s*(\d{4})", texto).group(1))
        datos = next(n for n in z.namelist() if n.startswith("conjunto_de_datos/") and n.endswith(".csv"))
        df = pd.read_csv(io.BytesIO(z.read(datos)), usecols=["codigo_act", "cve_ent"], dtype=str,
                         encoding="latin1")
    return anio, df


def procesar(copia: Path) -> pd.DataFrame:
    filas = []
    for _, nombre in ARCHIVOS:
        sector = nombre.split("_")[2]
        rama, ind = RAMAS[sector]
        anio, df = _leer(copia / nombre)
        sel = df[df["codigo_act"].str.startswith(rama)]
        # Una entidad sin registros en la rama tiene 0 establecimientos en el directorio.
        g = sel.groupby(sel["cve_ent"].str.zfill(2)).size().reindex(sorted(ENTIDADES), fill_value=0)
        filas += [{"nivel": "estatal", "unidad": u, "anio": anio, "indicador": ind, "valor": v} for u, v in g.items()]
        filas.append({"nivel": "nacional", "unidad": "MEX", "anio": anio, "indicador": ind, "valor": len(sel)})
    return pd.DataFrame(filas)
