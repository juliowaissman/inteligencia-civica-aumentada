"""International IDEA: Global State of Democracy (GSoD) Indices v10 (1975–2025).

CSV oficial enlazado desde https://www.idea.int/democracytracker/gsod-indices
(el enlace del sitio pasa por un proxy de descarga; aquí se usa la URL directa).
Las filas sin `iso3c` son agregados regionales y se descartan.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

ARCHIVOS = [("https://www.idea.int/sites/default/files/2026-06/gsod_indices_v10.csv", "gsod_indices_v10.csv")]

# id del indicador en el catálogo -> columna de estimación puntual del GSoD
COLUMNAS = {
    "gsod_participacion": "participation_est",
    "gsod_sociedad_civil": "civil_soc_est",
    "gsod_compromiso_civico": "civic_engage_est",
    "gsod_particip_electoral": "elect_part_est",
}


def procesar(copia: Path) -> pd.DataFrame:
    df = pd.read_csv(copia / ARCHIVOS[0][1], usecols=["iso3c", "year", *COLUMNAS.values()], low_memory=False)
    df = df.dropna(subset=["iso3c"])
    largo = df.melt(id_vars=["iso3c", "year"], var_name="col", value_name="valor").dropna()
    inv = {v: k for k, v in COLUMNAS.items()}
    return pd.DataFrame({
        "nivel": "internacional",
        "unidad": largo["iso3c"].astype(str).str.strip(),
        "anio": largo["year"].astype(int),
        "indicador": largo["col"].map(inv),
        "valor": largo["valor"],
    })
