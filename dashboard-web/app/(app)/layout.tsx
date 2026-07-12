import { auth, signOut } from "@/auth";
import { redirect } from "next/navigation";
import { NavLink } from "@/components/NavLink";

export default async function AppLayout({ children }: { children: React.ReactNode }) {
  const session = await auth();
  if (!session) redirect("/login");
  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">😂</div>
          <div>Meme <span>Engine</span></div>
        </div>
        <nav className="nav">
          <NavLink href="/overview"><span className="ico">📊</span>Overview</NavLink>
          <NavLink href="/controls"><span className="ico">🎛️</span>Controls</NavLink>
        </nav>
        <div className="who">
          <b>{session?.user?.name || "Admin"}</b>
          {session?.user?.email}
          <form
            action={async () => {
              "use server";
              await signOut({ redirectTo: "/login" });
            }}
          >
            <button className="btn" style={{ padding: "6px 12px", fontSize: 12 }} type="submit">
              Sign out
            </button>
          </form>
        </div>
      </aside>
      <main className="main">{children}</main>
    </div>
  );
}
