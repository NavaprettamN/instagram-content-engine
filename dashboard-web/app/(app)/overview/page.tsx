import { getSnapshots, getConfigValue } from "@/lib/data";
import { FollowerChart } from "@/components/FollowerChart";

export const dynamic = "force-dynamic";

function parse<T>(s: string | null, fallback: T): T {
  try { return s ? JSON.parse(s) : fallback; } catch { return fallback; }
}

export default async function Overview() {
  const [snaps, followerRaw, topRaw] = await Promise.all([
    getSnapshots(1),
    getConfigValue("follower_history"),
    getConfigValue("top_performers"),
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

  const kpis = [
    { l: "Followers", n: latestFollowers },
    { l: "Since last week", n: delta === null ? "—" : `${delta >= 0 ? "+" : ""}${delta}` },
    { l: "Top posts tracked", n: top.length },
  ];

  return (
    <>
      <h1>Overview</h1>
      <p className="sub">How the account is performing right now.</p>

      <div className="grid">
        {kpis.map((k) => (
          <div className="card kpi" key={k.l}>
            <div className="n">{typeof k.n === "number" ? k.n.toLocaleString() : k.n}</div>
            <div className="l">{k.l}</div>
          </div>
        ))}
      </div>

      <div className="section">
        <h2>Follower growth</h2>
        <div className="card">
          <FollowerChart points={followers.map((f) => ({ date: f.date, value: f.count }))} />
        </div>
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
          ) : <p className="muted">No performance data yet — runs after the weekly analytics job.</p>}
        </div>
      </div>

      <div className="section">
        <h2>Latest AI analysis</h2>
        <div className="card">
          {analysis
            ? <div style={{ whiteSpace: "pre-wrap", lineHeight: 1.6, fontSize: 14 }}>{analysis}</div>
            : <p className="muted">No weekly analysis yet.</p>}
        </div>
      </div>
    </>
  );
}
