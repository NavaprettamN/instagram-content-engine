import { signIn, auth } from "@/auth";
import { redirect } from "next/navigation";

export default async function Login() {
  if (await auth()) redirect("/overview");
  return (
    <div className="center">
      <div className="login">
        <div className="brand" style={{ fontSize: 22, marginBottom: 8 }}>
          Content <span>Engine</span>
        </div>
        <p className="muted" style={{ marginBottom: 28 }}>Sign in to your control panel</p>
        <form
          action={async () => {
            "use server";
            await signIn("google", { redirectTo: "/overview" });
          }}
        >
          <button className="btn primary" type="submit">Continue with Google</button>
        </form>
      </div>
    </div>
  );
}
