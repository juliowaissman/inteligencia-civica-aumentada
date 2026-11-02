"""Global Innovation Index 2026 (OMPI): puntaje GII y subíndices de insumos y productos.

La descarga oficial del GII Data Explorer no ofrece un enlace directo automatizable y el repositorio
TIND de la OMPI bloquea clientes automáticos. Los puntajes por economía se toman de los datos de las
gráficas Datawrapper incrustadas en el capítulo de resultados del informe oficial (fuente declarada en
las gráficas: "Global Innovation Index Database, WIPO, 2026").
"""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd
import requests

from ..descargar import AGENTE, bajar

PAGINA = "https://www.wipo.int/web-publications/global-innovation-index-2026/en/gii-2026-results.html"
GRAFICAS = {
    "7LeG9": "gii_puntaje_vs_pib.csv",  # ISO3, Economy, GDP per capita, ..., GII score
    "kb0qX": "gii_insumos_productos.csv",  # ISO3, NAME, INPUT, OUTPUT, ...
}
ANIO = 2026


def _version(id_grafica: str) -> str:
    r = requests.get(f"https://datawrapper.dwcdn.net/{id_grafica}/", headers={"User-Agent": AGENTE}, timeout=60)
    r.raise_for_status()
    m = re.search(rf"dwcdn\.net/{id_grafica}/(\d+)/", r.text)
    if not m:
        raise ValueError(f"gii: no se encontró la versión publicada de la gráfica {id_grafica}")
    return m.group(1)


def descargar(destino: Path) -> None:
    bajar(PAGINA, destino / "gii-2026-results.html")
    html = (destino / "gii-2026-results.html").read_text(encoding="utf-8")
    for id_grafica, nombre in GRAFICAS.items():
        if id_grafica not in html:
            raise ValueError(f"gii: la gráfica {id_grafica} ya no aparece en la página de resultados")
        v = _version(id_grafica)
        bajar(f"https://datawrapper.dwcdn.net/{id_grafica}/{v}/dataset.csv", destino / nombre)


def procesar(copia: Path) -> pd.DataFrame:
    a = pd.read_csv(copia / GRAFICAS["7LeG9"], keep_default_na=False)
    b = pd.read_csv(copia / GRAFICAS["kb0qX"], keep_default_na=False)
    partes = [
        pd.DataFrame({"unidad": a["ISO3"], "indicador": "gii_total", "valor": a["GII score"]}),
        pd.DataFrame({"unidad": b["ISO3"], "indicador": "gii_insumos", "valor": b["INPUT"]}),
        pd.DataFrame({"unidad": b["ISO3"], "indicador": "gii_productos", "valor": b["OUTPUT"]}),
    ]
    df = pd.concat(partes, ignore_index=True)
    df["valor"] = pd.to_numeric(df["valor"], errors="coerce")
    return df.assign(nivel="internacional", anio=ANIO)
