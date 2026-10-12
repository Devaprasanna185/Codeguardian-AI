
export default function DiffView({ rows, fixedCode }) {
  const copy = () => navigator.clipboard?.writeText(fixedCode);
  const cell = (tag, side) =>
    side === "L" ? (tag === "replace" || tag === "delete" ? "bg-red-500/15" : "") : (tag === "replace" || tag === "insert" ? "bg-emerald-500/15" : "");
  return (
    <section aria-label="Suggested patch">
      <div className="mb-2 flex items-center justify-between">
        <h3 className="font-semibold">Suggested patch</h3>
        <button onClick={copy} className="rounded-md bg-guard px-3 py-1.5 text-sm font-medium text-ink-950 hover:bg-guard-dark hover:text-white">
          Copy fixed code
        </button>
      </div>
      <div className="grid grid-cols-2 border-b border-ink-700 pb-1 text-xs text-ink-500">
        <span>Original</span><span>Proposed fix</span>
      </div>
      <div className="overflow-x-auto rounded-lg border border-ink-700 bg-ink-900 font-mono text-[13px] leading-6">
        {rows.map((r, i) => (
          <div key={i} className="grid min-w-[640px] grid-cols-2">
            <div className={`flex ${cell(r.tag, "L")}`}>
              <span className="w-10 shrink-0 pr-2 text-right text-ink-500">{r.left_no ?? ""}</span>
              <pre className="whitespace-pre-wrap break-all pr-2">{r.left || " "}</pre>
            </div>
            <div className={`flex border-l border-ink-700 ${cell(r.tag, "R")}`}>
              <span className="w-10 shrink-0 pr-2 text-right text-ink-500">{r.right_no ?? ""}</span>
              <pre className="whitespace-pre-wrap break-all pr-2">{r.right || " "}</pre>
            </div>
          </div>
        ))}
      </div>
      <p className="mt-2 text-xs text-ink-500">Review every change before using it. AI patches can be wrong.</p>
    </section>
  );
}
