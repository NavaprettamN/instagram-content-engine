import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Content Engine",
  description: "Instagram content engine control panel",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
