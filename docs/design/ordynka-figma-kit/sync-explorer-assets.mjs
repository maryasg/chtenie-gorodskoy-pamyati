#!/usr/bin/env node
/**
 * Скачивает PNG/JPG фасада MOSCOW_001 с GitHub Pages (без локального Archiview).
 * node docs/design/ordynka-figma-kit/sync-explorer-assets.mjs
 */
import { mkdir, writeFile } from 'node:fs/promises'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const OUT = path.join(__dirname, 'assets')
const BASE =
  process.env.ORDYNKA_ASSET_BASE ??
  'https://maryasg.github.io/chtenie-gorodskoy-pamyati/pr-preview/pr-152/explorer/MOSCOW_001'

const FILES = [
  'comparisons/cmp_005/marked-facade.png',
  'comparisons/cmp_005/marked-facade-labeled.png',
  'comparisons/cmp_005/historical-rectified.png',
  'comparisons/cmp_005/modern-rectified.png',
  'comparisons/cmp_008/marked-facade-labeled.png',
  'comparisons/cmp_009/marked-facade-labeled.png',
  'time-layers/1840.jpg',
  'time-layers/1924.jpg',
  'time-layers/1930.jpg',
  'time-layers/2026.jpg',
]

const mapLocal = (rel) => {
  if (rel.startsWith('comparisons/cmp_005/')) return path.join('cmp_005', path.basename(rel))
  if (rel.startsWith('comparisons/cmp_008/')) return path.join('cmp_008', path.basename(rel))
  if (rel.startsWith('comparisons/cmp_009/')) return path.join('cmp_009', path.basename(rel))
  return rel
}

for (const rel of FILES) {
  const dest = path.join(OUT, mapLocal(rel))
  await mkdir(path.dirname(dest), { recursive: true })
  const url = `${BASE}/${rel}`
  const res = await fetch(url)
  if (!res.ok) {
    console.warn('skip', rel, res.status)
    continue
  }
  const buf = Buffer.from(await res.arrayBuffer())
  await writeFile(dest, buf)
  console.log('ok', mapLocal(rel), `${(buf.length / 1024).toFixed(0)} KiB`)
}
