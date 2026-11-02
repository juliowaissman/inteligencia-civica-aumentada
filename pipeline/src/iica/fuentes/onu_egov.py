"""ONU DESA: E-Government Survey (EGDI, EPART, OSI, HCI, TII), ediciones 2003–2024.

El Data Center (https://publicadministration.un.org/egovkb/en-us/data-center) es una
página ASP.NET (DotNetNuke). La descarga es un postback del botón "Download Data":
se hace un GET para obtener __VIEWSTATE y demás campos ocultos, y luego un POST por
edición con todos los países seleccionados. Cada respuesta es un CSV
`EGOV_DATA_<año>.csv` con todas las sub-series. El servidor es lento (1–3 min por
petición), por eso los tiempos de espera son largos.
"""

from __future__ import annotations

import time
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup

from ..descargar import AGENTE

URL = "https://publicadministration.un.org/egovkb/en-us/data-center"
P = "dnn$ctr633$Dispatch$Index$"
EDICIONES = [2003, 2004, 2005, 2008, 2010, 2012, 2014, 2016, 2018, 2020, 2022, 2024]

# columna del CSV -> id del indicador en el catálogo
COLUMNAS = {
    "E-Government Index": "egov_egdi",
    "E-Participation Index": "egov_epi",
    "Online Service Index": "egov_osi",
    "Human Capital Index": "egov_hci",
    "Telecommunication Infrastructure Index": "egov_tii",
}

# Nombre de país tal como aparece en los CSV de la ONU -> ISO 3166-1 alfa-3.
# Construido a mano a partir de los 193 Estados miembros de la ONU.
ISO3 = {
    "Afghanistan": "AFG", "Albania": "ALB", "Algeria": "DZA", "Andorra": "AND", "Angola": "AGO",
    "Antigua and Barbuda": "ATG", "Argentina": "ARG", "Armenia": "ARM", "Australia": "AUS",
    "Austria": "AUT", "Azerbaijan": "AZE", "Bahamas": "BHS", "Bahrain": "BHR", "Bangladesh": "BGD",
    "Barbados": "BRB", "Belarus": "BLR", "Belgium": "BEL", "Belize": "BLZ", "Benin": "BEN",
    "Bhutan": "BTN", "Bolivia": "BOL", "Bolivia (Plurinational State of)": "BOL",
    "Bosnia and Herzegovina": "BIH", "Botswana": "BWA", "Brazil": "BRA",
    "Brunei Darussalam": "BRN", "Bulgaria": "BGR", "Burkina Faso": "BFA", "Burundi": "BDI",
    "Cabo Verde": "CPV", "Cape Verde": "CPV", "Cambodia": "KHM", "Cameroon": "CMR", "Canada": "CAN",
    "Central African Republic": "CAF", "Chad": "TCD", "Chile": "CHL", "China": "CHN",
    "Colombia": "COL", "Comoros": "COM", "Congo": "COG", "Costa Rica": "CRI",
    "Côte d'Ivoire": "CIV", "Cote d'Ivoire": "CIV", "Côte d’Ivoire": "CIV", "Croatia": "HRV",
    "Cuba": "CUB", "Cyprus": "CYP", "Czech Republic": "CZE", "Czechia": "CZE",
    "Democratic People's Republic of Korea": "PRK", "Democratic Republic of the Congo": "COD",
    "Denmark": "DNK", "Djibouti": "DJI", "Dominica": "DMA", "Dominican Republic": "DOM",
    "Ecuador": "ECU", "Egypt": "EGY", "El Salvador": "SLV", "Equatorial Guinea": "GNQ",
    "Eritrea": "ERI", "Estonia": "EST", "Eswatini": "SWZ", "Swaziland": "SWZ", "Ethiopia": "ETH",
    "Fiji": "FJI", "Finland": "FIN", "France": "FRA", "Gabon": "GAB", "Gambia": "GMB",
    "Georgia": "GEO", "Georgia (Country)": "GEO", "Germany": "DEU", "Ghana": "GHA", "Greece": "GRC", "Grenada": "GRD",
    "Guatemala": "GTM", "Guinea": "GIN", "Guinea-Bissau": "GNB", "Guyana": "GUY", "Haiti": "HTI",
    "Honduras": "HND", "Hungary": "HUN", "Iceland": "ISL", "India": "IND", "Indonesia": "IDN",
    "Iran": "IRN", "Iran (Islamic Republic of)": "IRN", "Iraq": "IRQ", "Ireland": "IRL",
    "Israel": "ISR", "Italy": "ITA", "Jamaica": "JAM", "Japan": "JPN", "Jordan": "JOR",
    "Kazakhstan": "KAZ", "Kenya": "KEN", "Kiribati": "KIR", "Kuwait": "KWT", "Kyrgyzstan": "KGZ",
    "Lao People's Democratic Republic": "LAO", "Latvia": "LVA", "Lebanon": "LBN", "Lesotho": "LSO",
    "Liberia": "LBR", "Libya": "LBY", "Libyan Arab Jamahiriya": "LBY", "Liechtenstein": "LIE",
    "Lithuania": "LTU", "Luxembourg": "LUX", "Madagascar": "MDG", "Malawi": "MWI",
    "Malaysia": "MYS", "Maldives": "MDV", "Mali": "MLI", "Malta": "MLT", "Marshall Islands": "MHL",
    "Mauritania": "MRT", "Mauritius": "MUS", "Mexico": "MEX", "Micronesia": "FSM",
    "Micronesia (Federated States of)": "FSM", "Monaco": "MCO", "Mongolia": "MNG",
    "Montenegro": "MNE", "Morocco": "MAR", "Mozambique": "MOZ", "Myanmar": "MMR", "Namibia": "NAM",
    "Nauru": "NRU", "Nepal": "NPL", "Netherlands": "NLD", "Netherlands (Kingdom of the)": "NLD",
    "New Zealand": "NZL", "Nicaragua": "NIC", "Niger": "NER", "Nigeria": "NGA",
    "North Macedonia": "MKD", "The former Yugoslav Republic of Macedonia": "MKD", "Norway": "NOR",
    "Oman": "OMN", "Pakistan": "PAK", "Palau": "PLW", "Panama": "PAN", "Papua New Guinea": "PNG",
    "Paraguay": "PRY", "Peru": "PER", "Philippines": "PHL", "Poland": "POL", "Portugal": "PRT",
    "Qatar": "QAT", "Republic of Korea": "KOR", "Republic of Moldova": "MDA", "Romania": "ROU",
    "Russian Federation": "RUS", "Rwanda": "RWA", "Saint Kitts and Nevis": "KNA",
    "Saint Lucia": "LCA", "Saint Vincent and the Grenadines": "VCT", "Samoa": "WSM",
    "San Marino": "SMR", "Sao Tome and Principe": "STP", "Saudi Arabia": "SAU", "Senegal": "SEN",
    "Serbia": "SRB", "Serbia and Montenegro": "SCG", "Seychelles": "SYC", "Sierra Leone": "SLE",
    "Singapore": "SGP", "Slovakia": "SVK", "Slovenia": "SVN", "Solomon Islands": "SLB",
    "Somalia": "SOM", "South Africa": "ZAF", "South Sudan": "SSD", "Spain": "ESP",
    "Sri Lanka": "LKA", "Sudan": "SDN", "Suriname": "SUR", "Sweden": "SWE", "Switzerland": "CHE",
    "Syrian Arab Republic": "SYR", "Tajikistan": "TJK", "Thailand": "THA", "Timor-Leste": "TLS",
    "Togo": "TGO", "Tonga": "TON", "Trinidad and Tobago": "TTO", "Tunisia": "TUN",
    "Turkey": "TUR", "Türkiye": "TUR", "Turkiye": "TUR", "Turkmenistan": "TKM", "Tuvalu": "TUV",
    "Uganda": "UGA", "Ukraine": "UKR", "United Arab Emirates": "ARE",
    "United Kingdom of Great Britain and Northern Ireland": "GBR", "United Kingdom": "GBR",
    "United Republic of Tanzania": "TZA", "United States of America": "USA", "Uruguay": "URY",
    "Uzbekistan": "UZB", "Vanuatu": "VUT", "Venezuela": "VEN",
    "Venezuela (Bolivarian Republic of)": "VEN", "Viet Nam": "VNM", "Yemen": "YEM",
    "Zambia": "ZMB", "Zimbabwe": "ZWE",
}


