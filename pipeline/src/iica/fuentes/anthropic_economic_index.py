"""Anthropic Economic Index: uso de Claude por país (publicación del 2026-06-26, Hugging Face).

El archivo de Claude.ai pesa unos 220 MB (no se versiona en git). Se lee por bloques y solo se
conservan las filas nacionales de la categoría "overall".
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

NOMBRE = "aei_claude_ai_2026-06-26.csv"
ARCHIVOS = [(
    f"https://huggingface.co/datasets/Anthropic/EconomicIndex/resolve/main/release_2026_06_26/data/{NOMBRE}",
    NOMBRE,
)]
METRICAS = {"aei_uso_per_capita": "usage_per_capita_index", "aei_uso_pct": "usage_pct"}


def procesar(copia: Path) -> pd.DataFrame:
    partes = []
    for b in pd.read_csv(copia / NOMBRE, chunksize=1_000_000, keep_default_na=False,
                         usecols=["date_start", "geo_id", "geo_level", "category_name", "metric_id", "value"]):
        partes.append(b[(b["geo_level"] == "country") & (b["category_name"] == "overall")
                        & b["metric_id"].isin(METRICAS.values())])
    d = pd.concat(partes, ignore_index=True)
    # La publicación trae dos meses (abril y mayo de 2026); se toma solo el mes más reciente
    # para tener un valor por país y año.
    d = d[d["date_start"] == d["date_start"].max()]
    inv = {v: k for k, v in METRICAS.items()}
    return pd.DataFrame({"nivel": "internacional", "unidad": d["geo_id"],
                         "anio": d["date_start"].str[:4].astype(int),
                         "indicador": d["metric_id"].map(inv), "valor": pd.to_numeric(d["value"])})
