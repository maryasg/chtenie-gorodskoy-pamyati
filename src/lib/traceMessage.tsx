export function splitTraceMessage(text: string): { body: string; source?: string } {
  const marker = '\n\nИсточник:'
  const idx = text.indexOf(marker)
  if (idx === -1) return { body: text }
  return {
    body: text.slice(0, idx).trim(),
    source: text.slice(idx + marker.length).trim(),
  }
}

export function TraceMessageBody({
  text,
  bodyClassName = '',
  sourceClassName = '',
}: {
  text: string
  bodyClassName?: string
  sourceClassName?: string
}) {
  const { body, source } = splitTraceMessage(text)
  return (
    <>
      <span className={bodyClassName}>{body}</span>
      {source ? (
        <span className={`mt-2 block ${sourceClassName}`}>Источник: {source}</span>
      ) : null}
    </>
  )
}
