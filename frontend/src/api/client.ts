const BASE = '/api'

export interface Finding {
  id: string
  scan_id: string
  filename: string
  category: string
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | 'INFO'
  title: string
  description: string
  affected_lines: number[]
  affected_code: string | null
  recommendation: string
  exploit_scenario: string
  test_stub: string | null
  false_positive: boolean
  confidence: string
}

export interface ScanSummary {
  id: string
  filename: string | null
  status: string
  triggered_by: string
  critical_count: number
  high_count: number
  medium_count: number
  low_count: number
  info_count: number
  created_at: string
  completed_at: string | null
}

export interface ScanDetail extends ScanSummary {
  findings: Finding[]
  node_latencies: string | null
  total_tokens: number
}

export interface EvalMetrics {
  total_scans: number
  avg_findings_per_scan: { critical: number; high: number; medium: number }
  false_positive_rate_pct: number
  avg_tokens_per_scan: number
  avg_node_latencies_sec: Record<string, number>
}

export const api = {
  async getScans(): Promise<ScanSummary[]> {
    const res = await fetch(`${BASE}/scans`)
    if (!res.ok) throw new Error('Failed to fetch scans')
    return res.json()
  },

  async getScan(id: string): Promise<ScanDetail> {
    const res = await fetch(`${BASE}/scans/${id}`)
    if (!res.ok) throw new Error('Scan not found')
    return res.json()
  },

  async getEval(): Promise<EvalMetrics> {
    const res = await fetch(`${BASE}/eval`)
    if (!res.ok) throw new Error('Failed to fetch eval metrics')
    return res.json()
  },

  async explain(source: string, filename: string) {
    const res = await fetch(`${BASE}/explain`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ source, filename }),
    })
    if (!res.ok) throw new Error('Explain failed')
    return res.json()
  },

  streamAnalyze(source: string, filename: string, onEvent: (e: Record<string, unknown>) => void): () => void {
    const controller = new AbortController()

    fetch(`${BASE}/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ source, filename }),
      signal: controller.signal,
    }).then(async (res) => {
      const reader = res.body!.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              onEvent(JSON.parse(line.slice(6)))
            } catch {}
          }
        }
      }
    }).catch(() => {})

    return () => controller.abort()
  },
}
