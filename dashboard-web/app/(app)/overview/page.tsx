import { getSnapshots, getConfigValue, getRecentMedia, IgMedia } from "@/lib/data";
import { FollowerChart } from "@/components/FollowerChart";

export const dynamic = "force-dynamic";

function parse<T>(s: string | null, fallback: T): T {
  try { return s ? JSON.parse(s) : fallback; } catch { return fallback; }
}

function PostCard({ m }: { m: IgMedia }) {
  const img = m.thumbnail_url || (m.media_type !== "VIDEO" ? m.media_url : null);
  const kind = m.media_product_type === "REELS" ? "🎬" : m.media_type === "CAROUSEL_ALBUM" ? "🖼️" : "📷";
  return (
    <a className="post" href={m.permalink} target="_blank" rel="noopener">
      {img
        ? <img src={img} alt={m.caption?.slice(0, 60) || "Instagram post"} loading="lazy" />
        : <div className="noimg">{m.caption?.slice(0, 70) || "View post"}</div>}
      <span className="kind">{kind}</span>
      <div className="meta">
        <span>❤️ {m.like_count ?? "–"}</span>
        <span>💬 {m.comments_count ?? "–"}</span>
        <span style={{ marginLeft: "auto", fontWeight: 600, color: "#c9cde4" }}>
          {m.timestamp?.slice(5, 10)}
        </span>
      </div>
    </a>
  );
}

export default async function Overview() {
  const [snaps, followerRaw, topRaw, media] = await Promise.all([
    getSnapshots(1),
    getConfigValue("follower_history"),
    getConfigValue("top_performers"),
    getRecentMedia(12),
  ]);

  const followers = parse<{ date: string; count: number }[]>(followerRaw, []);
  const top = parse<{ hook: string; type: string; score: number; saved: number; shares: number }[]>(topRaw, []);
  const latestFollowers = followers.at(-1)?.count ?? "—";
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
        <div className="card kpi">
          <div className="n">{typeof latestFollowers === "number" ? latestFollowers.toLocaleString() : latestFollowers}</div>
          <div className="l">Followers</div>
        </div>
        <div className="card kpi">
          <div className={`n ${delta === null ? "" : delta >= 0 ? "up" : "down"}`}>
            {delta === null ? "—" : `${delta >= 0 ? "+" : ""}${delta.toLocaleString()}`}
          </div>
          <div className="l">Since last week</div>
        </div>
        {media.length > 0 && (
          <>
            <div className="card kpi">
              <div className="n">{totalLikes.toLocaleString()}</div>
              <div className="l">Likes · last {media.length} posts</div>
            </div>
            <div className="card kpi">
              <div className="n">{totalComments.toLocaleString()}</div>
              <div className="l">Comments · last {media.length} posts</div>
            </div>
          </>
        )}
      </div>

      <div className="section" style={{ marginTop: 26 }}>
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

      <div className="section">
        <h2>Top performers</h2>
        <div className="card scroll">
          {top.length ? (
            <table>
              <thead><tr><th>Post</th><th>Type</th><th>Saves</th><th>Shares</th><th>Score</th></tr></thead>
              <tbody>
                {top.map((t, i) => (
                  <tr key={i}>
                    <td>{(t.hook || "").slice(0, 70)}</td>
                    <td><span className={`tag ${t.type}`}>{t.type}</span></td>
                    <td>{t.saved}</td>
                    <td>{t.shares}</td>
                    <td>{Math.round(t.score)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : <p className="muted">No performance data yet — fills in after the weekly analytics job.</p>}
        </div>
      </div>

      <div className="section">
        <h2>Latest AI analysis</h2>
        <div className="card">
          {analysis
            ? <div className="prose">{analysis}</div>
            : <p className="muted">No weekly analysis yet.</p>}
        </div>
      </div>
    </>
  );
}
