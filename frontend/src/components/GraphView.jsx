import { useEffect, useState } from "react";
import { api, errMsg } from "../services/api";
import GraphCanvas from "./GraphCanvas";

export default function GraphView({ repo }) {
  const [level, setLevel] = useState("file");
  const [data, setData] = useState(null);
  const [err, setErr] = useState("");
  useEffect(() => {
    if (repo?.status !== "indexed") return;
    setErr(""); api.graph(repo.repository_id, level).then(setData).catch((e) => setErr(errMsg(e)));
  }, [repo?.repository_id, repo?.status, level]);
  if (!repo) return <p className="p-8 text-slate-400">No repository selected.</p>;
  return (
    <div className="flex h-full flex-col gap-3 p-4">
      <div className="flex items-center gap-3 text-sm">
        <span>Architecture graph:</span>
        <select value={level} onChange={(e) => setLevel(e.target.value)} className="rounded bg-slate-800 p-1">
          <option value="file">File dependencies</option>
          <option value="full">File → Class → Function (full)</option>
        </select>
        {data?.truncated && <span className="text-amber-400">Large graph truncated for display.</span>}
        {err && <span className="text-red-400">{err}</span>}
      </div>
      <div className="flex-1">{data && <GraphCanvas data={data} />}</div>
    </div>
  );
}
