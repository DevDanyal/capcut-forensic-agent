import type { VideoInfo as VideoInfoType } from "@/lib/api";
import { formatDuration } from "@/lib/api";

interface Props {
  info: VideoInfoType;
}

const ITEMS = [
  { key: "duration" as const, label: "Duration", icon: MdDuration },
  { key: "resolution" as const, label: "Resolution", icon: MdResolution },
  { key: "fps" as const, label: "Frame Rate", icon: MdFPS },
  { key: "aspect" as const, label: "Aspect", icon: MdAspect },
  { key: "frames" as const, label: "Frames Analyzed", icon: MdFrames },
  { key: "format" as const, label: "Format", icon: MdFormat },
];

export default function VideoInfo({ info }: Props) {
  const values: Record<string, string> = {
    duration: formatDuration(info.duration_seconds),
    resolution: `${info.width}\u00D7${info.height}`,
    fps: `${info.fps}`,
    aspect: info.aspect_ratio,
    frames: `${info.total_frames_analyzed}`,
    format: info.filename.split(".").pop()?.toUpperCase() ?? "Unknown",
  };

  return (
    <div className="bg-[var(--color-bg-card)] rounded-[var(--radius-card)] border border-[var(--color-border)] p-5 mb-4 transition-all duration-300 hover:border-[var(--color-accent)]/30">
      <div className="flex items-center gap-2 text-sm font-semibold text-[var(--color-text-secondary)] mb-5">
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
          <rect x="1.5" y="1.5" width="13" height="13" rx="3" stroke="currentColor" strokeWidth="1.5" />
          <path d="M6 4.5v7l5.5-3.5L6 4.5z" fill="currentColor" />
        </svg>
        Video Information
      </div>
      <div className="grid grid-cols-2 gap-3">
        {ITEMS.map((item) => {
          const val = values[item.key];
          const Icon = item.icon;
          return (
            <div
              key={item.key}
              className="flex items-center gap-3 px-3 py-2.5 rounded-xl bg-[var(--color-bg-elevated)] border border-[var(--color-border)]"
            >
              <span className="w-7 h-7 rounded-lg flex items-center justify-center text-[var(--color-accent)] bg-[var(--color-accent-dim)] shrink-0">
                <Icon />
              </span>
              <div className="flex flex-col min-w-0">
                <span className="text-[0.55rem] font-semibold uppercase tracking-wider text-[var(--color-text-tertiary)]">
                  {item.label}
                </span>
                <span className="text-[0.8rem] font-bold font-[var(--font-mono)] tabular-nums truncate">
                  {val}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

/* ── Icons ── */

function MdDuration() {
  return (
    <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
      <circle cx="7" cy="7" r="5.5" stroke="currentColor" strokeWidth="1.3" />
      <path d="M7 4v3.5L9.5 9" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" />
    </svg>
  );
}

function MdResolution() {
  return (
    <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
      <rect x="1.5" y="2.5" width="11" height="9" rx="1.5" stroke="currentColor" strokeWidth="1.3" />
      <path d="M10 8v1.5a.5.5 0 01-.5.5H8" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" />
    </svg>
  );
}

function MdFPS() {
  return (
    <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
      <rect x="1" y="1" width="12" height="12" rx="2" stroke="currentColor" strokeWidth="1.3" />
      <path d="M4.5 5h5M4.5 7h3.5M4.5 9h5" stroke="currentColor" strokeWidth="1.1" strokeLinecap="round" />
    </svg>
  );
}

function MdAspect() {
  return (
    <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
      <rect x="1" y="3" width="12" height="8" rx="1" stroke="currentColor" strokeWidth="1.3" />
      <path d="M3 6.5v1M11 6.5v1M6.5 3v8" stroke="currentColor" strokeWidth="1.1" strokeLinecap="round" />
    </svg>
  );
}

function MdFrames() {
  return (
    <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
      <rect x="2" y="2" width="10" height="10" rx="1.5" stroke="currentColor" strokeWidth="1.3" />
      <path d="M2 5h10M5 2v10" stroke="currentColor" strokeWidth="1.1" />
    </svg>
  );
}

function MdFormat() {
  return (
    <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
      <path d="M4 3l-2 4 2 4M10 3l2 4-2 4M5 7h4" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}
