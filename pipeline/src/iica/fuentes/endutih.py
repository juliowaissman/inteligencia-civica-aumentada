"""ENDUTIH (INEGI): tabulados por entidad federativa, ediciones 2020–2025.

Se usan tres tabulados publicados por el INEGI en cada edición (mismo código de archivo):
  - <año>_uedo550: personas usuarias de TIC por entidad (población de 6 años y más).
  - <año>_h2ed110: hogares con equipamiento de TIC por entidad.
  - <año>_u2ed244: personas usuarias de internet por entidad, según principales usos.
Se toma la columna "Por ciento" tal como la publica el INEGI (estimaciones con factor de expansión
ya aplicado por el INEGI); no se recalcula nada desde microdatos.
"""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

from ._inegi import bajar_inegi, clave, nivel, num

ANIOS = [2020, 2021, 2022, 2023, 2024, 2025]
TABULADOS = ["uedo550", "h2ed110", "u2ed244"]

# indicador -> (tabulado, regex del encabezado de columna)
INDICADORES = {
    "endutih_internet": ("uedo550", r"usuari[oa]s de internet"),
    "endutih_hogares_computadora": ("h2ed110", r"^computadora$"),
    "endutih_hogares_internet": ("h2ed110", r"^internet$"),
    "endutih_internet_gobierno": ("u2ed244", r"interactuar con el gobierno"),
}


def _ruta(anio: int, tab: str) -> str:
    programa = "dutih" if anio <= 2022 else "endutih"
    return f"programas/{programa}/{anio}/tabulados/{anio}_{tab}.xlsx"


def descargar(destino: Path) -> None:
    for anio in ANIOS:
        for tab in TABULADOS:
            bajar_inegi(_ruta(anio, tab), destino / f"{anio}_{tab}.xlsx")


def _limpia(v) -> str:
    return re.sub(r"\s+", " ", str(v)).strip() if isinstance(v, str) else ""


def _columna_porciento(df: pd.DataFrame, patron: str) -> tuple[int, int]:
    """Fila del encabezado 'Entidad Federativa' y columna 'Por ciento' bajo el encabezado buscado."""
    for i in range(min(len(df), 15)):
        if _limpia(df.iat[i, 0]).lower().startswith("entidad federativa"):
            for j in range(1, df.shape[1]):
                # quita llamadas de nota pegadas al final (p. ej. "Telefoníaa")
                if re.search(patron, _limpia(df.iat[i, j]), re.I):
                    sub = _limpia(df.iat[i + 1, j + 1]).lower()
                    if sub != "por ciento":
                        raise ValueError(f"se esperaba 'Por ciento' junto a {df.iat[i, j]!r}, hay {sub!r}")
                    return i, j + 1
            raise ValueError(f"no se encontró la columna /{patron}/")
    raise ValueError("no se encontró la fila 'Entidad Federativa'")


def procesar(copia: Path) -> pd.DataFrame:
    filas = []
    for anio in ANIOS:
        for ind, (tab, patron) in INDICADORES.items():
            ruta = copia / f"{anio}_{tab}.xlsx"
            df = pd.read_excel(ruta, sheet_name=0, header=None)
            i0, col = _columna_porciento(df, patron)
            vistos = set()
            for i in range(i0 + 2, len(df)):
                c = clave(df.iat[i, 0])
                if not c or c in vistos:
                    continue
                vistos.add(c)
                filas.append({"nivel": nivel(c), "unidad": c, "anio": anio,
                              "indicador": ind, "valor": num(df.iat[i, col])})
            if len(vistos) != 33:
                raise ValueError(f"{ruta.name} {ind}: {len(vistos)} unidades (se esperaban 33)")
    return pd.DataFrame(filas)
