/**
 * Full-page and per-block PNGs for Figma import.
 * Run: node docs/design/ordynka-figma-kit/capture-screenshots.mjs
 * Requires: dev server at BASE_URL (npm run dev).
 */
import { chromium } from 'playwright'
import { mkdir } from 'node:fs/promises'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const OUT = path.join(__dirname, 'assets', 'reference')
const BASE_URL =
  process.env.ORDYNKA_SCREENSHOT_URL ??
  'http://127.0.0.1:5173/chtenie-gorodskoy-pamyati/v2/building/MOSCOW_001_kumaninykh/'

const BLOCKS = [
  'A-CARD-HEADER',
  'B-HERO-GRID',
  'C-FACADE-READING',
  'D-NARRATIVE',
  'E-DOSSIER',
]

await mkdir(OUT, { recursive: true })

const browser = await chromium.launch()
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } })
await page.goto(BASE_URL, { waitUntil: 'networkidle', timeout: 120_000 })
await page.waitForSelector('[data-figma-block="A-CARD-HEADER"]', { timeout: 60_000 })
await page.waitForTimeout(1500)

await page.screenshot({
  path: path.join(OUT, '00-full-page-1440.png'),
  fullPage: true,
})

for (const id of BLOCKS) {
  const el = page.locator(`[data-figma-block="${id}"]`)
  await el.scrollIntoViewIfNeeded()
  await page.waitForTimeout(300)
  await el.screenshot({ path: path.join(OUT, `${id}.png`) })
}

await browser.close()
console.log('Saved screenshots to', OUT)
