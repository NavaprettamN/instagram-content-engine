import NextAuth from "next-auth";
import Google from "next-auth/providers/google";

// Admin allowlist. Defaults to the owner so a fresh deploy is locked down even
// before ALLOWED_EMAILS is configured; set the env var to add/replace admins.
const allowed = (process.env.ALLOWED_EMAILS || "navaprettam.n214@gmail.com")
  .split(",")
  .map((s) => s.trim().toLowerCase())
  .filter(Boolean);

export const { handlers, auth, signIn, signOut } = NextAuth({
  trustHost: true, // Vercel auto-trusts; this also covers local `next start` / self-host
  providers: [Google],
  callbacks: {
    // Only allow-listed Google accounts get in.
    signIn({ profile }) {
      const email = profile?.email?.toLowerCase();
      return !!email && allowed.includes(email);
    },
  },
  pages: { signIn: "/login" },
});
