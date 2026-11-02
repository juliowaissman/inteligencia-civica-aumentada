// Gráficos con Observable Plot. Cada función dibuja dentro de un contenedor.
import * as Plot from "@observablehq/plot";
import { feature } from "topojson-client";
import { DIM_COLOR, DIM_CORTO, num } from "../lib/formato";

const BASE = import.meta.env.BASE_URL;
const ancho = (el: HTMLElement) => Math.max(320, el.clientWidth);
const estilo = { background: "transparent", color: "currentColor", fontSize: "13px", fontFamily: "inherit" };

function montar(el: HTMLElement, svg: Element) {
  el.replaceChildren(svg);
}

/** Barras horizontales del índice con su intervalo de rangos (sensibilidad). */
export function ranking(el: HTMLElement, unidades: any[], resaltar: Record<string, string>) {
  const datos = unidades.filter((u) => u.indice !== null).sort((a, b) => b.indice - a.indice);
  const color = (u: any) => resaltar[u.id] ?? "#8f9bc4";
  montar(el, Plot.plot({
    width: ancho(el),
    height: datos.length * 17 + 50,
    marginLeft: 150,
    marginRight: 70,
    style: estilo,
    x: { domain: [0, 100], label: "IICA parcial (0–100)", grid: true },
    y: { domain: datos.map((d) => d.corto), label: null },
    marks: [
      Plot.barX(datos, { x: "indice", y: "corto", fill: color, title: (d: any) =>
        `${d.nombre}\nIICA: ${num(d.indice)}\nLugar ${d.rango} (intervalo ${d.rango_p5}–${d.rango_p95})` }),
      Plot.text(datos, { x: "indice", y: "corto", text: (d: any) => `${num(d.indice)}  [${d.rango_p5}–${d.rango_p95}]`,
        dx: 4, textAnchor: "start", fontSize: 11, fill: "currentColor" }),
    ],
  }));
}

/** Perfil por dimensión de varias series (barras agrupadas). */
export function perfil(el: HTMLElement, series: { nombre: string; color: string; dims: Record<string, number | null> }[]) {
  const filas = series.flatMap((s) => Object.entries(s.dims).map(([d, v]) => ({ serie: s.nombre, dim: `${d}. ${DIM_CORTO[d]}`, v })));
  montar(el, Plot.plot({
    width: ancho(el),
    height: 330,
    marginBottom: 60,
    style: estilo,
    color: { domain: series.map((s) => s.nombre), range: series.map((s) => s.color), legend: true },
    // En pantallas angostas solo se muestra el número de la dimensión.
    fx: { label: null, tickFormat: (d: string) => ancho(el) < 640 ? d.split(".")[0] : d.length > 18 ? d.slice(0, 17) + "…" : d },
    x: { axis: null, domain: series.map((s) => s.nombre) },
    y: { domain: [0, 100], label: "Puntaje (0–100)", grid: true },
    marks: [
      Plot.barY(filas.filter((f) => f.v !== null), { fx: "dim", x: "serie", y: "v", fill: "serie",
        title: (f: any) => `${f.serie}\n${f.dim}: ${num(f.v)}` }),
      Plot.ruleY([0]),
    ],
  }));
}

/** Serie de tiempo por dimensión (nivel nacional). */
export function serie(el: HTMLElement, filas: any[]) {
  const largo = filas.flatMap((r) => [
    ...Object.entries(r.dims).filter(([, v]) => v !== null).map(([d, v]) => ({ anio: r.anio, serie: `${d}. ${DIM_CORTO[d]}`, v, dim: d })),
    ...(r.indice !== null ? [{ anio: r.anio, serie: "IICA-N agregado", v: r.indice, dim: "0" }] : []),
  ]);
  const dominio = [...new Set(largo.map((f) => f.serie))].sort();
  const rango = dominio.map((s) => s === "IICA-N agregado" ? "currentColor" : DIM_COLOR[s[0]]);
  montar(el, Plot.plot({
    width: ancho(el),
    height: 380,
    style: estilo,
    color: { domain: dominio, range: rango, legend: true },
    x: { label: null, tickFormat: "d" },
    y: { domain: [0, 100], label: "Puntaje (0–100, límites fijos)", grid: true },
    marks: [
      Plot.lineY(largo, { x: "anio", y: "v", stroke: "serie", strokeWidth: (d: any) => d.dim === "0" ? 3.5 : 1.8, marker: "circle" }),
      Plot.tip(largo, Plot.pointer({ x: "anio", y: "v", title: (d: any) => `${d.serie}\n${d.anio}: ${num(d.v)}` })),
    ],
  }));
}

async function topo(nombre: string, objeto: string) {
  const t = await (await fetch(`${BASE}geo/${nombre}`)).json();
  return feature(t, t.objects[objeto]) as any;
}

/** Mapa coroplético de países (solo se colorean los países de comparación). */
export async function mapaMundo(el: HTMLElement, unidades: any[], campo: (u: any) => number | null, etiqueta: string) {
  const geo = await topo("mundo.topo.json", "paises");
  const val = new Map(unidades.map((u) => [u.id, u]));
  montar(el, Plot.plot({
    width: ancho(el),
    projection: { type: "equal-earth", domain: { type: "FeatureCollection", features: geo.features.filter((f: any) => val.has(f.properties.iso3)) } },
    style: estilo,
    color: { type: "linear", domain: [0, 100], scheme: "blues", legend: true, label: etiqueta, unknown: "#d9dce6" },
    marks: [
      Plot.geo(geo, { fill: (f: any) => { const u = val.get(f.properties.iso3); return u ? campo(u) : null; },
        stroke: "white", strokeWidth: 0.4,
        title: (f: any) => { const u = val.get(f.properties.iso3); return u ? `${u.nombre}: ${num(campo(u))}` : ""; } }),
      Plot.geo(geo.features.filter((f: any) => f.properties.iso3 === "MEX"), { stroke: "#b8007c", strokeWidth: 2 }),
    ],
  }));
}

/** Mapa coroplético de las 32 entidades. */
export async function mapaEstados(el: HTMLElement, unidades: any[], campo: (u: any) => number | null, etiqueta: string) {
  const geo = await topo("estados.topo.json", "estados");
  const val = new Map(unidades.map((u) => [u.id, u]));
  montar(el, Plot.plot({
    width: ancho(el),
    projection: { type: "conic-conformal", parallels: [17.5, 29.5], rotate: [102, 0], domain: geo },
    style: estilo,
    color: { type: "linear", domain: [0, 100], scheme: "blues", legend: true, label: etiqueta },
    marks: [
      Plot.geo(geo, { fill: (f: any) => campo(val.get(f.properties.cve)), stroke: "white", strokeWidth: 0.6,
        title: (f: any) => { const u = val.get(f.properties.cve); return `${u?.nombre}: ${num(campo(u))} (lugar ${u?.rango})`; } }),
      Plot.geo(geo.features.filter((f: any) => ["08", "26"].includes(f.properties.cve)), { stroke: "#b8007c", strokeWidth: 2.2 }),
    ],
  }));
}
