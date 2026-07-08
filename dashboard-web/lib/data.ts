// Server-only Supabase access via its REST (PostgREST) API — keeps the
// service_role key on the server and avoids an extra SDK dependency.
import "server-only";

const URL = process.env.SUPABASE_URL;
const KEY = process.env.SUPABASE_KEY;

async function rest(path: string): Promise<any[]> {
  if (!URL || !KEY) throw new Error("SUPABASE_URL / SUPABASE_KEY not set");
  const r = await fetch(`${URL}/rest/v1/${path}`, {
    headers: { apikey: KEY, Authorization: `Bearer ${KEY}` },
    cache: "no-store",
  });
  if (!r.ok) throw new Error(`Supabase ${r.status}: ${await r.text()}`);
  return r.json();
}

export type Idea = {
  id: number;
  hook: string;
  status: string;
  content_type: string | null;
  created_at: string;
  published_at: string | null;
  image_paths: string | null;
  post_id: string | null;
};

export async function getIdeas(limit = 100): Promise<Idea[]> {
  return rest(`content_ideas?select=*&order=created_at.desc&limit=${limit}`);
}

export async function getSnapshots(limit = 20): Promise<any[]> {
  return rest(`analytics_snapshots?select=*&order=date.desc&limit=${limit}`);
}

export async function getConfigValue(key: string): Promise<string | null> {
  const rows = await rest(`config?select=value&key=eq.${encodeURIComponent(key)}`);
  return rows[0]?.value ?? null;
}

export function counts(ideas: Idea[]) {
  const by: Record<string, number> = {};
  for (const i of ideas) by[i.status] = (by[i.status] || 0) + 1;
  return by;
}
