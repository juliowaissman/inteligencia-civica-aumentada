"""Mapas base (TopoJSON) para los coropletas del sitio.

Produce dos archivos en `site/public/geo/`:

- `estados.topo.json` (objeto `estados`): las 32 entidades federativas, capa `00ent`
  (áreas geoestadísticas estatales) del **Marco Geoestadístico 2025** del INEGI
  (UPC 794551163061, archivo "Marco Geoestadístico Integrado 2025",
  `mg_2025_integrado.zip`). Licencia: Términos de Libre Uso de la Información del INEGI.
  El zip integrado pesa ~245 MB; para no bajarlo entero se leen por HTTP Range solo
  los miembros necesarios (`00ent.*`, metadatos y catálogo de entidades). El servidor
  del INEGI acepta peticiones Range (HTTP 206).
  Propiedades: `cve` ("01"–"32") y `nombre` (NOMGEO del INEGI).
  Se reproyecta a WGS84 y se simplifica con mapshaper (Visvalingam, topología compartida).

- `mundo.topo.json` (objeto `paises`): Natural Earth 1:110m (dominio público) tal como lo
  empaqueta `world-atlas@2.0.2` (`countries-110m.json`, ids ISO 3166-1 numéricos).
  Se agrega `iso3` con la equivalencia numérico→alfa-3 de GeoNames `countryInfo.txt`
  (CC BY 4.0). Los polígonos sin código ISO numérico (p. ej. Kosovo, Chipre del Norte,
  Somalilandia) quedan con `iso3 = null`.

Los crudos quedan en `datos/crudos/geo_inegi/<fecha>/` y `datos/crudos/geo_mundo/<fecha>/`
con su `procedencia.json`. Requiere Node.js (`npx mapshaper@0.7.101`).

Uso (desde `pipeline/`): `uv run python -m iica.geo`
"""

from __future__ import annotations

import datetime as dt
import io
import json
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path

import requests

from .descargar import AGENTE, _sha256, bajar
from .fuentes._paises import ARCHIVO_GEONAMES, URL_GEONAMES, bajar_geonames, numerico_a_iso3
from .rutas import CRUDOS, ENTIDADES, RAIZ

SALIDA = RAIZ / "site" / "public" / "geo"
MAPSHAPER = ["npx", "--yes", "mapshaper@0.7.101"]

URL_FICHA_INEGI = "https://www.inegi.org.mx/app/biblioteca/ficha.html?upc=794551163061"
URL_MG_INTEGRADO = (
    "https://www.inegi.org.mx/contenidos/productos/prod_serv/contenidos/espanol/bvinegi/"
    "productos/geografia/marcogeo/794551163061/mg_2025_integrado.zip"
)
MIEMBROS_INEGI = [
    "conjunto_de_datos/00ent.shp",
    "conjunto_de_datos/00ent.shx",
    "conjunto_de_datos/00ent.dbf",
    "conjunto_de_datos/00ent.prj",
    "conjunto_de_datos/00ent.cpg",
    "catalogos/áreas_geoestadísticas_estatales.csv",
    "metadatos/metadato_mgi_2025.txt",
    "metadatos/mgi_2025.xml",
]
LICENCIA_INEGI = (
    "Términos de Libre Uso de la Información del INEGI "
    "(https://www.inegi.org.mx/inegi/terminos.html)"
)

URL_WORLD_ATLAS = "https://cdn.jsdelivr.net/npm/world-atlas@2.0.2/countries-110m.json"

# Simplificación: porcentaje de vértices que se conservan (ajustado para ~100–300 KB).
SIMPLIFICAR_ESTADOS = "2%"


class _ArchivoRemoto(io.RawIOBase):
    """Archivo de solo lectura sobre HTTP con peticiones Range, para leer un zip remoto."""

    BLOQUE = 4 << 20

    def __init__(self, url: str):
        self.url, self.pos = url, 0
        r = requests.get(url, headers={"User-Agent": AGENTE, "Range": "bytes=0-3"}, timeout=60)
        r.raise_for_status()
        if r.status_code != 206 or r.content != b"PK\x03\x04":
            raise RuntimeError(f"{url}: el servidor no devolvió un zip con soporte de Range")
        self.tam = int(r.headers["Content-Range"].split("/")[1])
        self._ini, self._datos = 0, b""

    def readable(self):
        return True

    def seekable(self):
        return True

    def tell(self):
        return self.pos

    def seek(self, desp, desde=0):
        self.pos = {0: desp, 1: self.pos + desp, 2: self.tam + desp}[desde]
        return self.pos

    def readinto(self, b):
        if self.pos >= self.tam:
            return 0
        fin_cache = self._ini + len(self._datos)
        if not (self._ini <= self.pos < fin_cache):
            fin = min(self.pos + max(len(b), self.BLOQUE), self.tam) - 1
            r = requests.get(
                self.url, headers={"User-Agent": AGENTE, "Range": f"bytes={self.pos}-{fin}"}, timeout=300
            )
            r.raise_for_status()
            self._ini, self._datos = self.pos, r.content
        i = self.pos - self._ini
        trozo = self._datos[i : i + len(b)]
        b[: len(trozo)] = trozo
        self.pos += len(trozo)
        return len(trozo)


