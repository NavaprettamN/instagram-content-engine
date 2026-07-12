import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Meme Engine",
  description: "Instagram meme account control panel",
};

// Resolve the theme before first paint to avoid a flash of the wrong colors:
// use the saved choice, else fall back to the OS preference.
const themeInit = `(function(){try{var t=localStorage.getItem('theme');if(t!=='light'&&t!=='dark'){t=window.matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light';}document.documentElement.setAttribute('data-theme',t);}catch(e){}})();`;

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeInit }} />
      </head>
      <body>{children}</body>
    </html>
  );
}
