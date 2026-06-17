"use client";

import type { FrameData } from "@/lib/api";
import { formatDuration } from "@/lib/api";
import { useState } from "react";

interface Props {
  frames: FrameData[];
}

export default function FrameGallery({ frames }: Props) {
  const [preview, setPreview] = useState<FrameData | null>(null);
  const [loaded, setLoaded] = useState<Set<number>>(new Set());

  if (frames.length === 0) return null;

  return (
    <>
      <div className="bg-[var(--color-bg-card)] rounded-[var(--radius-card)] border border-[var(--color-border)] mb-4 overflow-hidden transition-all duration-300 hover:border-[var(--color-accent)]/30">
        <div className="flex items-center justify-between px-5 py-4 border-b border-[var(--color-border)]">
          <div className="flex items-center gap-2 text-sm">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none" className="text-[var(--color-accent)]">
              <rect x="1.5" y="1.5" width="5" height="5" rx="1" stroke="currentColor" strokeWidth="1.5" />
              <rect x="9.5" y="1.5" width="5" height="5" rx="1" stroke="currentColor" strokeWidth="1.5" />
              <rect x="1.5" y="9.5" width="5" height="5" rx="1" stroke="currentColor" strokeWidth="1.5" />
              <rect x="9.5" y="9.5" width="5" height="5" rx="1" stroke="currentColor" strokeWidth="1.5" />
            </svg>
            <span className="font-semibold">Frame Samples</span>
          </div>
          <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-[var(--color-accent-dim)] text-[var(--color-accent)] border border-[var(--color-accent)]/20">
            {frames.length}
          </span>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-3 p-5">
          {frames.map((f, i) => (
            <div
              key={i}
              className="group rounded-xl overflow-hidden bg-[var(--color-bg-elevated)] relative cursor-pointer transition-all duration-200 hover:scale-[1.03] hover:shadow-[0_8px_30px_rgba(0,0,0,0.5)] hover:z-10"
              onClick={() => setPreview(f)}
            >
              <div className="aspect-video overflow-hidden">
                {!loaded.has(i) && (
                  <div className="absolute inset-0 bg-[var(--color-bg-elevated)] animate-pulse" />
                )}
                <img
                  src={f.data}
                  alt={`frame at ${formatDuration(f.time)}`}
                  className={`w-full h-full object-cover block transition-all duration-500 group-hover:scale-105 ${
                    loaded.has(i) ? "opacity-100" : "opacity-0"
                  }`}
                  loading="lazy"
                  onLoad={() => setLoaded((prev) => new Set(prev).add(i))}
                />
              </div>
              {/* Gradient overlay + timestamp */}
              <div className="absolute bottom-0 inset-x-0 bg-gradient-to-t from-black/90 via-black/40 to-transparent p-2.5 pt-6">
                <span className="text-[0.6rem] font-bold font-mono text-white/90 drop-shadow-[0_1px_2px_rgba(0,0,0,0.5)]">
                  {formatDuration(f.time)}
                </span>
              </div>
              {/* View label on hover */}
              <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity duration-200 bg-black/30">
                <span className="text-[0.65rem] font-semibold px-3 py-1.5 rounded-lg bg-black/70 text-white/90 backdrop-blur-sm">
                  View full
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Lightbox */}
      {preview && (
        <div
          className="fixed inset-0 bg-black/90 z-50 flex items-center justify-center p-4 cursor-pointer backdrop-blur-sm"
          onClick={() => setPreview(null)}
        >
          <div
            className="relative max-w-[85vw] max-h-[88vh] rounded-2xl overflow-hidden shadow-[0_12px_60px_rgba(0,0,0,0.7)] border border-[var(--color-border)] bg-black animate-[fadeIn_0.2s_ease-out]"
            onClick={(e) => e.stopPropagation()}
          >
            <img
              src={preview.data}
              alt="frame preview"
              className="w-full h-full object-contain max-h-[88vh] max-w-[85vw]"
            />
            <div className="absolute bottom-0 inset-x-0 bg-gradient-to-t from-black/90 via-black/40 to-transparent p-4 pt-10 flex items-center justify-between">
              <span className="text-sm font-bold font-mono text-white/90">
                {formatDuration(preview.time)}
              </span>
              <button
                onClick={() => setPreview(null)}
                className="text-[0.65rem] font-semibold px-3 py-1.5 rounded-lg bg-white/10 text-white/80 hover:bg-white/20 transition-colors border border-white/10"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
