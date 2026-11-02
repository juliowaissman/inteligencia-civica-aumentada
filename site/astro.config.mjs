import { defineConfig } from "astro/config";
import mdx from "@astrojs/mdx";

// Publicado en GitHub Pages: https://juliowaissman.github.io/inteligencia-civica-aumentada/
export default defineConfig({
  site: "https://juliowaissman.github.io",
  base: "/inteligencia-civica-aumentada",
  trailingSlash: "always",
  integrations: [mdx()],
});
