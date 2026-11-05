import { useEffect, useState } from "react";
import { api, errMsg } from "../services/api";

const Row = ({ k, ok, v, hint }) => (
  <div className="rounded bg-slate-800 p-3 text-sm">
    <div className="flex justify-between"><span>{k}</span><b className={ok ? "text-green-400" : "text-amber-400"}>{v}</b></div>
    {!ok && hint && <div className="mt-1 font-mono text-xs text-slate-400">{hint}</div>}
  </div>
);

export default function Settings() {
  const [h, setH] = useState(null);
  const [err, setErr] = useState("");
  const load = () => { setErr(""); api.health().then(setH).catch((e) => setErr(errMsg(e))); };
  useEffect(load, []);
  return (
    <div className="max-w-xl space-y-3 p-6">
      <div className="flex items-center justify-between"><h2 className="text-lg font-semibold">Local AI status</h2><button onClick={load} className="rounded bg-slate-800 px-3 py-1 text-sm hover:bg-slate-700">Refresh</button></div>
      {err && <p className="text-red-400">{err}</p>}
      {h && <>
        <Row k="Backend" ok v={h.status} />
        <Row k="Ollama (local LLM)" ok={h.ollama_running} v={h.ollama_running ? "running" : "not running"} hint="Start the Ollama app, or run: ollama serve" />
        <Row k={`Model: ${h.ollama_model}`} ok={h.ollama_model_installed} v={h.ollama_model_installed ? "downloaded" : "not downloaded"} hint={`ollama pull ${h.ollama_model}`} />
        <Row k="Embeddings" ok v={`${h.embedding_provider} (${h.embedding_model})`} />
        <Row k="Graph backend" ok={h.graph_backend !== "neo4j" || h.neo4j} v={h.graph_backend === "neo4j" ? (h.neo4j ? "Neo4j connected" : "Neo4j offline") : "NetworkX (local)"} hint="Start Neo4j or set GRAPH_BACKEND=networkx" />
      </>}
      <p className="text-xs text-slate-500">Everything runs on your computer. No API keys, no cloud calls.</p>
    </div>
  );
}
