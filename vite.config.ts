import { copyFileSync, existsSync, mkdirSync } from "node:fs"
import { join } from "node:path"
import { defineConfig } from "vite"
import react from "@vitejs/plugin-react"
import tailwindcss from "@tailwindcss/vite"
import { BUILDINGS } from "./src/data/buildings"

const SPA_FALLBACK_PATHS = [
  "v2",
  "v2/map",
  "method",
  "tour",
  "explorer",
  "building",
  ...BUILDINGS.map((b) => `v2/building/${b.id}`),
]

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
        if (!existsSync(index)) {
          return
        }
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
