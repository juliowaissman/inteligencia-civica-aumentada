"""Lectura y validación del catálogo de fuentes (`pipeline/catalogo/*.yaml`)."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

from .rutas import CATALOGO

DIMENSIONES = {
    1: "Capacidades cívicas y humanas",
    2: "Inteligencia colectiva",
    3: "Integración ética de la IA",
    4: "Instituciones habilitadoras y cocreación",
    5: "Valor público democrático",
    6: "Continuidad y retroalimentación",
}
CAPAS = {"instalada", "activacion", "resultado"}
NIVELES = {"internacional", "nacional", "estatal"}


@dataclass
class Indicador:
    id: str
    nombre: str
    dimension: int
    capa: str
    sentido: int  # +1: más es mejor; -1: más es peor
    unidad: str = ""
    nota: str = ""
    # "por_100k": dividir entre la población (CONAPO o Banco Mundial) antes de normalizar
    transformacion: str = ""


@dataclass
class Fuente:
    id: str
    nombre: str
    editor: str
    url: str
    licencia: str
    redistribuible: bool
    cita: str
    niveles: list[str]
    descarga: str  # "automatica" o "manual"
    instrucciones: str = ""
    estado: str = "candidata"  # candidata | verificada | descartada
    motivo: str = ""
    indicadores: list[Indicador] = field(default_factory=list)


def _validar(f: Fuente, ruta: Path) -> None:
    errores = []
    if f.descarga not in {"automatica", "manual"}:
        errores.append(f"descarga inválida: {f.descarga}")
    if not set(f.niveles) <= NIVELES:
        errores.append(f"niveles inválidos: {f.niveles}")
    if f.estado not in {"candidata", "verificada", "descartada"}:
        errores.append(f"estado inválido: {f.estado}")
    for i in f.indicadores:
        if i.dimension not in DIMENSIONES:
            errores.append(f"{i.id}: dimensión {i.dimension}")
        if i.capa not in CAPAS:
            errores.append(f"{i.id}: capa {i.capa}")
        if i.sentido not in (1, -1):
            errores.append(f"{i.id}: sentido {i.sentido}")
    if errores:
        raise ValueError(f"{ruta.name}: " + "; ".join(errores))


def cargar(directorio: Path = CATALOGO) -> dict[str, Fuente]:
    fuentes: dict[str, Fuente] = {}
    for ruta in sorted(directorio.glob("*.yaml")):
        d = yaml.safe_load(ruta.read_text(encoding="utf-8"))
        inds = [Indicador(**i) for i in d.pop("indicadores", [])]
        f = Fuente(**d, indicadores=inds)
        if f.id != ruta.stem:
            raise ValueError(f"{ruta.name}: id '{f.id}' no coincide con el nombre del archivo")
        _validar(f, ruta)
        fuentes[f.id] = f
    return fuentes
