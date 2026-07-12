"use client";
// Toggles the `data-theme` attribute on <html> and persists the choice.
// The initial theme is resolved before paint by an inline script in the root
// layout (avoids a flash), so here we just read/flip it after mount.
import { useEffect, useState } from "react";
import { Icon } from "./Icon";

export function ThemeToggle() {
  const [theme, setTheme] = useState<"light" | "dark">("light");
  const [ready, setReady] = useState(false);

  useEffect(() => {
    const t = document.documentElement.getAttribute("data-theme");
    setTheme(t === "dark" ? "dark" : "light");
    setReady(true);
  }, []);

  function toggle() {
    const next = theme === "dark" ? "light" : "dark";
    document.documentElement.setAttribute("data-theme", next);
    try { localStorage.setItem("theme", next); } catch {}
    setTheme(next);
  }

  return (
    <button
      className="btn theme-toggle"
      onClick={toggle}
      type="button"
      aria-label="Toggle color theme"
      // Hide until mounted so the label matches the resolved theme (no flicker).
      style={ready ? undefined : { visibility: "hidden" }}
    >
      <Icon name={theme === "dark" ? "sun" : "moon"} size={15} />
      <span>{theme === "dark" ? "Light mode" : "Dark mode"}</span>
    </button>
  );
}
