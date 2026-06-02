import { copyFileSync } from "node:fs"
import { join } from "node:path"
import { defineConfig } from "vite"
import react from "@vitejs/plugin-react"
import tailwindcss from "@tailwindcss/vite"

export default defineConfig({
  base: "/chtenie-gorodskoy-pamyati/",
  plugins: [
    react(),
    tailwindcss(),
    {
      // GitHub Pages: прямые ссылки (/building/...) отдают 404.html = тот же SPA
      name: "github-pages-spa-fallback",
      closeBundle() {
        const out = join(__dirname, "dist")
        copyFileSync(join(out, "index.html"), join(out, "404.html"))
      },
    },
  ],
})
