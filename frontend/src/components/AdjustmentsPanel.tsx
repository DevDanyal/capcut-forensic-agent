"use client";

import type { Adjustments } from "@/lib/api";
import { getCapcutLocation } from "@/lib/capcut-locations";
import { useEffect, useState } from "react";

interface Props {
  adjustments: Adjustments;
}

const ADJUST_KEY_MAP: Record<string, string> = {
  brightness: "Brightness",
  contrast: "Contrast",
  saturation: "Saturation",
  temperature: "Temperature",
  highlights: "Highlights",
  shadows: "Shadows",
  vibrance: "Vibrance",
  sharpness: "Sharpness",
  blacks: "Blacks",
  whites: "Whites",
};

const CAPCUT_RANGES: Record<string, { min: number; max: number; scale: number }> = {
  brightness: { min: -50, max: 50, scale: 0.5 },
  contrast: { min: -50, max: 50, scale: 0.5 },
  saturation: { min: -50, max: 50, scale: 0.5 },
  exposure: { min: -5, max: 5, scale: 1 },
  highlights: { min: -50, max: 50, scale: 0.5 },
  shadows: { min: -50, max: 50, scale: 0.5 },
  whites: { min: -50, max: 50, scale: 0.5 },
  blacks: { min: -50, max: 50, scale: 0.5 },
  temperature: { min: -50, max: 50, scale: 0.5 },
  tint: { min: -50, max: 50, scale: 0.5 },
  vibrance: { min: -50, max: 50, scale: 1 },
  sharpness: { min: 0, max: 100, scale: 1 },
};

function toCapcut(key: string, value: number): number {
  const r = CAPCUT_RANGES[key] || { min: -50, max: 50, scale: 0.5 };
  return Math.max(r.min, Math.min(r.max, Math.round(value * r.scale)));
}

export default function AdjustmentsPanel({ adjustments }: Props) {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    const t = setTimeout(() => setMounted(true), 150);
    return () => clearTimeout(t);
  }, []);

  const entries = Object.entries(adjustments)
    .filter(([key]) => key in ADJUST_KEY_MAP)
    .filter((entry) => Math.abs(entry[1]) > 1);

  if (entries.length === 0) return null;

  return (
    <div className="bg-[var(--color-bg-card)] rounded-[var(--radius-card)] border border-[var(--color-border)] mb-4 overflow-hidden transition-all duration-300 hover:border-[var(--color-accent)]/30">
      {/* Header */}
      <div className="flex items-center justify-between px-5 py-4 border-b border-[var(--color-border)]">
        <div className="flex items-center gap-2 text-sm">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none" className="text-[var(--color-accent)]">
            <circle cx="8" cy="8" r="6" stroke="currentColor" strokeWidth="1.5" />
            <path d="M8 4v8M4 8h8" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" />
          </svg>
          <span className="font-semibold">Adjustments</span>
          <span className="text-[var(--color-text-tertiary)] font-normal text-[0.8em]">
            &middot; CapCut Adjustments panel
          </span>
        </div>
        <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-[var(--color-accent-dim)] text-[var(--color-accent)] border border-[var(--color-accent)]/20">
          {entries.length}
        </span>
      </div>

      {/* Apply order hint */}
      <div className="px-5 pt-4 pb-0">
        <p className="text-[0.6rem] text-[var(--color-text-tertiary)] leading-relaxed">
          Apply in CapCut in this order: Exposure &rarr; Contrast &rarr; Highlights/Shadows &rarr; Whites/Blacks &rarr; Brightness &rarr; Saturation/Vibrance &rarr; Temperature/Tint &rarr; Sharpness
        </p>
      </div>
      {/* Rings */}
      <div className="px-5 py-4">
        <div className="grid grid-cols-[repeat(auto-fill,minmax(90px,1fr))] gap-y-6 gap-x-2 justify-items-center">
          {entries.map(([name, value], i) => {
            const capcutVal = toCapcut(name, value);
            const r = CAPCUT_RANGES[name] || { min: -50, max: 50, scale: 0.5 };
            const rangeMax = Math.max(Math.abs(r.min), Math.abs(r.max));
            const absVal = Math.abs(capcutVal);
            const isPositive = capcutVal >= 0;
            const color = isPositive ? "var(--color-green)" : "var(--color-red)";
            const R = 22;
            const circumference = 2 * Math.PI * R;
            const targetOffset = circumference - (absVal / rangeMax) * circumference;
            const animDelay = `${i * 50}ms`;

            return (
              <div key={name} className="flex flex-col items-center gap-2">
                {/* Ring */}
                <div className="relative w-[60px] h-[60px] flex items-center justify-center">
                  {/* Glow behind */}
                  <div
                    className="absolute inset-0 rounded-full opacity-0 transition-opacity duration-500"
                    style={{
                      background: `radial-gradient(circle, ${color}22 0%, transparent 70%)`,
                      opacity: mounted ? 0.6 : 0,
                      transitionDelay: animDelay,
                    }}
                  />
                  <svg width="60" height="60" viewBox="0 0 60 60" className="absolute inset-0 -rotate-90">
                    {/* Background ring */}
                    <circle
                      cx="30" cy="30" r={R}
                      fill="none" stroke="var(--color-border)" strokeWidth="3.5"
                    />
                    {/* Progress ring */}
                    <circle
                      cx="30" cy="30" r={R}
                      fill="none" stroke={color} strokeWidth="3.5"
                      strokeLinecap="round"
                      strokeDasharray={circumference}
                      strokeDashoffset={mounted ? targetOffset : circumference}
                      style={{
                        transition: `stroke-dashoffset 0.9s cubic-bezier(0.34, 1.56, 0.64, 1) ${animDelay}`,
                        filter: mounted ? `drop-shadow(0 0 4px ${color}66)` : "none",
                        transitionProperty: "stroke-dashoffset, filter",
                      }}
                    />
                  </svg>
                  {/* Value */}
                  <span
                    className="text-[0.7rem] font-bold font-[var(--font-mono)] tabular-nums z-10"
                    style={{ color }}
                  >
                    {isPositive ? "+" : ""}{capcutVal}
                  </span>
                </div>
                {/* Label */}
                <span className="text-[0.62rem] text-[var(--color-text-secondary)] text-center leading-tight max-w-[80px] font-medium">
                  {ADJUST_KEY_MAP[name] || name.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())}
                </span>
                {(() => {
                  const loc = getCapcutLocation(ADJUST_KEY_MAP[name] || name.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase()));
                  return loc ? (
                    <span className="text-[0.45rem] text-[var(--color-text-tertiary)] text-center leading-tight max-w-[80px]">
                      {loc.path}
                    </span>
                  ) : null;
                })()}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
