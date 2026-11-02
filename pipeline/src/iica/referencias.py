"""Convierte referencias.bib (y referencias_*.bib) en JSON para el sitio."""

from __future__ import annotations

import json
import re

import bibtexparser

from .rutas import RAIZ, SITIO_DATOS


def _limpiar(t: str) -> str:
    t = re.sub(r"\\url\{([^}]*)\}", r"\1", t)
    t = re.sub(r"\\emph\{([^}]*)\}", r"\1", t)
    t = t.replace("\\&", "&").replace("--", "–").replace("{", "").replace("}", "")
    return re.sub(r"\s+", " ", t).strip()


def _autores_cortos(autor: str) -> str:
    nombres = [a.strip() for a in autor.split(" and ") if a.strip()]
    apellidos = [n.split(",")[0].strip() if "," in n else n for n in nombres]
    apellidos = [_limpiar(a) for a in apellidos]
    if len(apellidos) == 1:
        return apellidos[0]
    if len(apellidos) == 2:
        return f"{apellidos[0]} y {apellidos[1]}"
    return f"{apellidos[0]} et al."


def entradas() -> list[dict]:
    todas = []
    for ruta in sorted(RAIZ.glob("referencias*.bib")):
        lib = bibtexparser.parse_string(ruta.read_text(encoding="utf-8"))
        for e in lib.entries:
            d = {k.lower(): f.value for k, f in e.fields_dict.items()}
            d["ID"] = e.key
            todas.append(d)
    return todas


def a_json() -> dict:
    out = {}
    for e in entradas():
        autor = e.get("author", e.get("editor", e.get("organization", "s. a.")))
        anio = e.get("year", "s. f.")
        partes = [_limpiar(autor) + f" ({anio}).", _limpiar(e.get("title", "")) + "."]
        for campo in ("journal", "booktitle", "howpublished", "publisher", "institution"):
            if campo in e:
                partes.append(_limpiar(e[campo]) + ".")
        if "volume" in e:
            partes.append(f"Vol. {e['volume']}" + (f"({e['number']})" if "number" in e else "") + ".")
        if "pages" in e:
            partes.append(_limpiar(e["pages"]) + ".")
        if "note" in e:
            partes.append(_limpiar(e["note"]) + ".")
        url = e.get("url") or (f"https://doi.org/{e['doi']}" if "doi" in e else "")
        out[e["ID"]] = {
            "corta": f"{_autores_cortos(autor)}, {anio}",
            "titulo": _limpiar(e.get("title", "")),
            "completa": " ".join(partes),
            "url": url,
            "orden": _limpiar(autor).lower() + anio,
        }
    return out


def main() -> None:
    SITIO_DATOS.mkdir(parents=True, exist_ok=True)
    datos = a_json()
    (SITIO_DATOS / "referencias.json").write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✓ {len(datos)} referencias → {SITIO_DATOS / 'referencias.json'}")


if __name__ == "__main__":
    main()
