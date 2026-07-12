import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Meme Engine",
  description: "Instagram meme account control panel",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
