import {
  getSnapshots, getConfigValue, getRecentMedia, getAccountInsights, IgMedia,
} from "@/lib/data";
import { FollowerChart } from "@/components/FollowerChart";
import { Icon, IconName } from "@/components/Icon";

export const dynamic = "force-dynamic";

function parse<T>(s: string | null, fallback: T): T {
  try { return s ? JSON.parse(s) : fallback; } catch { return fallback; }
}

const fmt = (n: number | null | undefined) =>
  typeof n === "number" ? n.toLocaleString() : "–";

function Kpi({
  value, label, icon, tone,
}: {
  value: React.ReactNode; label: string; icon: IconName; tone?: "up" | "down";
}) {
  return (
    <div className="card kpi">
      <span className="kpi-ico"><Icon name={icon} size={16} /></span>
      <div className={`n ${tone ?? ""}`}>{value}</div>
      <div className="l">{label}</div>
    </div>
  );
}

function PostCard({ m }: { m: IgMedia }) {
  const img = m.thumbnail_url || (m.media_type !== "VIDEO" ? m.media_url : null);
  const kindIcon: IconName =
    m.media_product_type === "REELS" ? "film"
    : m.media_type === "CAROUSEL_ALBUM" ? "grid"
    : "image";
  return (
    <a className="post" href={m.permalink} target="_blank" rel="noopener">
      {img
        ? <img src={img} alt={m.caption?.slice(0, 60) || "Instagram post"} loading="lazy" />
        : <div className="noimg">{m.caption?.slice(0, 70) || "View post"}</div>}
      <span className="kind"><Icon name={kindIcon} size={14} /></span>
      <div className="meta">
        <span className="stat"><Icon name="heart" size={13} /> {fmt(m.like_count)}</span>
        <span className="stat"><Icon name="message" size={13} /> {fmt(m.comments_count)}</span>
        {m.reach != null && (
          <span className="stat"><Icon name="eye" size={13} /> {fmt(m.reach)}</span>
        )}
        <span className="date-badge">{m.timestamp?.slice(5, 10)}</span>
      </div>
    </a>
  );
}

const INSIGHT_TILES: { key: keyof AccountInsightKeys; label: string; icon: IconName }[] = [
  { key: "reach", label: "Accounts reached", icon: "eye" },
  { key: "interactions", label: "Account interactions", icon: "activity" },
  { key: "engaged", label: "Accounts engaged", icon: "users" },
  { key: "profileViews", label: "Profile views", icon: "target" },
  { key: "likes", label: "Likes", icon: "heart" },
  { key: "comments", label: "Comments", icon: "message" },
  { key: "saves", label: "Saves", icon: "bookmark" },
  { key: "shares", label: "Shares", icon: "share" },
  { key: "linkTaps", label: "Link-in-bio taps", icon: "link" },
];
type AccountInsightKeys = {
  reach: number | null; interactions: number | null; engaged: number | null;
  profileViews: number | null; likes: number | null; comments: number | null;
  saves: number | null; shares: number | null; linkTaps: number | null;
};

