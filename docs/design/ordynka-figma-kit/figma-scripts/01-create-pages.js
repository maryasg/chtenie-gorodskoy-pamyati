// use_figma · skillNames: figma-use, figma-generate-design
// Creates 4 pages in the target design file.

const pageNames = [
  '00 · Карта сайта',
  '01 · Схема проекта',
  '02 · Design tokens',
  '03 · Карточка · слои',
  '04 · Референс',
]

figma.root.children[0].name = pageNames[0]
const createdPageIds = [figma.root.children[0].id]

for (let i = 1; i < pageNames.length; i++) {
  const p = figma.createPage()
  p.name = pageNames[i]
  createdPageIds.push(p.id)
}

await figma.setCurrentPageAsync(figma.root.children[0])

return { createdPageIds, pageNames }
