// Utilidades compartidas: formato de números (es-MX) y colores por dimensión.

export const DIM_COLOR: Record<string, string> = {
  "1": "#2c5cd6", // azul (aclarado para que funcione en modo claro y oscuro)
  "2": "#0099d9", // cian
  "3": "#b8007c", // magenta
  "4": "#008e45", // verde
  "5": "#d42a32", // rojo
  "6": "#c9a800", // amarillo oscurecido
};

export const DIM_CORTO: Record<string, string> = {
  "1": "Capacidades cívicas y humanas",
  "2": "Inteligencia colectiva",
  "3": "IA ética y gobierno digital",
  "4": "Instituciones habilitadoras",
  "5": "Valor público democrático",
  "6": "Continuidad e innovación",
};

export const CAPA: Record<string, string> = {
  instalada: "Capacidad instalada",
  activacion: "Activación",
  resultado: "Resultado emergente",
};

const nf = (d: number) => new Intl.NumberFormat("es-MX", { maximumFractionDigits: d, minimumFractionDigits: d });

export function num(x: number | null | undefined, d = 1): string {
  if (x === null || x === undefined || Number.isNaN(x)) return "sin información";
  return nf(d).format(x);
}

/** Decimales adecuados según la magnitud del valor original. */
export function valor(x: number | null | undefined): string {
  if (x === null || x === undefined) return "sin información";
  const a = Math.abs(x);
  return num(x, a >= 1000 ? 0 : a >= 10 ? 1 : a >= 1 ? 2 : 3);
}

export function unidadMedida(ind: { unidad_medida?: string | null; transformacion?: string | null }): string {
  if (ind.transformacion === "por_100k") return "por 100 mil hab.";
  return ind.unidad_medida ?? "";
}
