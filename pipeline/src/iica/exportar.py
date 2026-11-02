"""Exporta resultados para el sitio (JSON/CSV) y para el artículo (figuras PDF y cifras.tex).

Ninguna cifra del sitio ni del artículo se escribe a mano: todas salen de aquí.
"""

from __future__ import annotations

import json
import shutil

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from babel import Locale  # noqa: E402

from . import catalogo, referencias  # noqa: E402
from .catalogo import DIMENSIONES  # noqa: E402
from .descargar import ultima_copia  # noqa: E402
from .fuentes import banco_mundial  # noqa: E402
from .indice import cargar_config, cargar_panel, metadatos_indicadores, transformar  # noqa: E402
from .rutas import AMERICA_LATINA, ARTICULO, ENTIDADES, OCDE, PROCESADOS, RAIZ, SITIO_DATOS  # noqa: E402

COLORES = {1: "#001d7e", 2: "#0099d9", 3: "#b8007c", 4: "#008e45", 5: "#bd0811", 6: "#b8a600"}
NOMBRES_CORTOS = {1: "Capacidades", 2: "Int. colectiva", 3: "IA y gob. digital",
                  4: "Instituciones", 5: "Valor público", 6: "Continuidad"}
ENT_CORTO = {"05": "Coahuila", "16": "Michoacán", "30": "Veracruz", "09": "CDMX", "15": "Estado de México"}


def _leer(nombre: str, **kw) -> pd.DataFrame:
    return pd.read_csv(PROCESADOS / nombre, keep_default_na=False, na_values=[""], **kw)


def _limpio(x):
    if isinstance(x, (float, np.floating)):
        return None if np.isnan(x) else round(float(x), 4)
    if isinstance(x, np.integer):
        return int(x)
    return x


def nombres_paises() -> pd.DataFrame:
    p = banco_mundial.paises(ultima_copia("banco_mundial"))
    _, datos = json.loads((ultima_copia("banco_mundial") / "paises.json").read_text())
    iso2 = {d["id"]: d["iso2Code"] for d in datos}
    loc = Locale("es")
    p["iso2"] = p["unidad"].map(iso2)
    p["nombre_es"] = [loc.territories.get(c, n) for c, n in zip(p["iso2"], p["nombre"])]
    return p.set_index("unidad")


def _unidades(res: pd.DataFrame, nivel: str, ind_ids: list[str]) -> list[dict]:
    out = []
    if nivel == "internacional":
        nom = nombres_paises()
    for u, f in res.iterrows():
        d = {
            "id": u,
            "nombre": nom.loc[u, "nombre_es"] if nivel == "internacional" else ENTIDADES[u],
            "corto": (nom.loc[u, "nombre_es"] if nivel == "internacional" else ENT_CORTO.get(u, ENTIDADES[u])),
            "indice": _limpio(f["indice_geometrico"]),
            "aritmetico": _limpio(f["indice_aritmetico"]),
            "rango": _limpio(f["rango"]),
            "rango_p5": int(round(f["rango_p5"])),
            "rango_p95": int(round(f["rango_p95"])),
            "dims": {str(k): _limpio(f.get(f"dim_{k}")) for k in DIMENSIONES if f"dim_{k}" in f},
            "norm": {i: _limpio(f.get(f"norm_{i}")) for i in ind_ids},
            "valores": {i: _limpio(f.get(f"valor_{i}")) for i in ind_ids},
        }
        if nivel == "internacional":
            d["iso2"] = nom.loc[u, "iso2"]
            d["grupos"] = [g for g, lst in (("AL", AMERICA_LATINA), ("OCDE", OCDE)) if u in lst]
        out.append(d)
    return out


def _contexto(ids: list[str], meta: pd.DataFrame, nivel: str, unis: list[str]) -> dict:
    if not ids:
        return {}
    panel = transformar(cargar_panel(meta, ids), meta, "estatal" if nivel == "estatal" else "internacional")
    out = {}
    for i in ids:
        d = panel[(panel["indicador"] == i) & panel["unidad"].isin(unis)]
        if d.empty:
            continue
        a = int(d["anio"].max())
        ult = d[d["anio"] == a].groupby("unidad")["valor"].mean()
        out[i] = {"anio": a, **_meta_ind(meta, i), "valores": {k: _limpio(v) for k, v in ult.items()}}
    return out


