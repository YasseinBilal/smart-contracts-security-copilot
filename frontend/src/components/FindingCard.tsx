import { useState } from 'react'
import { ChevronDown, ChevronRight, Code2, FlaskConical, ShieldCheck } from 'lucide-react'
import type { Finding } from '../api/client'
import { SeverityBadge } from './SeverityBadge'

interface Props {
  finding: Finding
}

export function FindingCard({ finding }: Props) {
  const [open, setOpen] = useState(false)
  const [tab, setTab] = useState<'details' | 'code' | 'test' | 'cvl'>('details')

  return (
    <div className="border border-[#30363d] rounded-lg bg-[#161b22] overflow-hidden">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center gap-3 px-4 py-3 text-left hover:bg-[#1f2937] transition-colors"
      >
        {open ? <ChevronDown size={14} className="text-[#8b949e]" /> : <ChevronRight size={14} className="text-[#8b949e]" />}
        <SeverityBadge severity={finding.severity} />
        <span className="text-[#c9d1d9] font-medium text-sm flex-1">{finding.title}</span>
        <span className="text-[#8b949e] text-xs">{finding.filename}</span>
        {finding.affected_lines.length > 0 && (
          <span className="text-[#8b949e] text-xs">L{finding.affected_lines[0]}</span>
        )}
      </button>

      {open && (
        <div className="border-t border-[#30363d]">
          <div className="flex gap-1 px-4 pt-3">
            {(['details', 'code', 'test', 'cvl'] as const).map((t) => (
              <button
                key={t}
                onClick={() => setTab(t)}
                className={`px-3 py-1 text-xs rounded transition-colors ${
                  tab === t
                    ? 'bg-[#1f6feb] text-white'
                    : 'text-[#8b949e] hover:text-[#c9d1d9]'
                }`}
              >
                {t === 'details' ? 'Details' : t === 'code' ? 'Code' : t === 'test' ? 'Test Stub' : 'CVL Property'}
              </button>
            ))}
          </div>

          <div className="p-4 space-y-3 text-sm">
            {tab === 'details' && (
              <>
                <div>
                  <p className="text-[#8b949e] text-xs uppercase tracking-wider mb-1">Description</p>
                  <p className="text-[#c9d1d9] leading-relaxed">{finding.description}</p>
                </div>
                <div>
                  <p className="text-[#8b949e] text-xs uppercase tracking-wider mb-1">Exploit Scenario</p>
                  <p className="text-orange-300/80 leading-relaxed">{finding.exploit_scenario}</p>
                </div>
                <div>
                  <p className="text-[#8b949e] text-xs uppercase tracking-wider mb-1">Recommendation</p>
                  <p className="text-green-300/80 leading-relaxed">{finding.recommendation}</p>
                </div>
                <div className="flex gap-4 text-xs text-[#8b949e]">
                  <span>Category: <span className="text-[#c9d1d9]">{finding.category}</span></span>
                  <span>Confidence: <span className="text-[#c9d1d9]">{finding.confidence}</span></span>
                </div>
              </>
            )}

            {tab === 'code' && (
              <div>
                <p className="text-[#8b949e] text-xs mb-2">Affected lines: {finding.affected_lines.join(', ')}</p>
                <pre className="bg-[#0d1117] border border-[#30363d] rounded p-3 overflow-x-auto text-xs text-[#c9d1d9] leading-relaxed">
                  {finding.affected_code || 'No code snippet available'}
                </pre>
              </div>
            )}

            {tab === 'test' && (
              <div>
                {finding.test_stub ? (
                  <pre className="bg-[#0d1117] border border-[#30363d] rounded p-3 overflow-x-auto text-xs text-[#c9d1d9] leading-relaxed">
                    {finding.test_stub}
                  </pre>
                ) : (
                  <p className="text-[#8b949e] text-sm">No test stub generated (only generated for CRITICAL/HIGH findings).</p>
                )}
              </div>
            )}

            {tab === 'cvl' && (
              <div>
                {finding.cvl_property ? (
                  <>
                    <p className="text-[#8b949e] text-xs mb-2">Certora CVL — paste into a <code className="text-[#c9d1d9]">.spec</code> file and run with the Prover</p>
                    <pre className="bg-[#0d1117] border border-[#30363d] rounded p-3 overflow-x-auto text-xs text-[#c9d1d9] leading-relaxed">
                      {finding.cvl_property}
                    </pre>
                  </>
                ) : (
                  <p className="text-[#8b949e] text-sm">No CVL property generated (only generated for CRITICAL/HIGH findings).</p>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
