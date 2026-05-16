interface Props {
  severity: string
  size?: 'sm' | 'md'
}

const styles: Record<string, string> = {
  CRITICAL: 'bg-red-900/40 text-red-400 border border-red-800',
  HIGH:     'bg-orange-900/40 text-orange-400 border border-orange-800',
  MEDIUM:   'bg-yellow-900/40 text-yellow-400 border border-yellow-800',
  LOW:      'bg-blue-900/40 text-blue-400 border border-blue-800',
  INFO:     'bg-gray-800/40 text-gray-400 border border-gray-700',
}

export function SeverityBadge({ severity, size = 'sm' }: Props) {
  const cls = styles[severity] || styles.INFO
  const pad = size === 'sm' ? 'px-2 py-0.5 text-xs' : 'px-3 py-1 text-sm'
  return (
    <span className={`inline-flex items-center rounded font-mono font-semibold ${pad} ${cls}`}>
      {severity}
    </span>
  )
}
