import { useEffect, useState } from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { evaluationRow, evaluationMetric } from '../lib/evaluationModes.js'
import { api } from '../api.js'
import { formatMetricValue } from '../lib/formatMetric.js'

const COLORS = ['#6ea8fe', '#f7768e', '#9ece6a', '#e0af68', '#bb9af7', '#7dcfff']

// One panel per method, stacked vertically, each showing metricKey's curve
// over checkpoints for every run of that method in the current dataset -
// so a method with three models (or one model swept over several lrs)
// shows all of those lines together on the same panel.
export default function ResultsGraph({ rows, metricKey, methodMeta, modelMeta, evaluation = 'original' }) {
  const [series, setSeries] = useState({})

  useEffect(() => {
    if (!rows.length) {
      setSeries({})
      return
    }
    Promise.all(rows.map((r) => api.checkpoints(r.run).then((cs) => [r.run, cs]))).then((pairs) =>
      setSeries(Object.fromEntries(pairs)),
    )
  }, [rows])

  const methods = [...new Set(rows.map((r) => r.method))]
  if (!methods.length) return <p className="dataset-missing">No results for this dataset yet.</p>

  return (
    <div className="graph-stack">
      {methods.map((method) => {
        const methodRuns = rows.filter((r) => r.method === method)
        const stepsSet = new Set()
        methodRuns.forEach((r) => (series[r.run] || []).forEach((c) => stepsSet.add(c.step)))
        const steps = [...stepsSet].sort((a, b) => a - b)
        const chartData = steps.map((step) => {
          const point = { step }
          for (const r of methodRuns) {
            const row = (series[r.run] || []).find((c) => c.step === step)
            if (row) point[r.run] = evaluationRow(row, evaluation)[metricKey === 'total_sec' ? 'elapsed_sec' : metricKey]
          }
          return point
        })

        return (
          <div className="chart-wrap" key={method}>
            <h3>{methodMeta[method]?.label || method}</h3>
            <ResponsiveContainer width="100%" height={280}>
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
                <XAxis dataKey="step" />
                <YAxis tickFormatter={(value) => formatMetricValue(evaluationMetric(metricKey, evaluation), value)} width={75} />
                <Tooltip formatter={(value) => formatMetricValue(evaluationMetric(metricKey, evaluation), value)} />
                <Legend />
                {methodRuns.map((r, i) => (
                  <Line
                    key={r.run}
                    type="monotone"
                    dataKey={r.run}
                    name={`${modelMeta[r.model]?.label || r.model}${methodRuns.length > 1 && methodRuns.filter((x) => x.model === r.model).length > 1 ? ` (${r.run})` : ''}`}
                    stroke={COLORS[i % COLORS.length]}
                    dot={false}
                  />
                ))}
              </LineChart>
            </ResponsiveContainer>
          </div>
        )
      })}
    </div>
  )
}
