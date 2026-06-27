import { useEffect, useState } from 'react'
import { useParams } from '@tanstack/react-router'
import { api, ScanDetail as ScanDetailType } from '../api/client'
import { FindingCard } from '../components/FindingCard'
import { SeverityBadge } from '../components/SeverityBadge'

export function ScanDetail() {
  const { scanId } = useParams({ from: '/scans/$scanId' })
  const [scan, setScan] = useState<ScanDetailType | null>(null)
  const [filter, setFilter] = useState('ALL')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    api.getScan(scanId)
      .then(setScan)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [scanId])

  if (loading) return <div className="p-8 text-[#8b949e]">Loading scan...</div>
  if (error || !scan) return <div className="p-8 text-red-400">{error || 'Scan not found'}</div>

  const severities = ['ALL', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'INFO']
  const filtered = filter === 'ALL' ? scan.findings : scan.findings.filter((f) => f.severity === filter)

  const latencies = scan.node_latencies ? JSON.parse(scan.node_latencies) : {}

  return (
    <div className="max-w-5xl mx-auto px-6 py-8 space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-[#c9d1d9]">{scan.filename || 'Scan Detail'}</h1>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-5 gap-3">
        {(['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'INFO'] as const).map((sev) => {
          const count = scan[`${sev.toLowerCase()}_count` as keyof typeof scan] as number
          return (
            <div key={sev} className="bg-[#161b22] border border-[#30363d] rounded-lg p-3 text-center">
              <SeverityBadge severity={sev} size="sm" />
              <div className="text-2xl font-bold text-[#c9d1d9] mt-2">{count}</div>
            </div>
          )
        })}
      </div>

      {/* Latency breakdown */}
      {/* Filter */}
      <div className="flex gap-2 flex-wrap">
        {severities.map((s) => (
          <button
            key={s}
            onClick={() => setFilter(s)}
            className={`px-3 py-1 text-xs rounded transition-colors ${
              filter === s
                ? 'bg-[#1f6feb] text-white'
                : 'border border-[#30363d] text-[#8b949e] hover:text-[#c9d1d9]'
            }`}
          >
            {s}
          </button>
        ))}
      </div>

      {/* Findings */}
      <div className="space-y-2">
        {filtered.length === 0 ? (
          <div className="text-center py-8 text-[#8b949e]">
            {filter === 'ALL' ? 'No findings in this scan.' : `No ${filter} findings.`}
          </div>
        ) : (
          filtered.map((f) => <FindingCard key={f.id} finding={f} />)
        )}
      </div>
    </div>
  )
}
