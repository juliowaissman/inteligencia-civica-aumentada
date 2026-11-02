"""Calcula los IICA parciales (internacional, nacional y estatal) según `niveles.yaml`."""

from __future__ import annotations

import json

import numpy as np
import pandas as pd
import yaml

from . import catalogo, metodo
from .descargar import ultima_copia
from .rutas import AMERICA_LATINA, ENTIDADES, OCDE, PIPELINE, PROCESADOS

GRUPOS = {"america_latina": AMERICA_LATINA, "ocde": OCDE}


def cargar_config() -> dict:
    return yaml.safe_load((PIPELINE / "niveles.yaml").read_text(encoding="utf-8"))


def metadatos_indicadores(fuentes) -> pd.DataFrame:
    filas = []
    for f in fuentes.values():
        for i in f.indicadores:
            filas.append({"indicador": i.id, "nombre": i.nombre, "dimension": i.dimension,
                          "capa": i.capa, "sentido": i.sentido, "unidad_medida": i.unidad,
                          "transformacion": i.transformacion, "nota": i.nota,
                          "fuente": f.id, "fuente_nombre": f.nombre, "editor": f.editor,
                          "cita": f.cita, "licencia": f.licencia, "estado": f.estado})
    return pd.DataFrame(filas).set_index("indicador")


def cargar_panel(meta: pd.DataFrame, ids: list[str]) -> pd.DataFrame:
    fuentes = meta.loc[ids, "fuente"].unique()
    partes = [pd.read_csv(PROCESADOS / f"{f}.csv", dtype={"unidad": str}, keep_default_na=False, na_values=[""]) for f in fuentes]
    panel = pd.concat(partes)
    return panel[panel["indicador"].isin(ids)]


def poblacion(nivel: str) -> pd.DataFrame:
    if nivel == "estatal":
        p = pd.read_csv(PROCESADOS / "conapo_poblacion.csv", dtype={"unidad": str}, keep_default_na=False, na_values=[""])
        return p[p["indicador"] == "poblacion_total"][["unidad", "anio", "valor"]].rename(
            columns={"valor": "poblacion"})
    from .fuentes import banco_mundial
    return banco_mundial.poblacion(ultima_copia("banco_mundial"))


def transformar(panel: pd.DataFrame, meta: pd.DataFrame, nivel: str) -> pd.DataFrame:
    por_hab = [i for i in panel["indicador"].unique() if meta.loc[i, "transformacion"] == "por_100k"]
    if not por_hab:
        return panel
    pob = poblacion(nivel).sort_values("anio")
    m = panel["indicador"].isin(por_hab)
    # Población del mismo año o, si aún no se publica, del año disponible más reciente.
    sub = pd.merge_asof(panel[m].sort_values("anio"), pob.rename(columns={"anio": "anio_pob"}),
                        left_on="anio", right_on="anio_pob", by="unidad", direction="backward")
    sub = sub.dropna(subset=["poblacion"])  # unidades sin población quedan sin tasa
    sub["valor"] = sub["valor"] / sub["poblacion"] * 100_000
    return pd.concat([panel[~m], sub.drop(columns=["poblacion", "anio_pob"])])


def unidades(cfg: dict, nivel: str) -> list[str]:
    if nivel == "estatal":
        return list(ENTIDADES)
    u = set()
    for g in cfg["comparacion"]:
        u |= set(GRUPOS[g])
    return sorted(u)


def corte(panel: pd.DataFrame, ids: list[str], unis: list[str], cfg: dict):
    """Para cada indicador, el año más reciente (≤ anio_maximo) con cobertura suficiente."""
    cols, anios = {}, {}
    for i in ids:
        d = panel[(panel["indicador"] == i) & panel["unidad"].isin(unis)
                  & (panel["anio"] <= cfg["anio_maximo"])]
        cobertura = d.groupby("anio")["unidad"].nunique() / len(unis)
        validos = cobertura[cobertura >= cfg["cobertura_minima"]]
        if validos.empty:
            anios[i] = None
            continue
        a = int(validos.index.max())
        anios[i] = a
        cols[i] = d[d["anio"] == a].groupby("unidad")["valor"].mean()
    crudo = pd.DataFrame(cols).reindex(unis)
    return crudo, anios


def evaluar(crudo: pd.DataFrame, meta: pd.DataFrame, limites: dict | None = None,
            completa: bool = False):
    """Normaliza y agrega. Sin límites fijos, primero se tratan los atípicos (regla JRC-COIN)."""
    tratados, winsor = {}, {}
    for c in crudo.columns:
        if limites:
            tratados[c], winsor[c] = crudo[c], 0
        else:
            tratados[c], winsor[c] = metodo.tratar_atipicos(crudo[c])
    norm = pd.DataFrame({
        c: metodo.normalizar(tratados[c], int(meta.loc[c, "sentido"]),
                             *(limites[c] if limites else (None, None)))
        for c in crudo.columns
    })
    dim_de = {c: int(meta.loc[c, "dimension"]) for c in crudo.columns}
    dims = metodo.puntajes_dimension(norm, dim_de, completa=completa)
    return norm, dims, dim_de, winsor


