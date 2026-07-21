// use_figma · page: 03 · Карточка · слои
// Full layer tree A–E with sublayers (editable names).

const INK = { r: 17 / 255, g: 17 / 255, b: 17 / 255 }
const BG = { r: 247 / 255, g: 247 / 255, b: 245 / 255 }
const RED = { r: 227 / 255, g: 30 / 255, b: 36 / 255 }
const MUTED = { r: 107 / 255, g: 107 / 255, b: 107 / 255 }

const LAYERS = [
  {
    block: 'A · CARD-HEADER',
    children: ['A1 · badge + Object ID', 'A2 · title + geo', 'A3 · map link + dating'],
  },
  {
    block: 'B · HERO-GRID',
    layout: '3 col: legend | facade | inspector',
    children: [
      'B1 · legend',
      'B2 · labeled facade (image)',
      'B3 · inspector',
      '  B3a · layer checklist',
      '  B3b · crossfade 1840→2026',
    ],
  },
  {
    block: 'C · FACADE-READING',
    layout: '2 col: main | overlay groups',
    children: [
      'C1a · section titles',
      'C1b · comparison picker',
      'C1c · ArchiviewFacadePanel',
      'C1d · photo density slider',
      'C1e · registration filter',
      'C2 · overlay groups L·01 K·02 A·03',
    ],
  },
  {
    block: 'D · NARRATIVE',
    children: ['D1 · summary quote', 'D2 · assessment counters (4)'],
  },
  {
    block: 'E · DOSSIER',
    children: [
      'E1 · timeline table',
      'E2a · artifacts',
      'E2b · sources',
      'E3 · tech footer',
    ],
  },
]

async function loadFonts() {
  const mono = { family: 'IBM Plex Mono', style: 'Regular' }
  try {
    await figma.loadFontAsync(mono)
  } catch (_) {
    await figma.loadFontAsync({ family: 'Inter', style: 'Regular' })
    return { mono: { family: 'Inter', style: 'Regular' } }
  }
  return { mono }
}

function solid(c) {
  return [{ type: 'SOLID', color: c }]
}

const targetPage = figma.root.children.find((p) => p.name === '03 · Карточка · слои')
await figma.setCurrentPageAsync(targetPage)

const fonts = await loadFonts()
const createdNodeIds = []

const card = figma.createAutoLayout('VERTICAL', {
  name: 'ORDYNKA / MOSCOW_001 / Desktop 1440',
  x: 40,
  y: 40,
  width: 1360,
  itemSpacing: 0,
  fills: solid(BG),
  strokes: solid(INK),
  strokeWeight: 1,
})
createdNodeIds.push(card.id)

const chrome = figma.createAutoLayout('HORIZONTAL', {
  name: 'CHROME · LayoutV2 (вне макета на сайте)',
  width: 1360,
  paddingLeft: 16,
  paddingRight: 16,
  paddingTop: 10,
  paddingBottom: 10,
  fills: solid({ r: 0.92, g: 0.92, b: 0.9 }),
  strokes: solid(MUTED),
  strokeWeight: 1,
  dashPattern: [4, 4],
})
const chromeT = figma.createText()
chromeT.fontName = fonts.mono
chromeT.fontSize = 9
chromeT.fills = solid(MUTED)
chromeT.characters = 'CHROME — шапка v2, навигация (не часть CARD)'
chrome.appendChild(chromeT)
card.appendChild(chrome)
createdNodeIds.push(chrome.id, chromeT.id)

for (const section of LAYERS) {
  const block = figma.createAutoLayout('VERTICAL', {
    name: section.block,
    width: 1360,
    itemSpacing: 8,
    paddingLeft: 20,
    paddingRight: 20,
    paddingTop: 16,
    paddingBottom: 16,
    fills: solid({ r: 1, g: 1, b: 1 }),
    strokes: solid(INK),
    strokeWeight: 1,
  })

  const head = figma.createText()
  head.fontName = fonts.mono
  head.fontSize = 11
  head.fills = solid(section.block.startsWith('B') ? RED : INK)
  head.characters = section.block + (section.layout ? ` · ${section.layout}` : '')
  block.appendChild(head)
  createdNodeIds.push(head.id)

  if (section.block.includes('B2') || section.block.includes('HERO')) {
    const imgPh = figma.createAutoLayout('VERTICAL', {
      name: 'B2 · labeled facade (image)',
      width: 1280,
      paddingTop: 80,
      paddingBottom: 80,
      itemSpacing: 8,
      fills: solid(BG),
      strokes: solid(INK),
      strokeWeight: 1,
    })
    const ph = figma.createText()
    ph.fontName = fonts.mono
    ph.fontSize = 9
    ph.fills = solid(MUTED)
    ph.characters = 'Перетащите: assets/cmp_005/marked-facade-labeled.png'
    imgPh.appendChild(ph)
    block.appendChild(imgPh)
    createdNodeIds.push(imgPh.id, ph.id)
  }

  for (const child of section.children) {
    if (child.includes('B2 ·')) continue
    const row = figma.createAutoLayout('HORIZONTAL', {
      name: child.trim(),
      width: 1280,
      paddingLeft: 12,
      paddingTop: 6,
      paddingBottom: 6,
      itemSpacing: 8,
      fills: solid(BG),
      strokes: solid(MUTED),
      strokeWeight: 1,
    })
    const dot = figma.createRectangle()
    dot.resize(8, 8)
    dot.fills = solid(child.trim().startsWith('C2') ? RED : INK)
    row.appendChild(dot)
    const t = figma.createText()
    t.fontName = fonts.mono
    t.fontSize = 10
    t.fills = solid(INK)
    t.characters = child.trim()
    row.appendChild(t)
    block.appendChild(row)
    createdNodeIds.push(row.id, dot.id, t.id)
  }

  card.appendChild(block)
  createdNodeIds.push(block.id)
}

const hint = figma.createText()
hint.name = 'import-hint'
hint.x = 40
hint.y = card.y + card.height + 24
hint.fontName = fonts.mono
hint.fontSize = 9
hint.fills = solid(MUTED)
hint.characters =
  'Референс: страница 04 или docs/design/ordynka-figma-kit/assets/reference/*.png'
figma.currentPage.appendChild(hint)
createdNodeIds.push(hint.id)

return { createdNodeIds, pageId: targetPage.id, cardFrameId: card.id }
