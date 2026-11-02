"""ENCUCI 2020 (INEGI): solo cifras nacionales.

La ENCUCI 2020 no es representativa por entidad (solo nacional, 6 regiones y dominio urbano/rural),
por eso la fuente está `descartada` para el índice estatal. Aquí se leen solo cifras nacionales
publicadas en los tabulados básicos (bloque "Estimaciones puntuales", fila "Estados Unidos Mexicanos").
"""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

from ._inegi import bajar_inegi, num

BASE = "programas/encuci/2020/tabulados/{f}.xlsx"
ARCHIVOS = {
    "I": "I_Intereses_y_conocimiento_sobre_asuntos_publicos_y_democracia",
    "III": "III_Relaciones_con_individuos_asociaciones_y_poder_publico",
    "IV": "IV_Participacion",
}
# indicador -> (archivo, hoja, encabezado que debe aparecer, posición del valor entre los números de la fila)
INDICADORES = {
    "encuci_interes_mucho": ("I", "1.15", r"Grado de preocupaci.n o inter.s", 2),
    "encuci_asociacion_12m": ("III", "3.9", r"participado en un grupo o asociaci.n\s+en los .ltimos 12 meses", 6),
    "encuci_voluntariado_12m": ("IV", "4.1", r"Condici.n de haber realizado alg.n trabajo voluntario", 2),
    "encuci_accion_publica_12m": ("IV", "4.14", r"Realizaci.n de actividades relacionadas", 4),
}


def descargar(destino: Path) -> None:
    for f in ARCHIVOS.values():
        bajar_inegi(BASE.format(f=f), destino / f"{f}.xlsx")


def procesar(copia: Path) -> pd.DataFrame:
    filas = []
    for ind, (arch, hoja, encabezado, pos) in INDICADORES.items():
        df = pd.read_excel(copia / f"{ARCHIVOS[arch]}.xlsx", sheet_name=hoja, header=None)
        texto = " ".join(str(v) for v in df.iloc[:20].values.ravel() if isinstance(v, str))
        if not re.search(encabezado, texto):
            raise ValueError(f"encuci {hoja}: no aparece /{encabezado}/")
        fila = df[df[0].astype(str).str.strip() == "Estados Unidos Mexicanos"].iloc[0]  # estimaciones puntuales
        nums = [num(v) for v in fila.tolist()[1:] if num(v) is not None]
        filas.append({"nivel": "nacional", "unidad": "MEX", "anio": 2020, "indicador": ind, "valor": nums[pos]})
    return pd.DataFrame(filas)
