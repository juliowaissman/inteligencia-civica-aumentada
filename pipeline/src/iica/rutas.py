"""Rutas del proyecto y catálogos de unidades (países y entidades)."""

from pathlib import Path

RAIZ = Path(__file__).resolve().parents[3]
PIPELINE = RAIZ / "pipeline"
CATALOGO = PIPELINE / "catalogo"
CRUDOS = RAIZ / "datos" / "crudos"
PROCESADOS = RAIZ / "datos" / "procesados"
BIB = RAIZ / "referencias.bib"
SITIO_DATOS = RAIZ / "site" / "src" / "data"
ARTICULO = RAIZ / "articulo"

# Claves INEGI de las 32 entidades federativas (Marco Geoestadístico).
ENTIDADES = {
    "01": "Aguascalientes", "02": "Baja California", "03": "Baja California Sur",
    "04": "Campeche", "05": "Coahuila de Zaragoza", "06": "Colima",
    "07": "Chiapas", "08": "Chihuahua", "09": "Ciudad de México",
    "10": "Durango", "11": "Guanajuato", "12": "Guerrero", "13": "Hidalgo",
    "14": "Jalisco", "15": "México", "16": "Michoacán de Ocampo",
    "17": "Morelos", "18": "Nayarit", "19": "Nuevo León", "20": "Oaxaca",
    "21": "Puebla", "22": "Querétaro", "23": "Quintana Roo",
    "24": "San Luis Potosí", "25": "Sinaloa", "26": "Sonora", "27": "Tabasco",
    "28": "Tamaulipas", "29": "Tlaxcala", "30": "Veracruz de Ignacio de la Llave",
    "31": "Yucatán", "32": "Zacatecas",
}

# Países de comparación: América Latina y el Caribe (ISO3) y miembros de la OCDE (2026).
AMERICA_LATINA = [
    "ARG", "BOL", "BRA", "CHL", "COL", "CRI", "CUB", "DOM", "ECU", "SLV",
    "GTM", "HND", "MEX", "NIC", "PAN", "PRY", "PER", "URY", "VEN", "HTI",
    "JAM", "TTO",
]
OCDE = [
    "AUS", "AUT", "BEL", "CAN", "CHL", "COL", "CRI", "CZE", "DNK", "EST",
    "FIN", "FRA", "DEU", "GRC", "HUN", "ISL", "IRL", "ISR", "ITA", "JPN",
    "KOR", "LVA", "LTU", "LUX", "MEX", "NLD", "NZL", "NOR", "POL", "PRT",
    "SVK", "SVN", "ESP", "SWE", "CHE", "TUR", "GBR", "USA",
]