def _meta_ind(meta: pd.DataFrame, i: str) -> dict:
    m = meta.loc[i]
    return {k: _limpio(m[k]) for k in ["nombre", "dimension", "capa", "sentido", "unidad_medida",
                                        "transformacion", "nota", "fuente", "fuente_nombre",
                                        "editor", "cita", "licencia"]}


def exportar_corte(nivel: str, resumen: dict, meta: pd.DataFrame, cfg: dict) -> dict:
    res = _leer(f"resultado_{nivel}.csv", dtype={"unidad": str}).set_index("unidad")
    coh = _leer(f"coherencia_{nivel}.csv")
    ids = [i["id"] for i in resumen["indicadores"]]
    unis = list(res.index)
    datos = {
        "nivel": nivel,
        "dimensiones": {str(k): v for k, v in DIMENSIONES.items()},
        "indicadores": [{**{k: _limpio(v) for k, v in i.items() if k in ("id", "anio", "winsorizados")},
                         **_meta_ind(meta, i["id"])} for i in resumen["indicadores"]],
        "dimensiones_debiles": resumen["dimensiones_debiles"],
        "dimensiones_sin_dato": resumen["dimensiones_sin_dato"],
        "unidades": _unidades(res, nivel, ids),
        "coherencia": [{k: _limpio(v) for k, v in r.items()} for r in coh.to_dict("records")],
        "contexto": _contexto(cfg.get("contexto", []), meta, nivel, unis),
    }
    if nivel == "estatal":
        mx = {}
        panel = transformar(cargar_panel(meta, ids), meta, "estatal")
        for i in ids:
            a = next(x["anio"] for x in resumen["indicadores"] if x["id"] == i)
            v = panel[(panel["indicador"] == i) & (panel["unidad"] == "MEX") & (panel["anio"] == a)]["valor"]
            mx[i] = _limpio(v.iloc[0]) if len(v) else None
        datos["nacional_valores"] = mx
    return datos


def exportar_nacional(resumen: dict, meta: pd.DataFrame) -> dict:
    res = _leer("resultado_nacional.csv")
    ids = [i["id"] for i in resumen["indicadores"]]
    serie = []
    for _, f in res.iterrows():
        serie.append({
            "anio": int(f["anio"]),
            "indice": _limpio(f["indice_geometrico"]),
            "dims": {str(k): _limpio(f.get(f"dim_{k}")) for k in DIMENSIONES if f"dim_{k}" in f},
            "valores": {i: _limpio(f.get(f"valor_{i}")) for i in ids},
            "norm": {i: _limpio(f.get(f"norm_{i}")) for i in ids},
        })
    return {"nivel": "nacional", "desde": resumen["desde"], "limites": resumen["limites"],
            "dimensiones": {str(k): v for k, v in DIMENSIONES.items()},
            "indicadores": [{"id": i, **_meta_ind(meta, i)} for i in ids], "serie": serie}


def exportar_fuentes() -> list[dict]:
    out = []
    for f in catalogo.cargar().values():
        out.append({"id": f.id, "nombre": f.nombre, "editor": f.editor, "url": f.url,
                    "licencia": f.licencia, "redistribuible": f.redistribuible, "cita": f.cita,
                    "niveles": f.niveles, "estado": f.estado, "motivo": f.motivo,
                    "descarga": f.descarga,
                    "indicadores": [{"id": i.id, "nombre": i.nombre, "dimension": i.dimension}
                                    for i in f.indicadores]})
    return out


# ---------------------------------------------------------------- figuras

def _estilo():
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8.5, "axes.spines.top": False,
                         "axes.spines.right": False, "axes.titlesize": 9.5, "figure.dpi": 150})


