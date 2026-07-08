import NextAuth from "next-auth";
import Google from "next-auth/providers/google";

const allowed = (process.env.ALLOWED_EMAILS || "")
  .split(",")
  .map((s) => s.trim().toLowerCase())
  .filter(Boolean);

export const { handlers, auth, signIn, signOut } = NextAuth({
  trustHost: true, // Vercel auto-trusts; this also covers local `next start` / self-host
  providers: [Google],
  callbacks: {
    // Only allow-listed Google accounts get in. Empty list = any account.
    signIn({ profile }) {
      const email = profile?.email?.toLowerCase();
      return !!email && (allowed.length === 0 || allowed.includes(email));
    },
  },
  pages: { signIn: "/login" },
});
