import { useEffect, useState } from 'react'
import {
  Brain, CheckCircle2, Database, FileCode2, FileText,
  FlaskConical, Loader2, ScanLine, Shield, ShieldCheck, X,
} from 'lucide-react'
import type { LucideIcon } from 'lucide-react'

const STAGES: { key: string; label: string; Icon: LucideIcon }[] = [
  { key: 'parsing',      label: 'Parsing Solidity AST',                 Icon: FileCode2    },
  { key: 'static_scan',  label: 'Running static detectors',             Icon: ScanLine     },
  { key: 'memory_query', label: 'Searching exploit knowledge base',      Icon: Database     },
  { key: 'ai_reasoning', label: 'GPT-4o reasoning over findings',        Icon: Brain        },
  { key: 'test_gen',     label: 'Generating Foundry test stubs',         Icon: FlaskConical },
  { key: 'property_gen', label: 'Generating Certora CVL property stubs', Icon: ShieldCheck  },
  { key: 'explain',      label: 'Building plain-English explanation',    Icon: FileText     },
]

interface Props {
  open: boolean
  currentStage: string | null
  completedStages: string[]
  error: string | null
  onClose: () => void
}

export function ScanProgress({ open, currentStage, completedStages, error, onClose }: Props) {
  const [mounted, setMounted] = useState(false)
  const [visible, setVisible] = useState(false)

  useEffect(() => {
    if (open) {
      setMounted(true)
      // Defer so the initial opacity-0 class is painted first, enabling the transition
      requestAnimationFrame(() => requestAnimationFrame(() => setVisible(true)))
    } else {
      setVisible(false)
      const t = setTimeout(() => setMounted(false), 350)
      return () => clearTimeout(t)
    }
  }, [open])

  if (!mounted) return null

  const doneCount = completedStages.length
  const total = STAGES.length

  return (
    <div
      className={`fixed inset-0 z-50 flex items-center justify-center p-6 transition-opacity duration-300 ${
        visible ? 'opacity-100' : 'opacity-0'
      }`}
    >
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/70 backdrop-blur-sm" onClick={error ? onClose : undefined} />

      {/* Panel */}
      <div
        className={`relative bg-[#0d1117] border border-[#30363d] rounded-2xl w-full max-w-lg shadow-2xl
          transition-transform duration-300 ${visible ? 'translate-y-0' : 'translate-y-6'}`}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 pt-5 pb-4 border-b border-[#30363d]">
          <div className="flex items-center gap-2">
            <Shield size={16} className="text-red-500" />
            <span className="text-[#c9d1d9] text-sm font-semibold">
              {error ? 'Scan failed' : doneCount === total ? 'Scan complete' : 'Analyzing contract…'}
            </span>
          </div>
          <div className="flex items-center gap-3">
            {!error && (
              <span className="text-[#8b949e] text-xs tabular-nums">
                {doneCount} / {total}
              </span>
            )}
            {(error || doneCount === total) && (
              <button
                onClick={onClose}
                className="text-[#8b949e] hover:text-[#c9d1d9] transition-colors"
                aria-label="Close"
              >
                <X size={16} />
              </button>
            )}
          </div>
        </div>

        {/* Step rows */}
        <div className="px-6 py-4 space-y-2">
          {STAGES.map(({ key, label, Icon }) => {
            const isDone   = completedStages.includes(key)
            const isActive = currentStage === key

            return (
              <div
                key={key}
                className={`flex items-center gap-4 px-4 py-3 rounded-xl border transition-all duration-300 ${
                  isDone
                    ? 'bg-green-950/30 border-green-900/60'
                    : isActive
                    ? 'bg-blue-950/40 border-[#1f6feb]/60 shadow-[0_0_12px_rgba(31,111,235,0.15)]'
                    : 'bg-[#161b22] border-[#30363d]'
                }`}
              >
                {/* Icon */}
                <Icon
                  size={18}
                  className={`flex-shrink-0 transition-colors duration-300 ${
                    isDone ? 'text-green-500' : isActive ? 'text-blue-400' : 'text-[#484f58]'
                  }`}
                />

                {/* Label */}
                <span
                  className={`flex-1 text-sm transition-colors duration-300 ${
                    isDone
                      ? 'text-[#8b949e]'
                      : isActive
                      ? 'text-[#c9d1d9] font-medium'
                      : 'text-[#484f58]'
                  }`}
                >
                  {label}
                </span>

                {/* Status badge */}
                {isDone ? (
                  <span className="flex items-center gap-1 text-xs text-green-400 bg-green-900/40 px-2.5 py-1 rounded-full">
                    <CheckCircle2 size={11} />
                    Done
                  </span>
                ) : isActive ? (
                  <span className="flex items-center gap-1.5 text-xs text-blue-400 bg-blue-900/40 px-2.5 py-1 rounded-full">
                    <Loader2 size={11} className="animate-spin" />
                    Running
                  </span>
                ) : (
                  <span className="text-xs text-[#484f58] bg-[#21262d] px-2.5 py-1 rounded-full">
                    Pending
                  </span>
                )}
              </div>
            )
          })}
        </div>

        {/* Error message */}
        {error && (
          <div className="mx-6 mb-5 p-3 bg-red-900/20 border border-red-800/60 rounded-lg text-red-400 text-sm">
            {error}
          </div>
        )}
      </div>
    </div>
  )
}
