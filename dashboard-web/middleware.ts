export { auth as middleware } from "@/auth";

// Protect everything except the login page, the auth API, and static assets.
export const config = {
  matcher: ["/((?!login|api/auth|_next/static|_next/image|favicon.ico).*)"],
};
