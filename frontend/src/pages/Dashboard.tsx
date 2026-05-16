import { useEffect, useState } from 'react'
import { Link } from '@tanstack/react-router'
import { api, ScanSummary } from '../api/client'
import { SeverityBadge } from '../components/SeverityBadge'

export function Dashboard() {
  const [scans, setScans] = useState<ScanSummary[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.getScans().then(setScans).finally(() => setLoading(false))
  }, [])

  if (loading) return <div className="p-8 text-[#8b949e]">Loading scans...</div>

  return (
    <div className="max-w-5xl mx-auto px-6 py-8 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold text-[#c9d1d9]">Scan History</h1>
        <span className="text-[#8b949e] text-sm">{scans.length} scans</span>
      </div>

      {scans.length === 0 ? (
        <div className="text-center py-16 text-[#8b949e]">
          No scans yet. <Link to="/" className="text-[#1f6feb] hover:underline">Run your first analysis</Link>.
        </div>
      ) : (
        <div className="border border-[#30363d] rounded-lg overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-[#161b22] text-[#8b949e] text-xs uppercase tracking-wider">
              <tr>
                <th className="text-left px-4 py-3">File</th>
                <th className="text-left px-4 py-3">Trigger</th>
                <th className="text-center px-3 py-3">Critical</th>
                <th className="text-center px-3 py-3">High</th>
                <th className="text-center px-3 py-3">Medium</th>
                <th className="text-center px-3 py-3">Low</th>
                <th className="text-left px-4 py-3">Date</th>
                <th className="text-left px-4 py-3">Status</th>
              </tr>
            </thead>
            <tbody>
              {scans.map((scan, i) => (
                <tr
                  key={scan.id}
                  className={`border-t border-[#30363d] hover:bg-[#1f2937] transition-colors ${i % 2 === 0 ? 'bg-[#0d1117]' : 'bg-[#161b22]'}`}
                >
                  <td className="px-4 py-3">
                    <Link
                      to="/scans/$scanId"
                      params={{ scanId: scan.id }}
                      className="text-[#1f6feb] hover:underline font-mono text-xs"
                    >
                      {scan.filename || '(direct input)'}
                    </Link>
                  </td>
                  <td className="px-4 py-3 text-[#8b949e] text-xs">{scan.triggered_by}</td>
                  <td className="px-3 py-3 text-center">
                    {scan.critical_count > 0 ? <span className="text-red-400 font-bold">{scan.critical_count}</span> : <span className="text-[#484f58]">—</span>}
                  </td>
                  <td className="px-3 py-3 text-center">
                    {scan.high_count > 0 ? <span className="text-orange-400 font-bold">{scan.high_count}</span> : <span className="text-[#484f58]">—</span>}
                  </td>
                  <td className="px-3 py-3 text-center">
                    {scan.medium_count > 0 ? <span className="text-yellow-400">{scan.medium_count}</span> : <span className="text-[#484f58]">—</span>}
                  </td>
                  <td className="px-3 py-3 text-center">
                    {scan.low_count > 0 ? <span className="text-blue-400">{scan.low_count}</span> : <span className="text-[#484f58]">—</span>}
                  </td>
                  <td className="px-4 py-3 text-[#8b949e] text-xs">
                    {new Date(scan.created_at).toLocaleString()}
                  </td>
                  <td className="px-4 py-3">
                    <span className={`text-xs px-2 py-0.5 rounded ${
                      scan.status === 'completed' ? 'bg-green-900/30 text-green-400' :
                      scan.status === 'running' ? 'bg-blue-900/30 text-blue-400' :
                      scan.status === 'failed' ? 'bg-red-900/30 text-red-400' :
                      'bg-gray-800 text-gray-400'
                    }`}>
                      {scan.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
