import { copyFileSync, mkdirSync } from "node:fs"
import { join } from "node:path"
import { defineConfig } from "vite"
import react from "@vitejs/plugin-react"
import tailwindcss from "@tailwindcss/vite"

/** GitHub Pages отдаёт index.html только из папки маршрута — без этого /v2/ даёт 404 */
const SPA_FALLBACK_PATHS = ["v2", "v2/map", "method", "tour", "explorer", "building"]

export default defineConfig({
  base: "/chtenie-gorodskoy-pamyati/",
  plugins: [
    react(),
    tailwindcss(),
    {
      name: "github-pages-spa-fallback",
      closeBundle() {
        const out = join(__dirname, "dist")
        const index = join(out, "index.html")
        copyFileSync(index, join(out, "404.html"))
        for (const route of SPA_FALLBACK_PATHS) {
          const dir = join(out, route)
          mkdirSync(dir, { recursive: true })
          copyFileSync(index, join(dir, "index.html"))
        }
      },
    },
  ],
})
