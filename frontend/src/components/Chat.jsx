import { useEffect, useRef, useState } from "react";
import { api, errMsg } from "../services/api";

const EXAMPLES = [
  { icon: "📍", q: "Where are student marks stored?", desc: "Locates data persistence model & methods" },
  { icon: "💥", q: "If I modify StudentService.java, which files may be affected?", desc: "Graph reverse reachability & dependency impact" },
  { icon: "🔐", q: "Where is password validation implemented?", desc: "Explores AuthService & security logic" },
  { icon: "🔄", q: "Explain how login works across the codebase.", desc: "Traces call flow from Login to AuthService" }
];

export default function Chat({ repo, onOpenFile }) {
  const [msgs, setMsgs] = useState([]);
  const [q, setQ] = useState("");
  const [loading, setLoading] = useState(false);
  const bottom = useRef();

  useEffect(() => { setMsgs([]); }, [repo?.repository_id]);
  useEffect(() => bottom.current?.scrollIntoView({ behavior: "smooth" }), [msgs, loading]);

  const send = async (text) => {
    const question = (text ?? q).trim();
    if (!question || loading) return;
    const history = msgs.filter((m) => !m.error).map((m) => ({ role: m.role, content: m.content }));
    setMsgs((m) => [...m, { role: "user", content: question }]);
    setQ(""); setLoading(true);
    try {
      const r = await api.chat(repo.repository_id, question, history);
      setMsgs((m) => [...m, { role: "assistant", content: r.answer, sources: r.sources, tools: r.tools_used, llmError: r.llm_error }]);
    } catch (e) {
      setMsgs((m) => [...m, { role: "assistant", content: errMsg(e), error: true }]);
    } finally { setLoading(false); }
  };

  if (!repo) {
    return (
      <div className="flex h-full flex-col items-center justify-center p-8 text-center">
        <div className="h-16 w-16 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-3xl mb-4 shadow-inner">
          💡
        </div>
        <h3 className="text-base font-semibold text-slate-200">No Repository Selected</h3>
        <p className="mt-1 max-w-sm text-xs text-slate-400">
          Select an indexed codebase from the sidebar or click <b className="text-indigo-400">Load sample project</b> to begin.
        </p>
      </div>
    );
  }

  if (repo.status !== "indexed") {
    return (
      <div className="flex h-full flex-col items-center justify-center p-8 text-center">
        <div className="h-14 w-14 rounded-2xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-2xl mb-4 animate-bounce">
          ⏳
        </div>
        <h3 className="text-sm font-semibold text-slate-200">
          Repository Status: <span className="text-amber-400 capitalize">{repo.status}</span>
        </h3>
        {repo.error ? (
          <p className="mt-2 text-xs text-rose-400 max-w-md">{repo.error}</p>
        ) : (
          <p className="mt-1 text-xs text-slate-400">
            Parsing AST, building knowledge graph, and generating code chunks...
          </p>
        )}
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col bg-slate-950">
      {/* Messages Scroll Area */}
      <div className="flex-1 space-y-5 overflow-y-auto p-6">
        {!msgs.length && (
          <div className="mx-auto max-w-2xl py-8">
            <div className="text-center mb-8">
              <span className="inline-block rounded-full bg-indigo-500/10 border border-indigo-500/30 px-3 py-1 text-xs font-medium text-indigo-400">
                Agentic Hybrid GraphRAG
              </span>
              <h2 className="mt-3 text-lg font-bold text-slate-100">
                Ask anything about <span className="text-indigo-400">{repo.repository_name}</span>
              </h2>
              <p className="mt-1 text-xs text-slate-400">
                The agent inspects AST relationships, calls, dependencies, and vector semantics.
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {EXAMPLES.map((e, idx) => (
                <button
                  key={idx}
                  onClick={() => send(e.q)}
                  className="glow-card flex flex-col text-left rounded-xl bg-slate-900/80 border border-slate-800/80 p-3.5 hover:border-indigo-500/50 transition group"
                >
                  <div className="flex items-center gap-2 font-medium text-xs text-slate-200 group-hover:text-indigo-300">
                    <span>{e.icon}</span>
                    <span>{e.q}</span>
                  </div>
                  <span className="mt-1.5 text-[11px] text-slate-500">{e.desc}</span>
                </button>
              ))}
            </div>
          </div>
        )}

        {msgs.map((m, i) => (
          <div
            key={i}
            className={`flex flex-col ${
              m.role === "user" ? "items-end" : "items-start"
            }`}
          >
            <div
              className={`max-w-2xl rounded-2xl px-4 py-3 text-xs leading-relaxed shadow-sm ${
                m.role === "user"
                  ? "bg-gradient-to-r from-indigo-600 to-indigo-500 text-white rounded-br-none"
                  : m.error
                  ? "bg-rose-950/60 border border-rose-800/60 text-rose-200 rounded-bl-none"
                  : "bg-slate-900/95 border border-slate-800 text-slate-200 rounded-bl-none"
              }`}
            >
              <div className="whitespace-pre-wrap font-sans">{m.content}</div>

              {m.llmError && (
                <div className="mt-2.5 rounded-lg bg-amber-950/60 border border-amber-800/50 p-2 text-[11px] text-amber-300">
                  ⚠️ {m.llmError}
                </div>
              )}

              {m.tools?.length > 0 && (
                <div className="mt-3 flex flex-wrap items-center gap-1.5 border-t border-slate-800/80 pt-2 text-[10px]">
                  <span className="text-slate-400">Agent tools:</span>
                  {m.tools.map((t) => (
                    <span
                      key={t}
                      className="rounded bg-indigo-950/80 border border-indigo-700/50 px-1.5 py-0.5 font-mono text-indigo-300"
                    >
                      {t}
                    </span>
                  ))}
                </div>
              )}

              {m.sources?.length > 0 && (
                <details className="mt-2.5 text-[11px]" open={!!m.llmError}>
                  <summary className="cursor-pointer font-medium text-indigo-400 hover:text-indigo-300">
                    Verified Sources &amp; Citations ({m.sources.length})
                  </summary>
                  <ul className="mt-2 space-y-1.5">
                    {m.sources.map((s, j) => (
                      <li
                        key={j}
                        className="rounded-lg bg-slate-950/80 border border-slate-800/90 p-2 font-mono text-[11px]"
                      >
                        <div className="flex items-center justify-between">
                          <button
                            className="text-indigo-300 hover:underline font-semibold"
                            onClick={() => onOpenFile(s.file_path, s.start_line)}
                          >
                            {s.file_path}:{s.start_line}-{s.end_line}
                          </button>
                          <span className="text-[10px] text-slate-500 uppercase">{s.kind}</span>
                        </div>
                        {(s.class_name || s.function_name) && (
                          <div className="mt-1 text-[10px] text-slate-400 font-sans">
                            {[s.class_name && `class ${s.class_name}`, s.function_name && `fn ${s.function_name}`]
                              .filter(Boolean)
                              .join(" • ")}
                          </div>
                        )}
                      </li>
                    ))}
                  </ul>
                </details>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex items-center gap-2 text-xs text-indigo-400">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-indigo-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-indigo-500"></span>
            </span>
            <span className="font-medium animate-pulse">Agent is planning tools &amp; synthesizing answer...</span>
          </div>
        )}
        <div ref={bottom} />
      </div>

      {/* Input Bar */}
      <div className="border-t border-slate-800/80 bg-slate-900/60 p-4 backdrop-blur-md">
        <div className="mx-auto flex max-w-4xl gap-2.5">
          <input
            className="flex-1 rounded-xl bg-slate-800/90 border border-slate-700/60 px-4 py-2.5 text-xs text-slate-200 placeholder:text-slate-500 outline-none transition focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
            placeholder="Ask questions about functions, classes, dependencies or architecture..."
            value={q}
            onChange={(e) => setQ(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && send()}
          />
          <button
            onClick={() => send()}
            disabled={loading || !q.trim()}
            className="rounded-xl bg-indigo-600 px-5 py-2.5 text-xs font-semibold text-white shadow-md shadow-indigo-600/30 hover:bg-indigo-500 transition disabled:opacity-40"
          >
            Send
          </button>
          <button
            onClick={() => setMsgs([])}
            className="rounded-xl bg-slate-800 border border-slate-700/60 px-3.5 py-2.5 text-xs font-medium text-slate-400 hover:bg-slate-700 hover:text-slate-200 transition"
          >
            Clear
          </button>
        </div>
      </div>
    </div>
  );
}
