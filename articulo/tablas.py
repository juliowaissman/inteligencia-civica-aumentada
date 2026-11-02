"""Genera tablas LaTeX y cifras adicionales del artículo a partir de los JSON del pipeline.

Uso (desde articulo/):  uv run --project ../pipeline python tablas.py
Ningún número del artículo se escribe a mano: sale de cifras.tex (pipeline) o de aquí.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import yaml

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent
DATOS = RAIZ / "site" / "src" / "data"
SALIDA = AQUI / "tablas"
SALIDA.mkdir(exist_ok=True)

AL = {"ARG", "BOL", "BRA", "CHL", "COL", "CRI", "CUB", "DOM", "ECU", "SLV", "GTM", "HND", "MEX",
      "NIC", "PAN", "PRY", "PER", "URY", "VEN", "HTI", "JAM", "TTO"}
CORTO = {1: "Capacidades cívicas y humanas", 2: "Inteligencia colectiva",
         3: "Integración ética de la IA y gobierno digital", 4: "Instituciones habilitadoras y cocreación",
         5: "Valor público democrático", 6: "Continuidad y retroalimentación"}
CAPAS = {"instalada": "Capacidad instalada", "activacion": "Activación", "resultado": "Resultado emergente"}
LETRAS = "ABCDEF"


def esc(t: str) -> str:
    for a, b in (("\\", r"\textbackslash{}"), ("&", r"\&"), ("%", r"\%"), ("_", r"\_"), ("#", r"\#"),
                 ("$", r"\$"), ("~", r"\textasciitilde{}"), ("^", r"\textasciicircum{}")):
        t = t.replace(a, b)
    return t


def num(x, dec=1) -> str:
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return "s.\\,d."
    s = f"{x:,.{dec}f}"
    return s.replace(",", "\\,").replace(".", "{,}")


def macro(n, v) -> str:
    return f"\\newcommand{{\\{n}}}{{{v}}}"


def cargar(n):
    return json.loads((DATOS / f"{n}.json").read_text(encoding="utf-8"))


intl, est, nac = cargar("internacional"), cargar("estatal"), cargar("nacional")
fuentes = cargar("fuentes")


def dec_para(v):
    if v is None:
        return 1
    a = abs(v)
    return 3 if a < 2 else (1 if a < 1000 else 0)


CORTA = {"banco_mundial": "Banco Mundial", "vdem": "V-Dem v16", "github_innovation": "GitHub IG",
         "girai": "GIRAI 2026", "dsp": "DSP v8", "onu_egov": "ONU E-Gov", "wjp": "WJP", "gii": "GII (OMPI)",
         "endutih": "ENDUTIH", "anuies": "ANUIES", "osc": "Reg. Fed. OSC", "cnge": "CNGE", "mga": "MGA",
         "ine_participacion": "INE", "encig": "ENCIG", "sni": "SNII", "denue": "DENUE", "impi": "IMPI"}


def tabla_indicadores(datos, destino, columnas_valor, titulo, etiqueta):
    claves = sorted({i["cita"] for i in datos["indicadores"]})
    titulo = titulo + r" Fuentes: \parencite{" + ",".join(claves) + "}."
    unis = {u["id"]: u for u in datos["unidades"]}
    cab = " & ".join(n for n, _ in columnas_valor)
    L = [r"{\footnotesize", r"\begin{longtable}{@{}p{0.4cm}" + r">{\raggedright\arraybackslash}" + f"p{{{7.0 - 0.75 * len(columnas_valor):.2f}cm}}" + r">{\raggedright\arraybackslash}p{1.8cm}p{0.7cm}" + "r" * len(columnas_valor) + "@{}}",
         rf"\caption{{{titulo}}}\label{{{etiqueta}}}\\", r"\toprule",
         rf"D. & Indicador & Fuente & Año & {cab}\\", r"\midrule", r"\endfirsthead",
         r"\toprule", rf"D. & Indicador & Fuente & Año & {cab}\\", r"\midrule", r"\endhead",
         r"\bottomrule", r"\endfoot"]
    for i in datos["indicadores"]:
        nombre = esc(i["nombre"])
        if i["transformacion"] == "por_100k":
            nombre += " [por 100 mil hab.]"
        if i["sentido"] == -1:
            nombre += " ($-$)"
        crudos = [datos["nacional_valores"].get(i["id"]) if u == "NAC" else unis[u]["valores"].get(i["id"])
                  for _, u in columnas_valor]
        m = max((abs(v) for v in crudos if v is not None), default=0)
        dec = 2 if m < 2 else (1 if m < 1000 else 0)
        vals = [num(v, dec) for v in crudos]
        L.append(rf"{i['dimension']} & {nombre} & {CORTA.get(i['fuente'], esc(i['fuente']))} & {i['anio']} & " + " & ".join(vals) + r"\\")
    L += [r"\end{longtable}", "}"]
    (SALIDA / destino).write_text("\n".join(L) + "\n", encoding="utf-8")


tabla_indicadores(intl, "indicadores_internacional.tex", [("México", "MEX")],
                  "Indicadores del IICA-I (internacional), año utilizado y valor de México en su escala original. "
                  "($-$): menor es mejor. Los conteos se expresan por 100 mil habitantes.", "tab:ind-intl")
tabla_indicadores(est, "indicadores_estatal.tex", [("Nacional", "NAC"), ("Chih.", "08"), ("Son.", "26")],
                  "Indicadores del IICA-E (estatal), año utilizado y valores nacional, de Chihuahua y de Sonora "
                  "en su escala original (s.\\,d.: sin dato publicado en ese nivel).", "tab:ind-est")

# --- Cobertura por dimensión y capa
nac_ids = {i["id"] for i in nac["indicadores"]}
filas = []
for d in range(1, 7):
    celdas = []
    for datos in (intl, est):
        for c in CAPAS:
            n = sum(1 for i in datos["indicadores"] if i["dimension"] == d and i["capa"] == c)
            celdas.append(str(n) if n else r"\textemdash")
    n_nac = sum(1 for i in nac["indicadores"] if i["dimension"] == d)
    celdas.append(str(n_nac) if n_nac else r"\textemdash")
    filas.append(rf"{d}. {CORTO[d]} & " + " & ".join(celdas) + r"\\")
cob = [r"\begin{table}[htbp]\centering\footnotesize",
       r"\caption{Cobertura: número de indicadores por dimensión, capa y nivel. Ningún nivel tiene indicadores de "
       r"resultados emergentes; las celdas vacías no se imputan.}\label{tab:cobertura}",
       r"\begin{tabular}{@{}p{5.2cm}cccccc c@{}}", r"\toprule",
       r" & \multicolumn{3}{c}{IICA-I} & \multicolumn{3}{c}{IICA-E} & IICA-N\\",
       r"\cmidrule(lr){2-4}\cmidrule(lr){5-7}",
       r"Dimensión & Inst. & Activ. & Result. & Inst. & Activ. & Result. & Total\\", r"\midrule",
       *filas, r"\bottomrule", r"\end{tabular}", r"\end{table}"]
(SALIDA / "cobertura.tex").write_text("\n".join(cob) + "\n", encoding="utf-8")

# --- Coherencia (alertas)
def tabla_coherencia(datos, destino, titulo, etiqueta, poblacion=False):
    nombres = {i["id"]: i["nombre"] for i in datos["indicadores"]}
    cols = r"p{0.4cm}>{\raggedright\arraybackslash}p{6.0cm}rr" + ("r" if poblacion else "") + r">{\raggedright\arraybackslash}p{2.6cm}"
    cab = r"D. & Indicador & $r$ dim. & $r$ índice" + (r" & $r$ pob." if poblacion else "") + r" & Alerta\\"
    L = [r"\begin{table}[htbp]\centering\scriptsize", rf"\caption{{{titulo}}}\label{{{etiqueta}}}",
         rf"\begin{{tabular}}{{@{{}}{cols}@{{}}}}", r"\toprule", cab, r"\midrule"]
    for r in datos["coherencia"]:
        fila = [str(r["dimension"]), esc(nombres[r["indicador"]]), num(r["r_dimension"], 2), num(r["r_indice"], 2)]
        if poblacion:
            fila.append(num(r.get("r_poblacion"), 2))
        alerta = (r["alerta"] or "").replace("domina el índice (r>0.95)", "domina el índice")
        alerta = alerta.replace("subrepresentado (|r|<0.3)", "subrepresentado").replace("relación negativa (r<-0.3)", "relación negativa")
        fila.append(esc(alerta))
        L.append(" & ".join(fila) + r"\\")
    L += [r"\bottomrule", r"\end{tabular}", r"\end{table}"]
    (SALIDA / destino).write_text("\n".join(L) + "\n", encoding="utf-8")


tabla_coherencia(intl, "coherencia_internacional.tex",
                 "Coherencia estadística del IICA-I: correlación de Pearson de cada indicador normalizado con su "
                 "dimensión y con el índice. Alertas según los umbrales de JRC-COIN.", "tab:coh-intl")
tabla_coherencia(est, "coherencia_estatal.tex",
                 "Coherencia estadística del IICA-E. La última columna numérica es la correlación con la población "
                 "(sesgo de tamaño si $r>0{,}6$).", "tab:coh-est", poblacion=True)

# --- Tabla de entidades (todas)
filas = []
for u in sorted(est["unidades"], key=lambda u: u["rango"]):
    nombre = esc(u["nombre"])
    if u["id"] in ("08", "26"):
        nombre = rf"\textbf{{{nombre}}}"
    dims = " & ".join(num(u["dims"][str(d)]) for d in range(1, 7))
    filas.append(rf"{int(u['rango'])} & {nombre} & {num(u['indice'])} & {int(u['rango_p5'])}--{int(u['rango_p95'])} & {dims}\\")
tab = [r"{\scriptsize", r"\begin{longtable}{@{}rp{4.2cm}rcrrrrrr@{}}",
       r"\caption{IICA-E por entidad federativa: índice (media geométrica), intervalo de rangos p5--p95 del "
       r"análisis de sensibilidad y puntajes por dimensión (0--100).}\label{tab:entidades}\\",
       r"\toprule", r"Lugar & Entidad & IICA-E & Rango p5--p95 & D1 & D2 & D3 & D4 & D5 & D6\\", r"\midrule",
       r"\endfirsthead", r"\toprule", r"Lugar & Entidad & IICA-E & Rango p5--p95 & D1 & D2 & D3 & D4 & D5 & D6\\",
       r"\midrule", r"\endhead", r"\bottomrule", r"\endfoot", *filas, r"\end{longtable}", "}"]
(SALIDA / "entidades.tex").write_text("\n".join(tab) + "\n", encoding="utf-8")

# --- Cifras adicionales
C = ["% Generado por tablas.py: no editar a mano."]
verificadas = [f for f in fuentes if f["estado"] == "verificada"]
candidatas = [f for f in fuentes if f["estado"] == "candidata"]
C += [macro("NFuentesVerificadas", len(verificadas)), macro("NFuentesCandidatas", len(candidatas)),
      macro("NFuentesTotal", len(fuentes)),
      macro("NIndIntl", len(intl["indicadores"])), macro("NIndEst", len(est["indicadores"])),
      macro("NIndNac", len(nac["indicadores"])),
      macro("NAbiertasVerif", sum(1 for f in verificadas if f["redistribuible"]))]
lic_cerradas = sorted({f["id"] for f in verificadas if not f["redistribuible"]})
C.append(macro("NNoRedistrib", len(lic_cerradas)))

unis = {u["id"]: u for u in intl["unidades"]}
validos = [u for u in intl["unidades"] if u["indice"] is not None]
for d in range(1, 7):
    al = [u["dims"][str(d)] for u in validos if u["id"] in AL and u["dims"][str(d)] is not None]
    oc = [u["dims"][str(d)] for u in validos if "OCDE" in u["grupos"] and u["dims"][str(d)] is not None]
    C.append(macro(f"ALmedDim{LETRAS[d-1]}", num(float(np.median(al)))))
    C.append(macro(f"OCDEmedDim{LETRAS[d-1]}", num(float(np.median(oc)))))
C.append(macro("ALmedIndice", num(float(np.median([u["indice"] for u in validos if u["id"] in AL])))))
C.append(macro("OCDEmedIndice", num(float(np.median([u["indice"] for u in validos if "OCDE" in u["grupos"]])))))
orden = sorted(validos, key=lambda u: -u["indice"])
C.append(macro("PrimerPais", orden[0]["nombre"]))
C.append(macro("PrimerPaisIndice", num(orden[0]["indice"])))
C.append(macro("UltimoPais", orden[-1]["nombre"]))
C.append(macro("UltimoPaisIndice", num(orden[-1]["indice"])))
oc_orden = [u for u in orden if "OCDE" in u["grupos"]]
C.append(macro("MXrangoOCDE", 1 + [u["id"] for u in oc_orden].index("MEX")))
C.append(macro("NOCDE", len(oc_orden)))
C.append(macro("MXaritmetico", num(unis["MEX"]["aritmetico"])))
al_orden = [u for u in orden if u["id"] in AL]
C.append(macro("PrimerAL", al_orden[0]["nombre"]))
C.append(macro("PrimerALIndice", num(al_orden[0]["indice"])))

coh_i = {r["indicador"]: r for r in intl["coherencia"]}
C.append(macro("CohWJP", num(coh_i["wjp_gob_abierto"]["r_indice"], 2)))
C.append(macro("CohWGIvoz", num(coh_i["wgi_voz"]["r_indice"], 2)))
coh_e = {r["indicador"]: r for r in est["coherencia"]}
C.append(macro("CohPartPres", num(coh_e["participacion_presidencia"]["r_indice"], 2)))
C.append(macro("CohCorrup", num(coh_e["encig_prevalencia_corrupcion"]["r_indice"], 2)))
C.append(macro("CohConfianza", num(coh_e["encig_confianza_gob_estatal"]["r_indice"], 2)))
C.append(macro("NSubrepEst", sum(1 for r in est["coherencia"] if r["alerta"] and "subrep" in r["alerta"])))
C.append(macro("MaxRpobEst", num(max(abs(r["r_poblacion"]) for r in est["coherencia"] if r.get("r_poblacion") is not None), 2)))
C.append(macro("NWinsorEst", sum(1 for i in est["indicadores"] if i["winsorizados"])))
C.append(macro("NWinsorIntl", sum(1 for i in intl["indicadores"] if i["winsorizados"])))

e = {u["id"]: u for u in est["unidades"]}
C.append(macro("NEnt", len(est["unidades"])))
ultima = max(est["unidades"], key=lambda u: u["rango"])
C.append(macro("UltimaEnt", esc(ultima["nombre"])))
C.append(macro("UltimaEntIndice", num(ultima["indice"])))
seg = sorted(est["unidades"], key=lambda u: u["rango"])[1]
C.append(macro("SegundaEnt", esc(seg["nombre"])))
C.append(macro("SegundaEntIndice", num(seg["indice"])))
C.append(macro("MedEntIndice", num(float(np.median([u["indice"] for u in est["unidades"]])))))
for d in range(1, 7):
    C.append(macro(f"EntMedDim{LETRAS[d-1]}", num(float(np.median([u["dims"][str(d)] for u in est["unidades"]])))))
for cve, n in (("08", "CHH"), ("26", "SON")):
    C.append(macro(f"{n}aritmetico", num(e[cve]["aritmetico"])))

# Serie nacional
s = nac["serie"]
d4 = [(r["anio"], r["dims"]["4"]) for r in s if r["dims"].get("4") is not None]
d5 = [(r["anio"], r["dims"]["5"]) for r in s if r["dims"].get("5") is not None]
d1 = [(r["anio"], r["dims"]["1"]) for r in s if r["dims"].get("1") is not None]
d2 = [(r["anio"], r["dims"]["2"]) for r in s if r["dims"].get("2") is not None]
d6 = [(r["anio"], r["dims"]["6"]) for r in s if r["dims"].get("6") is not None]
for nombre, serie in (("Done", d1), ("Dtwo", d2), ("Dfour", d4), ("Dfive", d5), ("Dsix", d6)):
    C.append(macro(f"NAC{nombre}ini", num(serie[0][1])))
    C.append(macro(f"NAC{nombre}iniAnio", serie[0][0]))
    C.append(macro(f"NAC{nombre}fin", num(serie[-1][1])))
    C.append(macro(f"NAC{nombre}finAnio", serie[-1][0]))
C.append(macro("NACdesde", nac["desde"]))

# Contexto estatal (IDD-Mex)
ctx = est["contexto"].get("idd_mex")
if ctx:
    C.append(macro("IDDanio", ctx["anio"]))
    C.append(macro("IDDchh", num(ctx["valores"]["08"], 2)))
    C.append(macro("IDDson", num(ctx["valores"]["26"], 2)))
    ids = [u["id"] for u in est["unidades"]]
    a = np.array([e[i]["indice"] for i in ids])
    b = np.array([ctx["valores"].get(i, np.nan) for i in ids], dtype=float)
    m = ~np.isnan(b)
    import pandas as pd
    rho = pd.Series(a[m]).rank().corr(pd.Series(b[m]).rank())  # Spearman = Pearson de rangos
    C.append(macro("RhoIDD", num(rho, 2)))

(SALIDA / "cifras_extra.tex").write_text("\n".join(C) + "\n", encoding="utf-8")

# Lista de fuentes no redistribuibles (para la sección de licencias)
nombres = {f["id"]: f["editor"].split("(")[0].strip() for f in fuentes}
(SALIDA / "no_redistribuibles.tex").write_text(
    ", ".join(rf"\citeauthor{{{next(f['cita'] for f in fuentes if f['id']==i)}}}" for i in lic_cerradas) + "\n",
    encoding="utf-8")
(SALIDA / "bibrecursos.tex").write_text(
    "\n".join(rf"\addbibresource{{../{b.name}}}" for b in sorted(RAIZ.glob("referencias*.bib"))) + "\n",
    encoding="utf-8")
print("✓ tablas generadas en", SALIDA)
