// use_figma · page: 02 · Design tokens

const INK = { r: 17 / 255, g: 17 / 255, b: 17 / 255 }
const BG = { r: 247 / 255, g: 247 / 255, b: 245 / 255 }
const MUTED = { r: 107 / 255, g: 107 / 255, b: 107 / 255 }

const COLORS = [
  { name: 'ink', hex: '#111111', usage: 'текст, сетка', rgb: INK },
  { name: 'muted', hex: '#6B6B6B', usage: 'вторичный текст', rgb: MUTED },
  { name: 'red', hex: '#E31E24', usage: 'акцент, Verified', rgb: { r: 227 / 255, g: 30 / 255, b: 36 / 255 } },
  { name: 'bg', hex: '#F7F7F5', usage: 'фон страницы', rgb: BG },
  { name: 'white', hex: '#FFFFFF', usage: 'панели', rgb: { r: 1, g: 1, b: 1 } },
  { name: 'overlayLost', hex: '#E31E24', usage: 'L·01', rgb: { r: 227 / 255, g: 30 / 255, b: 36 / 255 } },
  { name: 'overlayKept', hex: '#059669', usage: 'K·02', rgb: { r: 5 / 255, g: 150 / 255, b: 105 / 255 } },
  { name: 'overlayAdded', hex: '#0284C7', usage: 'A·03', rgb: { r: 2 / 255, g: 132 / 255, b: 199 / 255 } },
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

const targetPage = figma.root.children.find((p) => p.name === '02 · Design tokens')
await figma.setCurrentPageAsync(targetPage)

const mono = await loadMono()
const createdNodeIds = []

const board = figma.createAutoLayout('VERTICAL', {
  name: 'TOKENS / Arki v2',
  x: 80,
  y: 80,
  itemSpacing: 20,
  paddingLeft: 28,
  paddingRight: 28,
  paddingTop: 28,
  paddingBottom: 28,
  fills: solid(BG),
  strokes: solid(INK),
  strokeWeight: 1,
})
createdNodeIds.push(board.id)

const h = figma.createText()
h.fontName = mono
h.fontSize = 14
h.fills = solid(INK)
h.characters = 'Design tokens · OrdynkaArkiPage'
h.name = 'heading'
board.appendChild(h)
createdNodeIds.push(h.id)

const typeBlock = figma.createAutoLayout('VERTICAL', { name: 'Typography', itemSpacing: 8, width: 800 })
const typeLines = [
  'Serif: Cormorant Garamond — заголовки, цитата D1',
  'Mono: IBM Plex Mono 10px, letter-spacing 0.12em, uppercase — UI',
  'CSS: src/v2/arki-theme.css',
]
for (const line of typeLines) {
  const t = figma.createText()
  t.fontName = mono
  t.fontSize = 10
  t.fills = solid(INK)
  t.characters = line
  typeBlock.appendChild(t)
  createdNodeIds.push(t.id)
}
board.appendChild(typeBlock)
createdNodeIds.push(typeBlock.id)

const grid = figma.createAutoLayout('HORIZONTAL', {
  name: 'Colors',
  itemSpacing: 16,
  layoutWrap: 'WRAP',
  width: 800,
})

for (const c of COLORS) {
  const card = figma.createAutoLayout('VERTICAL', {
    name: `color / ${c.name}`,
    itemSpacing: 6,
    width: 160,
  })
  const sw = figma.createRectangle()
  sw.name = 'swatch'
  sw.resize(160, 72)
  sw.fills = solid(c.rgb)
  sw.strokes = solid(INK)
  sw.strokeWeight = 1
  card.appendChild(sw)
  const t1 = figma.createText()
  t1.fontName = mono
  t1.fontSize = 9
  t1.fills = solid(INK)
  t1.characters = `${c.name} · ${c.hex}`
  card.appendChild(t1)
  const t2 = figma.createText()
  t2.fontName = mono
  t2.fontSize = 8
  t2.fills = solid(MUTED)
  t2.characters = c.usage
  card.appendChild(t2)
  grid.appendChild(card)
  createdNodeIds.push(card.id, sw.id, t1.id, t2.id)
}

board.appendChild(grid)
createdNodeIds.push(grid.id)

return { createdNodeIds, pageId: targetPage.id }
