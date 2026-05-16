import { useState, useRef, useCallback } from 'react'
import { useNavigate } from '@tanstack/react-router'
import { Shield, Zap, Link, Loader2 } from 'lucide-react'
import { api } from '../api/client'
import { ScanProgress } from '../components/ScanProgress'
import { FindingCard } from '../components/FindingCard'
import { SeverityBadge } from '../components/SeverityBadge'
import type { Finding } from '../api/client'

const EXAMPLE_CONTRACT = `// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/// @notice Deliberately vulnerable ETH vault — reentrancy + unprotected admin
/// Mimics The DAO hack pattern ($60M, 2016)
contract VulnerableVault {
    mapping(address => uint256) public balances;
    address public owner;
    bool public paused;

    event Deposit(address indexed user, uint256 amount);
    event Withdrawal(address indexed user, uint256 amount);

    constructor() {
        owner = msg.sender;
    }

    function deposit() public payable {
        require(!paused, "Paused");
        balances[msg.sender] += msg.value;
        emit Deposit(msg.sender, msg.value);
    }

    // VULNERABILITY: CEI violation — external call before state update
    function withdraw(uint256 amount) public {
        require(balances[msg.sender] >= amount, "Insufficient balance");
        require(!paused, "Paused");

        (bool sent, ) = msg.sender.call{value: amount}("");
        require(sent, "Transfer failed");

        balances[msg.sender] -= amount; // state update too late
        emit Withdrawal(msg.sender, amount);
    }

    // VULNERABILITY: no access control — anyone can pause or drain
    function setPaused(bool _paused) public {
        paused = _paused;
    }

    function emergencyWithdraw() public {
        payable(msg.sender).transfer(address(this).balance);
    }

    function getBalance() public view returns (uint256) {
        return address(this).balance;
    }
}`

function githubToRaw(url: string): string | null {
  const m = url.match(/^https?:\/\/github\.com\/([^/]+\/[^/]+)\/blob\/(.+)$/)
  if (!m) return null
  return `https://raw.githubusercontent.com/${m[1]}/${m[2]}`
}

