// Tiny dependency-free SVG line chart for a series of {date, value} points.
export function FollowerChart({ points }: { points: { date: string; value: number }[] }) {
  if (points.length < 2) {
    return <p className="muted">Not enough follower snapshots yet to chart a trend.</p>;
  }
  const W = 720, H = 180, P = 28;
  const xs = points.map((_, i) => i);
  const ys = points.map((p) => p.value);
  const minY = Math.min(...ys), maxY = Math.max(...ys);
  const spanY = maxY - minY || 1;
  const x = (i: number) => P + (i / (xs.length - 1)) * (W - 2 * P);
  const y = (v: number) => H - P - ((v - minY) / spanY) * (H - 2 * P);
  const d = points.map((p, i) => `${i ? "L" : "M"}${x(i).toFixed(1)},${y(p.value).toFixed(1)}`).join(" ");
  const area = `${d} L${x(xs.length - 1).toFixed(1)},${H - P} L${x(0).toFixed(1)},${H - P} Z`;
  return (
    <svg viewBox={`0 0 ${W} ${H}`} width="100%" role="img" aria-label="Follower growth">
      <defs>
        <linearGradient id="fg" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#7c5cff" stopOpacity="0.35" />
          <stop offset="100%" stopColor="#7c5cff" stopOpacity="0" />
        </linearGradient>
      </defs>
      <path d={area} fill="url(#fg)" />
      <path d={d} fill="none" stroke="#7c5cff" strokeWidth="2.5" />
      <text x={P} y={16} fill="#9aa0bd" fontSize="12">{maxY.toLocaleString()}</text>
      <text x={P} y={H - 6} fill="#9aa0bd" fontSize="12">{minY.toLocaleString()}</text>
    </svg>
  );
}
