import { useEffect, useMemo, useState } from "react";
import { api, errMsg } from "../services/api";

function buildTree(files) {
  const root = {};
  files.forEach((f) => { let n = root; f.path.split("/").forEach((p, i, a) => { n[p] = n[p] || (i === a.length - 1 ? { __file: f } : {}); n = n[p]; }); });
  return root;
}

function Node({ name, node, depth, onPick, active }) {
  const [open, setOpen] = useState(true);
  if (node.__file) return <div style={{ paddingLeft: depth * 14 }} onClick={() => onPick(node.__file.path)} className={`cursor-pointer rounded px-2 py-1 text-sm hover:bg-slate-800 ${active === node.__file.path ? "bg-slate-800 text-indigo-300" : ""}`}>📄 {name}</div>;
  return (
    <div>
      <div style={{ paddingLeft: depth * 14 }} className="cursor-pointer px-2 py-1 text-sm font-medium" onClick={() => setOpen(!open)}>{open ? "📂" : "📁"} {name}</div>
      {open && Object.entries(node).sort(([a, x], [b, y]) => (!!x.__file - !!y.__file) || a.localeCompare(b)).map(([k, v]) => <Node key={k} name={k} node={v} depth={depth + 1} onPick={onPick} active={active} />)}
    </div>
  );
}

export default function FileExplorer({ repo, openPath, openLine, onOpenFile }) {
  const [files, setFiles] = useState([]);
  const [content, setContent] = useState("");
  const [err, setErr] = useState("");
  useEffect(() => { if (repo) api.files(repo.repository_id).then(setFiles).catch((e) => setErr(errMsg(e))); }, [repo?.repository_id, repo?.status]);
  useEffect(() => { if (repo && openPath) api.file(repo.repository_id, openPath).then((r) => setContent(r.content)).catch((e) => setErr(errMsg(e))); }, [openPath]);
  useEffect(() => { if (openLine) document.getElementById(`ln-${openLine}`)?.scrollIntoView({ block: "center" }); }, [content, openLine]);
  const tree = useMemo(() => buildTree(files), [files]);
  if (!repo) return <p className="p-8 text-slate-400">No repository selected.</p>;
  return (
    <div className="flex h-full">
      <div className="w-72 shrink-0 overflow-y-auto border-r border-slate-800 p-2">
        <div className="px-2 py-1 font-semibold">📁 {repo.repository_name}</div>
        {Object.entries(tree).sort(([a, x], [b, y]) => (!!x.__file - !!y.__file) || a.localeCompare(b)).map(([k, v]) => <Node key={k} name={k} node={v} depth={1} onPick={onOpenFile} active={openPath} />)}
      </div>
      <div className="flex-1 overflow-auto bg-slate-900 p-4">
        {err && <p className="text-red-400">{err}</p>}
        {openPath ? <><div className="mb-2 font-mono text-xs text-slate-400">{openPath}</div>
          <pre className="text-xs leading-5">{content.split("\n").map((l, i) => <div id={`ln-${i + 1}`} key={i} className={i + 1 === openLine ? "bg-indigo-900/50" : ""}><span className="mr-3 inline-block w-8 select-none text-right text-slate-600">{i + 1}</span>{l}</div>)}</pre></>
          : <p className="text-slate-400">Select a file to view its source code.</p>}
      </div>
    </div>
  );
}
