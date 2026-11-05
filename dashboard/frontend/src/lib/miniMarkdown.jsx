// A small Markdown renderer for text the backend passes through from a
// project document (CRITERIA.md's review guides): paragraphs, nested "- "
// lists with wrapped lines, pipe tables, **bold**, *italic* and `code`.
// Anything else shows as plain text.

const INLINE = /(\*\*[^*]+\*\*|\*[^*\s][^*]*\*|`[^`]+`)/g

function Inline({ text }) {
  return text.split(INLINE).map((part, i) => {
    if (part.startsWith('**') && part.endsWith('**') && part.length > 4) return <strong key={i}>{part.slice(2, -2)}</strong>
    if (part.startsWith('`') && part.endsWith('`') && part.length > 2) return <code key={i}>{part.slice(1, -1)}</code>
    if (part.startsWith('*') && part.endsWith('*') && part.length > 2) return <em key={i}>{part.slice(1, -1)}</em>
    return part
  })
}

const indentOf = (line) => line.length - line.trimStart().length

// Blocks: {type: 'p', text} | {type: 'list', items} | {type: 'table', rows}.
// A list item: {text, children: list items, after: text that follows its children}.
export function parseMarkdown(md) {
  const blocks = []
  let block = null
  let stack = [] // open list items: {item, content} where content is the indent of its text
  const close = () => { block = null; stack = [] }
  for (const raw of (md || '').split('\n')) {
    const line = raw.replace(/\s+$/, '')
    if (!line.trim()) { close(); continue }
    const item = line.match(/^(\s*)[-*] (.*)$/)
    if (line.trimStart().startsWith('|')) {
      if (block?.type !== 'table') { close(); block = { type: 'table', rows: [] }; blocks.push(block) }
      const cells = line.trim().replace(/^\||\|$/g, '').split('|').map((c) => c.trim())
      if (!cells.every((c) => /^:?-+:?$/.test(c))) block.rows.push(cells)
    } else if (item) {
      const indent = item[1].length
      const node = { text: item[2], children: [], after: '' }
      if (block?.type !== 'list') { close(); block = { type: 'list', items: [] }; blocks.push(block) }
      while (stack.length && stack[stack.length - 1].content > indent) stack.pop()
      const parent = stack[stack.length - 1]
      if (parent && indent >= parent.content) parent.item.children.push(node)
      else { if (parent) stack.pop(); block.items.push(node) }
      stack.push({ item: node, content: indent + 2 })
    } else if (block?.type === 'list' && stack.length) {
      // A wrapped line continues the deepest item it is indented under; text
      // after an item's sub-list is kept as its closing paragraph.
      const indent = indentOf(line)
      while (stack.length > 1 && stack[stack.length - 1].content > indent) stack.pop()
      const { item: target } = stack[stack.length - 1]
      if (target.children.length) target.after = `${target.after} ${line.trim()}`.trim()
      else target.text = `${target.text} ${line.trim()}`
    } else if (block?.type === 'p') {
      block.text = `${block.text} ${line.trim()}`
    } else {
      close()
      block = { type: 'p', text: line.trim() }
      blocks.push(block)
    }
  }
  return blocks
}

function List({ items }) {
  return (
    <ul>
      {items.map((it, i) => (
        <li key={i}>
          <Inline text={it.text} />
          {it.children.length > 0 && <List items={it.children} />}
          {it.after && <p><Inline text={it.after} /></p>}
        </li>
      ))}
    </ul>
  )
}

export default function Markdown({ text, className = '' }) {
  return (
    <div className={`mini-md ${className}`}>
      {parseMarkdown(text).map((b, i) => {
        if (b.type === 'list') return <List key={i} items={b.items} />
        if (b.type === 'table') {
          const [head, ...body] = b.rows
          return (
            <div key={i} className="mini-md-table">
              <table>
                <thead><tr>{head.map((h, j) => <th key={j}><Inline text={h} /></th>)}</tr></thead>
                <tbody>{body.map((row, r) => <tr key={r}>{row.map((c, j) => <td key={j}><Inline text={c} /></td>)}</tr>)}</tbody>
              </table>
            </div>
          )
        }
        return <p key={i}><Inline text={b.text} /></p>
      })}
    </div>
  )
}
