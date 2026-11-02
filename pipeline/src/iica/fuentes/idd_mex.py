"""IDD-Mex: Índice de Desarrollo Democrático de México (Fundación Konrad Adenauer, Polilat y otros).

idd-mex.org no responde desde 2025, así que se usan copias de web.archive.org:
- Página "Rankings 2024" (captura 2025-11-14): gráficas Highcharts con el puntaje del IDD-Mex por
  entidad para cada edición 2010-2024 (sin 2016). Se leen las parejas categoría/valor `y` de las
  gráficas `containerIDD<AAAA>`. Ediciones 2010-2020 con 3 decimales; 2021-2024 con 2 o 3.
- "SERIES POR DIMENSION y POR INDICADOR IDD-MEX 2010-2020" (xlsx, captura 2022-05-03): hoja
  "IDD-MEX 2010-20", con el renglón "Promedio" (nacional publicado). Se usa también para comprobar
  que los valores de la página coinciden con el xlsx (2010-2020).
El nacional 2024 (4.722) se transcribe del informe IDD-Mex 2024 (PDF, p. 16).
"""

from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

import pandas as pd

from ..rutas import ENTIDADES

ARCHIVOS = [
    ("https://web.archive.org/web/20251114092054id_/https://idd-mex.org/rankings-2024/", "rankings-2024.html"),
    ("https://web.archive.org/web/20220503175656id_/https://idd-mex.org/wp-content/uploads/2021/02/"
     "SERIES-POR-DIMENSION-y-POR-INDICADOR-IDD-MEX-2010-2020-1.xlsx", "series_idd_mex_2010_2020.xlsx"),
]
# En la hoja resumen "IDD-MEX 2010-20" Baja California y Baja California Sur están intercambiadas en
# 2014 y 2015; las hojas anuales "IDD MEX 2014/2015" del mismo archivo coinciden con la página web.
INTERCAMBIO_XLSX = {(2014, "02"), (2014, "03"), (2015, "02"), (2015, "03")}
NACIONAL_2024 = 4.722  # Informe IDD-Mex 2024, p. 16 ("situándose en 4,722 puntos")


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower().strip()
    return " ".join(s.replace("(estado)", "").split())


CLAVES = {_norm(n): c for c, n in ENTIDADES.items()} | {
    "coahuila": "05", "michoacan": "16", "veracruz": "30", "estado de mexico": "15", "edomex": "15", "distrito federal": "09", "df": "09"}


def _graficas(html: str) -> dict[int, dict[str, float]]:
    ms = list(re.finditer(r"Highcharts\.chart\('containerIDD(\d{4})'", html))
    out = {}
    for i, m in enumerate(ms):
        fin = html.find("Highcharts.chart(", m.end())
        blk = html[m.start(): fin if fin > 0 else len(html)]
        cats = json.loads(re.search(r"categories:\s*(\[[^\]]*\])", blk).group(1))
        serie = blk[blk.find("series: [{"):]
        ys = [float(v) for v in re.findall(r"y:\s*(-?[\d.]+)", serie)]
        if len(cats) != 32 or len(ys) != 32:
            raise ValueError(f"IDD-Mex {m.group(1)}: {len(cats)} categorías y {len(ys)} valores")
        out[int(m.group(1))] = {CLAVES[_norm(c)]: y for c, y in zip(cats, ys)}
    return out


def procesar(copia: Path) -> pd.DataFrame:
    graf = _graficas((copia / ARCHIVOS[0][1]).read_text(encoding="utf-8", errors="replace"))
    x = pd.read_excel(copia / ARCHIVOS[1][1], sheet_name="IDD-MEX 2010-20", header=None)
    anios = [int(a) for a in x.iloc[1, 2:12]]
    filas = []
    for _, r in x.iloc[2:35].iterrows():
        nombre = str(r[1])
        for a, v in zip(anios, r[2:12]):
            if nombre == "Promedio":
                filas.append({"nivel": "nacional", "unidad": "MEX", "anio": a, "indicador": "idd_mex", "valor": float(v)})
            elif (a, CLAVES[_norm(nombre)]) not in INTERCAMBIO_XLSX and abs(graf[a][CLAVES[_norm(nombre)]] - float(v)) > 0.0006:
                raise ValueError(f"IDD-Mex {a} {nombre}: página {graf[a][CLAVES[_norm(nombre)]]} ≠ xlsx {v}")
    for a, d in graf.items():
        filas += [{"nivel": "estatal", "unidad": u, "anio": a, "indicador": "idd_mex", "valor": v} for u, v in d.items()]
    filas.append({"nivel": "nacional", "unidad": "MEX", "anio": 2024, "indicador": "idd_mex", "valor": NACIONAL_2024})
    return pd.DataFrame(filas)
