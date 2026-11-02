"""Global Data Barometer, 2.ª edición: puntaje nacional y puntajes de los clústeres fundacionales."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

NOMBRE = "gdb-2024-full-data.csv"
ARCHIVOS = [(f"https://storage.googleapis.com/gdb-2024-analysis/open_data_2nd_edition/{NOMBRE}", NOMBRE)]
# Evidencia primaria del 31-ago-2022 al 1-sep-2024 (informe, cap. Metodología); el archivo se rotula 2024.
ANIO = 2024
CLUSTERES = {
    "gdb_gobernanza": "Governance Foundation",
    "gdb_competencias": "Critical Competencies",
    "gdb_acceso_equitativo": "Equitable Access",
}


def procesar(copia: Path) -> pd.DataFrame:
    d = pd.read_csv(copia / NOMBRE, usecols=["iso3", "indicator_type", "cluster", "score"], low_memory=False)
    total = d[d["indicator_type"] == "GDB score"].assign(indicador="gdb_total")
    cl = d[(d["indicator_type"] == "Cluster") & d["cluster"].isin(CLUSTERES.values())]
    cl = cl.assign(indicador=cl["cluster"].map({v: k for k, v in CLUSTERES.items()}))
    out = pd.concat([total, cl], ignore_index=True)
    if out.duplicated(["iso3", "indicador"]).any():
        raise ValueError("gdb: más de un puntaje por país e indicador")
    return pd.DataFrame({"nivel": "internacional", "unidad": out["iso3"], "anio": ANIO,
                         "indicador": out["indicador"], "valor": out["score"]})
