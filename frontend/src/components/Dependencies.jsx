import { useEffect, useState } from "react";
import { api, errMsg } from "../services/api";
import GraphCanvas from "./GraphCanvas";

const List = ({ title, items, color }) => (
  <div className="rounded-lg bg-slate-800 p-3">
    <div className={`mb-1 text-sm font-semibold ${color}`}>{title} ({items.length})</div>
    {items.length ? items.map((f) => <div key={f} className="font-mono text-xs">{f}</div>) : <div className="text-xs text-slate-500">none</div>}
  </div>
);

export default function Dependencies({ repo }) {
  const [files, setFiles] = useState([]);
  const [file, setFile] = useState("");
  const [dep, setDep] = useState(null);
  const [err, setErr] = useState("");
  useEffect(() => { if (repo?.status === "indexed") api.files(repo.repository_id).then((f) => setFiles(f)).catch((e) => setErr(errMsg(e))); }, [repo?.repository_id, repo?.status]);
  useEffect(() => { if (file) { setErr(""); api.deps(repo.repository_id, file).then(setDep).catch((e) => setErr(errMsg(e))); } }, [file]);
  if (!repo) return <p className="p-8 text-slate-400">No repository selected.</p>;
  return (
    <div className="flex h-full flex-col gap-3 p-4">
      <select value={file} onChange={(e) => setFile(e.target.value)} className="w-96 rounded bg-slate-800 p-2 text-sm">
        <option value="">Select a file to analyze…</option>
        {files.map((f) => <option key={f.path} value={f.path}>{f.path}</option>)}
      </select>
      {err && <p className="text-red-400">{err}</p>}
      {dep && (
        <div className="grid flex-1 grid-cols-1 gap-3 lg:grid-cols-3">
          <div className="space-y-3">
            <List title="Depends on" items={dep.depends_on} color="text-indigo-300" />
            <List title="Used by" items={dep.used_by} color="text-green-300" />
            <List title="Potentially affected if modified" items={dep.impacted} color="text-red-300" />
          </div>
          <div className="lg:col-span-2"><GraphCanvas data={dep} highlight={dep.file} /></div>
        </div>
      )}
    </div>
  );
}
