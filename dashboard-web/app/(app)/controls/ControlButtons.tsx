"use client";
import { useState } from "react";
import { Icon, IconName } from "@/components/Icon";

const JOBS: {
  wf: string; icon: IconName; label: string; desc: string; hasFormat?: boolean;
}[] = [
  {
    wf: "meme.yml",
    icon: "film",
    label: "Post a meme reel",
    desc: "Build + auto-publish a meme reel now (also reposts it to Stories)",
    hasFormat: true,
  },
  {
    wf: "comment_reply.yml",
    icon: "message",
    label: "Reply to comments",
    desc: "Poll new comments and reply on-brand",
  },
  {
    wf: "analytics.yml",
    icon: "bar-chart",
    label: "Refresh analytics",
    desc: "Pull Meta insights + weekly AI analysis",
  },
  {
    wf: "linkbio.yml",
    icon: "link",
    label: "Rebuild link-in-bio",
    desc: "Redeploy the bio page to GitHub Pages",
  },
];

const FORMATS = [
  { v: "auto", label: "Auto", hint: "alternate per run" },
  { v: "video", label: "Video", hint: "Reddit video, original audio" },
  { v: "images", label: "Images", hint: "image meme + CC music" },
];

type RunState = { state: "running" | "ok" | "error"; msg: string };

export function ControlButtons() {
  const [status, setStatus] = useState<Record<string, RunState>>({});
  const [format, setFormat] = useState("auto");

  async function run(wf: string, inputs?: Record<string, string>) {
    setStatus((s) => ({ ...s, [wf]: { state: "running", msg: "Starting…" } }));
    try {
      const r = await fetch("/api/trigger", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ workflow: wf, inputs }),
      });
      const j = await r.json();
      setStatus((s) => ({
        ...s,
        [wf]: r.ok
          ? { state: "ok", msg: "Started" }
          : { state: "error", msg: String(j.error || r.status) },
      }));
    } catch (e) {
      setStatus((s) => ({ ...s, [wf]: { state: "error", msg: String(e) } }));
    }
  }

  return (
    <div className="grid" style={{ gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))" }}>
      {JOBS.map((j) => (
        <div className="card job" key={j.wf}>
          <div className="job-head">
            <span className="job-icon"><Icon name={j.icon} size={18} /></span>
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
              disabled={status[j.wf]?.state === "running"}
            >
              Run now
            </button>
            {status[j.wf] && (
              <span className={`run-status ${status[j.wf].state === "error" ? "bad" : ""}`}>
                {status[j.wf].state === "ok" && <Icon name="check" size={14} />}
                {status[j.wf].state === "error" && <Icon name="x" size={14} />}
                {status[j.wf].msg}
              </span>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}
