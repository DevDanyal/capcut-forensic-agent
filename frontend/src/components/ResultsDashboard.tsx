"use client";

import type { AnalysisResult } from "@/lib/api";
import { useState, useEffect } from "react";
import VideoInfo from "./VideoInfo";
import AdjustmentsPanel from "./AdjustmentsPanel";
import FilterGrid from "./FilterGrid";
import Timeline from "./Timeline";
import FrameGallery from "./FrameGallery";

interface Props {
  result: AnalysisResult;
  onReset: () => void;
}

function simpleHash(s: string): number {
  let h = 0;
  for (let i = 0; i < s.length; i++) {
    h = (h * 31 + s.charCodeAt(i)) | 0;
  }
  return Math.abs(h);
}

function fmtCaseId(filename: string): string {
  const num = (simpleHash(filename) % 90000) + 10000;
  return `CT-${num}`;
}

export default function ResultsDashboard({ result, onReset }: Props) {
  const { analysis, frames } = result;
  const { video_info, summary, filters, effects, shots, transitions } = analysis;
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const t = setTimeout(() => setVisible(true), 50);
    return () => clearTimeout(t);
  }, []);

  const totalEdits = summary?.estimated_edits_count || 0;
  const totalFilters = (filters?.length || 0) + (effects?.length || 0);
  const totalShots = shots?.length || 0;
  const totalTransitions = transitions?.length || 0;

  const editSeverity =
    totalEdits <= 3 ? { label: "Light", color: "var(--color-green)", bg: "var(--color-green-dim)" }
      : totalEdits <= 8 ? { label: "Moderate", color: "var(--color-orange)", bg: "var(--color-orange-dim)" }
      : { label: "Heavy", color: "var(--color-red)", bg: "var(--color-red-dim)" };

  return (
    <section className="flex-1 px-4 py-8 max-w-[1100px] mx-auto w-full relative z-10">
      {/* ── Header ── */}
      <div style={{ animation: visible ? "fadeInUp 0.4s ease-out both" : "none" }}>
        <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4 mb-3">
          <div>
            <div className="flex items-center gap-3 mb-1.5">
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[0.6rem] font-bold uppercase tracking-[0.12em] bg-[var(--color-accent-dim)] text-[var(--color-accent)] border border-[var(--color-accent)]/20">
                <span className="w-1.5 h-1.5 rounded-full bg-[var(--color-accent)] animate-[pulse_1.5s_ease-in-out_infinite]" />
                {fmtCaseId(video_info.filename)}
              </span>
              <span className="text-[0.65rem] font-mono text-[var(--color-text-tertiary)] tabular-nums">
                {new Date().toLocaleDateString("en-US", {
                  year: "numeric", month: "short", day: "numeric",
                })}
              </span>
            </div>
            <h1 className="text-[clamp(1.5rem,3.5vw,2.2rem)] font-bold tracking-tight leading-tight">
              Forensic Report
            </h1>
            <div className="flex items-center gap-2 mt-1.5">
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-[var(--color-bg-elevated)] border border-[var(--color-border)] text-[0.65rem] font-semibold text-[var(--color-text-secondary)]">
                <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                  <path d="M7 1H3a1 1 0 00-1 1v8a1 1 0 001 1h6a1 1 0 001-1V4l-3-3z" stroke="currentColor" strokeWidth="1.2" />
                  <path d="M7 1v3h3" stroke="currentColor" strokeWidth="1.2" />
                </svg>
                <span className="max-w-[260px] truncate" title={video_info.filename}>
                  {video_info.filename}
                </span>
              </span>
              <span className="px-2 py-1 rounded-lg text-[0.55rem] font-bold uppercase tracking-wider bg-[var(--color-accent-dim)] text-[var(--color-accent)] border border-[var(--color-accent)]/20">
                {video_info.filename.split(".").pop()?.toUpperCase() || "FILE"}
              </span>
            </div>
          </div>
          <button
            onClick={onReset}
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg text-sm font-semibold border border-[var(--color-border)] text-[var(--color-text-secondary)] bg-transparent cursor-pointer transition-all duration-200 hover:border-[var(--color-accent)] hover:text-[var(--color-text-primary)] hover:bg-[var(--color-accent-dim)] hover:shadow-[0_0_24px_var(--color-accent-dim)] whitespace-nowrap shrink-0"
          >
            <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
              <path d="M2 8a6 6 0 0110.47-4M14 2v4h-4M14 8a6 6 0 01-10.47 4M2 14v-4h4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
            New Analysis
          </button>
        </div>
        <div className="h-px bg-gradient-to-r from-[var(--color-accent)]/50 via-[var(--color-accent)]/15 to-transparent mb-6" />
      </div>

      {/* ── Key Metrics ── */}
      <div
        className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6"
        style={{ animation: visible ? "fadeInUp 0.4s ease-out 0.08s both" : "none" }}
      >
        {[
          { icon: MdEdits, label: "Edits Found", value: totalEdits, badge: editSeverity.label, color: editSeverity.color, bg: editSeverity.bg },
          { icon: MdFilters, label: "Filters & Effects", value: totalFilters, color: "var(--color-accent)", bg: "var(--color-accent-dim)" },
          { icon: MdShots, label: "Shots Detected", value: totalShots, color: "var(--color-green)", bg: "var(--color-green-dim)" },
          { icon: MdTransitions, label: "Transitions", value: totalTransitions, color: "var(--color-teal)", bg: "var(--color-orange-dim)" },
        ].map((m, i) => (
          <MetricCard key={i} icon={m.icon} label={m.label} value={m.value} color={m.color} bg={m.bg} badge={m.badge} />
        ))}
      </div>

      {/* ── Two-column: Video Info + Filters ── */}
      <div
        className="grid grid-cols-1 lg:grid-cols-5 gap-4 mb-4"
        style={{ animation: visible ? "fadeInUp 0.4s ease-out 0.16s both" : "none" }}
      >
        <div className="lg:col-span-2">
          <VideoInfo info={video_info} />
        </div>
        <div className="lg:col-span-3">
          <FilterGrid filters={[...filters.filter((f) => f.type !== "adjustments"), ...effects]} />
        </div>
      </div>

      {/* ── Adjustments ── */}
      <div style={{ animation: visible ? "fadeInUp 0.4s ease-out 0.24s both" : "none" }}>
        <AdjustmentsPanel adjustments={analysis.adjustments} />
      </div>

      {/* ── Timeline ── */}
      <div style={{ animation: visible ? "fadeInUp 0.4s ease-out 0.32s both" : "none" }}>
        <Timeline analysis={analysis} />
      </div>

      {/* ── Frames ── */}
      <div style={{ animation: visible ? "fadeInUp 0.4s ease-out 0.40s both" : "none" }}>
        <FrameGallery frames={frames} />
      </div>
    </section>
  );
}

