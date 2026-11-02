"""INAI–CIDE: Métrica de Gobierno Abierto (MGA), ediciones 2017, 2019 y 2021, por entidad federativa.

- 2021: CSV de resultados por estado publicado en el micrositio oficial de la Métrica en shinyapps
  (la "é" del nombre va en forma descompuesta, e%CC%81). Se usan ga_indice, t_indice y p_indice tal cual.
  El CSV no trae fila nacional; el valor nacional (0.48, 0.61, 0.35) se transcribe del Reporte final
  de la MGA 2021 (sección "3. Resultados"), que también se descarga como respaldo.
- 2019: xlsx "Resultados Métrica 2019" (copia de web.archive.org del micrositio del INAI), hoja
  "Estado " (promedios ponderados por número de sujetos obligados) y hoja "Totales" para el nacional.
- 2017: xlsx "Comparador-entidades-final" (web.archive.org), hoja BR con un renglón por sujeto obligado.
  El archivo no trae agregados estatales: se calcula el promedio simple por entidad, que reproduce
  la tabla del Anexo 5 del Reporte de Resultados (feb. 2017, pp. 85-86); el nacional es el promedio
  de toda la muestra (0.389, publicado como 0.39).
Fila "Federal"/"Federación" (sujetos obligados federales) se excluye: no es una entidad.
"""

from __future__ import annotations

import unicodedata
from pathlib import Path

import pandas as pd

from ..rutas import ENTIDADES

SHINY = "https://lnppmicrositio.shinyapps.io/metrica_gobierno_abierto_2021/"
WB = "https://web.archive.org/web/{ts}id_/https://micrositios.inai.org.mx/gobiernoabierto/en/wp-content/uploads/"
ARCHIVOS = [
    (SHINY + "bases/Resultados%20Me%CC%81trica%202021_Estado.csv", "mga2021_estado.csv"),
    (SHINY + "documentos/Reporte%20final_MGA%202021.pdf", "mga2021_reporte_final.pdf"),
    (WB.format(ts="20210213201902") + "2019/03/Resultados-M%C3%A9trica-2019.xlsx", "mga2019_resultados.xlsx"),
    (WB.format(ts="20210213202158") + "2018/07/Comparador-entidades-final.xlsx", "mga2017_comparador_entidades.xlsx"),
    (WB.format(ts="20210213202140") + "2018/07/ReportedeResultadosMetricafeb17.pdf", "mga2017_reporte.pdf"),
]
# Nacional 2021 transcrito del Reporte final MGA 2021, sección 3 "Resultados".
NACIONAL_2021 = {"mga_indice": 0.48, "mga_transparencia": 0.61, "mga_participacion": 0.35}
IND = {"ga": "mga_indice", "t": "mga_transparencia", "p": "mga_participacion"}


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower().strip()
    return " ".join(s.split())


CLAVES = {_norm(n): c for c, n in ENTIDADES.items()} | {
    "coahuila": "05", "michoacan": "16", "veracruz": "30"}
FEDERAL = {"federal", "0 - federacion"}


def _filas(df: pd.DataFrame, col_ent: str, cols: dict[str, str], anio: int) -> list[dict]:
    filas = []
    for _, r in df.iterrows():
        n = _norm(r[col_ent])
        if n in FEDERAL or n.startswith("notas"):
            continue
        if n not in CLAVES:
            raise ValueError(f"MGA {anio}: entidad no reconocida {r[col_ent]!r}")
        for col, ind in cols.items():
            filas.append({"nivel": "estatal", "unidad": CLAVES[n], "anio": anio, "indicador": ind, "valor": r[col]})
    return filas


def procesar(copia: Path) -> pd.DataFrame:
    cols = {f"{k}_indice": v for k, v in IND.items()}
    filas = []
    # 2021
    d21 = pd.read_csv(copia / "mga2021_estado.csv")
    filas += _filas(d21, "estado", cols, 2021)
    filas += [{"nivel": "nacional", "unidad": "MEX", "anio": 2021, "indicador": i, "valor": v}
              for i, v in NACIONAL_2021.items()]
    # 2019
    x19 = copia / "mga2019_resultados.xlsx"
    d19 = pd.read_excel(x19, sheet_name="Estado ")
    filas += _filas(d19, "estado", cols, 2019)
    tot = pd.read_excel(x19, sheet_name="Totales", header=None).set_index(0)[1]
    for etiqueta, ind in (("Índice de gobierno abierto", "mga_indice"), ("Subíndice de transparencia", "mga_transparencia"),
                          ("Subíndice de participación", "mga_participacion")):
        filas.append({"nivel": "nacional", "unidad": "MEX", "anio": 2019, "indicador": ind, "valor": float(tot[etiqueta])})
    # 2017: promedios simples por entidad de la hoja BR
    br = pd.read_excel(copia / "mga2017_comparador_entidades.xlsx", sheet_name="BR")
    c17 = {"GA": "mga_indice", "T": "mga_transparencia", "P": "mga_participacion"}
    g = br.groupby("edo")[list(c17)].mean().reset_index()
    filas += _filas(g, "edo", c17, 2017)
    filas += [{"nivel": "nacional", "unidad": "MEX", "anio": 2017, "indicador": i, "valor": br[c].mean()}
              for c, i in c17.items()]
    return pd.DataFrame(filas)
