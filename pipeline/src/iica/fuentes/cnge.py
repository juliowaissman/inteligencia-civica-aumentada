"""CNGE (INEGI): Censo Nacional de Gobiernos Estatales, ediciones 2023–2025 (módulo 1).

Datos abiertos (CSV dentro de zip) de las secciones de participación ciudadana, transparencia y
trámites, más un tabulado básico para equipo informático. Cada edición capta datos del año
anterior (CNGE 2025 -> año 2024); en `anio` se registra la edición del censo.

Los nombres de variables cambian entre ediciones; están en VARIABLES y documentados en el catálogo.
Valores especiales de los diccionarios (NA, NSS, ND, NP) se tratan como faltantes al sumar.
"""

from __future__ import annotations

import io
import re
import zipfile
from pathlib import Path

import pandas as pd

from ._inegi import bajar_inegi, nivel
from ..rutas import ENTIDADES

DA = "programas/cnge/{a}/datosabiertos/m1/{f}_csv.zip"
ZIPS = {
    2025: {"particip": "conjunto_de_datos_particip_ciudadana_cnge2025",
           "transp": "conjunto_de_datos_trans_accinfopub_protdatpers_cnge2025",
           "tramites": "conjunto_de_datos_tramite_servicio_cnge2025"},
    2024: {"particip": "particip_ciudadana_cnge2024",
           "transp": "trans_accinfopub_protdatpers_cnge2024"},
    2023: {"particip": "particip_ciudadana_cnge2023",
           "transp": "trans_accinfopub_protdatpers_cnge2023"},
}
TABULADO_TIC = ("programas/cnge/2025/tabulados/cnge2025_est_org_rec.xlsx", "cnge2025_est_org_rec.xlsx")

# Variables por edición (diccionarios de datos de cada paquete)
VARIABLES = {
    2025: dict(p1="m1s6p1", p1_ent="cve_ent", p2="m1s6p2", p2_ent="cve_ent", delib="nivein4", coges="nivein5",
               recib="m1s4p8", recib_cols=[f"mracpr{i}" for i in range(1, 14)], resp="m1s4p12", resp_ent="cve_ent"),
    2024: dict(p1="m1s6p1", p1_ent="enticve1", p2="m1s6p2", p2_ent="enticve1", delib="nincid3", coges="nincid4",
               recib="m1s4p8", recib_cols=[f"mracce{i}" for i in range(1, 14)], resp="m1s4p12", resp_ent="enticve1"),
    2023: dict(p1="m1s6p1", p1_ent="cve_entidad", p2="m1s6p2", p2_ent="enticve1", delib="nincid3", coges="nincid4",
               recib="m1s4p7", recib_cols=[f"mracce{i}" for i in range(1, 14)], resp="m1s4p11", resp_ent="enticve1"),
}
NO_ESPACIO = {"", "NO APLICA", "NA", "NSS", "ND", "NP"}


def descargar(destino: Path) -> None:
    for anio, zips in ZIPS.items():
        for f in zips.values():
            bajar_inegi(DA.format(a=anio, f=f), destino / f"{f}_csv.zip")
    bajar_inegi(TABULADO_TIC[0], destino / TABULADO_TIC[1])


def _csv(ruta_zip: Path, tabla: str) -> pd.DataFrame:
    """Lee conjunto_de_datos/<tabla>_cnge<año>.csv de un zip (tolera rutas con '\\')."""
    with zipfile.ZipFile(ruta_zip) as z:
        nombres = [n for n in z.namelist()
                   if re.search(rf"conjunto_de_datos[\\/]{tabla}_cnge\d{{4}}\.csv$", n)]
        if len(nombres) != 1:
            raise ValueError(f"{ruta_zip.name}: {tabla} -> {nombres}")
        crudo = z.read(nombres[0])
    for enc in ("utf-8-sig", "latin-1"):
        try:
            return pd.read_csv(io.BytesIO(crudo), dtype=str, encoding=enc, keep_default_na=False)
        except UnicodeDecodeError:
            continue
    raise ValueError(f"no se pudo decodificar {nombres[0]}")


def _num(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s, errors="coerce")  # NA, NSS, ND, NP -> NaN


def _norm_nombre(s: pd.Series) -> pd.Series:
    return s.str.upper().str.replace(r"\s+", " ", regex=True).str.strip()


