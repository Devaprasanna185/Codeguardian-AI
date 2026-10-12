import { SEV } from "./severity";

// Read-only listing; lines with findings are tinted by the worst severity on that line.
export default function CodeView({ code, findings, activeId, onPick }) {
  const order = ["critical", "high", "medium", "low", "info"];
  const byLine = {};
  findings.forEach((f) => {
    for (let l = f.line_start; l <= f.line_end; l++) {
      const cur = byLine[l];
      if (!cur || order.indexOf(f.severity) < order.indexOf(cur.severity)) byLine[l] = f;
    }
  });
  return (
    <div className="overflow-x-auto rounded-lg border border-ink-700 bg-ink-900 font-mono text-[13px] leading-6">
      {code.split("\n").map((text, i) => {
        const f = byLine[i + 1];
        const active = f && f.id === activeId;
        return (
          <div
            key={i}
            onClick={() => f && onPick(f.id)}
            className={`flex ${f ? `${SEV[f.severity].line} cursor-pointer` : ""} ${active ? "ring-1 ring-inset ring-guard" : ""}`}
          >
            <span className="w-12 shrink-0 select-none pr-3 text-right text-ink-500">{i + 1}</span>
            <pre className="whitespace-pre pr-4">{text || " "}</pre>
          </div>
        );
      })}
    </div>
  );
}
