"use client";
import { useState } from "react";

const JOBS = [
  { wf: "research.yml", label: "Research ideas", desc: "Pull trends → generate new content ideas" },
  { wf: "generate.yml", label: "Generate content", desc: "Turn approved ideas into reels/carousels" },
  { wf: "publish.yml", label: "Publish next post", desc: "Post the next queued item to Instagram" },
  { wf: "meme.yml", label: "Post a meme reel", desc: "Build + auto-publish a meme reel now" },
  { wf: "analytics.yml", label: "Refresh analytics", desc: "Pull Meta insights + weekly AI analysis" },
];

export function ControlButtons() {
  const [status, setStatus] = useState<Record<string, string>>({});

  async function run(wf: string) {
    setStatus((s) => ({ ...s, [wf]: "starting…" }));
    try {
      const r = await fetch("/api/trigger", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ workflow: wf }),
      });
      const j = await r.json();
      setStatus((s) => ({ ...s, [wf]: r.ok ? "✓ started" : `✗ ${j.error || r.status}` }));
    } catch (e) {
      setStatus((s) => ({ ...s, [wf]: `✗ ${String(e)}` }));
    }
  }

  return (
    <div className="grid" style={{ gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))" }}>
      {JOBS.map((j) => (
        <div className="card" key={j.wf}>
          <div style={{ fontWeight: 700, marginBottom: 4 }}>{j.label}</div>
          <div className="muted" style={{ fontSize: 13, marginBottom: 14 }}>{j.desc}</div>
          <div className="row" style={{ alignItems: "center" }}>
            <button className="btn primary" onClick={() => run(j.wf)}>Run now</button>
            <span className="muted" style={{ fontSize: 13 }}>{status[j.wf] || ""}</span>
          </div>
        </div>
      ))}
    </div>
  );
}
