import { useState } from "react";
import CodeView from "./CodeView";
import DiffView from "./DiffView";
import FindingCard from "./FindingCard";
import { SEV } from "./severity";

export function ScoreBar({ summary }) {
  const color = summary.score >= 80 ? "text-emerald-300" : summary.score >= 50 ? "text-amber-200" : "text-red-300";
  return (
    <div className="flex flex-wrap items-center gap-x-6 gap-y-2 rounded-lg border border-ink-700 bg-ink-900 p-4">
      <div>
        <div className={`text-3xl font-semibold ${color}`}>{summary.score}<span className="text-base text-ink-500">/100</span></div>
        <div className="text-xs text-ink-500">Code health</div>
      </div>
      <div className="flex flex-wrap gap-2">
        {Object.entries(summary.counts).filter(([, n]) => n > 0).map(([k, n]) => (
          <span key={k} className={`rounded px-2 py-0.5 text-xs font-medium ring-1 ${SEV[k].cls}`}>{n} {SEV[k].label}</span>
        ))}
        {summary.total === 0 && <span className="text-sm text-emerald-300">No issues found 🎉</span>}
      </div>
    </div>
  );
}

export default function Results({ result, code }) {
  const [active, setActive] = useState(null);
  const pick = (id) => {
    setActive(id);
    document.getElementById(`finding-${id}`)?.scrollIntoView({ behavior: "smooth", block: "nearest" });
  };
  return (
    <div className="space-y-6">
      <ScoreBar summary={result.summary} />
      {result.warnings.map((w) => (
        <p key={w} className="rounded-md border border-amber-400/30 bg-amber-500/10 px-3 py-2 text-sm text-amber-100">{w}</p>
      ))}
      {result.ai_error && <p className="text-xs text-ink-500">AI detail: {result.ai_error}</p>}
      <div className="grid gap-6 lg:grid-cols-2">
        <div>
          <h2 className="mb-2 font-semibold">Your code</h2>
          <CodeView code={code} findings={result.findings} activeId={active} onPick={pick} />
        </div>
        <div className="space-y-3">
          <h2 className="font-semibold">Findings ({result.findings.length})</h2>
          {result.findings.map((f) => <FindingCard key={f.id} f={f} active={f.id === active} onPick={setActive} />)}
        </div>
      </div>
      {result.fixed_code && <DiffView rows={result.diff_rows} fixedCode={result.fixed_code} />}
    </div>
  );
}