def _procedencia(destino: Path, datos: dict) -> None:
    datos["sha256"] = {
        p.name: _sha256(p) for p in sorted(destino.iterdir()) if p.is_file() and p.name != "procedencia.json"
    }
    (destino / "procedencia.json").write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")


def bajar_inegi(destino: Path) -> Path:
    """Extrae del zip integrado del INEGI (por HTTP Range) solo la capa 00ent y sus metadatos."""
    destino.mkdir(parents=True, exist_ok=True)
    remoto = _ArchivoRemoto(URL_MG_INTEGRADO)
    with zipfile.ZipFile(io.BufferedReader(remoto, 1 << 16)) as z:
        crc = {}
        for m in MIEMBROS_INEGI:
            info = z.getinfo(m)
            with z.open(info) as src, (destino / Path(m).name).open("wb") as dst:
                shutil.copyfileobj(src, dst)  # zipfile verifica el CRC32 al leer
            crc[Path(m).name] = f"{info.CRC:08x}"
    _procedencia(destino, {
        "fuente": "geo_inegi",
        "nombre": "Marco Geoestadístico 2025 (INEGI), capa 00ent: áreas geoestadísticas estatales",
        "producto": "Marco Geoestadístico 2025, UPC 794551163061, archivo 'Marco Geoestadístico Integrado 2025'",
        "url": URL_MG_INTEGRADO,
        "url_ficha": URL_FICHA_INEGI,
        "tamano_zip_bytes": remoto.tam,
        "miembros_extraidos": MIEMBROS_INEGI,
        "crc32_en_zip": crc,
        "nota": "Se extrajeron solo estos miembros del zip remoto con peticiones HTTP Range; "
                "sha256 se refiere a los archivos extraídos.",
        "licencia": LICENCIA_INEGI,
        "fecha_acceso": dt.date.today().isoformat(),
    })
    return destino


def bajar_mundo(destino: Path) -> Path:
    destino.mkdir(parents=True, exist_ok=True)
    bajar(URL_WORLD_ATLAS, destino / "countries-110m.json")
    bajar_geonames(destino)
    _procedencia(destino, {
        "fuente": "geo_mundo",
        "nombre": "Natural Earth 1:110m Admin 0 – Countries (vía world-atlas 2.0.2) y GeoNames countryInfo",
        "url": {"countries-110m.json": URL_WORLD_ATLAS, ARCHIVO_GEONAMES: URL_GEONAMES},
        "licencia": {
            "countries-110m.json": "Dominio público (Natural Earth, https://www.naturalearthdata.com/about/terms-of-use/); "
                                   "empaquetado world-atlas bajo ISC",
            ARCHIVO_GEONAMES: "CC BY 4.0 (GeoNames)",
        },
        "fecha_acceso": dt.date.today().isoformat(),
    })
    return destino


def _mapshaper(*args: str, cwd: Path) -> None:
    subprocess.run([*MAPSHAPER, *args], cwd=cwd, check=True)


def construir_estados(copia: Path, salida: Path) -> Path:
    salida.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        _mapshaper(
            "-i", str(copia / "00ent.shp"), "encoding=latin1",  # 00ent.cpg dice "88591" (ISO-8859-1)
            "-each", "cve=CVE_ENT, nombre=NOMGEO",
            "-filter-fields", "cve,nombre",
            # se simplifica en la proyección original (LCC, metros) y luego se pasa a WGS84
            "-simplify", SIMPLIFICAR_ESTADOS, "keep-shapes",
            "-proj", "wgs84",
            "-clean",
            "-rename-layers", "estados",
            "-o", str(salida), "format=topojson", "quantization=100000",
            cwd=Path(tmp),
        )
    topo = json.loads(salida.read_text(encoding="utf-8"))
    cves = sorted(g["properties"]["cve"] for g in topo["objects"]["estados"]["geometries"])
    if cves != sorted(ENTIDADES):
        raise RuntimeError(f"estados.topo.json: claves inesperadas {cves}")
    return salida


def construir_mundo(copia: Path, salida: Path) -> Path:
    salida.parent.mkdir(parents=True, exist_ok=True)
    topo = json.loads((copia / "countries-110m.json").read_text(encoding="utf-8"))
    a_iso3 = numerico_a_iso3(copia)
    paises = topo["objects"].pop("countries")
    topo["objects"] = {"paises": paises}  # se descarta el objeto 'land'
    for g in paises["geometries"]:
        num = g.get("id")
        g.setdefault("properties", {})["iso3"] = a_iso3.get(str(int(num))) if num else None
    salida.write_text(json.dumps(topo, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    faltan = {"MEX", "USA", "BRA", "CHL"} - {g["properties"]["iso3"] for g in paises["geometries"]}
    if faltan:
        raise RuntimeError(f"mundo.topo.json: faltan {faltan}")
    return salida


def main() -> None:
    hoy = dt.date.today().isoformat()
    inegi = bajar_inegi(CRUDOS / "geo_inegi" / hoy)
    mundo = bajar_mundo(CRUDOS / "geo_mundo" / hoy)
    for ruta in (construir_estados(inegi, SALIDA / "estados.topo.json"),
                 construir_mundo(mundo, SALIDA / "mundo.topo.json")):
        print(f"{ruta.relative_to(RAIZ)}: {ruta.stat().st_size / 1024:.0f} KB")


if __name__ == "__main__":
    main()
