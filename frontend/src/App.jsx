import { useCallback, useEffect, useState } from "react";
import { api, errMsg } from "./services/api";
import Sidebar from "./components/Sidebar";
import Chat from "./components/Chat";
import Dashboard from "./components/Dashboard";
import FileExplorer from "./components/FileExplorer";
import GraphView from "./components/GraphView";
import Dependencies from "./components/Dependencies";
import Settings from "./components/Settings";

export default function App() {
  const [repos, setRepos] = useState([]);
  const [currentId, setCurrentId] = useState("");
  const [tab, setTab] = useState("chat");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [open, setOpen] = useState({ path: "", line: 0 });
  const current = repos.find((r) => r.repository_id === currentId);

  const refresh = useCallback(() => api.repos().then(setRepos).catch((e) => setError(errMsg(e))), []);
  useEffect(() => { refresh(); }, [refresh]);

  // Poll while a repository is being indexed
  useEffect(() => {
    if (!repos.some((r) => ["pending", "indexing"].includes(r.status))) return;
    const t = setInterval(refresh, 2000);
    return () => clearInterval(t);
  }, [repos, refresh]);

  const add = async (fn) => {
    setBusy(true); setError("");
    try {
      const r = await fn();
      await refresh();
      setCurrentId(r.repository_id);
      setTab("dashboard");
    } catch (e) {
      setError(errMsg(e));
    } finally {
      setBusy(false);
    }
  };

  const openFile = (path, line = 0) => { setOpen({ path, line }); setTab("files"); };

  return (
    <div className="flex h-screen flex-col bg-slate-950 font-sans text-slate-100">
      {/* Top Header with Glass Effect */}
      <header className="glass-panel z-10 flex items-center justify-between px-6 py-3.5 border-b border-slate-800/80 shadow-md">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-tr from-indigo-600 via-indigo-500 to-purple-500 shadow-lg shadow-indigo-500/25">
            <span className="text-lg">⚡</span>
          </div>
          <div>
            <h1 className="text-base font-bold tracking-tight bg-gradient-to-r from-white via-slate-200 to-slate-400 bg-clip-text text-transparent">
              Codebase AI Assistant
            </h1>
            <p className="text-[11px] font-medium tracking-wide text-indigo-400/90 uppercase">
              Agentic GraphRAG • Knowledge Graph Engine
            </p>
          </div>
        </div>

        {current && (
          <div className="flex items-center gap-2.5 rounded-full bg-slate-900/90 border border-slate-800/90 px-3.5 py-1.5 shadow-sm">
            <span className="relative flex h-2.5 w-2.5">
              {["pending", "indexing"].includes(current.status) ? (
                <>
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-amber-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-amber-500"></span>
                </>
              ) : current.status === "indexed" ? (
                <>
                  <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500 shadow-sm shadow-emerald-500/50"></span>
                </>
              ) : (
                <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-rose-500"></span>
              )}
            </span>
            <span className="font-mono text-xs font-medium text-slate-200">{current.repository_name}</span>
            <span className="text-xs text-slate-400 capitalize">({current.status})</span>
          </div>
        )}
      </header>

      {/* Global Error Banner */}
      {error && (
        <div className="bg-rose-950/70 border-b border-rose-800/60 px-6 py-2.5 text-xs text-rose-200 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span>⚠️</span>
            <span>{error}</span>
          </div>
          <button className="rounded px-2 py-0.5 font-medium underline hover:text-white" onClick={() => setError("")}>
            Dismiss
          </button>
        </div>
      )}

      {/* Main Body */}
      <div className="flex min-h-0 flex-1 overflow-hidden">
        <Sidebar
          repos={repos}
          current={current}
          onSelect={setCurrentId}
          tab={tab}
          onTab={setTab}
          busy={busy}
          onUpload={(f) => add(() => api.upload(f))}
          onGithub={(u) => add(() => api.github(u))}
          onSample={() => add(api.sample)}
        />
        <main className="min-w-0 flex-1 overflow-auto bg-gradient-to-b from-slate-950 via-slate-900/70 to-slate-950">
          {tab === "chat" && <Chat repo={current} onOpenFile={openFile} />}
          {tab === "dashboard" && <Dashboard repo={current} />}
          {tab === "files" && <FileExplorer repo={current} openPath={open.path} openLine={open.line} onOpenFile={openFile} />}
          {tab === "graph" && <GraphView repo={current} />}
          {tab === "deps" && <Dependencies repo={current} />}
          {tab === "settings" && <Settings />}
        </main>
      </div>
    </div>
  );
}