def _formulario(html: str) -> list[tuple[str, str]]:
    form = BeautifulSoup(html, "lxml").find("form")
    datos = [(i["name"], i.get("value", "")) for i in form.find_all("input", type="hidden") if i.get("name")]
    for sel in form.find_all("select"):
        n = sel.get("name", "")
        if n.startswith(P) and n not in (P + "ddlYear", P + "ddlIndexTypes"):
            datos += [(n, o.get("value", "")) for o in sel.find_all("option", selected=True)]
    return [(k, v) for k, v in datos if k not in ("__EVENTTARGET", "__EVENTARGUMENT")]


def descargar(destino: Path) -> None:
    s = requests.Session()
    s.headers["User-Agent"] = AGENTE
    base = _formulario(s.get(URL, timeout=600).text)
    for anio in EDICIONES:
        datos = base + [
            (P + "ddlYear", str(anio)),
            (P + "ddlIndexTypes", "2"),
            ("__EVENTTARGET", P + "btnDownloadData"),
            ("__EVENTARGUMENT", ""),
        ]
        for intento in range(3):
            try:
                r = s.post(URL, data=datos, timeout=900)
                r.raise_for_status()
                break
            except requests.RequestException:
                if intento == 2:
                    raise
                time.sleep(30)
        if "attachment" not in r.headers.get("Content-Disposition", "") or b"Survey Year" not in r.content[:200]:
            raise RuntimeError(f"onu_egov {anio}: la respuesta no es el CSV esperado")
        (destino / f"EGOV_DATA_{anio}.csv").write_bytes(r.content)


def procesar(copia: Path) -> pd.DataFrame:
    filas = []
    for ruta in sorted(copia.glob("EGOV_DATA_*.csv")):
        df = pd.read_csv(ruta, encoding="utf-8-sig")
        df["Country Name"] = df["Country Name"].astype(str).str.strip()
        sin = set(df["Country Name"]) - set(ISO3)
        if sin:
            raise ValueError(f"{ruta.name}: países sin ISO3 {sorted(sin)}")
        for col, ind in COLUMNAS.items():
            d = df[["Survey Year", "Country Name", col]].dropna()
            for anio, pais, valor in d.itertuples(index=False):
                filas.append({"nivel": "internacional", "unidad": ISO3[pais], "anio": int(anio),
                              "indicador": ind, "valor": valor})
    return pd.DataFrame(filas)
