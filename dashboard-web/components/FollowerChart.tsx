"use client";
// Dependency-free SVG line chart with a crosshair + tooltip hover layer.
// Single series → no legend (the section title names it); the last point is
// direct-labeled. Grid and axis text stay recessive; values use text tokens.
import { useRef, useState } from "react";

const LINE = "#2383e2"; // accent blue, validated against the white card surface
const GRID = "#ebebea";
const AXIS = "#9b9a95";
const LABEL = "#37352f";
const CARD = "#ffffff";

export function FollowerChart({ points }: { points: { date: string; value: number }[] }) {
  const wrap = useRef<HTMLDivElement>(null);
  const [hover, setHover] = useState<number | null>(null);

  if (points.length < 2) {
    return <p className="muted">Not enough follower snapshots yet to chart a trend — the weekly analytics job adds one point per week.</p>;
  }
  const W = 720, H = 200, P = 34;
  const ys = points.map((p) => p.value);
  const minY = Math.min(...ys), maxY = Math.max(...ys);
  const spanY = maxY - minY || 1;
  const x = (i: number) => P + (i / (points.length - 1)) * (W - 2 * P);
  const y = (v: number) => H - P - ((v - minY) / spanY) * (H - 2 * P);
  const d = points.map((p, i) => `${i ? "L" : "M"}${x(i).toFixed(1)},${y(p.value).toFixed(1)}`).join(" ");
  const area = `${d} L${x(points.length - 1).toFixed(1)},${H - P} L${x(0).toFixed(1)},${H - P} Z`;
  const last = points[points.length - 1];

  function onMove(e: React.MouseEvent<SVGSVGElement>) {
    const rect = e.currentTarget.getBoundingClientRect();
    const px = ((e.clientX - rect.left) / rect.width) * W;
    const i = Math.round(((px - P) / (W - 2 * P)) * (points.length - 1));
    setHover(Math.max(0, Math.min(points.length - 1, i)));
  }

  const h = hover === null ? null : points[hover];
  return (
    <div ref={wrap} style={{ position: "relative" }}>
      <svg
        viewBox={`0 0 ${W} ${H}`}
        width="100%"
        role="img"
        aria-label={`Follower count, ${points[0].date} to ${last.date}`}
        onMouseMove={onMove}
        onMouseLeave={() => setHover(null)}
        style={{ display: "block", cursor: "crosshair" }}
      >
        <defs>
          <linearGradient id="fg" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={LINE} stopOpacity="0.30" />
            <stop offset="100%" stopColor={LINE} stopOpacity="0" />
          </linearGradient>
        </defs>
        {/* recessive gridlines at min / mid / max (mid only when its label is distinct) */}
        {[...new Map(
          [minY, (minY + maxY) / 2, maxY].map((v) => [Math.round(v), v]),
        ).values()].map((v, i) => (
          <g key={i}>
            <line x1={P} x2={W - P} y1={y(v)} y2={y(v)} stroke={GRID} strokeWidth="1" />
            <text x={P - 6} y={y(v) + 4} fill={AXIS} fontSize="11" textAnchor="end">
              {Math.round(v).toLocaleString()}
            </text>
          </g>
        ))}
        <path d={area} fill="url(#fg)" />
        <path d={d} fill="none" stroke={LINE} strokeWidth="2" strokeLinejoin="round" />
        {/* direct label on the latest point */}
        <circle cx={x(points.length - 1)} cy={y(last.value)} r="4" fill={LINE} stroke={CARD} strokeWidth="2" />
        <text x={x(points.length - 1) - 8} y={y(last.value) - 10} fill={LABEL} fontSize="12" fontWeight="700" textAnchor="end">
          {last.value.toLocaleString()}
        </text>
        {/* crosshair + hovered point */}
        {h && hover !== null && (
          <g>
            <line x1={x(hover)} x2={x(hover)} y1={P - 10} y2={H - P} stroke={AXIS} strokeWidth="1" strokeDasharray="3 3" />
            <circle cx={x(hover)} cy={y(h.value)} r="5" fill={LINE} stroke={CARD} strokeWidth="2" />
          </g>
        )}
        {/* x-axis endpoints */}
        <text x={P} y={H - 8} fill={AXIS} fontSize="11">{points[0].date}</text>
        <text x={W - P} y={H - 8} fill={AXIS} fontSize="11" textAnchor="end">{last.date}</text>
      </svg>
      {h && hover !== null && (
        <div
          className="chart-tip"
          style={{ left: `${(x(hover) / W) * 100}%`, top: `${(y(h.value) / H) * 100}%` }}
        >
          <span className="d">{h.date}</span>
          {h.value.toLocaleString()} followers
        </div>
      )}
    </div>
  );
}
