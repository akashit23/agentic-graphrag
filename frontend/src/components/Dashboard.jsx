import { useState } from "react";
import { api, errMsg } from "../services/api";

export default function Dashboard({ repo }) {
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");

  if (!repo) return <p className="p-8 text-xs text-slate-400">No repository selected.</p>;
  const s = repo.stats || {};
  const cards = [
    { label: "Indexed Files", val: s.files, icon: "📄", color: "from-blue-600/20 to-cyan-600/20", border: "border-cyan-500/30" },
    { label: "Class Definitions", val: s.classes, icon: "🏛️", color: "from-emerald-600/20 to-teal-600/20", border: "border-emerald-500/30" },
    { label: "Functions & Methods", val: s.functions, icon: "⚙️", color: "from-amber-600/20 to-orange-600/20", border: "border-amber-500/30" },
    { label: "Graph Relationships", val: s.relationships, icon: "🕸️", color: "from-purple-600/20 to-indigo-600/20", border: "border-indigo-500/30" },
    { label: "Vector Chunks", val: s.chunks, icon: "🧩", color: "from-rose-600/20 to-pink-600/20", border: "border-rose-500/30" }
  ];

  const run = async () => {
    setLoading(true); setErr("");
    try { setAnalysis(await api.analyze(repo.repository_id)); } catch (e) { setErr(errMsg(e)); } finally { setLoading(false); }
  };

  return (
    <div className="space-y-6 p-6 max-w-6xl">
      {/* Title Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-800/80 pb-5">
        <div>
          <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2">
            <span>Repository:</span>
            <span className="bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">
              {repo.repository_name}
            </span>
          </h2>
          <div className="mt-1 flex items-center gap-3 text-xs text-slate-400">
            <span>Status: <b className={repo.status === "indexed" ? "text-emerald-400" : "text-amber-400 capitalize"}>{repo.status}</b></span>
            <span>•</span>
            <span>Source: <span className="font-mono">{repo.source_type}</span></span>
            <span>•</span>
            <span>Graph Backend: <span className="font-mono text-indigo-300">{s.graph_backend || "networkx"}</span></span>
          </div>
        </div>

        <button
          onClick={run}
          disabled={loading || repo.status !== "indexed"}
          className="rounded-xl bg-indigo-600 px-4 py-2 text-xs font-semibold text-white shadow-md shadow-indigo-600/20 hover:bg-indigo-500 transition disabled:opacity-40"
        >
          {loading ? "Synthesizing Analysis..." : "🔍 Run Deep Repository Analysis"}
        </button>
      </div>

      {/* Metric Cards Grid */}
      <div className="grid grid-cols-2 gap-3.5 md:grid-cols-5">
        {cards.map((c, i) => (
          <div
            key={i}
            className={`glow-card rounded-2xl bg-gradient-to-b ${c.color} bg-slate-900/90 border ${c.border} p-4 shadow-sm`}
          >
            <div className="flex items-center justify-between">
              <span className="text-xl">{c.icon}</span>
              <span className="text-2xl font-extrabold text-slate-100">{c.val ?? "—"}</span>
            </div>
            <div className="mt-2 text-[11px] font-medium text-slate-300">{c.label}</div>
          </div>
        ))}
      </div>

      {/* Languages & Metadata summary */}
      <div className="rounded-2xl bg-slate-900/80 border border-slate-800/80 p-4">
        <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400">Languages Detected</h4>
        <div className="mt-2.5 flex flex-wrap gap-2">
          {Object.entries(s.languages || {}).map(([lang, count]) => (
            <span
              key={lang}
              className="rounded-lg bg-slate-800/90 border border-slate-700/60 px-2.5 py-1 text-xs text-slate-300"
            >
              <b className="capitalize text-indigo-300">{lang}</b>: {count} {count === 1 ? "file" : "files"}
            </span>
          ))}
          {!Object.keys(s.languages || {}).length && (
            <span className="text-xs text-slate-500">None detected</span>
          )}
        </div>
      </div>

      {err && <p className="text-xs text-rose-400">{err}</p>}

      {/* Analysis Output */}
      {analysis && (
        <div className="rounded-2xl bg-slate-900/95 border border-slate-800 p-5 shadow-lg">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3 mb-3">
            <h3 className="text-sm font-bold text-slate-100">Deep Codebase Analysis</h3>
            <span className="text-[10px] font-mono rounded bg-indigo-950 border border-indigo-700/60 px-2 py-0.5 text-indigo-300">
              {analysis.llm_used ? "LLM Synthesized" : "Graph Facts Fallback"}
            </span>
          </div>
          <pre className="whitespace-pre-wrap font-sans text-xs leading-relaxed text-slate-300">
            {analysis.summary}
          </pre>
        </div>
      )}
    </div>
  );
}
