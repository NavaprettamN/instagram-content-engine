import { auth, signOut } from "@/auth";
import { redirect } from "next/navigation";
import { NavLink } from "@/components/NavLink";
import { Icon } from "@/components/Icon";
import { ThemeToggle } from "@/components/ThemeToggle";

export default async function AppLayout({ children }: { children: React.ReactNode }) {
  const session = await auth();
  if (!session) redirect("/login");
  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">M</div>
          <div>Meme Engine</div>
        </div>
        <nav className="nav">
          <NavLink href="/overview"><span className="ico"><Icon name="grid" size={17} /></span>Overview</NavLink>
          <NavLink href="/controls"><span className="ico"><Icon name="sliders" size={17} /></span>Controls</NavLink>
        </nav>
        <ThemeToggle />
        <div className="who">
          <b>{session?.user?.name || "Admin"}</b>
          {session?.user?.email}
          <form
            action={async () => {
              "use server";
              await signOut({ redirectTo: "/login" });
            }}
          >
            <button className="btn" style={{ padding: "6px 12px", fontSize: 12.5 }} type="submit">
              <Icon name="logout" size={14} /> Sign out
            </button>
          </form>
        </div>
      </aside>
      <main className="main">{children}</main>
    </div>
  );
}
