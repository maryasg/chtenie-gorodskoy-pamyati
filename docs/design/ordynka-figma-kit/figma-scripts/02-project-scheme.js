// use_figma · page: 01 · Схема проекта
// Site architecture + link to Ordynka card blocks.

const INK = { r: 17 / 255, g: 17 / 255, b: 17 / 255 }
const BG = { r: 247 / 255, g: 247 / 255, b: 245 / 255 }
const RED = { r: 227 / 255, g: 30 / 255, b: 36 / 255 }
const MUTED = { r: 107 / 255, g: 107 / 255, b: 107 / 255 }

async function loadFonts() {
  const mono = { family: 'IBM Plex Mono', style: 'Regular' }
  const serif = { family: 'Cormorant Garamond', style: 'Regular' }
  try {
    await figma.loadFontAsync(mono)
  } catch (_) {
    await figma.loadFontAsync({ family: 'Inter', style: 'Regular' })
    return { mono: { family: 'Inter', style: 'Regular' }, serif: { family: 'Inter', style: 'Regular' } }
  }
  try {
    await figma.loadFontAsync(serif)
  } catch (_) {
    return { mono, serif: mono }
  }
  return { mono, serif }
}

function solid(c) {
  return [{ type: 'SOLID', color: c }]
}

const targetPage = figma.root.children.find((p) => p.name === '01 · Схема проекта')
await figma.setCurrentPageAsync(targetPage)

const fonts = await loadFonts()
const createdNodeIds = []

const root = figma.createAutoLayout('VERTICAL', {
  name: 'SCHEME / Site + v2 + Ordynka',
  x: 80,
  y: 80,
  width: 960,
  paddingLeft: 32,
  paddingRight: 32,
  paddingTop: 32,
  paddingBottom: 32,
  itemSpacing: 24,
  fills: solid(BG),
  strokes: solid(INK),
  strokeWeight: 1,
})
createdNodeIds.push(root.id)

const title = figma.createText()
title.name = 'title'
title.fontName = fonts.serif
title.fontSize = 36
title.fills = solid(INK)
title.characters = 'Память стен · схема проекта (v2)'
root.appendChild(title)
createdNodeIds.push(title.id)

const sub = figma.createText()
sub.name = 'subtitle'
sub.fontName = fonts.mono
sub.fontSize = 10
sub.fills = solid(MUTED)
sub.characters =
  'Repo: chtenie-gorodskoy-pamyati · branch cursor/lovable-design-v2-3b69 · PR #152'
root.appendChild(sub)
createdNodeIds.push(sub.id)

function box(name, lines, accent = false) {
  const f = figma.createAutoLayout('VERTICAL', {
    name,
    itemSpacing: 6,
    paddingLeft: 16,
    paddingRight: 16,
    paddingTop: 12,
    paddingBottom: 12,
    fills: solid({ r: 1, g: 1, b: 1 }),
    strokes: solid(accent ? RED : INK),
    strokeWeight: 1,
    width: 896,
  })
  for (const line of lines) {
    const t = figma.createText()
    t.fontName = fonts.mono
    t.fontSize = 10
    t.fills = solid(line.startsWith('→') ? MUTED : INK)
    t.characters = line
    f.appendChild(t)
    createdNodeIds.push(t.id)
  }
  root.appendChild(f)
  createdNodeIds.push(f.id)
  return f
}

box('SITE / GitHub Pages', [
  'Base: /chtenie-gorodskoy-pamyati/',
  'v1 production: /  (Layout, без изменений в PR)',
  'v2 preview: /v2/  (LayoutV2, arki-theme)',
  'PR preview: /pr-preview/pr-152/v2/...',
])

box('V2 / Routes (src/App.tsx)', [
  '/v2/ → HomeV2',
  '/v2/map → MapPageV2',
  '/v2/building/:id → BuildingPageV2',
])

box('BUILDING / Router (BuildingPageV2.tsx)', [
  'id === MOSCOW_001_kumaninykh → OrdynkaArkiPage',
  'иначе → BuildingPageV2Default (manifest plates)',
], true)

box('ORDYNKA / Code map', [
  'Страница: src/v2/pages/building/OrdynkaArkiPage.tsx',
  'Стили: src/v2/arki-theme.css',
  'Данные: src/data/buildings/moscow001.ts',
  'Archiview: public/explorer/MOSCOW_001/ (cmp_005 default)',
  'Референс UI: arki-view-magic Lovable /building/05',
])

const cardTitle = figma.createText()
cardTitle.name = 'card-blocks-title'
cardTitle.fontName = fonts.mono
cardTitle.fontSize = 11
cardTitle.fills = solid(RED)
cardTitle.characters = 'CARD · уровни (страница 03) — CHROME вне карточки (LayoutV2)'
root.appendChild(cardTitle)
createdNodeIds.push(cardTitle.id)

const row = figma.createAutoLayout('HORIZONTAL', { name: 'CARD / block codes', itemSpacing: 8, width: 896 })
const blocks = ['A HEADER', 'B HERO', 'C FACADE', 'D NARRATIVE', 'E DOSSIER']
for (const b of blocks) {
  const chip = figma.createAutoLayout('HORIZONTAL', {
    name: b,
    paddingLeft: 10,
    paddingRight: 10,
    paddingTop: 8,
    paddingBottom: 8,
    fills: solid(INK),
  })
  const t = figma.createText()
  t.fontName = fonts.mono
  t.fontSize = 9
  t.fills = solid({ r: 1, g: 1, b: 1 })
  t.characters = b
  chip.appendChild(t)
  row.appendChild(chip)
  createdNodeIds.push(chip.id, t.id)
}
root.appendChild(row)
createdNodeIds.push(row.id)

const note = figma.createText()
note.name = 'edit-hint'
note.fontName = fonts.mono
note.fontSize = 9
note.fills = solid(MUTED)
note.characters =
  'Правки в Figma и в коде — по кодам A1, B2, C1c… См. layer-tree.json в репозитории.'
root.appendChild(note)
createdNodeIds.push(note.id)

return { createdNodeIds, pageId: targetPage.id }
