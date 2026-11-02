"""ENCIG (INEGI): tabulados básicos por entidad federativa, ediciones 2017–2025.

Representatividad: la ENCIG es representativa por entidad solo para áreas urbanas de 100 mil
habitantes y más. Se leen las estimaciones publicadas (archivos *_est.xlsx); las hojas se
localizan por su título, porque la numeración de cuadros cambia entre ediciones.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from ._inegi import bajar_inegi, confianza, filas_entidad, hoja_por_titulo, leer_hoja, nivel, ultimo_numero

BASE = "programas/encig/{a}/tabulados/{f}.xlsx"
# año -> {tema: nombre de archivo sin extensión}
ARCHIVOS_ANIO = {
    2025: {"corrupcion": "IV_corrupcion_encig2025_est",
           "confianza": "VI_confianza_institucional_encig_2025_est",
           "servicios": "II_evaluacion_servicios_bajo_demanda_encig2025_est"},
    2023: {"corrupcion": "IV_corrupcion_encig2023_est",
           "confianza": "VI_confianza_institucional_encig_2023_est",
           "servicios": "II_evaluacion_servicios_bajo_demanda_encig2023_est"},
    2021: {"corrupcion": "IV_corrupcion_encig2021_est",
           "confianza": "VI_confianza_institucional_encig_2021_est"},
    2019: {"confianza": "VI_confianza_institucional_encig_2019_est"},
    2017: {"confianza": "VI_confianza_institucional_encig2017_est"},
}

# Títulos de los cuadros (regex sobre las primeras filas de cada hoja)
T_PREVALENCIA = (r"Poblaci.n de 18 a.os y m.s que tuvo contacto con alg\S* servidor\S* p.blic\S*,? "
                 r"por entidad federativa( de residencia)? y sexo,? seg.n experiencia con alg.n acto de corrupci.n")
T_CONFIANZA = (r"Poblaci.n de 18 a.os y m.s que (habita|reside) .* por entidad federativa,? (y diversas )?"
               r"instituciones y sectores,? seg.n nivel de confianza")
T_SATISFACCION = r"Total de opiniones emitidas sobre servicios p.blicos b.sicos y bajo demanda"


def descargar(destino: Path) -> None:
    for anio, archivos in ARCHIVOS_ANIO.items():
        for f in archivos.values():
            bajar_inegi(BASE.format(a=anio, f=f), destino / f"{f}.xlsx")


def _fila(c, anio, ind, valor):
    return {"nivel": nivel(c), "unidad": c, "anio": anio, "indicador": ind, "valor": valor}


def procesar(copia: Path) -> pd.DataFrame:
    filas = []
    for anio, archivos in ARCHIVOS_ANIO.items():
        if "corrupcion" in archivos:
            ruta = copia / f"{archivos['corrupcion']}.xlsx"
            df = leer_hoja(ruta, hoja_por_titulo(ruta, T_PREVALENCIA))
            # primera fila de cada entidad = total (las siguientes son Hombres/Mujeres);
            # última columna = "Tasa por cada 100 000 habitantes"
            for c, fila in filas_entidad(df).items():
                filas.append(_fila(c, anio, "encig_prevalencia_corrupcion", ultimo_numero(fila)))
        if "confianza" in archivos:
            ruta = copia / f"{archivos['confianza']}.xlsx"
            df = leer_hoja(ruta, hoja_por_titulo(ruta, T_CONFIANZA))
            for c, v in confianza(df, r"^Gobiernos? [Ee]statal(es)?\d*$").items():
                filas.append(_fila(c, anio, "encig_confianza_gob_estatal", v))
        if "servicios" in archivos:
            ruta = copia / f"{archivos['servicios']}.xlsx"
            df = leer_hoja(ruta, hoja_por_titulo(ruta, T_SATISFACCION))
            for c, fila in filas_entidad(df).items():
                filas.append(_fila(c, anio, "encig_satisfaccion_servicios", ultimo_numero(fila)))
    out = pd.DataFrame(filas)
    n = out.groupby(["indicador", "anio"]).unidad.nunique()
    if (n != 33).any():
        raise ValueError(f"encig: cobertura incompleta\n{n[n != 33]}")
    return out
