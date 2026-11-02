"""Equivalencias de códigos de país (ISO 3166-1) a partir de GeoNames.

Algunas fuentes publican códigos ISO2, códigos numéricos M49/ISO o nombres de país
en lugar de ISO3. Para convertirlos sin escribir tablas a mano, las fuentes que lo
necesitan descargan `countryInfo.txt` de GeoNames (CC BY 4.0,
https://download.geonames.org/export/dump/) junto con sus crudos y usan estas funciones.
"""

from __future__ import annotations

from pathlib import Path

from ..descargar import bajar

URL_GEONAMES = "https://download.geonames.org/export/dump/countryInfo.txt"
ARCHIVO_GEONAMES = "geonames_countryInfo.txt"


def bajar_geonames(destino: Path) -> None:
    bajar(URL_GEONAMES, destino / ARCHIVO_GEONAMES)


def _filas(copia: Path):
    for linea in (copia / ARCHIVO_GEONAMES).read_text(encoding="utf-8").splitlines():
        if not linea or linea.startswith("#"):
            continue
        c = linea.split("\t")
        # columnas: ISO, ISO3, ISO-Numeric, fips, Country, ...
        yield c[0], c[1], c[2], c[4]


def iso2_a_iso3(copia: Path) -> dict[str, str]:
    return {iso2: iso3 for iso2, iso3, _, _ in _filas(copia)}


def numerico_a_iso3(copia: Path) -> dict[str, str]:
    return {str(int(num)): iso3 for _, iso3, num, _ in _filas(copia) if num.strip().isdigit()}


def nombre_a_iso3(copia: Path, alias: dict[str, str] | None = None) -> dict[str, str]:
    """Nombre en inglés (GeoNames) -> ISO3, más los alias que declare cada fuente."""
    d = {nombre: iso3 for _, iso3, _, nombre in _filas(copia)}
    d.update(alias or {})
    return d