export function Home() {
  const [githubUrl, setGithubUrl] = useState('')
  const [fetchingUrl, setFetchingUrl] = useState(false)
  const [source, setSource] = useState(EXAMPLE_CONTRACT)
  const [filename, setFilename] = useState('VulnerableVault.sol')
  const [running, setRunning] = useState(false)
  const [currentStage, setCurrentStage] = useState<string | null>(null)
  const [completedStages, setCompletedStages] = useState<string[]>([])
  const [error, setError] = useState<string | null>(null)
  const [findings, setFindings] = useState<Finding[]>([])
  const [scanId, setScanId] = useState<string | null>(null)
  const [filter, setFilter] = useState<string>('ALL')
  const stopRef = useRef<(() => void) | null>(null)
  const navigate = useNavigate()

  const handleUrlChange = async (url: string) => {
    setGithubUrl(url)
    const rawUrl = githubToRaw(url.trim())
    if (!rawUrl) return
    setFetchingUrl(true)
    try {
      const res = await fetch(rawUrl)
      if (!res.ok) return
      const text = await res.text()
      setSource(text)
      const parts = url.split('/')
      setFilename(parts[parts.length - 1] || 'contract.sol')
    } finally {
      setFetchingUrl(false)
    }
  }

  const STAGES_ORDER = ['parsing', 'static_scan', 'memory_query', 'ai_reasoning', 'test_gen', 'explain']

  const handleAnalyze = useCallback(() => {
    if (!source.trim()) return
    setRunning(true)
    // Show the first stage as active immediately — parse starts the moment we click
    setCurrentStage('parsing')
    setCompletedStages([])
    setError(null)
    setFindings([])
    setScanId(null)

    const stop = api.streamAnalyze(source, filename, (event) => {
      const stage = event.stage as string
      if (stage === 'done') {
        const report = event.report as Record<string, unknown>
        const scanIdVal = event.scan_id as string
        const rawFindings = (report?.findings as Finding[]) || []
        setFindings(rawFindings)
        setScanId(scanIdVal)
        setCompletedStages(STAGES_ORDER)
        setCurrentStage(null)
        setRunning(false)
      } else if (stage === 'error') {
        setError(event.message as string)
        setRunning(false)
      } else {
        // Treat the SSE event as "this stage finished — advance to the next"
        const idx = STAGES_ORDER.indexOf(stage)
        if (idx >= 0) {
          setCompletedStages(STAGES_ORDER.slice(0, idx + 1))
          setCurrentStage(STAGES_ORDER[idx + 1] ?? null)
        }
      }
    })
    stopRef.current = stop
  }, [source, filename])

  const severities = ['ALL', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'INFO']
  const visibleFindings = filter === 'ALL' ? findings : findings.filter((f) => f.severity === filter)
  const counts = { CRITICAL: 0, HIGH: 0, MEDIUM: 0, LOW: 0, INFO: 0 }
  findings.forEach((f) => { counts[f.severity as keyof typeof counts]++ })

  return (
    <div className="max-w-5xl mx-auto px-6 py-10 space-y-8">
      {/* Hero */}
      <div className="text-center space-y-3">
        <div className="flex justify-center">
          <Shield size={40} className="text-red-500" />
        </div>
        <h1 className="text-3xl font-bold text-[#c9d1d9]">SentinelAI</h1>
        <p className="text-[#8b949e] text-sm max-w-xl mx-auto">
          Paste a GitHub contract URL or raw Solidity source to get researcher-level vulnerability
          findings with exploit scenarios and Foundry test stubs.
        </p>
      </div>

      {/* Analyzer */}
      <div className="space-y-3">
        {/* GitHub URL input */}
        <div className="flex items-center bg-[#161b22] border border-[#30363d] rounded px-3 gap-2 focus-within:border-[#1f6feb]">
          <Link size={14} className="text-[#8b949e] flex-shrink-0" />
          <input
            value={githubUrl}
            onChange={(e) => handleUrlChange(e.target.value)}
            placeholder="https://github.com/.../blob/.../Contract.sol  (auto-fetches)"
            className="flex-1 bg-transparent py-2 text-sm text-[#c9d1d9] focus:outline-none"
          />
          {fetchingUrl && <Loader2 size={14} className="text-[#8b949e] animate-spin flex-shrink-0" />}
        </div>

        <div className="flex gap-3">
          <button
            onClick={handleAnalyze}
            disabled={running || !source.trim()}
            className="flex items-center gap-2 px-4 py-2 bg-[#1f6feb] hover:bg-[#388bfd] disabled:opacity-50 text-white text-sm rounded transition-colors"
          >
            <Zap size={14} />
            {running ? 'Analyzing...' : 'Analyze Contract'}
          </button>
          {scanId && (
            <button
              onClick={() => navigate({ to: '/scans/$scanId', params: { scanId } })}
              className="px-4 py-2 border border-[#30363d] text-[#8b949e] hover:text-[#c9d1d9] text-sm rounded transition-colors"
            >
              View Full Report
            </button>
          )}
        </div>
        <textarea
          value={source}
          onChange={(e) => {
            setSource(e.target.value)
            // Auto-derive filename from the contract name when pasting source directly
            if (!githubUrl.trim()) {
              const m = e.target.value.match(/\bcontract\s+(\w+)/)
              setFilename(m ? `${m[1]}.sol` : 'contract.sol')
            }
          }}
          rows={16}
          className="w-full bg-[#0d1117] border border-[#30363d] rounded p-4 text-sm text-[#c9d1d9] font-mono leading-relaxed focus:outline-none focus:border-[#1f6feb] resize-none"
          placeholder="Paste Solidity source here, or fetch from a GitHub URL above..."
          spellCheck={false}
        />
      </div>

      {/* Progress — stays visible on error so the message shows */}
      {(running || error) && (
        <div className="bg-[#161b22] border border-[#30363d] rounded-lg p-4">
          <ScanProgress
            currentStage={currentStage}
            completedStages={completedStages}
            error={error}
          />
        </div>
      )}

      {/* Results */}
      {findings.length > 0 && (
        <div className="space-y-4">
          <div className="flex items-center gap-4 flex-wrap">
            <span className="text-[#8b949e] text-sm">{findings.length} findings</span>
            {Object.entries(counts).map(([sev, count]) =>
              count > 0 ? (
                <span key={sev} className="flex items-center gap-1">
                  <SeverityBadge severity={sev} />
                  <span className="text-[#c9d1d9] text-sm font-mono">{count}</span>
                </span>
              ) : null
            )}
          </div>

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

          <div className="space-y-2">
            {visibleFindings.map((f) => (
              <FindingCard key={f.id} finding={f} />
            ))}
          </div>
        </div>
      )}

      {findings.length === 0 && !running && scanId && (
        <div className="text-center py-8 text-green-400">
          ✓ No vulnerabilities detected in this contract.
        </div>
      )}
    </div>
  )
}
