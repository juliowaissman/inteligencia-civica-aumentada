"""Utilidades comunes para leer tabulados y datos abiertos del INEGI (grupo C).

No es una fuente: lo usan endutih, encig, envipe y cnge.
"""

from __future__ import annotations

import base64
import re
import unicodedata
from pathlib import Path

import pandas as pd
import requests

from ..descargar import AGENTE, bajar
from ..rutas import ENTIDADES

CONTENIDOS = "https://www.inegi.org.mx/contenidos"


def _norm(texto: str) -> str:
    t = unicodedata.normalize("NFKD", str(texto)).encode("ascii", "ignore").decode()
    t = re.sub(r"[^a-z ]", " ", t.lower())
    return re.sub(r"\s+", " ", t).strip()


_NOMBRES = {_norm(v): k for k, v in ENTIDADES.items()}
_NOMBRES.update({
    "coahuila": "05", "michoacan": "16", "veracruz": "30", "estado de mexico": "15",
    "distrito federal": "09", "ciudad de mexico": "09",
    "estados unidos mexicanos": "MEX", "nacional": "MEX", "total nacional": "MEX",
})


def clave(nombre) -> str | None:
    """Clave INEGI de 2 dígitos (o "MEX") a partir del nombre que aparece en un tabulado."""
    if not isinstance(nombre, str):
        return None
    n = _norm(nombre)
    return _NOMBRES.get(n)


def nivel(cve: str) -> str:
    return "nacional" if cve == "MEX" else "estatal"


def leer_hoja(ruta: Path, hoja) -> pd.DataFrame:
    return pd.read_excel(ruta, sheet_name=hoja, header=None)


def hoja_por_titulo(ruta: Path, patron: str, filas: int = 12) -> str:
    """Nombre de la única hoja cuyo encabezado (primeras filas) coincide con `patron`."""
    xl = pd.ExcelFile(ruta)
    hallazgos = []
    for h in xl.sheet_names:
        if h.lower().startswith(("índice", "indice", "resumen")):
            continue
        df = pd.read_excel(xl, sheet_name=h, header=None, nrows=filas)
        # solo la primera columna: ahí está el título, partido en varias filas
        texto = " ".join(str(v) for v in df.iloc[:, 0] if isinstance(v, str))
        if re.search(patron, re.sub(r"\s+", " ", texto), re.I):
            hallazgos.append(h)
    if len(hallazgos) != 1:
        raise ValueError(f"{ruta.name}: se esperaba 1 hoja con /{patron}/, hay {hallazgos}")
    return hallazgos[0]


def filas_entidad(df: pd.DataFrame, col: int = 0) -> dict[str, pd.Series]:
    """Primera fila de cada entidad (y del total nacional) según el nombre en la columna `col`."""
    out: dict[str, pd.Series] = {}
    for _, fila in df.iterrows():
        c = clave(fila.iloc[col])
        if c and c not in out:
            out[c] = fila
    return out


def bloques(df: pd.DataFrame, patron_fila: str) -> dict[str, pd.Series]:
    """Tabulados en bloques: una fila con el nombre de la entidad y debajo filas por categoría.

    Devuelve, por entidad, la fila cuya primera celda coincide con `patron_fila`.
    """
    out: dict[str, pd.Series] = {}
    actual = None
    for _, fila in df.iterrows():
        c0 = fila.iloc[0]
        c = clave(c0)
        if c:
            actual = c
            continue
        if actual and isinstance(c0, str) and re.search(patron_fila, c0.strip(), re.I):
            if actual in out:
                raise ValueError(f"fila /{patron_fila}/ repetida en {actual}")
            out[actual] = fila
    return out


def columnas_confianza(df: pd.DataFrame) -> tuple[int, int]:
    """Columnas 'Relativos' de 'Mucha confianza' y 'Algo de confianza' (la de relativos va justo después)."""
    for i in range(min(len(df), 20)):
        fila = [re.sub(r"\s+", " ", str(v)).strip().lower() for v in df.iloc[i]]
        if "mucha confianza" in fila and "algo de confianza" in fila:
            jm, ja = fila.index("mucha confianza"), fila.index("algo de confianza")
            sub = [str(df.iat[i + 1, j + 1]).strip().lower() for j in (jm, ja)]
            if sub != ["relativos", "relativos"]:
                raise ValueError(f"encabezado inesperado bajo 'Mucha/Algo de confianza': {sub}")
            return jm + 1, ja + 1
    raise ValueError("no se encontraron las columnas 'Mucha confianza' / 'Algo de confianza'")


def confianza(df: pd.DataFrame, patron_fila: str) -> dict[str, float]:
    """% con mucha o algo de confianza = suma de los dos porcentajes publicados por el INEGI."""
    jm, ja = columnas_confianza(df)
    out = {}
    for c, fila in bloques(df, patron_fila).items():
        m, a = num(fila.iloc[jm]), num(fila.iloc[ja])
        if m is not None and a is not None:
            out[c] = m + a
    return out


def ultimo_numero(fila: pd.Series) -> float | None:
    vals = [num(v) for v in fila.tolist()]
    vals = [v for v in vals if v is not None]
    return vals[-1] if vals else None


def num(x) -> float | None:
    v = pd.to_numeric(x, errors="coerce")
    return None if pd.isna(v) else float(v)


def lista_archivos(id_biinegi: int, tipo: int) -> list[dict]:
    """Consulta el servicio de descarga masiva del sitio del INEGI (solo para exploración)."""
    t = base64.b64encode(b"Todas").decode()
    url = (
        "https://www.inegi.org.mx/app/api/descarga/componente/descargamasiva/lista/archivoscompaginacion"
        f"?tema=0&subtema=0&areaGeografica=0&proyecto=0&anio=0&tipodocto={tipo}&agrupacion={t}"
        f"&idBiinegi={id_biinegi}&desde=1&hasta=1000&textoBuscar=&ordenar=orden&ingles=0&datosAbiertos=0&orden=asc"
    )
    return requests.get(url, headers={"User-Agent": AGENTE}, timeout=60).json()


def bajar_inegi(ruta_contenidos: str, destino: Path) -> Path:
    """Descarga `https://www.inegi.org.mx/contenidos/<ruta>` y verifica que no sea la página de error HTML."""
    bajar(f"{CONTENIDOS}/{ruta_contenidos}", destino)
    with destino.open("rb") as fh:
        cabeza = fh.read(4)
    if cabeza[:2] != b"PK":  # xlsx y zip empiezan con PK
        destino.unlink()
        raise RuntimeError(f"El INEGI no devolvió un archivo válido para {ruta_contenidos}")
    return destino