/* ── Metric Icon SVGs ── */

function MdEdits() {
  return (
    <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
      <path d="M3 13.5V15h1.5l7.37-7.37-1.5-1.5L3 13.5zM14.71 5.63a.5.5 0 000-.71l-.63-.63a.5.5 0 00-.71 0L12 5.66l1.34 1.34 1.37-1.37z" fill="currentColor" />
    </svg>
  );
}

function MdFilters() {
  return (
    <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
      <path d="M2.5 2.5h13v2.5L11 9.5V15l-4-2V9.5L2.5 5V2.5z" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round" />
    </svg>
  );
}

function MdShots() {
  return (
    <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
      <rect x="1.5" y="3.5" width="15" height="11" rx="2" stroke="currentColor" strokeWidth="1.5" />
      <path d="M6 6.5v5l4-2.5-4-2.5z" fill="currentColor" />
    </svg>
  );
}

function MdTransitions() {
  return (
    <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
      <path d="M1.5 9h5M11.5 9h5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
      <path d="M6.5 5.5l3.5 3.5-3.5 3.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

/* ── Metric Card ── */

function MetricCard({ icon: Icon, label, value, color, bg, badge }: {
  icon: React.FC;
  label: string;
  value: number;
  color: string;
  bg: string;
  badge?: string;
}) {
  return (
    <div
      className="rounded-[var(--radius-card)] border border-[var(--color-border)] p-4 transition-all duration-200 hover:border-[var(--color-accent)]/30"
      style={{ background: "var(--color-bg-card)" }}
    >
      <div className="flex items-center gap-2.5 mb-2.5">
        <span className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ background: bg, color }}>
          <Icon />
        </span>
        <span className="text-[0.65rem] font-semibold uppercase tracking-wider text-[var(--color-text-secondary)]">
          {label}
        </span>
      </div>
      <div className="flex items-center gap-2.5">
        <span className="text-[1.6rem] font-bold leading-none tabular-nums" style={{ color }}>
          {value}
        </span>
        {badge && (
          <span className="text-[0.55rem] font-bold px-2 py-0.5 rounded-full uppercase tracking-wider" style={{ background: bg, color }}>
            {badge}
          </span>
        )}
      </div>
    </div>
  );
}
