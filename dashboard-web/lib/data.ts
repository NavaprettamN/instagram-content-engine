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
  // Per-post insights (merged in from the /insights edge; null when the metric
  // isn't available for that media type or the call failed).
  reach: number | null;
  saved: number | null;
  shares: number | null;
  views: number | null;
  total_interactions: number | null;
};

const IG = "https://graph.instagram.com/v21.0";

// Per-media insights. Reels expose more metrics than feed images, and asking
// for a metric a media type doesn't support fails the whole request — so we
// request per-type metric sets and tolerate any failure by returning {}.
async function getMediaInsights(
  id: string,
  isVideo: boolean,
  tok: string,
): Promise<Record<string, number>> {
  const metrics = isVideo
    ? "reach,saved,shares,views,total_interactions"
    : "reach,saved,shares,total_interactions";
  try {
    const r = await fetch(
      `${IG}/${id}/insights?metric=${metrics}&access_token=${tok}`,
      { next: { revalidate: 300 } },
    );
    if (!r.ok) return {};
    const j = await r.json();
    const out: Record<string, number> = {};
    for (const m of j.data || []) {
      const v = m.total_value?.value ?? m.values?.[0]?.value;
      if (typeof v === "number") out[m.name] = v;
    }
    return out;
  } catch {
    return {};
  }
}

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
      `${IG}/${uid}/media?fields=${fields}&limit=${limit}&access_token=${tok}`,
      { next: { revalidate: 300 } }, // 5-min cache; engagement doesn't need live reads
    );
    if (!r.ok) return [];
    const j = await r.json();
    const posts: IgMedia[] = (j.data || []).filter(
      (m: IgMedia) => m.media_product_type !== "STORY",
    );
    // Enrich each post with its insights in parallel.
    return Promise.all(
      posts.map(async (m) => {
        const ins = await getMediaInsights(m.id, m.media_type === "VIDEO", tok);
        return {
          ...m,
          reach: ins.reach ?? null,
          saved: ins.saved ?? null,
          shares: ins.shares ?? null,
          views: ins.views ?? null,
          total_interactions: ins.total_interactions ?? null,
        };
      }),
    );
  } catch {
    return [];
  }
}

export type AccountInsights = {
  days: number;
  reach: number | null;
  interactions: number | null; // total_interactions
  engaged: number | null; // accounts_engaged
  profileViews: number | null;
  likes: number | null;
  comments: number | null;
  saves: number | null;
  shares: number | null;
  linkTaps: number | null; // profile_links_taps
};

// Account-level insights over the last `days` days. Each metric is fetched
// separately so one unsupported/erroring metric can't blank the whole panel;
// whatever succeeds is shown, the rest fall back to null.
export async function getAccountInsights(days = 30): Promise<AccountInsights | null> {
  const tok = process.env.META_ACCESS_TOKEN;
  const uid = process.env.INSTAGRAM_USER_ID;
  if (!tok || !uid) return null;

  const until = Math.floor(Date.now() / 1000);
  const since = until - days * 86400;

  async function metric(name: string): Promise<number | null> {
    try {
      const r = await fetch(
        `${IG}/${uid}/insights?metric=${name}&period=day&metric_type=total_value` +
          `&since=${since}&until=${until}&access_token=${tok}`,
        { next: { revalidate: 300 } },
      );
      if (!r.ok) return null;
      const j = await r.json();
      const v = j.data?.[0]?.total_value?.value;
      return typeof v === "number" ? v : null;
    } catch {
      return null;
    }
  }

  const [
    reach, interactions, engaged, profileViews,
    likes, comments, saves, shares, linkTaps,
  ] = await Promise.all([
    metric("reach"),
    metric("total_interactions"),
    metric("accounts_engaged"),
    metric("profile_views"),
    metric("likes"),
    metric("comments"),
    metric("saves"),
    metric("shares"),
    metric("profile_links_taps"),
  ]);

  const insights: AccountInsights = {
    days, reach, interactions, engaged, profileViews,
    likes, comments, saves, shares, linkTaps,
  };
  // If every metric failed (e.g. insights not permitted for this account),
  // signal "no data" rather than a panel full of dashes.
  const any = Object.values(insights).some((v, i) => i > 0 && v !== null);
  return any ? insights : null;
}
