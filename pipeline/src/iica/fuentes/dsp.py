"""Digital Society Project (DSP), conjunto de datos v8 (país-año, 2000–2025)."""

from __future__ import annotations

import zipfile
from pathlib import Path

import pandas as pd

ZIP = "DigitalSocietyProject-v8-CSV.zip"
ARCHIVOS = [(f"https://digitalsocietyproject.org/wp-content/uploads/2026/03/{ZIP}", ZIP)]
CSV = "DigitalSocietyProject-v8-CSV/DSP_CY_v8.csv"

# id del indicador -> variable del DSP (estimación puntual del modelo de medición)
VARIABLES = {
    "dsp_ciberseguridad_gob": "v2smgovcapsec",
    "dsp_capacidad_regulacion": "v2smregcap",
    "dsp_privacidad_ley": "v2smprivcon",
    "dsp_medios_perspectivas": "v2smonper",
    "dsp_polarizacion": "v2smpolsoc",
}
# Códigos propios de V-Dem sin equivalente ISO 3166-1 (Gaza, Somalilandia, Zanzíbar).
NO_ISO = {"PSG", "SML", "ZZB"}


def procesar(copia: Path) -> pd.DataFrame:
    with zipfile.ZipFile(copia / ZIP) as z, z.open(CSV) as fh:
        d = pd.read_csv(fh, usecols=["country_text_id", "year", *VARIABLES.values()])
    d = d[~d["country_text_id"].isin(NO_ISO)]
    largo = d.melt(id_vars=["country_text_id", "year"], var_name="var", value_name="valor")
    inv = {v: k for k, v in VARIABLES.items()}
    return pd.DataFrame({"nivel": "internacional", "unidad": largo["country_text_id"], "anio": largo["year"],
                         "indicador": largo["var"].map(inv), "valor": largo["valor"]})