def fig_ranking(datos: dict, destino, resaltar: dict, alto: float):
    u = sorted([x for x in datos["unidades"] if x["indice"] is not None], key=lambda x: x["indice"])
    fig, ax = plt.subplots(figsize=(6.3, alto))
    y = np.arange(len(u))
    col = [resaltar.get(x["id"], "#9aa3c2") for x in u]
    ax.barh(y, [x["indice"] for x in u], color=col, height=0.7)
    ax.set_yticks(y, [x["corto"] for x in u])
    ax.set_xlim(0, 100)
    ax.set_xlabel("IICA parcial (0–100, media geométrica de dimensiones)")
    for yi, x in zip(y, u):
        ax.text(x["indice"] + 1, yi, f"{x['indice']:.1f}  [{x['rango_p5']:.0f}–{x['rango_p95']:.0f}]",
                va="center", fontsize=6.5, color="#4a4f63")
    ax.tick_params(axis="y", labelsize=6.8)
    fig.tight_layout()
    fig.savefig(destino)
    plt.close(fig)


def fig_perfil(series: dict[str, list[float]], colores: dict[str, str], destino, titulo=""):
    dims = list(DIMENSIONES)
    x = np.arange(len(dims))
    w = 0.8 / len(series)
    fig, ax = plt.subplots(figsize=(6.3, 2.8))
    for k, (nombre, vals) in enumerate(series.items()):
        ax.bar(x + (k - (len(series) - 1) / 2) * w, [np.nan if v is None else v for v in vals],
               width=w, label=nombre, color=colores[nombre])
    ax.set_xticks(x, [f"{d}.\n{NOMBRES_CORTOS[d]}" for d in dims], fontsize=7.5)
    ax.set_ylim(0, 100)
    ax.set_ylabel("Puntaje de dimensión (0–100)")
    ax.legend(frameon=False, fontsize=7.5, ncols=len(series))
    if titulo:
        ax.set_title(titulo)
    fig.tight_layout()
    fig.savefig(destino)
    plt.close(fig)


def fig_nacional(nac: dict, destino):
    s = pd.DataFrame([{"anio": r["anio"], "indice": r["indice"], **{f"d{k}": v for k, v in r["dims"].items()}}
                      for r in nac["serie"]]).set_index("anio")
    fig, ax = plt.subplots(figsize=(6.3, 3.0))
    for d in DIMENSIONES:
        c = f"d{d}"
        if c in s and s[c].notna().any():
            ax.plot(s.index, s[c], marker="o", ms=2.5, lw=1.3, color=COLORES[d], label=f"{d}. {NOMBRES_CORTOS[d]}")
    if s["indice"].notna().any():
        ax.plot(s.index, s["indice"], color="black", lw=2.2, label="IICA-N (agregado)")
    ax.set_ylim(0, 100)
    ax.set_ylabel("Puntaje (0–100, límites fijos)")
    ax.legend(frameon=False, fontsize=6.8, ncols=3, loc="upper center", bbox_to_anchor=(0.5, -0.12))
    fig.tight_layout()
    fig.savefig(destino)
    plt.close(fig)


def _mediana_dims(unidades: list[dict], ids: set[str] | None = None) -> list[float]:
    sel = [u for u in unidades if ids is None or u["id"] in ids]
    return [float(np.nanmedian([u["dims"].get(str(d)) if u["dims"].get(str(d)) is not None else np.nan
                                for u in sel])) for d in DIMENSIONES]


# ---------------------------------------------------------------- cifras.tex

def _macro(nombre: str, valor) -> str:
    return f"\\newcommand{{\\{nombre}}}{{{valor}}}"


def _num(x, dec=1) -> str:
    return f"{x:.{dec}f}".replace(".", "{,}")


