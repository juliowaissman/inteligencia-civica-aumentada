# Cómo agregar una fuente al pipeline del IICA

Regla de oro: **no inventar datos**. Una fuente entra al índice solo si su dato se descarga y se lee desde el origen. Si no se puede, la fuente queda como `candidata` o `descartada`, con su `motivo` y, si aplica, instrucciones de descarga manual.

## Archivos por fuente (ejemplo de referencia: `banco_mundial`)
1. `catalogo/<id>.yaml`: metadatos e indicadores. Mira `catalogo/banco_mundial.yaml`.
   - `licencia`: tal como la declara el editor. Si no declara ninguna, pon "Sin licencia declarada".
   - `redistribuible`: `true` solo si la licencia permite redistribuir (CC0, CC BY, CC BY-SA, datos abiertos de gobierno de México como los Términos de Libre Uso del INEGI).
   - `cita`: una clave BibTeX. La entrada va en el archivo `.bib` de tu grupo.
   - `estado`: `verificada` (descargada y leída, con el valor de México o de las entidades comprobado), `candidata` (aún no) o `descartada` (no sirve; explica por qué en `motivo`).
   - `descarga`: `automatica` o `manual`. Si es manual, escribe `instrucciones` paso a paso para que una persona la haga.
   - En cada indicador: `dimension` (1–6, ver abajo), `capa` (instalada | activacion | resultado) y `sentido` (1 si más es mejor, −1 si más es peor).
2. `src/iica/fuentes/<id>.py`, con:
   - `ARCHIVOS = [(url, nombre)]` o `def descargar(destino: Path)`. Usa `iica.descargar.bajar(url, ruta)`.
   - `def procesar(copia: Path) -> pd.DataFrame` con las columnas `nivel, unidad, anio, indicador, valor`:
     - `nivel`: `internacional` (unidad = ISO3), `nacional` (unidad = "MEX") o `estatal` (unidad = clave INEGI de 2 dígitos, "01"–"32"; ver `iica.rutas.ENTIDADES`).
     - Los valores deben venir **tal cual los publica la fuente**. La normalización se hace después, en `indice.py`.
     - Las tasas por habitante solo pueden usar poblaciones de una fuente citada.

## Comandos
```
uv run iica catalogo
uv run iica descargar --fuente <id>
uv run iica cobertura --fuente <id>
```

## Dimensiones del IICA
1. Capacidades cívicas y humanas
2. Inteligencia colectiva
3. Integración ética de la IA (y gobierno digital)
4. Instituciones habilitadoras y cocreación
5. Valor público democrático
6. Continuidad y retroalimentación

## Notas
- No agregues dependencias con `uv add`. Si necesitas una, avísalo en tu reporte. Ya están disponibles: pandas, requests, openpyxl, xlrd, pyreadstat, beautifulsoup4, lxml, pyarrow, pyyaml.
- No edites archivos de otras fuentes ni los módulos núcleo (`catalogo.py`, `descargar.py`, `procesar.py`, `cli.py`, `rutas.py`).
- Reporta el tamaño de los archivos crudos: los de más de 20 MB no se versionarán en git.