def calcular_corte(nivel: str, cfg: dict, meta: pd.DataFrame) -> dict:
    ids = cfg["indicadores"]
    unis = unidades(cfg, nivel)
    panel = transformar(cargar_panel(meta, ids), meta, nivel)
    crudo, anios = corte(panel, ids, unis, cfg)
    sin_dato = [i for i, a in anios.items() if a is None]
    norm, dims, dim_de, winsor = evaluar(crudo, meta)
    geo = metodo.geometrica(dims)
    ari = metodo.aritmetica(dims)
    sens = metodo.sensibilidad(dims)
    pob = None
    if nivel == "estatal":
        p = poblacion("estatal")
        pob = p[p["anio"] == p["anio"].max()].set_index("unidad")["poblacion"]
    coh = metodo.coherencia(norm, dims, geo, dim_de, pob)

    res = pd.DataFrame({"indice_geometrico": geo, "indice_aritmetico": ari,
                        "rango": metodo.rangos(geo)}).join(sens)
    res = res.join(dims.add_prefix("dim_")).join(norm.add_prefix("norm_")).join(crudo.add_prefix("valor_"))
    res.index.name = "unidad"
    res.to_csv(PROCESADOS / f"resultado_{nivel}.csv")
    coh.to_csv(PROCESADOS / f"coherencia_{nivel}.csv", index=False)

    dims_presentes = sorted(dims.columns.tolist())
    return {
        "nivel": nivel,
        "unidades": unis,
        "indicadores": [{"id": i, "anio": anios[i], "winsorizados": winsor.get(i, 0), **_meta_json(meta, i)}
                        for i in ids],
        "sin_dato": sin_dato,
        "dimensiones_con_dato": dims_presentes,
        "dimensiones_sin_dato": [d for d in catalogo.DIMENSIONES if d not in dims_presentes],
        "dimensiones_debiles": [d for d in dims_presentes
                                if sum(1 for c in crudo.columns if dim_de[c] == d) < 2],
    }


def calcular_nacional(cfg: dict, meta: pd.DataFrame) -> dict:
    """Serie de México con límites fijos (min-max del panel de comparación en todo el periodo)."""
    ids = cfg["indicadores"]
    unis = unidades(cfg, "nacional")
    panel = transformar(cargar_panel(meta, ids), meta, "internacional")
    panel = panel[panel["unidad"].isin(unis) & panel["anio"].between(cfg["desde"], cfg["anio_maximo"])]
    limites = {}
    for i in ids:
        v = panel[panel["indicador"] == i]["valor"].reset_index(drop=True)
        v, _ = metodo.tratar_atipicos(v)
        limites[i] = (v.min(), v.max())
    mx = panel[panel["unidad"] == "MEX"].pivot_table(index="anio", columns="indicador", values="valor")
    anios = range(cfg["desde"], int(mx.index.max()) + 1)
    # Las series bienales (ONU) se arrastran un año; una dimensión solo se calcula
    # en los años en que todos sus indicadores tienen dato (composición constante).
    mx = mx.reindex(index=anios, columns=ids)
    bienales = [i for i in ids if meta.loc[i, "fuente"] in cfg.get("bienales", [])]
    mx[bienales] = mx[bienales].ffill(limit=1)
    mx = mx.loc[: mx.dropna(how="all", subset=[i for i in ids if i not in bienales]).index.max()]
    norm, dims, dim_de, _ = evaluar(mx, meta, limites, completa=True)
    dims = dims.dropna(how="all")
    norm, mx = norm.loc[dims.index], mx.loc[dims.index]
    res = pd.DataFrame({"indice_geometrico": metodo.geometrica(dims)}).join(dims.add_prefix("dim_"))
    res = res.join(norm.add_prefix("norm_")).join(mx.add_prefix("valor_"))
    res.index.name = "anio"
    res.to_csv(PROCESADOS / "resultado_nacional.csv")
    return {"nivel": "nacional", "desde": cfg["desde"], "limites": {k: list(map(float, v)) for k, v in limites.items()},
            "indicadores": [{"id": i, **_meta_json(meta, i)} for i in ids]}


def _meta_json(meta: pd.DataFrame, i: str) -> dict:
    m = meta.loc[i]
    return {k: (None if (isinstance(v, float) and np.isnan(v)) else (int(v) if isinstance(v, np.integer) else v))
            for k, v in m.items()}


def main() -> None:
    fuentes = catalogo.cargar()
    meta = metadatos_indicadores(fuentes)
    cfg = cargar_config()
    resumen = {}
    for nivel in ("internacional", "estatal"):
        if cfg.get(nivel, {}).get("indicadores"):
            resumen[nivel] = calcular_corte(nivel, cfg[nivel], meta)
            print(f"✓ {nivel}: {len(resumen[nivel]['indicadores'])} indicadores")
    if cfg.get("nacional", {}).get("indicadores"):
        resumen["nacional"] = calcular_nacional(cfg["nacional"], meta)
        print("✓ nacional")
    (PROCESADOS / "resumen_niveles.json").write_text(
        json.dumps(resumen, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
