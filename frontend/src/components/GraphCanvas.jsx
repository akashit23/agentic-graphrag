import { useEffect, useRef, useState } from "react";
import cytoscape from "cytoscape";

const COLORS = {
  File: "#6366f1",        // Indigo
  Class: "#10b981",       // Emerald
  Function: "#f59e0b",    // Amber
  Method: "#f97316",      // Orange
  Module: "#94a3b8",      // Slate
  Repository: "#ec4899"   // Pink
};

export default function GraphCanvas({ data, highlight }) {
  const ref = useRef();
  const [selected, setSelected] = useState(null);

  useEffect(() => {
    if (!data) return;
    const ids = new Set(data.nodes.map((n) => n.id));
    const cy = cytoscape({
      container: ref.current,
      elements: [
        ...data.nodes.map((n) => ({
          data: {
            id: n.id,
            label: n.name,
            kind: n.label,
            path: n.path,
            start: n.start_line,
            end: n.end_line
          }
        })),
        ...data.edges
          .filter((e) => ids.has(e.source) && ids.has(e.target))
          .map((e, i) => ({
            data: { id: `e${i}`, source: e.source, target: e.target, label: e.type }
          })),
      ],
      style: [
        {
          selector: "node",
          style: {
            label: "data(label)",
            "font-size": 10,
            color: "#f1f5f9",
            "text-valign": "bottom",
            "text-margin-y": 4,
            "background-color": (n) => COLORS[n.data("kind")] || "#64748b",
            width: 22,
            height: 22,
            "border-width": 1.5,
            "border-color": "#1e293b"
          }
        },
        {
          selector: "node[kind = 'File']",
          style: { shape: "round-rectangle", width: 30, height: 22 }
        },
        {
          selector: "edge",
          style: {
            width: 1.5,
            "line-color": "#334155",
            "target-arrow-color": "#475569",
            "target-arrow-shape": "triangle",
            "curve-style": "bezier",
            "arrow-scale": 0.8
          }
        },
        {
          selector: ".sel",
          style: {
            "border-width": 3,
            "border-color": "#38bdf8",
            "shadow-blur": 15,
            "shadow-color": "#38bdf8",
            "shadow-opacity": 0.6
          }
        },
        {
          selector: "edge.sel",
          style: {
            "line-color": "#38bdf8",
            "target-arrow-color": "#38bdf8",
            label: "data(label)",
            "font-size": 9,
            color: "#38bdf8",
            width: 2.5
          }
        },
        {
          selector: ".hl",
          style: {
            "background-color": "#f43f5e",
            "border-color": "#ffe4e6",
            "border-width": 3
          }
        },
      ],
      layout: {
        name: "cose",
        animate: false,
        nodeRepulsion: 12000,
        idealEdgeLength: 100
      },
    });

    if (highlight) cy.getElementById(`file:${highlight}`).addClass("hl");

    cy.on("tap", "node", (e) => {
      cy.elements().removeClass("sel");
      const n = e.target;
      n.addClass("sel");
      n.connectedEdges().addClass("sel");
      setSelected({
        ...n.data(),
        links: n.connectedEdges().map((x) =>
          `${x.source().data("label")} —[${x.data("label")}]→ ${x.target().data("label")}`
        )
      });
    });

    return () => cy.destroy();
  }, [data, highlight]);

  return (
    <div className="relative h-full min-h-[460px] rounded-2xl overflow-hidden border border-slate-800 bg-slate-950/90 shadow-inner">
      <div ref={ref} className="h-full w-full" />
      
      {/* Legend Badge Overlay */}
      <div className="absolute left-4 top-4 flex flex-wrap gap-2 text-[10px] glass-panel px-3 py-1.5 rounded-xl shadow-md">
        {Object.entries(COLORS).map(([k, c]) => (
          <span key={k} className="flex items-center gap-1.5 font-medium text-slate-300">
            <span style={{ backgroundColor: c }} className="h-2.5 w-2.5 rounded-full shadow-sm" />
            {k}
          </span>
        ))}
      </div>

      {/* Selected Node Details Drawer */}
      {selected && (
        <div className="absolute bottom-4 right-4 max-h-64 w-84 overflow-auto rounded-2xl glass-panel p-4 text-xs shadow-xl border border-slate-700/80">
          <div className="flex items-center justify-between pb-2 border-b border-slate-800">
            <b className="text-slate-100">{selected.kind}: {selected.label}</b>
            <button
              onClick={() => setSelected(null)}
              className="text-slate-400 hover:text-white text-xs px-1"
            >
              ✕
            </button>
          </div>
          {selected.path && (
            <div className="mt-2 font-mono text-[11px] text-indigo-300">
              {selected.path}{selected.start ? `:${selected.start}-${selected.end}` : ""}
            </div>
          )}
          <div className="mt-2.5 text-[10px] font-semibold text-slate-400 uppercase tracking-wider">
            Connected Edges ({selected.links.length})
          </div>
          <ul className="mt-1 space-y-1 text-slate-300 font-mono text-[11px]">
            {selected.links.slice(0, 20).map((l, i) => (
              <li key={i} className="rounded bg-slate-900/80 px-2 py-1 border border-slate-800/80">
                {l}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
