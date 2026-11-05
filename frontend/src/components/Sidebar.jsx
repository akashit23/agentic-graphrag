import { useState } from "react";

const TABS = [
  ["chat", "💬", "Chat & Query"],
  ["dashboard", "📊", "Repository Stats"],
  ["files", "📁", "Code Explorer"],
  ["graph", "🕸️", "Visual Graph"],
  ["deps", "🔗", "Impact & Deps"],
  ["settings", "⚙️", "System & LLM"]
];

export default function Sidebar({ repos, current, onSelect, tab, onTab, onUpload, onGithub, onSample, busy }) {
  const [url, setUrl] = useState("");

  return (
    <aside className="w-72 shrink-0 border-r border-slate-800/80 bg-slate-900/90 p-4 flex flex-col gap-5 overflow-y-auto backdrop-blur-md">
      {/* Repository Selector */}
      <div className="space-y-1.5">
        <label className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">Target Codebase</label>
        <div className="relative">
          <select
            className="w-full appearance-none rounded-xl bg-slate-800/80 border border-slate-700/60 p-2.5 text-xs font-medium text-slate-200 outline-none transition focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
            value={current?.repository_id || ""}
            onChange={(e) => onSelect(e.target.value)}
          >
            <option value="">— Select Repository —</option>
            {repos.map((r) => (
              <option key={r.repository_id} value={r.repository_id}>
                {r.repository_name} ({r.status})
              </option>
            ))}
          </select>
          <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2.5 text-slate-400 text-xs">
            ▼
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <nav className="flex flex-col gap-1">
        {TABS.map(([k, icon, label]) => {
          const isActive = tab === k;
          return (
            <button
              key={k}
              onClick={() => onTab(k)}
              className={`flex items-center gap-3 rounded-xl px-3.5 py-2.5 text-left text-xs font-medium transition-all duration-150 ${
                isActive
                  ? "bg-gradient-to-r from-indigo-600 to-indigo-500 text-white shadow-md shadow-indigo-600/30"
                  : "text-slate-300 hover:bg-slate-800/70 hover:text-white"
              }`}
            >
              <span className="text-base">{icon}</span>
              <span>{label}</span>
            </button>
          );
        })}
      </nav>

      {/* Ingestion & Action Panel */}
      <div className="mt-auto space-y-2.5 border-t border-slate-800/80 pt-4">
        <label className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">Import Codebase</label>
        
        {/* Upload ZIP */}
        <label className="flex items-center justify-center gap-2 cursor-pointer rounded-xl bg-slate-800/90 border border-slate-700/50 p-2.5 text-center text-xs font-medium text-slate-200 hover:bg-slate-700/80 hover:border-slate-600 transition shadow-sm">
          <span>📦</span>
          <span>Upload Project ZIP</span>
          <input
            type="file"
            accept=".zip"
            className="hidden"
            disabled={busy}
            onChange={(e) => e.target.files[0] && onUpload(e.target.files[0])}
          />
        </label>

        {/* GitHub Clone */}
        <div className="space-y-1.5">
          <input
            className="w-full rounded-xl bg-slate-800/90 border border-slate-700/50 p-2.5 text-xs text-slate-200 placeholder:text-slate-500 outline-none transition focus:border-indigo-500"
            placeholder="https://github.com/user/repo"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
          />
          <button
            disabled={busy || !url}
            onClick={() => onGithub(url)}
            className="w-full rounded-xl bg-slate-800/90 border border-slate-700/60 p-2 text-xs font-medium text-slate-300 hover:bg-slate-700 hover:text-white transition disabled:opacity-40"
          >
            Clone &amp; Index Repo
          </button>
        </div>

        {/* Preloaded Sample Project Button */}
        <button
          disabled={busy}
          onClick={onSample}
          className="w-full rounded-xl bg-gradient-to-r from-indigo-600 to-purple-600 p-2.5 text-xs font-semibold text-white shadow-lg shadow-indigo-600/25 hover:from-indigo-500 hover:to-purple-500 transition disabled:opacity-50"
        >
          {busy ? "Indexing..." : "⚡ Load Sample Project"}
        </button>
      </div>
    </aside>
  );
}
