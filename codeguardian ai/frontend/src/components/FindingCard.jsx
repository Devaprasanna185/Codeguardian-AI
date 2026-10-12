import { SEV } from "./severity";

export default function FindingCard({ f, active, onPick }) {
  const s = SEV[f.severity];
  const pct = Math.round(f.confidence * 100);
  const lines = f.line_start === f.line_end ? `line ${f.line_start}` : `lines ${f.line_start}–${f.line_end}`;
  return (
    <article
      id={`finding-${f.id}`}
      onClick={() => onPick(f.id)}
      className={`rounded-lg border bg-ink-900 p-4 ${active ? "border-guard" : "border-ink-700"}`}
    >
      <header className="flex flex-wrap items-center gap-2">
        <span className={`rounded px-2 py-0.5 text-xs font-medium ring-1 ${s.cls}`}>{s.label}</span>
        <h3 className="font-semibold">{f.title}</h3>
        <span className="ml-auto font-mono text-xs text-ink-500">{lines}</span>
      </header>

      <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-ink-300">
        <span className="flex items-center gap-2" title="How sure we are that this is a real problem">
          Confidence
          <span className="h-1.5 w-24 overflow-hidden rounded bg-ink-700" role="meter" aria-valuenow={pct} aria-valuemin={0} aria-valuemax={100}>
            <span className={`block h-full ${s.bar}`} style={{ width: `${pct}%` }} />
          </span>
          {pct}%
        </span>
        {f.verified_by_static ? (
          <span className="text-emerald-300">✔ Confirmed by {f.source}{f.rule_id ? ` (${f.rule_id})` : ""}</span>
        ) : (
          <span className="text-amber-200">AI suggestion, not verified by a tool</span>
        )}
        {f.cwe && <span className="font-mono text-ink-500">{f.cwe}</span>}
      </div>

      {f.explanation && <p className="mt-3 text-sm leading-6">{f.explanation}</p>}
      {f.why_it_matters && (
        <p className="mt-2 text-sm leading-6 text-ink-300"><b className="font-medium text-ink-100">Why it matters: </b>{f.why_it_matters}</p>
      )}
      {f.suggested_fix && (
        <p className="mt-2 rounded-md bg-ink-800 px-3 py-2 text-sm leading-6"><b className="font-medium">How to fix: </b>{f.suggested_fix}</p>
      )}
    </article>
  );
}
