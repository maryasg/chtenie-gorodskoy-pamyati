// Copy into use_figma scripts if needed (not executed standalone).
const INK = { r: 17 / 255, g: 17 / 255, b: 17 / 255 }
const BG = { r: 247 / 255, g: 247 / 255, b: 245 / 255 }
const RED = { r: 227 / 255, g: 30 / 255, b: 36 / 255 }
const MUTED = { r: 107 / 255, g: 107 / 255, b: 107 / 255 }
const WHITE = { r: 1, g: 1, b: 1 }

async function loadFonts() {
  const candidates = [
    { family: 'IBM Plex Mono', style: 'Regular' },
    { family: 'IBM Plex Mono', style: 'Medium' },
    { family: 'Cormorant Garamond', style: 'Regular' },
    { family: 'Inter', style: 'Regular' },
  ]
  const loaded = { mono: candidates[0], serif: candidates[2] }
  for (const f of candidates) {
    try {
      await figma.loadFontAsync(f)
    } catch (_) {
      /* skip */
    }
  }
  try {
    await figma.loadFontAsync(loaded.mono)
  } catch (_) {
    loaded.mono = { family: 'Inter', style: 'Regular' }
    await figma.loadFontAsync(loaded.mono)
  }
  try {
    await figma.loadFontAsync(loaded.serif)
  } catch (_) {
    loaded.serif = loaded.mono
  }
  return loaded
}

function solid(color, opacity = 1) {
  return [{ type: 'SOLID', color, opacity }]
}

function frameBorder(node) {
  node.strokes = solid(INK)
  node.strokeWeight = 1
}

async function addText(parent, name, characters, font, size = 11, color = INK) {
  const t = figma.createText()
  t.name = name
  t.fontName = font
  t.fontSize = size
  t.fills = solid(color)
  t.characters = characters
  parent.appendChild(t)
  t.layoutSizingHorizontal = 'FILL'
  return t
}

function nextX(padding = 120) {
  let max = 0
  for (const n of figma.currentPage.children) {
    max = Math.max(max, n.x + n.width)
  }
  return max + padding
}
