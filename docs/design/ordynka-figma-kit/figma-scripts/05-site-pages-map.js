// use_figma · page: 00 · Карта сайта
// All routes v1 + v2 with src file paths.

const INK = { r: 17 / 255, g: 17 / 255, b: 17 / 255 }
const BG = { r: 247 / 255, g: 247 / 255, b: 245 / 255 }
const MUTED = { r: 107 / 255, g: 107 / 255, b: 107 / 255 }
const RED = { r: 227 / 255, g: 30 / 255, b: 36 / 255 }

const V1 = [
  ['/', 'MapPage.tsx', 'src/pages/MapPage.tsx'],
  ['/method', 'MethodPage', 'src/pages/MethodPage.tsx'],
  ['/tour', 'TourPage', 'src/pages/TourPage.tsx'],
  ['/explorer', 'ExplorerPage', 'src/pages/ExplorerPage.tsx'],
  ['/building/:id', 'BuildingPage', 'src/pages/BuildingPage.tsx'],
  ['/building/:id/ar', 'ARPage', 'src/pages/ARPage.tsx'],
  ['/expert/:id', 'ExpertReviewPage', 'src/pages/ExpertReviewPage.tsx'],
]

const V2 = [
  ['/v2/', 'HomeV2', 'src/v2/pages/HomeV2.tsx'],
  ['/v2/map', 'MapPageV2', 'src/v2/pages/MapPageV2.tsx'],
  ['/v2/building/:id', 'BuildingPageV2', 'src/v2/pages/BuildingPageV2.tsx'],
  ['  Ordynka id', 'OrdynkaArkiPage', 'src/v2/pages/building/OrdynkaArkiPage.tsx'],
  ['  other ids', 'BuildingPageV2 default', 'src/v2/pages/BuildingPageV2.tsx'],
]

async function loadMono() {
  const f = { family: 'IBM Plex Mono', style: 'Regular' }
  try {
    await figma.loadFontAsync(f)
    return f
  } catch (_) {
    const i = { family: 'Inter', style: 'Regular' }
    await figma.loadFontAsync(i)
    return i
  }
}

function solid(c) {
  return [{ type: 'SOLID', color: c }]
}

const targetPage = figma.root.children.find((p) => p.name === '00 · Карта сайта')
if (!targetPage) {
  return { error: 'Page 00 missing — run 01-create-pages.js first' }
}
await figma.setCurrentPageAsync(targetPage)

const mono = await loadMono()
const createdNodeIds = []

const root = figma.createAutoLayout('HORIZONTAL', {
  name: 'SITE MAP / routes + code',
  x: 60,
  y: 60,
  itemSpacing: 40,
  paddingLeft: 32,
  paddingRight: 32,
  paddingTop: 32,
  paddingBottom: 32,
  fills: solid(BG),
  strokes: solid(INK),
  strokeWeight: 1,
})
createdNodeIds.push(root.id)

function column(title, rows, accent) {
  const col = figma.createAutoLayout('VERTICAL', {
    name: title,
    itemSpacing: 10,
    width: 420,
  })
  const h = figma.createText()
  h.fontName = mono
  h.fontSize = 12
  h.fills = solid(accent ? RED : INK)
  h.characters = title
  col.appendChild(h)
  createdNodeIds.push(h.id)

  for (const [url, label, path] of rows) {
    const row = figma.createAutoLayout('VERTICAL', {
      name: `${label}`,
      itemSpacing: 2,
      paddingLeft: 12,
      paddingRight: 12,
      paddingTop: 8,
      paddingBottom: 8,
      fills: solid({ r: 1, g: 1, b: 1 }),
      strokes: solid(INK),
      strokeWeight: 1,
      width: 400,
    })
    const t1 = figma.createText()
    t1.fontName = mono
    t1.fontSize = 10
    t1.fills = solid(INK)
    t1.characters = url
    const t2 = figma.createText()
    t2.fontName = mono
    t2.fontSize = 9
    t2.fills = solid(MUTED)
    t2.characters = path
    row.appendChild(t1)
    row.appendChild(t2)
    col.appendChild(row)
    createdNodeIds.push(row.id, t1.id, t2.id)
  }
  root.appendChild(col)
  createdNodeIds.push(col.id)
}

column('v1 · Layout.tsx', V1, false)
column('v2 · LayoutV2.tsx', V2, true)

const data = figma.createAutoLayout('VERTICAL', {
  name: 'DATA + public',
  itemSpacing: 6,
  width: 360,
  paddingLeft: 16,
  paddingTop: 16,
  paddingBottom: 16,
  fills: solid({ r: 0.95, g: 0.95, b: 0.93 }),
  strokes: solid(MUTED),
  strokeWeight: 1,
})
const dataLines = [
  'src/data/buildings/*.ts',
  'src/data/explorer/*.ts',
  'public/explorer/MOSCOW_00*/',
  'docs/DEVELOPER_MAP_RU.md',
]
for (const line of dataLines) {
  const t = figma.createText()
  t.fontName = mono
  t.fontSize = 9
  t.fills = solid(INK)
  t.characters = line
  data.appendChild(t)
  createdNodeIds.push(t.id)
}
root.appendChild(data)
createdNodeIds.push(data.id)

return { createdNodeIds, pageId: targetPage.id }
