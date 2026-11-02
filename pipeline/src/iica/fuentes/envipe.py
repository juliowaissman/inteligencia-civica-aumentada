"""ENVIPE (INEGI): confianza en autoridades por entidad federativa, ediciones 2020–2025.

Se usa el tabulado básico "VI. Desempeño institucional" (estimaciones), cuadro "Población de 18
años y más que identifica a las autoridades de seguridad pública por entidad federativa y tipo de
autoridad según nivel de confianza en la misma" (6.4 en 2020–2022, 6.5 en 2023, 6.20 en 2024–2025).
La hoja se localiza por su título.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from ._inegi import bajar_inegi, confianza, hoja_por_titulo, leer_hoja, nivel

RUTAS = {
    2020: "programas/envipe/2020/Tabulados/vi_desempeno_institucional_2020_est.xlsx",
    **{a: f"programas/envipe/{a}/tabulados/VI_desempeno_institucional_{a}_est.xlsx"
       for a in (2021, 2022, 2023, 2024, 2025)},
}
TITULO = (r"Poblaci.n de 18 a.os y m.s que identifica a las autoridades de seguridad p.blica "
          r"por entidad federativa y tipo de autoridad,? seg.n nivel de confianza")
AUTORIDADES = {
    "envipe_confianza_policia_estatal": r"^Polic.a Estatal\d*$",
    "envipe_confianza_mp_fiscalia_estatal": r"^Ministerio P.blico \(MP\) y (Fiscal.as|Procuradur.as) Estatales\d*$",
    "envipe_confianza_jueces": r"^Jueces\d*$",
}


def descargar(destino: Path) -> None:
    for anio, ruta in RUTAS.items():
        bajar_inegi(ruta, destino / f"VI_desempeno_institucional_{anio}_est.xlsx")


def procesar(copia: Path) -> pd.DataFrame:
    filas = []
    for anio in RUTAS:
        ruta = copia / f"VI_desempeno_institucional_{anio}_est.xlsx"
        df = leer_hoja(ruta, hoja_por_titulo(ruta, TITULO))
        for ind, patron in AUTORIDADES.items():
            vals = confianza(df, patron)
            if len(vals) != 33:
                raise ValueError(f"envipe {anio} {ind}: {len(vals)} unidades (se esperaban 33)")
            filas += [{"nivel": nivel(c), "unidad": c, "anio": anio, "indicador": ind, "valor": v}
                      for c, v in vals.items()]
    return pd.DataFrame(filas)
