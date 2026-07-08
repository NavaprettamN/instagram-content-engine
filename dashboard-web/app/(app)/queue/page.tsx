import { getIdeas } from "@/lib/data";

export const dynamic = "force-dynamic";

function firstUrl(image_paths: string | null): string | null {
  try {
    const v = image_paths ? JSON.parse(image_paths) : null;
    const u = Array.isArray(v) ? v[0] : v;
    return typeof u === "string" && u.startsWith("http") ? u : null;
  } catch { return null; }
}

export default async function Queue() {
  const ideas = await getIdeas(150);
  return (
    <>
      <h1>Content Queue</h1>
      <p className="sub">Every idea and where it is in the pipeline.</p>
      <div className="card scroll">
        <table>
          <thead>
            <tr><th>ID</th><th>Hook</th><th>Type</th><th>Status</th><th>Created</th><th>Link</th></tr>
          </thead>
          <tbody>
            {ideas.map((i) => {
              const url = firstUrl(i.image_paths);
              const igLink = i.post_id ? `https://www.instagram.com/` : null;
              return (
                <tr key={i.id}>
                  <td className="muted">{i.id}</td>
                  <td>{(i.hook || "").slice(0, 64)}</td>
                  <td>{i.content_type && <span className={`tag ${i.content_type}`}>{i.content_type}</span>}</td>
                  <td><span className={`tag ${i.status}`}>{i.status.replace("_", " ")}</span></td>
                  <td className="muted">{i.created_at?.slice(0, 10)}</td>
                  <td>
                    {igLink && <a className="muted" href={igLink} target="_blank">post ↗</a>}
                    {!igLink && url && <a className="muted" href={url} target="_blank">media ↗</a>}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </>
  );
}