def cifras(intl: dict, est: dict, nac: dict) -> str:
    L = ["% Generado por iica.exportar: no editar a mano."]
    pais = {u["id"]: u for u in intl["unidades"]}
    mx = pais["MEX"]
    L += [_macro("MXindice", _num(mx["indice"])), _macro("MXrango", int(mx["rango"])),
          _macro("MXrangoBajo", int(mx["rango_p5"])), _macro("MXrangoAlto", int(mx["rango_p95"])),
          _macro("NPaises", len([u for u in intl["unidades"] if u["indice"] is not None]))]
    letras = "ABCDEF"
    for d in DIMENSIONES:
        L.append(_macro(f"MXdim{letras[d-1]}", _num(mx["dims"][str(d)])))
    al = [u for u in intl["unidades"] if "AL" in u["grupos"] and u["indice"] is not None]
    al_orden = sorted(al, key=lambda u: -u["indice"])
    L.append(_macro("MXrangoAL", 1 + [u["id"] for u in al_orden].index("MEX")))
    L.append(_macro("NAL", len(al_orden)))
    ent = {u["id"]: u for u in est["unidades"]}
    for cve, n in (("08", "CHH"), ("26", "SON"), ("09", "CDMX")):
        u = ent[cve]
        L += [_macro(f"{n}indice", _num(u["indice"])), _macro(f"{n}rango", int(u["rango"])),
              _macro(f"{n}rangoBajo", int(u["rango_p5"])), _macro(f"{n}rangoAlto", int(u["rango_p95"]))]
        for d in DIMENSIONES:
            L.append(_macro(f"{n}dim{letras[d-1]}", _num(u["dims"][str(d)])))
    serie = [r for r in nac["serie"] if r["indice"] is not None]
    L += [_macro("NACprimerAnio", serie[0]["anio"]), _macro("NACprimerIndice", _num(serie[0]["indice"])),
          _macro("NACultimoAnio", serie[-1]["anio"]), _macro("NACultimoIndice", _num(serie[-1]["indice"]))]
    return "\n".join(L) + "\n"


def main() -> None:
    _estilo()
    referencias.main()
    meta = metadatos_indicadores(catalogo.cargar())
    cfg = cargar_config()
    resumen = json.loads((PROCESADOS / "resumen_niveles.json").read_text())
    SITIO_DATOS.mkdir(parents=True, exist_ok=True)
    intl = exportar_corte("internacional", resumen["internacional"], meta, cfg["internacional"])
    est = exportar_corte("estatal", resumen["estatal"], meta, cfg["estatal"])
    nac = exportar_nacional(resumen["nacional"], meta)
    for nombre, d in (("internacional", intl), ("estatal", est), ("nacional", nac),
                      ("fuentes", exportar_fuentes())):
        (SITIO_DATOS / f"{nombre}.json").write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    # CSV descargables
    pub = RAIZ / "site" / "public" / "datos"
    pub.mkdir(parents=True, exist_ok=True)
    for f in ("resultado_internacional", "resultado_estatal", "resultado_nacional",
              "coherencia_internacional", "coherencia_estatal"):
        shutil.copy(PROCESADOS / f"{f}.csv", pub / f"{f}.csv")
    # Figuras y cifras del artículo
    fig_dir = ARTICULO / "figuras"
    fig_dir.mkdir(parents=True, exist_ok=True)
    fig_ranking(intl, fig_dir / "ranking_internacional.pdf", {"MEX": "#b8007c"}, 7.6)
    fig_ranking(est, fig_dir / "ranking_estatal.pdf", {"08": "#b8007c", "26": "#0099d9"}, 5.2)
    pais = {u["id"]: u for u in intl["unidades"]}
    fig_perfil({"México": [pais["MEX"]["dims"][str(d)] for d in DIMENSIONES],
                "Mediana América Latina": _mediana_dims(intl["unidades"], set(AMERICA_LATINA)),
                "Mediana OCDE": _mediana_dims(intl["unidades"], set(OCDE))},
               {"México": "#b8007c", "Mediana América Latina": "#0099d9", "Mediana OCDE": "#001d7e"},
               fig_dir / "perfil_mexico.pdf")
    ent = {u["id"]: u for u in est["unidades"]}
    fig_perfil({"Chihuahua": [ent["08"]["dims"][str(d)] for d in DIMENSIONES],
                "Sonora": [ent["26"]["dims"][str(d)] for d in DIMENSIONES],
                "Mediana de las 32 entidades": _mediana_dims(est["unidades"])},
               {"Chihuahua": "#b8007c", "Sonora": "#0099d9", "Mediana de las 32 entidades": "#9aa3c2"},
               fig_dir / "perfil_chihuahua_sonora.pdf")
    fig_nacional(nac, fig_dir / "serie_nacional.pdf")
    (ARTICULO / "cifras.tex").write_text(cifras(intl, est, nac), encoding="utf-8")
    print("✓ exportado: site/src/data/*.json, site/public/datos/*.csv, articulo/figuras/*.pdf, articulo/cifras.tex")
