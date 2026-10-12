import { useState } from "react";
import { reviewPR } from "../api";
import FindingCard from "./FindingCard";
import { ScoreBar } from "./Results";

export default function PRReview() {
  const [url, setUrl] = useState("");
  const [token, setToken] = useState("");
  const [useAi, setUseAi] = useState(true);
  const [post, setPost] = useState(false);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const [data, setData] = useState(null);

  const run = async () => {
    setBusy(true); setErr(""); setData(null);
    try { setData(await reviewPR(url.trim(), token.trim(), useAi, post)); }
    catch (e) { setErr(e.message); }
    finally { setBusy(false); }
  };

  return (
    <div className="space-y-6">
      <div className="space-y-3 rounded-lg border border-ink-700 bg-ink-900 p-4">
        <label className="block text-sm">Pull request URL
          <input value={url} onChange={(e) => setUrl(e.target.value)} placeholder="https://github.com/owner/repo/pull/123"
            className="mt-1 w-full rounded-md border border-ink-700 bg-ink-950 px-3 py-2 font-mono text-sm" />
        </label>
        <label className="block text-sm">GitHub token <span className="text-ink-500">(optional for public repos, required to post a comment)</span>
          <input type="password" value={token} onChange={(e) => setToken(e.target.value)} autoComplete="off"
            className="mt-1 w-full rounded-md border border-ink-700 bg-ink-950 px-3 py-2 font-mono text-sm" />
        </label>
        <div className="flex flex-wrap items-center gap-5 text-sm">
          <label className="flex items-center gap-2"><input type="checkbox" checked={useAi} onChange={(e) => setUseAi(e.target.checked)} />Use Gemma explanations</label>
          <label className="flex items-center gap-2"><input type="checkbox" checked={post} onChange={(e) => setPost(e.target.checked)} />Post result as a PR comment</label>
          <button onClick={run} disabled={busy || !url}
            className="ml-auto rounded-md bg-guard px-4 py-2 font-medium text-ink-950 hover:bg-guard-dark hover:text-white disabled:opacity-50">
            {busy ? "Reviewing…" : "Review pull request"}
          </button>
        </div>
        <p className="text-xs text-ink-500">Reviews up to 10 changed .py / .js files and only reports issues on lines the PR touched.</p>
      </div>

      {err && <p role="alert" className="rounded-md border border-red-400/40 bg-red-500/10 px-3 py-2 text-sm text-red-200">{err}</p>}

      {data && (
        <div className="space-y-6">
          {data.comment_posted && <p className="text-sm text-emerald-300">Comment posted to {data.owner}/{data.repo}#{data.number}.</p>}
          {data.files.length === 0 && <p className="text-sm text-ink-300">No Python or JavaScript files found in this PR.</p>}
          {data.files.map((f) => (
            <section key={f.filename} className="space-y-3">
              <h3 className="font-mono text-sm">{f.filename}</h3>
              <ScoreBar summary={f.summary} />
              {f.findings.map((x) => <FindingCard key={x.id} f={x} onPick={() => {}} />)}
            </section>
          ))}
        </div>
      )}
    </div>
  );
}
