import type { Analysis } from "@/lib/api";
import { formatDuration } from "@/lib/api";

interface Props {
  analysis: Analysis;
}

const TYPE_STYLE: Record<string, { bg: string; label: string; color: string }> = {
  shot: { bg: "var(--color-accent)", label: "Shot", color: "#8B5CF6" },
  cut: { bg: "var(--color-orange)", label: "Cut", color: "#F59E0B" },
  dissolve: { bg: "var(--color-green)", label: "Dissolve", color: "#06D6A0" },
  fade: { bg: "var(--color-red)", label: "Fade", color: "#EF4444" },
  wipe: { bg: "var(--color-teal)", label: "Wipe", color: "#22D3EE" },
};

export default function Timeline({ analysis }: Props) {
  const { shots, transitions, video_info } = analysis;
  const duration = video_info.duration_seconds;

  const segments: { left: number; width: number; type: string; label: string; isTransition: boolean }[] = [];

  shots.forEach((shot, i) => {
    const start = shot.start;
    const end = shot.end || duration;
    segments.push({
      left: (start / duration) * 100,
      width: ((end - start) / duration) * 100,
      type: "shot",
      label: `${i + 1}`,
      isTransition: false,
    });
  });

  transitions.forEach((t) => {
    const halfSpan = Math.min(0.25, duration * 0.015);
    const start = Math.max(0, t.time - halfSpan);
    const end = Math.min(duration, t.time + halfSpan);
    segments.push({
      left: (start / duration) * 100,
      width: ((end - start) / duration) * 100,
      type: t.type || "cut",
      label: t.type || "cut",
      isTransition: true,
    });
  });

  return (
    <div className="bg-[var(--color-bg-card)] rounded-[var(--radius-card)] border border-[var(--color-border)] mb-4 overflow-hidden transition-all duration-300 hover:border-[var(--color-accent)]/30">
      <div className="flex items-center justify-between px-5 py-4 border-b border-[var(--color-border)]">
        <div className="flex items-center gap-2 text-sm">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none" className="text-[var(--color-accent)]">
            <rect x="1.5" y="2.5" width="13" height="11" rx="2" stroke="currentColor" strokeWidth="1.5" />
            <path d="M5.5 6.5v3l2.5-1.5L5.5 6.5z" fill="currentColor" />
          </svg>
          <span className="font-semibold">Timeline</span>
          <span className="text-[var(--color-text-tertiary)] font-normal text-[0.8em]">
            &middot; {shots.length} shot{shots.length !== 1 ? "s" : ""}, {transitions.length} transition{transitions.length !== 1 ? "s" : ""}
          </span>
        </div>
      </div>
      <div className="px-5 py-5">
        {/* Timeline bar */}
        <div className="relative h-12 bg-[var(--color-bg-elevated)] rounded-xl overflow-hidden mb-3 ring-1 ring-inset ring-white/[0.03]">
          {/* Time ticks */}
          {Array.from({ length: Math.min(10, Math.floor(duration)) }, (_, i) => {
            const pos = ((i + 1) / Math.min(10, Math.floor(duration))) * 100;
            return (
              <div
                key={i}
                className="absolute top-0 bottom-0 w-px bg-white/[0.04]"
                style={{ left: `${pos}%` }}
              />
            );
          })}
          {segments.map((s, i) => {
            const style = TYPE_STYLE[s.type] || TYPE_STYLE.shot;
            return (
              <div
                key={i}
                className="absolute top-1 bottom-1 flex items-center justify-center text-[0.5rem] font-bold text-white/80 truncate transition-all duration-200 hover:brightness-125 hover:z-10"
                style={{
                  left: `${s.left}%`,
                  width: `${Math.max(s.width, s.isTransition ? 0.5 : 0.8)}%`,
                  background: s.isTransition
                    ? `linear-gradient(135deg, ${style.bg}, ${style.bg}99)`
                    : style.bg,
                  opacity: s.isTransition ? 0.9 : 0.35 + (s.width / 100) * 0.65,
                  borderRadius: s.isTransition ? "2px" : "4px",
                  zIndex: s.isTransition ? 2 : 1,
                  boxShadow: s.isTransition ? `0 0 8px ${style.bg}55` : "none",
                }}
                title={s.label}
              >
                {!s.isTransition && s.width > 2.5 && (
                  <span className="drop-shadow-[0_1px_2px_rgba(0,0,0,0.6)]">{s.label}</span>
                )}
              </div>
            );
          })}
        </div>

        {/* Bottom row: time markers + legend */}
        <div className="flex justify-between items-center">
          <span className="text-[0.65rem] font-mono text-[var(--color-text-tertiary)] tabular-nums font-semibold">
            0:00
          </span>

          {/* Legend pills */}
          <div className="flex items-center gap-3">
            <LegendPill color="var(--color-accent)" label="Shot" />
            <LegendPill color="var(--color-orange)" label="Cut" />
            <LegendPill color="var(--color-green)" label="Dissolve" />
            <LegendPill color="var(--color-red)" label="Fade" />
          </div>

          <span className="text-[0.65rem] font-mono text-[var(--color-text-tertiary)] tabular-nums font-semibold">
            {formatDuration(duration)}
          </span>
        </div>
      </div>
    </div>
  );
}

function LegendPill({ color, label }: { color: string; label: string }) {
  return (
    <span className="flex items-center gap-1.5 text-[0.55rem] font-semibold uppercase tracking-wider text-[var(--color-text-tertiary)]">
      <span className="w-2 h-2 rounded-sm" style={{ background: color }} />
      {label}
    </span>
  );
}
