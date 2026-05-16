import { useEffect, useState } from 'react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import { Activity } from 'lucide-react'
import { api, EvalMetrics } from '../api/client'

export function Eval() {
  const [metrics, setMetrics] = useState<EvalMetrics | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.getEval().then(setMetrics).finally(() => setLoading(false))
  }, [])

  if (loading) return <div className="p-8 text-[#8b949e]">Loading metrics...</div>
  if (!metrics) return <div className="p-8 text-red-400">Failed to load metrics</div>

  const latencyData = Object.entries(metrics.avg_node_latencies_sec).map(([node, lat]) => ({
    node,
    latency: lat,
  }))

  const severityData = [
    { name: 'Critical', value: metrics.avg_findings_per_scan.critical, color: '#ff4d4f' },
    { name: 'High', value: metrics.avg_findings_per_scan.high, color: '#fa8c16' },
    { name: 'Medium', value: metrics.avg_findings_per_scan.medium, color: '#fadb14' },
  ]

  return (
    <div className="max-w-5xl mx-auto px-6 py-8 space-y-8">
      <div className="flex items-center gap-3">
        <Activity size={20} className="text-blue-400" />
        <h1 className="text-xl font-semibold text-[#c9d1d9]">Pipeline Evaluation</h1>
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-4 gap-4">
        {[
          { label: 'Total Scans', value: metrics.total_scans },
          { label: 'False Positive Rate', value: `${metrics.false_positive_rate_pct}%` },
          { label: 'Avg Tokens / Scan', value: metrics.avg_tokens_per_scan.toLocaleString() },
          { label: 'Pipeline Nodes', value: Object.keys(metrics.avg_node_latencies_sec).length },
        ].map(({ label, value }) => (
          <div key={label} className="bg-[#161b22] border border-[#30363d] rounded-lg p-4">
            <p className="text-[#8b949e] text-xs uppercase tracking-wider">{label}</p>
            <p className="text-2xl font-bold text-[#c9d1d9] mt-1 font-mono">{value}</p>
          </div>
        ))}
      </div>

      {/* Node latency chart */}
      {latencyData.length > 0 && (
        <div className="bg-[#161b22] border border-[#30363d] rounded-lg p-4">
          <p className="text-[#8b949e] text-xs uppercase tracking-wider mb-4">
            Avg Latency per LangGraph Node (seconds)
          </p>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={latencyData} margin={{ top: 4, right: 8, left: 0, bottom: 4 }}>
              <XAxis
                dataKey="node"
                tick={{ fill: '#8b949e', fontSize: 11 }}
                axisLine={{ stroke: '#30363d' }}
                tickLine={false}
              />
              <YAxis
                tick={{ fill: '#8b949e', fontSize: 11 }}
                axisLine={{ stroke: '#30363d' }}
                tickLine={false}
              />
              <Tooltip
                contentStyle={{ background: '#161b22', border: '1px solid #30363d', borderRadius: 4 }}
                labelStyle={{ color: '#c9d1d9' }}
                itemStyle={{ color: '#1f6feb' }}
              />
              <Bar dataKey="latency" fill="#1f6feb" radius={[2, 2, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Avg severity per scan */}
      <div className="bg-[#161b22] border border-[#30363d] rounded-lg p-4">
        <p className="text-[#8b949e] text-xs uppercase tracking-wider mb-4">
          Avg Findings per Scan by Severity
        </p>
        <ResponsiveContainer width="100%" height={160}>
          <BarChart data={severityData} margin={{ top: 4, right: 8, left: 0, bottom: 4 }}>
            <XAxis dataKey="name" tick={{ fill: '#8b949e', fontSize: 11 }} axisLine={{ stroke: '#30363d' }} tickLine={false} />
            <YAxis tick={{ fill: '#8b949e', fontSize: 11 }} axisLine={{ stroke: '#30363d' }} tickLine={false} />
            <Tooltip
              contentStyle={{ background: '#161b22', border: '1px solid #30363d', borderRadius: 4 }}
              labelStyle={{ color: '#c9d1d9' }}
            />
            <Bar dataKey="value" radius={[2, 2, 0, 0]}>
              {severityData.map((entry) => (
                <Cell key={entry.name} fill={entry.color} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
