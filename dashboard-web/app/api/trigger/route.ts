import { auth } from "@/auth";
import { NextResponse } from "next/server";

// Kicks off a GitHub Actions workflow via workflow_dispatch. Requires a GH PAT
// with `workflow` scope in GH_PAT. Auth-gated to the signed-in dashboard user.
const ALLOWED = new Set([
  "meme.yml", "comment_reply.yml", "analytics.yml", "linkbio.yml",
]);
// Per-workflow dispatch inputs the dashboard may set (everything else is dropped).
const ALLOWED_INPUTS: Record<string, Record<string, Set<string>>> = {
  "meme.yml": { format: new Set(["auto", "video", "images"]) },
};

export async function POST(req: Request) {
  const session = await auth();
  if (!session) return NextResponse.json({ error: "unauthorized" }, { status: 401 });

  const { workflow, inputs } = await req.json().catch(() => ({}));
  if (!ALLOWED.has(workflow)) {
    return NextResponse.json({ error: "unknown workflow" }, { status: 400 });
  }
  const cleanInputs: Record<string, string> = {};
  for (const [k, v] of Object.entries(inputs || {})) {
    if (ALLOWED_INPUTS[workflow]?.[k]?.has(String(v))) cleanInputs[k] = String(v);
  }
  const pat = process.env.GH_PAT;
  const repo = process.env.GH_REPO;
  if (!pat || !repo) {
    return NextResponse.json({ error: "GH_PAT / GH_REPO not configured" }, { status: 500 });
  }

  const r = await fetch(
    `https://api.github.com/repos/${repo}/actions/workflows/${workflow}/dispatches`,
    {
      method: "POST",
      headers: {
        Authorization: `Bearer ${pat}`,
        Accept: "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
      },
      body: JSON.stringify({ ref: "main", inputs: cleanInputs }),
    },
  );
  if (r.status !== 204) {
    return NextResponse.json({ error: `GitHub ${r.status}: ${await r.text()}` }, { status: 502 });
  }
  return NextResponse.json({ ok: true });
}