def _participacion(zp: Path, v: dict) -> dict[str, pd.Series]:
    p1 = _csv(zp, v["p1"]).set_index(v["p1_ent"])["rnsnni1"].astype(int)
    apertura = p1.map({1: 1.0, 2: 0.0})  # 9, 96–98 -> NaN
    p2 = _csv(zp, v["p2"])
    p2 = p2.assign(ent=p2[v["p2_ent"]], esp=_norm_nombre(p2["nombre1"]))
    p2 = p2[~p2["esp"].isin(NO_ESPACIO)]
    # Un registro = espacio x tema. Se cuenta cada espacio una vez (mismo nombre en la entidad).
    espacios = p2.groupby("ent")["esp"].nunique()
    p2["dc"] = (p2[v["delib"]] == "1") | (p2[v["coges"]] == "1")
    delib = p2[p2["dc"]].groupby("ent")["esp"].nunique()
    idx = apertura.index
    return {
        "cnge_apertura_participacion": apertura,
        "cnge_espacios_participacion": espacios.reindex(idx).fillna(0).where(apertura.notna()),
        "cnge_espacios_deliberacion_cogestion": delib.reindex(idx).fillna(0).where(apertura.notna()),
        "cnge_registros_espacio_tema": p2.groupby("ent").size().reindex(idx).fillna(0).where(apertura.notna()),
    }


def _transparencia(zt: Path, v: dict) -> dict[str, pd.Series]:
    r = _csv(zt, v["recib"])
    ent = "cve_ent" if "cve_ent" in r.columns else "enticve1"
    recib = r[v["recib_cols"]].apply(_num).sum(axis=1).groupby(r[ent]).sum()
    s = _csv(zt, v["resp"])
    resp = _num(s["plares1"]).groupby(s[v["resp_ent"]]).sum()
    return {"cnge_solicitudes_info_recibidas": recib, "cnge_solicitudes_info_respondidas": resp}


def _tramites(zr: Path) -> dict[str, pd.Series]:
    t = _csv(zr, "m1s2p1")  # 24 tipos de trámite/servicio del catálogo tramitse_r por entidad
    ofrecido = t["rnsnni1"] == "1"
    linea = ofrecido & (t["medpre2"] == "1")
    transac = ofrecido & (t["sewebt3"] == "1")
    g = t.assign(of=ofrecido, li=linea, tr=transac).groupby("cve_ent")
    return {"cnge_tramites_ofrecidos": g["of"].sum().astype(float),
            "cnge_tramites_medios_electronicos": g["li"].sum().astype(float),
            "cnge_tramites_transaccionales": g["tr"].sum().astype(float)}


def _computadoras(ruta: Path) -> pd.Series:
    df = pd.read_excel(ruta, sheet_name="10", header=None)
    titulo = " ".join(str(x) for x in df.iloc[:5, 0] if isinstance(x, str))
    if "Equipo informático" not in titulo or str(df.iat[4, 4]).strip() != "Computadoras":
        raise ValueError("tabulado CNGE 2025 hoja 10: estructura inesperada")
    est = df[df[0].astype(str).str.strip() == "Estatal"]
    return pd.Series(_num(est[4]).values, index=est[2].astype(str).str.zfill(2))


SUMA_NACIONAL = {"cnge_espacios_participacion", "cnge_espacios_deliberacion_cogestion",
                 "cnge_registros_espacio_tema", "cnge_solicitudes_info_recibidas",
                 "cnge_solicitudes_info_respondidas", "cnge_computadoras"}


def procesar(copia: Path) -> pd.DataFrame:
    filas = []
    for anio, zips in ZIPS.items():
        v = VARIABLES[anio]
        series = {}
        series.update(_participacion(copia / f"{zips['particip']}_csv.zip", v))
        series.update(_transparencia(copia / f"{zips['transp']}_csv.zip", v))
        if "tramites" in zips:
            series.update(_tramites(copia / f"{zips['tramites']}_csv.zip"))
        if anio == 2025:
            series["cnge_computadoras"] = _computadoras(copia / TABULADO_TIC[1])
        for ind, s in series.items():
            s = s[s.index.isin(ENTIDADES)]
            if len(s) != 32:
                raise ValueError(f"cnge {anio} {ind}: {len(s)} entidades")
            for c, val in s.items():
                filas.append({"nivel": "estatal", "unidad": c, "anio": anio, "indicador": ind, "valor": val})
            if ind in SUMA_NACIONAL:
                filas.append({"nivel": nivel("MEX"), "unidad": "MEX", "anio": anio, "indicador": ind,
                              "valor": s.sum(min_count=32)})
    return pd.DataFrame(filas)
