# Inteligencia Cívica Aumentada

Materiales sobre la propuesta de **Inteligencia Cívica Aumentada (ICA)** de Ricardo Zenteno Fernández (SOMEE 2026) y una primera aproximación a su índice (**IICA**) con datos abiertos, en tres niveles: internacional, nacional y estatal. Se elaboró con la colaboración de la Maestría en Ciencia de Datos de la Universidad de Sonora.

| Carpeta | Contenido |
|---|---|
| `refs/` | Ponencia original (PDF). |
| `docs/` | Informe sobre la originalidad del concepto (LaTeX/PDF) y propuesta de indicadores (Fase 0). |
| `pipeline/` | Código en Python (con `uv`): descarga de fuentes, cálculo de los índices y exportación. Ver `pipeline/CONTRIBUIR.md`. |
| `datos/` | Copias fechadas de las fuentes que se pueden redistribuir (`crudos/`) y resultados (`procesados/`). |
| `articulo/` | Artículo en LaTeX. Sus figuras y cifras las genera el pipeline. |
| `site/` | Sitio estático (Astro), publicado con GitHub Pages. |
| `referencias*.bib` | Bibliografía común del artículo y del sitio. |

## Reproducir

```bash
cd pipeline
uv run iica descargar   # baja las fuentes verificadas
uv run iica procesar    # tablas limpias
uv run iica calcular    # índices, sensibilidad y coherencia (configuración en niveles.yaml)
uv run iica exportar    # datos del sitio, figuras y cifras del artículo
uv run pytest           # pruebas de la metodología

cd ../articulo && uv run --project ../pipeline python tablas.py && latexmk -pdf articulo.tex
cd ../site && npm ci && npm run build && npm run revisar
```

Para agregar una fuente: crear `pipeline/catalogo/<id>.yaml` y `pipeline/src/iica/fuentes/<id>.py` (ver `pipeline/CONTRIBUIR.md`) y añadir sus indicadores en `pipeline/niveles.yaml`.

Para editar el sitio: las páginas están en `site/src/pages/`. Toda cita usa `<Cita clave="..."/>`, y el build falla si la clave no existe en los archivos `.bib`.
