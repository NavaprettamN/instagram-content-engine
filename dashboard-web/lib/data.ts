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

export async function getSnapshots(limit = 20): Promise<any[]> {
  return rest(`analytics_snapshots?select=*&order=date.desc&limit=${limit}`);
}

export async function getConfigValue(key: string): Promise<string | null> {
  const rows = await rest(`config?select=value&key=eq.${encodeURIComponent(key)}`);
  return rows[0]?.value ?? null;
}

export type IgMedia = {
  id: string;
  caption: string | null;
  media_type: string; // IMAGE | VIDEO | CAROUSEL_ALBUM
  media_product_type: string; // FEED | REELS | STORY
  media_url: string | null;
  thumbnail_url: string | null;
  permalink: string;
  timestamp: string;
  like_count: number | null;
  comments_count: number | null;
};

// Recent posts straight from the Instagram API (server-side; token never
// reaches the browser). Optional: returns [] when the Meta env vars aren't
// configured or the call fails, so the dashboard degrades gracefully.
export async function getRecentMedia(limit = 12): Promise<IgMedia[]> {
  const tok = process.env.META_ACCESS_TOKEN;
  const uid = process.env.INSTAGRAM_USER_ID;
  if (!tok || !uid) return [];
  try {
    const fields =
      "id,caption,media_type,media_product_type,media_url,thumbnail_url," +
      "permalink,timestamp,like_count,comments_count";
    const r = await fetch(
      `https://graph.instagram.com/v21.0/${uid}/media?fields=${fields}&limit=${limit}&access_token=${tok}`,
      { next: { revalidate: 300 } }, // 5-min cache; engagement doesn't need live reads
    );
    if (!r.ok) return [];
    const j = await r.json();
    return (j.data || []).filter((m: IgMedia) => m.media_product_type !== "STORY");
  } catch {
    return [];
  }
}
