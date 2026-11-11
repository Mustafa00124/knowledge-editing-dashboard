// One row of method dots under a record or a question on the Datasets page:
// one dot per core editing method, split into 4 quarters, one per main model
// (clockwise from the top left: Qwen, Olmo, Llama, Mistral). A quarter is
// green when that model's answer after the edit passes (for unrelated
// questions: kept its own pre-edit answer), red when it fails, yellow when
// the judge was unclear, and grey when the method has no run that edited
// this record on that model. Clicking a dot opens the answers, one tab per
// model.

const PASS = new Set(['pass', 'kept'])
const FAIL = new Set(['original', 'none', 'other', 'changed'])

export function quarterState(dot) {
  if (!dot || !dot.status) return 'na'
  if (PASS.has(dot.status)) return 'pass'
  if (FAIL.has(dot.status)) return 'fail'
  return 'unclear'
}

// Quarter paths of a circle of radius r centred at (r, r), in model order.
function quarters(r) {
  const c = r
  return [
    `M${c},${c} L${c},0 A${r},${r} 0 0,0 0,${c} Z`,      // top left
    `M${c},${c} L${2 * r},${c} A${r},${r} 0 0,0 ${c},0 Z`, // top right
    `M${c},${c} L${c},${2 * r} A${r},${r} 0 0,0 ${2 * r},${c} Z`, // bottom right
    `M${c},${c} L0,${c} A${r},${r} 0 0,0 ${c},${2 * r} Z`, // bottom left
  ]
}

export function QuarterDot({ byModel, models, size = 12 }) {
  const r = size / 2
  return (
    <svg className="sids-method-dot-svg" width={size} height={size} viewBox={`0 0 ${size} ${size}`} aria-hidden="true">
      {quarters(r).map((d, i) => (
        <path key={i} d={d} className={`sids-mq is-${quarterState(byModel?.[models[i]])}`} />
      ))}
      <circle cx={r} cy={r} r={r - 0.5} className="sids-mq-ring" />
    </svg>
  )
}

const STATE_WORD = { pass: 'passed', fail: 'failed', unclear: 'unclear', na: 'not run' }

export default function MethodDots({ byMethod, methods, models, modelLabel, onOpen }) {
  return (
    <span className="sids-method-dots" role="group" aria-label="Editing methods, after the edit">
      {methods.map((m) => {
        const byModel = byMethod?.[m.key] || {}
        const ran = models.filter((mo) => byModel[mo])
        const title = `${m.label} after editing: ` + models.map((mo) =>
          `${modelLabel(mo)} ${STATE_WORD[quarterState(byModel[mo])]}`).join(', ')
        return (
          <button key={m.key} type="button" className="sids-method-dot" title={ran.length ? `${title}. Click for the answers.` : title}
            disabled={!ran.length} onClick={() => onOpen(m, ran[0] || models[0])}>
            <QuarterDot byModel={byModel} models={models} />
          </button>
        )
      })}
    </span>
  )
}
