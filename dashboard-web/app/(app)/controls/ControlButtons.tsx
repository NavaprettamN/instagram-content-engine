"use client";
import { useState } from "react";

const JOBS = [
  {
    wf: "meme.yml",
    icon: "🎬",
    label: "Post a meme reel",
    desc: "Build + auto-publish a meme reel now (also reposts it to Stories)",
    hasFormat: true,
  },
  {
    wf: "comment_reply.yml",
    icon: "💬",
    label: "Reply to comments",
    desc: "Poll new comments and reply on-brand",
  },
  {
    wf: "analytics.yml",
    icon: "📈",
    label: "Refresh analytics",
    desc: "Pull Meta insights + weekly AI analysis",
  },
  {
    wf: "linkbio.yml",
    icon: "🔗",
    label: "Rebuild link-in-bio",
    desc: "Redeploy the bio page to GitHub Pages",
  },
];

const FORMATS = [
  { v: "auto", label: "Auto", hint: "alternate per run" },
  { v: "video", label: "Video", hint: "Reddit video, original audio" },
  { v: "images", label: "Images", hint: "image meme + CC music" },
];

export function ControlButtons() {
  const [status, setStatus] = useState<Record<string, string>>({});
  const [format, setFormat] = useState("auto");

  async function run(wf: string, inputs?: Record<string, string>) {
    setStatus((s) => ({ ...s, [wf]: "starting…" }));
    try {
      const r = await fetch("/api/trigger", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ workflow: wf, inputs }),
      });
      const j = await r.json();
      setStatus((s) => ({ ...s, [wf]: r.ok ? "✓ started" : `✗ ${j.error || r.status}` }));
    } catch (e) {
      setStatus((s) => ({ ...s, [wf]: `✗ ${String(e)}` }));
    }
  }

  return (
    <div className="grid" style={{ gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))" }}>
      {JOBS.map((j) => (
        <div className="card job" key={j.wf}>
          <div className="job-head">
            <span className="job-icon">{j.icon}</span>
            <div>
              <div className="job-title">{j.label}</div>
              <div className="job-desc">{j.desc}</div>
            </div>
          </div>
          {j.hasFormat && (
            <div className="seg" role="radiogroup" aria-label="Reel format">
              {FORMATS.map((f) => (
                <button
                  key={f.v}
                  className={`seg-btn ${format === f.v ? "on" : ""}`}
                  onClick={() => setFormat(f.v)}
                  title={f.hint}
                  type="button"
                >
                  {f.label}
                </button>
              ))}
            </div>
          )}
          <div className="row" style={{ alignItems: "center", marginTop: "auto" }}>
            <button
              className="btn primary"
              onClick={() => run(j.wf, j.hasFormat ? { format } : undefined)}
            >
              Run now
            </button>
            <span className={`run-status ${status[j.wf]?.startsWith("✗") ? "bad" : ""}`}>
              {status[j.wf] || ""}
            </span>
          </div>
        </div>
      ))}
    </div>
  );
}
