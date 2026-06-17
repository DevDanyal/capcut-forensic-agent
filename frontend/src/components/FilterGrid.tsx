import type { Filter } from "@/lib/api";
import { getCapcutLocation } from "@/lib/capcut-locations";

interface Props {
  filters: Filter[];
}

const TYPE_META: Record<string, { label: string; bg: string; color: string; border: string }> = {
  filter: {
    label: "Filter", bg: "rgba(139,92,246,0.10)", color: "#8B5CF6", border: "rgba(139,92,246,0.25)",
  },
  effect: {
    label: "Effect", bg: "rgba(245,158,11,0.10)", color: "#F59E0B", border: "rgba(245,158,11,0.25)",
  },
  adjustments: {
    label: "Adjustment", bg: "rgba(34,211,238,0.10)", color: "#22D3EE", border: "rgba(34,211,238,0.25)",
  },
  transition: {
    label: "Transition", bg: "rgba(239,68,68,0.10)", color: "#EF4444", border: "rgba(239,68,68,0.25)",
  },
};

export default function FilterGrid({ filters }: Props) {
  if (filters.length === 0) return null;

  return (
    <div className="bg-[var(--color-bg-card)] rounded-[var(--radius-card)] border border-[var(--color-border)] overflow-hidden h-full transition-all duration-300 hover:border-[var(--color-accent)]/30">
      <div className="flex items-center justify-between px-5 py-4 border-b border-[var(--color-border)]">
        <div className="flex items-center gap-2 text-sm">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none" className="text-[var(--color-accent)]">
            <path d="M2 2h12v2.5L10.5 9v4.5l-3-1.5V9L2 4.5V2z" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round" />
          </svg>
          <span className="font-semibold">Filters & Effects</span>
        </div>
        <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-[var(--color-accent-dim)] text-[var(--color-accent)] border border-[var(--color-accent)]/20">
          {filters.length}
        </span>
      </div>
      <div className="p-4 space-y-2">
        {filters.map((f, i) => {
          const meta = TYPE_META[f.type] || TYPE_META.filter;
          const conf = f.confidence || 50;
          const barColor = conf >= 70 ? "var(--color-green)" : conf >= 45 ? "var(--color-orange)" : "var(--color-red)";

          return (
            <div
              key={i}
              className="flex items-center gap-3 px-4 py-3 rounded-xl bg-[var(--color-bg-elevated)] border border-[var(--color-border)] transition-all duration-200 hover:border-[var(--color-accent)]/40 hover:bg-[var(--color-bg-hover)]"
            >
              {/* Type indicator */}
              <div
                className="w-8 h-8 rounded-lg flex items-center justify-center shrink-0 text-[0.65rem] font-bold"
                style={{ background: meta.bg, color: meta.color, border: `1px solid ${meta.border}` }}
              >
                {f.name.charAt(0).toUpperCase()}
              </div>

              {/* Details */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="font-semibold text-sm truncate">{f.name}</span>
                  <span
                    className="text-[0.5rem] font-bold px-2 py-0.5 rounded-full uppercase tracking-[0.1em]"
                    style={{ background: meta.bg, color: meta.color, border: `1px solid ${meta.border}` }}
                  >
                    {meta.label}
                  </span>
                </div>

                {(() => {
                  const loc = getCapcutLocation(f.name);
                  return loc ? (
                    <div className="flex items-center gap-1.5 mt-1">
                      <span className="text-[0.55rem] font-semibold uppercase tracking-wider text-[var(--color-accent)]/70">
                        {loc.tab}
                      </span>
                      <span className="text-[0.5rem] text-[var(--color-text-tertiary)]">{loc.path}</span>
                    </div>
                  ) : null;
                })()}
                {Object.keys(f.parameters || {}).length > 0 && (
                  <div className="flex gap-2.5 mt-1 flex-wrap">
                    {Object.entries(f.parameters).map(([k, v]) => (
                      <span key={k} className="text-[0.6rem] text-[var(--color-text-tertiary)] font-mono">
                        {k}: <span className="font-semibold text-[var(--color-text-secondary)]">{Math.round(v)}</span>
                      </span>
                    ))}
                  </div>
                )}
              </div>

              {/* Confidence */}
              <div className="flex items-center gap-2 shrink-0">
                <div className="flex flex-col items-end gap-0.5">
                  <div className="w-14 h-1.5 rounded-full bg-[var(--color-border)] overflow-hidden hidden sm:block">
                    <div
                      className="h-full rounded-full transition-[width] duration-700"
                      style={{ width: `${conf}%`, background: barColor }}
                    />
                  </div>
                  <span className="text-[0.55rem] font-semibold font-mono tabular-nums" style={{ color: barColor }}>
                    {Math.round(conf)}%
                  </span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
