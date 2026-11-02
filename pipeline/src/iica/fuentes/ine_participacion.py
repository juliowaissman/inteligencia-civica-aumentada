"""INE: participación ciudadana por entidad en elecciones federales 2018, 2021 y 2024.

Fuente: los archivos JSON de resultados que alimentan los sitios oficiales de Cómputos Distritales del
INE (computos2018/2021/2024.ine.mx), un archivo nacional y uno por entidad para cada elección.
El valor es `porcentajeParticipacionCiudadana` tal como lo publica el INE (votos totales entre lista
nominal de las actas computadas). A nivel estatal el INE incluye el voto desde el extranjero asignado
a la entidad de origen y las casillas especiales.

Se comprueba que totalVotos / listaNominal reproduce el porcentaje publicado.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from ..descargar import bajar

# (año, indicador, sitio, carpeta, prefijo)
ELECCIONES = [
    (2018, "participacion_presidencia", "computos2018", "PRESIDENTE", "Presidente"),
    (2018, "participacion_diputaciones", "computos2018", "DIPUTADOS_MR", "Diputados_MR"),
    (2021, "participacion_diputaciones", "computos2021", "DIPUTADOS_MR", "Diputados_MR"),
    (2024, "participacion_presidencia", "computos2024", "PRESIDENTE", "Presidente"),
    (2024, "participacion_diputaciones", "computos2024", "DIPUTADOS_MR", "Diputados_MR"),
]


def _archivos():
    for anio, ind, sitio, carpeta, pref in ELECCIONES:
        base = f"https://{sitio}.ine.mx/assets/JSON/{carpeta}"
        yield anio, ind, "MEX", f"{base}/NACIONAL/{pref}_NACIONAL.json", f"{anio}_{pref}_NACIONAL.json"
        for n in range(1, 33):
            yield anio, ind, f"{n:02d}", f"{base}/ESTATAL/{pref}_ESTATAL_{n}.json", f"{anio}_{pref}_ESTATAL_{n}.json"


def descargar(destino: Path) -> None:
    for *_, url, nombre in _archivos():
        bajar(url, destino / nombre)


def procesar(copia: Path) -> pd.DataFrame:
    filas = []
    for anio, ind, unidad, _, nombre in _archivos():
        d = json.loads((copia / nombre).read_text(encoding="utf-8"))
        esperado = "NACIONAL" if unidad == "MEX" else "ESTATAL"
        if d["nivelNodo"] != esperado or (unidad != "MEX" and int(d["idNodo"]) != int(unidad)):
            raise ValueError(f"{nombre}: nodo inesperado {d['nivelNodo']} {d['idNodo']}")
        p = float(d["porcentajeParticipacionCiudadana"])
        calc = 100 * d["totalVotos"] / d["listaNominal"]
        # El INE trunca a 4 decimales. En los JSON estatales de diputaciones 2018 `totalVotos` solo trae
        # los votos de mayoría relativa, así que el cociente coincide con porcentajeParticipacionCiudadanaMR.
        refs = [p, d.get("porcentajeParticipacionCiudadanaMR")]
        if not any(r is not None and abs(calc - float(r)) <= 0.001 for r in refs):
            raise ValueError(f"{nombre}: {calc:.4f} no reproduce {refs}")
        filas.append({"nivel": "nacional" if unidad == "MEX" else "estatal", "unidad": unidad,
                      "anio": anio, "indicador": ind, "valor": p})
    return pd.DataFrame(filas)