export default async function Overview() {
  const [snaps, followerRaw, topRaw, media, insights] = await Promise.all([
    getSnapshots(1),
    getConfigValue("follower_history"),
    getConfigValue("top_performers"),
    getRecentMedia(12),
    getAccountInsights(30),
  ]);

  const followers = parse<{ date: string; count: number }[]>(followerRaw, []);
  const top = parse<{ hook: string; type: string; score: number; saved: number; shares: number }[]>(topRaw, []);
  const latestFollowers = followers.at(-1)?.count ?? null;
  const prevFollowers = followers.at(-2)?.count;
  const delta =
    typeof latestFollowers === "number" && typeof prevFollowers === "number"
      ? latestFollowers - prevFollowers
      : null;
  const analysis: string = snaps[0]?.analysis ?? "";
  const totalLikes = media.reduce((s, m) => s + (m.like_count || 0), 0);
  const totalComments = media.reduce((s, m) => s + (m.comments_count || 0), 0);

  return (
    <>
      <h1>Overview</h1>
      <p className="sub">How the meme account is performing right now.</p>

      <div className="grid">
        <Kpi
          icon="users"
          value={typeof latestFollowers === "number" ? latestFollowers.toLocaleString() : "—"}
          label="Followers"
        />
        <Kpi
          icon="trending-up"
          tone={delta === null ? undefined : delta >= 0 ? "up" : "down"}
          value={delta === null ? "—" : `${delta >= 0 ? "+" : ""}${delta.toLocaleString()}`}
          label="Since last week"
        />
        {media.length > 0 && (
          <>
            <Kpi icon="heart" value={totalLikes.toLocaleString()} label={`Likes · last ${media.length} posts`} />
            <Kpi icon="message" value={totalComments.toLocaleString()} label={`Comments · last ${media.length} posts`} />
          </>
        )}
      </div>

      {insights && (
        <div className="section" style={{ marginTop: 28 }}>
          <h2>Account insights · last {insights.days} days</h2>
          <div className="grid">
            {INSIGHT_TILES.map((t) =>
              t.key === "linkTaps" && insights.linkTaps == null ? null : (
                <Kpi key={t.key} icon={t.icon} value={fmt(insights[t.key])} label={t.label} />
              ),
            )}
          </div>
        </div>
      )}

      <div className="section" style={{ marginTop: 28 }}>
        <h2>Follower growth</h2>
        <div className="card">
          <FollowerChart points={followers.map((f) => ({ date: f.date, value: f.count }))} />
        </div>
      </div>

      <div className="section">
        <h2>Recent posts</h2>
        {media.length ? (
          <div className="posts">
            {media.map((m) => <PostCard key={m.id} m={m} />)}
          </div>
        ) : (
          <div className="card">
            <p className="muted" style={{ margin: 0 }}>
              Set <code>META_ACCESS_TOKEN</code> and <code>INSTAGRAM_USER_ID</code> in the
              deployment env to see recent posts with live engagement here.
            </p>
          </div>
        )}
      </div>

      {media.length > 0 && (
        <div className="section">
          <h2>Per-post breakdown</h2>
          <div className="card scroll" style={{ padding: 0 }}>
            <table>
              <thead>
                <tr>
                  <th>Post</th><th>Type</th><th>Date</th>
                  <th className="num">Reach</th><th className="num">Likes</th>
                  <th className="num">Comments</th><th className="num">Saves</th>
                  <th className="num">Shares</th>
                </tr>
              </thead>
              <tbody>
                {media.map((m) => (
                  <tr key={m.id}>
                    <td>
                      <a
                        href={m.permalink}
                        target="_blank"
                        rel="noopener"
                        style={{ color: "var(--accent)", display: "inline-flex", alignItems: "center", gap: 5 }}
                      >
                        {(m.caption || "View post").replace(/\s+/g, " ").slice(0, 46)}
                        <Icon name="external" size={12} />
                      </a>
                    </td>
                    <td>
                      <span className={`tag ${m.media_product_type === "REELS" ? "reel" : m.media_type}`}>
                        {m.media_product_type === "REELS" ? "Reel" : m.media_type === "CAROUSEL_ALBUM" ? "Carousel" : "Image"}
                      </span>
                    </td>
                    <td>{m.timestamp?.slice(0, 10)}</td>
                    <td className="num">{fmt(m.reach)}</td>
                    <td className="num">{fmt(m.like_count)}</td>
                    <td className="num">{fmt(m.comments_count)}</td>
                    <td className="num">{fmt(m.saved)}</td>
                    <td className="num">{fmt(m.shares)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      <div className="section">
        <h2>Top performers</h2>
        <div className="card scroll" style={{ padding: top.length ? 0 : undefined }}>
          {top.length ? (
            <table>
              <thead>
                <tr>
                  <th>Post</th><th>Type</th>
                  <th className="num">Saves</th><th className="num">Shares</th><th className="num">Score</th>
                </tr>
              </thead>
              <tbody>
                {top.map((t, i) => (
                  <tr key={i}>
                    <td>{(t.hook || "").slice(0, 70)}</td>
                    <td><span className={`tag ${t.type}`}>{t.type}</span></td>
                    <td className="num">{t.saved}</td>
                    <td className="num">{t.shares}</td>
                    <td className="num">{Math.round(t.score)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : <p className="muted" style={{ margin: 0 }}>No performance data yet — fills in after the weekly analytics job.</p>}
        </div>
      </div>

      <div className="section">
        <h2>Latest AI analysis</h2>
        <div className="card">
          {analysis
            ? <div className="prose">{analysis}</div>
            : <p className="muted" style={{ margin: 0 }}>No weekly analysis yet.</p>}
        </div>
      </div>
    </>
  );
}
