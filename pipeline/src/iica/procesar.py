"""Convierte las copias crudas en una tabla larga común y resume la cobertura.

Cada módulo `iica.fuentes.<id>` define `procesar(copia: Path) -> pd.DataFrame`
con columnas: nivel, unidad, anio, indicador, valor.
  - nivel: internacional | nacional | estatal
  - unidad: ISO3 (países) o clave INEGI de 2 dígitos (entidades)
  - indicador: id declarado en el catálogo de la fuente
"""

from __future__ import annotations

import importlib

import pandas as pd

from .catalogo import Fuente
from .descargar import ultima_copia
from .rutas import ENTIDADES, PROCESADOS

COLUMNAS = ["nivel", "unidad", "anio", "indicador", "valor"]


def procesar_fuente(fuente: Fuente) -> pd.DataFrame:
    copia = ultima_copia(fuente.id)
    if copia is None:
        raise RuntimeError(f"{fuente.id}: no hay copia descargada")
    mod = importlib.import_module(f"iica.fuentes.{fuente.id}")
    df = mod.procesar(copia)
    faltan = set(COLUMNAS) - set(df.columns)
    if faltan:
        raise ValueError(f"{fuente.id}: faltan columnas {faltan}")
    declarados = {i.id for i in fuente.indicadores}
    extra = set(df["indicador"]) - declarados
    if extra:
        raise ValueError(f"{fuente.id}: indicadores no declarados en el catálogo {extra}")
    df = df[COLUMNAS].dropna(subset=["valor"]).copy()
    df["anio"] = df["anio"].astype(int)
    df["valor"] = df["valor"].astype(float)
    df["fuente"] = fuente.id
    PROCESADOS.mkdir(parents=True, exist_ok=True)
    df.to_csv(PROCESADOS / f"{fuente.id}.csv", index=False)
    return df


def cobertura(fuentes: dict[str, Fuente], tablas: dict[str, pd.DataFrame]) -> pd.DataFrame:
    filas = []
    for f in fuentes.values():
        df = tablas.get(f.id)
        for ind in f.indicadores:
            fila = {
                "fuente": f.id,
                "indicador": ind.id,
                "nombre": ind.nombre,
                "dimension": ind.dimension,
                "capa": ind.capa,
                "estado_fuente": f.estado,
            }
            if df is None or df.empty:
                fila.update(niveles="", anios="", n_paises=0, n_entidades=0, mexico="sin información")
            else:
                d = df[df["indicador"] == ind.id]
                anios = sorted(d["anio"].unique())
                intl = d[d["nivel"] == "internacional"]
                est = d[d["nivel"] == "estatal"]
                mx = d[(d["unidad"] == "MEX")]
                fila.update(
                    niveles=",".join(sorted(d["nivel"].unique())),
                    anios=f"{anios[0]}–{anios[-1]}" if anios else "",
                    n_paises=intl["unidad"].nunique(),
                    n_entidades=est["unidad"].nunique(),
                    mexico="sí" if not mx.empty else "sin información",
                    entidades_completas="sí" if set(est["unidad"]) >= set(ENTIDADES) else "no",
                )
            filas.append(fila)
    out = pd.DataFrame(filas)
    if len(fuentes) > 1:  # solo la corrida completa escribe el resumen
        out.to_csv(PROCESADOS / "cobertura.csv", index=False)
    return out
