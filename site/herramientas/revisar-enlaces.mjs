// Revisa que todo enlace interno (href/src) del sitio construido apunte a un archivo existente
// y que cada ancla #id de la página de referencias exista. Uso: node herramientas/revisar-enlaces.mjs
import { readdirSync, readFileSync, existsSync, statSync } from "node:fs";
import { join } from "node:path";

const DIST = new URL("../dist/", import.meta.url).pathname;
const BASE = "/inteligencia-civica-aumentada/";
const paginas = [];
const recorrer = (d) => readdirSync(d).forEach((f) => {
  const p = join(d, f);
  statSync(p).isDirectory() ? recorrer(p) : p.endsWith(".html") && paginas.push(p);
});
recorrer(DIST);

const ids = new Map();
const idsDe = (archivo) => {
  if (!ids.has(archivo)) ids.set(archivo, new Set([...readFileSync(archivo, "utf8").matchAll(/\sid="([^"]+)"/g)].map((m) => m[1])));
  return ids.get(archivo);
};

let errores = 0;
for (const pag of paginas) {
  const html = readFileSync(pag, "utf8");
  for (const [, url] of html.matchAll(/(?:href|src)="([^"]+)"/g)) {
    if (!url.startsWith(BASE)) continue;
    const [ruta, ancla] = url.slice(BASE.length).split("#");
    let archivo = join(DIST, ruta);
    if (ruta === "" || ruta.endsWith("/")) archivo = join(archivo, "index.html");
    if (!existsSync(archivo)) { console.error(`✗ ${pag.replace(DIST, "")}: no existe ${url}`); errores++; continue; }
    if (ancla && archivo.endsWith(".html") && !idsDe(archivo).has(ancla)) {
      console.error(`✗ ${pag.replace(DIST, "")}: ancla inexistente ${url}`); errores++;
    }
  }
}
console.log(`${paginas.length} páginas revisadas, ${errores} enlace(s) roto(s).`);
process.exit(errores ? 1 : 0);
