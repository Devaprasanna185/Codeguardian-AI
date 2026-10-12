import { useRef, useState } from "react";
import { reviewCode } from "./api";
import PRReview from "./components/PRReview";
import Results from "./components/Results";

const SAMPLE = {
  python: `import subprocess, pickle

API_KEY = "sk_live_51HxxxxSECRET"

def run(cmd, items=[]):
    items.append(cmd)
    subprocess.call(cmd, shell=True)
    return items

def load(blob):
    return pickle.loads(blob)

def calc(expr):
    return eval(expr)
`,
  javascript: `var apiKey = "sk_live_51HxxxxSECRET";

function show(name) {
  document.getElementById("out").innerHTML = "Hello " + name;
}

function check(a, b) {
  if (a == b) { return eval(a); }
  try { go(); } catch (e) {}
}
`,
};

const EXT = { py: "python", js: "javascript", jsx: "javascript", mjs: "javascript" };

export default function App() {
  const [tab, setTab] = useState("code");
  const [language, setLanguage] = useState("python");
  const [code, setCode] = useState("");
  const [filename, setFilename] = useState("snippet");
  const [useAi, setUseAi] = useState(true);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const [result, setResult] = useState(null);
  const [reviewed, setReviewed] = useState("");
  const fileRef = useRef();

  const onFile = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const lang = EXT[file.name.split(".").pop().toLowerCase()];
    if (!lang) return setErr("Only .py, .js and .jsx files are supported.");
    setErr(""); setLanguage(lang); setFilename(file.name); setCode(await file.text());
  };

  const run = async () => {
    setBusy(true); setErr(""); setResult(null);
    try {
      const r = await reviewCode(code, language, filename, useAi);
      setReviewed(code); setResult(r);
    } catch (e) { setErr(e.message); }
    finally { setBusy(false); }
  };

  const tabCls = (t) => `px-4 py-2 text-sm font-medium border-b-2 ${tab === t ? "border-guard text-ink-100" : "border-transparent text-ink-500 hover:text-ink-300"}`;

  return (
    <div className="mx-auto max-w-6xl px-4 py-8">
      <header className="mb-8">
        <h1 className="text-2xl font-semibold">🛡️ CodeGuardian AI</h1>
        <p className="mt-1 max-w-xl text-ink-300">
          Paste Python or JavaScript and get plain-English explanations of bugs and security problems, with a fix you can compare line by line.
        </p>
      </header>

      <nav className="mb-6 flex border-b border-ink-700" aria-label="Mode">
        <button className={tabCls("code")} onClick={() => setTab("code")}>Review code</button>
        <button className={tabCls("pr")} onClick={() => setTab("pr")}>Review a GitHub PR</button>
      </nav>

      {tab === "pr" ? <PRReview /> : (
        <div className="space-y-6">
          <div className="space-y-3">
            <div className="flex flex-wrap items-center gap-3 text-sm">
              <label className="flex items-center gap-2">Language
                <select value={language} onChange={(e) => setLanguage(e.target.value)} className="rounded-md border border-ink-700 bg-ink-900 px-2 py-1.5">
                  <option value="python">Python</option>
                  <option value="javascript">JavaScript</option>
                </select>
              </label>
              <input ref={fileRef} type="file" accept=".py,.js,.jsx,.mjs" onChange={onFile} className="hidden" />
              <button onClick={() => fileRef.current.click()} className="rounded-md border border-ink-700 px-3 py-1.5 hover:bg-ink-800">Upload file</button>
              <button onClick={() => { setCode(SAMPLE[language]); setFilename("sample"); }} className="rounded-md border border-ink-700 px-3 py-1.5 hover:bg-ink-800">Load an example</button>
              <label className="ml-auto flex items-center gap-2">
                <input type="checkbox" checked={useAi} onChange={(e) => setUseAi(e.target.checked)} />
                Explain with Gemma
              </label>
            </div>
            <textarea
              value={code} onChange={(e) => setCode(e.target.value)} spellCheck={false} rows={14}
              aria-label="Code to review" placeholder="Paste your code here, or upload a file…"
              className="w-full rounded-lg border border-ink-700 bg-ink-900 p-4 font-mono text-[13px] leading-6"
            />
            <button onClick={run} disabled={busy || !code.trim()}
              className="rounded-md bg-guard px-5 py-2.5 font-medium text-ink-950 hover:bg-guard-dark hover:text-white disabled:opacity-50">
              {busy ? "Reviewing… (the model can take a minute)" : "Review my code"}
            </button>
          </div>

          {err && <p role="alert" className="rounded-md border border-red-400/40 bg-red-500/10 px-3 py-2 text-sm text-red-200">{err}</p>}
          {result && <Results result={result} code={reviewed} />}
        </div>
      )}

      <footer className="mt-16 border-t border-ink-700 pt-4 text-xs text-ink-500">
        Security findings are confirmed by Bandit, Ruff and pattern rules. Gemma writes the explanations and patches, so double-check them. MIT licensed.
      </footer>
    </div>
  );
}
