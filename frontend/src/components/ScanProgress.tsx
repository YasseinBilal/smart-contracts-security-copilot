import { CheckCircle2, Circle, Loader2 } from 'lucide-react'

const STAGES = [
  { key: 'parsing', label: 'Parsing Solidity AST' },
  { key: 'static_scan', label: 'Running static detectors' },
  { key: 'memory_query', label: 'Searching exploit knowledge base' },
  { key: 'ai_reasoning', label: 'GPT-4o reasoning over findings' },
  { key: 'test_gen', label: 'Generating Foundry test stubs' },
  { key: 'explain', label: 'Building plain-English explanation' },
]

interface Props {
  currentStage: string | null
  completedStages: string[]
  error: string | null
}

export function ScanProgress({ currentStage, completedStages, error }: Props) {
  return (
    <div className="space-y-2">
      {STAGES.map(({ key, label }) => {
        const isDone = completedStages.includes(key)
        const isActive = currentStage === key

        return (
          <div key={key} className="flex items-center gap-3 text-sm">
            {isDone ? (
              <CheckCircle2 size={16} className="text-green-500 flex-shrink-0" />
            ) : isActive ? (
              <Loader2 size={16} className="text-blue-400 animate-spin flex-shrink-0" />
            ) : (
              <Circle size={16} className="text-[#30363d] flex-shrink-0" />
            )}
            <span className={isDone ? 'text-[#8b949e]' : isActive ? 'text-[#c9d1d9]' : 'text-[#484f58]'}>
              {label}
            </span>
          </div>
        )
      })}
      {error && (
        <div className="mt-3 p-3 bg-red-900/20 border border-red-800 rounded text-red-400 text-sm">
          Error: {error}
        </div>
      )}
    </div>
  )
}
