"""Línea de comandos: `uv run iica <comando> [--fuente ID]`."""

from __future__ import annotations

import argparse
import sys
import traceback

from . import catalogo, descargar, procesar


def _seleccion(fuentes, ids):
    if not ids:
        return {k: v for k, v in fuentes.items() if v.estado == "verificada"}
    return {k: fuentes[k] for k in ids}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="iica")
    p.add_argument("comando", choices=["catalogo", "descargar", "procesar", "cobertura", "calcular", "exportar"])
    p.add_argument("--fuente", action="append", default=[], help="id de fuente (repetible)")
    a = p.parse_args(argv)

    fuentes = catalogo.cargar()
    sel = _seleccion(fuentes, a.fuente)
    fallos = 0

    if a.comando == "catalogo":
        for f in fuentes.values():
            print(f"{f.id:28} {f.estado:11} {f.descarga:10} {','.join(f.niveles):30} {len(f.indicadores)} ind.")
    elif a.comando == "descargar":
        for f in sel.values():
            try:
                print(f"↓ {f.id} → {descargar.descargar(f)}")
            except Exception as e:  # informe y seguir con las demás
                fallos += 1
                print(f"✗ {f.id}: {e}", file=sys.stderr)
    elif a.comando in ("procesar", "cobertura"):
        tablas = {}
        for f in sel.values():
            try:
                tablas[f.id] = procesar.procesar_fuente(f)
                print(f"✓ {f.id}: {len(tablas[f.id])} filas")
            except Exception as e:
                fallos += 1
                print(f"✗ {f.id}: {e}", file=sys.stderr)
                traceback.print_exc(limit=1)
        if a.comando == "cobertura":
            cob = procesar.cobertura(sel, tablas)
            print(cob.to_string(index=False))
    elif a.comando == "calcular":
        from . import indice
        indice.main()
    elif a.comando == "exportar":
        from . import exportar
        exportar.main()
    return 1 if fallos else 0


if __name__ == "__main__":
    raise SystemExit(main())
