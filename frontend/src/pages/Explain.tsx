import { useState } from 'react'
import { BookOpen, Link, Loader2 } from 'lucide-react'
import { api } from '../api/client'

function githubToRaw(url: string): string | null {
  // https://github.com/{owner}/{repo}/blob/{branch}/{path}
  // → https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{path}
  const m = url.match(/^https?:\/\/github\.com\/([^/]+\/[^/]+)\/blob\/(.+)$/)
  if (!m) return null
  return `https://raw.githubusercontent.com/${m[1]}/${m[2]}`
}

export function Explain() {
  const [githubUrl, setGithubUrl] = useState('')
  const [source, setSource] = useState('')
  const [filename, setFilename] = useState('contract.sol')
  const [fetching, setFetching] = useState(false)
  const [fetchError, setFetchError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<null | {
    summary: string
    privileged_functions: string[]
    trust_assumptions: string[]
    risk_notes: string
  }>(null)

  const fetchFromUrl = async (url: string) => {
    const rawUrl = githubToRaw(url.trim())
    if (!rawUrl) return
    setFetching(true)
    setFetchError(null)
    try {
      const res = await fetch(rawUrl)
      if (!res.ok) throw new Error(`GitHub returned ${res.status}`)
      const text = await res.text()
      setSource(text)
      const parts = url.split('/')
      setFilename(parts[parts.length - 1] || 'contract.sol')
    } catch (e: unknown) {
      setFetchError(e instanceof Error ? e.message : 'Failed to fetch')
    } finally {
      setFetching(false)
    }
  }

  const handleUrlChange = (url: string) => {
    setGithubUrl(url)
    setFetchError(null)
    if (githubToRaw(url.trim())) {
      fetchFromUrl(url)
    }
  }

  const handleExplain = async () => {
    if (!source.trim()) return
    setLoading(true)
    setResult(null)
    try {
      const r = await api.explain(source, filename)
      setResult(r)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-4xl mx-auto px-6 py-8 space-y-6">
      <div className="flex items-center gap-3">
        <BookOpen size={20} className="text-blue-400" />
        <h1 className="text-xl font-semibold text-[#c9d1d9]">Explain Contract</h1>
      </div>
      <p className="text-[#8b949e] text-sm">
        Paste a GitHub contract URL or raw Solidity source to get a plain-English breakdown — what
        it does, who can call what, and what trust assumptions it makes.
      </p>

      <div className="space-y-3">
        {/* GitHub URL fetcher */}
        <div className="flex gap-2">
          <div className="flex items-center flex-1 bg-[#161b22] border border-[#30363d] rounded px-3 gap-2 focus-within:border-[#1f6feb]">
            <Link size={14} className="text-[#8b949e] flex-shrink-0" />
            <input
              value={githubUrl}
              onChange={(e) => handleUrlChange(e.target.value)}
              placeholder="https://github.com/.../blob/.../Contract.sol  (auto-fetches on paste)"
              className="flex-1 bg-transparent py-2 text-sm text-[#c9d1d9] focus:outline-none"
            />
            {fetching && <Loader2 size={14} className="text-[#8b949e] animate-spin flex-shrink-0" />}
          </div>
        </div>
        {fetchError && <p className="text-red-400 text-xs">{fetchError}</p>}

        {/* Controls */}
        <div className="flex gap-3">
          <button
            onClick={handleExplain}
            disabled={loading || !source.trim()}
            className="px-4 py-2 bg-[#1f6feb] hover:bg-[#388bfd] disabled:opacity-50 text-white text-sm rounded transition-colors"
          >
            {loading ? 'Explaining...' : 'Explain'}
          </button>
        </div>

        <textarea
          value={source}
          onChange={(e) => setSource(e.target.value)}
          rows={14}
          className="w-full bg-[#0d1117] border border-[#30363d] rounded p-4 text-sm text-[#c9d1d9] font-mono focus:outline-none focus:border-[#1f6feb] resize-none"
          placeholder="Paste Solidity source here, or fetch from a GitHub URL above..."
          spellCheck={false}
        />
      </div>

      {result && (
        <div className="space-y-4">
          <div className="bg-[#161b22] border border-[#30363d] rounded-lg p-4 space-y-2">
            <p className="text-[#8b949e] text-xs uppercase tracking-wider">Summary</p>
            <p className="text-[#c9d1d9] text-sm leading-relaxed">{result.summary}</p>
          </div>

          {result.privileged_functions.length > 0 && (
            <div className="bg-[#161b22] border border-[#30363d] rounded-lg p-4 space-y-2">
              <p className="text-[#8b949e] text-xs uppercase tracking-wider">Privileged Functions</p>
              <div className="flex flex-wrap gap-2">
                {result.privileged_functions.map((fn) => (
                  <code key={fn} className="bg-[#0d1117] border border-[#30363d] rounded px-2 py-0.5 text-xs text-orange-300">
                    {fn}
                  </code>
                ))}
              </div>
            </div>
          )}

          {result.trust_assumptions.length > 0 && (
            <div className="bg-[#161b22] border border-[#30363d] rounded-lg p-4 space-y-2">
              <p className="text-[#8b949e] text-xs uppercase tracking-wider">Trust Assumptions</p>
              <ul className="space-y-1">
                {result.trust_assumptions.map((a, i) => (
                  <li key={i} className="text-[#c9d1d9] text-sm flex gap-2">
                    <span className="text-[#8b949e]">—</span>
                    {a}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {result.risk_notes && (
            <div className="bg-yellow-900/10 border border-yellow-800/40 rounded-lg p-4 space-y-2">
              <p className="text-yellow-400 text-xs uppercase tracking-wider">Risk Notes</p>
              <p className="text-[#c9d1d9] text-sm leading-relaxed">{result.risk_notes}</p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
