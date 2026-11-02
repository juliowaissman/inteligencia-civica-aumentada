"""Funciones puras de la metodología (Manual OCDE/JRC de indicadores compuestos).

- Normalización min-max a 0–100, invirtiendo los indicadores donde más es peor.
- Puntaje de dimensión: promedio simple de sus indicadores normalizados.
- Índice principal: media geométrica de las dimensiones (no compensatoria).
  Para evitar que un cero anule el producto, las dimensiones se reescalan
  de [0, 100] a [1, 100] solo dentro de la media geométrica.
- Sensibilidad: media aritmética y pesos aleatorios (Dirichlet) → intervalo de rangos.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def tratar_atipicos(s: pd.Series, max_valores: int = 5) -> tuple[pd.Series, int]:
    """Regla JRC-COIN: si |asimetría| > 2 y curtosis > 3.5, winsorizar (hasta 5 valores).

    Se recortan los valores extremos del lado de la asimetría al siguiente valor,
    uno por uno, hasta que la distribución deja de cumplir la regla.
    Devuelve la serie tratada y el número de valores winsorizados.
    """
    x = s.copy()
    n = 0
    while n < max_valores:
        v = x.dropna()
        if len(v) < 8 or not (abs(v.skew()) > 2 and v.kurt() > 3.5):
            break
        if v.skew() > 0:
            orden = v.sort_values(ascending=False)
            x[orden.index[: n + 1]] = orden.iloc[n + 1]
        else:
            orden = v.sort_values()
            x[orden.index[: n + 1]] = orden.iloc[n + 1]
        n += 1
    return x, n


def normalizar(s: pd.Series, sentido: int = 1, minimo: float | None = None,
               maximo: float | None = None) -> pd.Series:
    lo = s.min() if minimo is None else minimo
    hi = s.max() if maximo is None else maximo
    if hi == lo:
        return pd.Series(np.where(s.notna(), 100.0, np.nan), index=s.index)
    z = (s - lo) / (hi - lo) * 100
    z = z.clip(0, 100)
    return 100 - z if sentido == -1 else z


def puntajes_dimension(norm: pd.DataFrame, dim_de: dict[str, int], completa: bool = False) -> pd.DataFrame:
    """norm: filas = unidades, columnas = indicadores normalizados.

    completa=True exige todos los indicadores de la dimensión (si falta uno, NaN).
    """
    out = {}
    for d in sorted(set(dim_de.values())):
        cols = [c for c in norm.columns if dim_de.get(c) == d]
        if cols:
            out[d] = norm[cols].mean(axis=1, skipna=not completa)
    return pd.DataFrame(out)


def geometrica(dims: pd.DataFrame, pesos: np.ndarray | None = None) -> pd.Series:
    """Media geométrica ponderada; NaN si falta alguna dimensión."""
    k = dims.shape[1]
    w = np.full(k, 1 / k) if pesos is None else np.asarray(pesos) / np.sum(pesos)
    x = 1 + dims.to_numpy() * 0.99  # [0,100] -> [1,100]
    vals = np.exp(np.log(x) @ w)
    vals[np.isnan(dims.to_numpy()).any(axis=1)] = np.nan
    return pd.Series(vals, index=dims.index)


def aritmetica(dims: pd.DataFrame, pesos: np.ndarray | None = None) -> pd.Series:
    k = dims.shape[1]
    w = np.full(k, 1 / k) if pesos is None else np.asarray(pesos) / np.sum(pesos)
    vals = dims.to_numpy() @ w
    vals[np.isnan(dims.to_numpy()).any(axis=1)] = np.nan
    return pd.Series(vals, index=dims.index)


def rangos(s: pd.Series) -> pd.Series:
    return s.rank(ascending=False, method="min")


def sensibilidad(dims: pd.DataFrame, n: int = 1000, semilla: int = 2026) -> pd.DataFrame:
    """Intervalo de rangos (p5–p95) con pesos aleatorios y ambos tipos de agregación."""
    dims = dims.dropna()
    rng = np.random.default_rng(semilla)
    k = dims.shape[1]
    todos = []
    for _ in range(n):
        w = rng.dirichlet(np.ones(k))
        for f in (geometrica, aritmetica):
            todos.append(rangos(f(dims, w)))
    r = pd.concat(todos, axis=1)
    return pd.DataFrame({
        "rango_p5": r.quantile(0.05, axis=1),
        "rango_mediana": r.median(axis=1),
        "rango_p95": r.quantile(0.95, axis=1),
    })


def coherencia(norm: pd.DataFrame, dims: pd.DataFrame, indice: pd.Series,
               dim_de: dict[str, int], poblacion: pd.Series | None = None) -> pd.DataFrame:
    """Correlaciones (Pearson) con su dimensión y con el índice, más alertas JRC-COIN."""
    filas = []
    for c in norm.columns:
        d = dim_de[c]
        r_dim = norm[c].corr(dims[d]) if d in dims else np.nan
        r_ind = norm[c].corr(indice)
        alerta = []
        if r_ind > 0.95:
            alerta.append("domina el índice (r>0.95)")
        if abs(r_ind) < 0.3:
            alerta.append("subrepresentado (|r|<0.3)")
        if r_ind < -0.3:
            alerta.append("relación negativa (r<-0.3)")
        fila = {"indicador": c, "dimension": d, "r_dimension": r_dim, "r_indice": r_ind,
                "alerta": "; ".join(alerta)}
        if poblacion is not None:
            fila["r_poblacion"] = norm[c].corr(poblacion.reindex(norm.index))
        filas.append(fila)
    return pd.DataFrame(filas)
