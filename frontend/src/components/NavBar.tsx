import { Link } from '@tanstack/react-router'
import { Shield } from 'lucide-react'

export function NavBar() {
  return (
    <nav className="border-b border-[#30363d] bg-[#161b22] px-6 py-3 flex items-center gap-6">
      <Link to="/" className="flex items-center gap-2 text-[#c9d1d9] font-semibold hover:text-white">
        <Shield size={18} className="text-red-500" />
        SentinelAI
      </Link>
      <div className="flex gap-4 text-sm">
        <Link to="/dashboard" className="text-[#8b949e] hover:text-[#c9d1d9] transition-colors">
          Dashboard
        </Link>
        <Link to="/explain" className="text-[#8b949e] hover:text-[#c9d1d9] transition-colors">
          Explain
        </Link>
        <Link to="/eval" className="text-[#8b949e] hover:text-[#c9d1d9] transition-colors">
          Benchmarks
        </Link>
      </div>
    </nav>
  )
}
