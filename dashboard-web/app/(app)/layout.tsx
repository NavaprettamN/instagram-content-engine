import { auth, signOut } from "@/auth";
import { redirect } from "next/navigation";
import { NavLink } from "@/components/NavLink";

export default async function AppLayout({ children }: { children: React.ReactNode }) {
  const session = await auth();
  if (!session) redirect("/login");
  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="brand">Content <span>Engine</span></div>
        <nav className="nav">
          <NavLink href="/overview">Overview</NavLink>
          <NavLink href="/queue">Content Queue</NavLink>
          <NavLink href="/controls">Controls</NavLink>
        </nav>
        <div className="who">
          Signed in as<br />
          {session.user?.email}
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
