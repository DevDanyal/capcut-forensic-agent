"use client";

import { useState } from "react";
import { analyzeVideo, analyzeVideoUrl, compareVideos, type AnalysisResult, type CompareResult } from "@/lib/api";
import UploadZone from "@/components/UploadZone";
import CompareUpload from "@/components/CompareUpload";
import LoadingScreen from "@/components/LoadingScreen";
import ResultsDashboard from "@/components/ResultsDashboard";

export default function Home() {
  const [mode, setMode] = useState<"single" | "compare">("single");
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [compareResult, setCompareResult] = useState<CompareResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleFile = async (file: File) => {
    setUploading(true);
    setError(null);
    setResult(null);
    setCompareResult(null);
    try {
      const data = await analyzeVideo(file);
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Analysis failed");
    } finally {
      setUploading(false);
    }
  };

  const handleUrl = async (url: string) => {
    setUploading(true);
    setError(null);
    setResult(null);
    setCompareResult(null);
    try {
      const data = await analyzeVideoUrl(url);
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Analysis failed");
    } finally {
      setUploading(false);
    }
  };

  const handleCompare = async (original: File, edited: File) => {
    setUploading(true);
    setError(null);
    setResult(null);
    setCompareResult(null);
    try {
      const data = await compareVideos(original, edited);
      setCompareResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Comparison failed");
    } finally {
      setUploading(false);
    }
  };

  const reset = () => {
    setResult(null);
    setCompareResult(null);
    setUploading(false);
    setError(null);
  };

  return (
    <>
      <nav className="sticky top-0 z-50 bg-[rgba(10,10,15,0.85)] backdrop-blur-md border-b border-[var(--color-border)]">
        <div className="max-w-[1200px] mx-auto px-5 py-3 flex items-center justify-between">
          <div className="flex items-center gap-2.5 font-bold text-lg tracking-tight">
            <svg width="28" height="28" viewBox="0 0 28 28" fill="none" className="shrink-0">
              <rect x="2" y="2" width="24" height="24" rx="6" stroke="currentColor" strokeWidth="2" />
              <path d="M10 8v12l10-6-10-6z" fill="currentColor" opacity="0.8" />
            </svg>
            CapCut Forensic
          </div>
          <span className="text-[0.7rem] font-semibold uppercase tracking-wider px-2.5 py-1 rounded-full bg-[var(--color-accent)] text-white">
            Agent
          </span>
        </div>
      </nav>

      <main className="flex-1 flex flex-col">
        {!uploading && !result && !compareResult && (
          <>
            <div className="flex justify-center gap-2 pt-8 pb-0">
              <button
                onClick={() => setMode("single")}
                className={`px-4 py-2 rounded-lg text-sm font-semibold transition-all cursor-pointer ${
                  mode === "single"
                    ? "bg-[var(--color-accent)] text-white shadow-[0_0_20px_var(--color-accent-dim)]"
                    : "border border-[var(--color-border)] text-[var(--color-text-secondary)] hover:border-[var(--color-accent)]/50"
                }`}
              >
                Single Video
              </button>
              <button
                onClick={() => setMode("compare")}
                className={`px-4 py-2 rounded-lg text-sm font-semibold transition-all cursor-pointer ${
                  mode === "compare"
                    ? "bg-[var(--color-accent)] text-white shadow-[0_0_20px_var(--color-accent-dim)]"
                    : "border border-[var(--color-border)] text-[var(--color-text-secondary)] hover:border-[var(--color-accent)]/50"
                }`}
              >
                Before / After
              </button>
            </div>
            {mode === "single" ? (
              <UploadZone onFile={handleFile} onUrl={handleUrl} />
            ) : (
              <CompareUpload onCompare={handleCompare} />
            )}
          </>
        )}
        {uploading && !result && !compareResult && <LoadingScreen />}
        {error && (
          <div className="flex-1 flex items-center justify-center px-4">
            <div className="text-center max-w-sm">
              <p className="text-[var(--color-red)] mb-4">{error}</p>
              <button
                onClick={reset}
                className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg text-sm font-semibold border border-[var(--color-border)] text-[var(--color-text-secondary)] bg-transparent cursor-pointer transition-all duration-200 hover:border-[var(--color-accent)]"
              >
                Try Again
              </button>
            </div>
          </div>
        )}
        {result && <ResultsDashboard result={result} onReset={reset} />}
        {compareResult && <CompareDashboard result={compareResult} onReset={reset} />}
      </main>

      <footer className="text-center py-6 text-[var(--color-text-tertiary)] text-xs border-t border-[var(--color-border)]">
        CapCut Forensic Agent &mdash; AI-Powered Video Analysis
      </footer>
    </>
  );
}

function CompareDashboard({ result, onReset }: { result: CompareResult; onReset: () => void }) {
  const { adjustments, filters, effects, video_info } = result;
  const totalEdits = Object.keys(adjustments).length + filters.length + effects.length;
  const editSeverity =
    totalEdits <= 3 ? { label: "Light", color: "var(--color-green)" }
      : totalEdits <= 8 ? { label: "Moderate", color: "var(--color-orange)" }
      : { label: "Heavy", color: "var(--color-red)" };

  return (
    <section className="flex-1 px-4 py-8 max-w-[1100px] mx-auto w-full">
      <div className="flex items-center justify-between mb-6">
        <div>
          <div className="flex items-center gap-3 mb-1.5">
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[0.55rem] font-bold uppercase tracking-[0.12em] bg-[var(--color-accent-dim)] text-[var(--color-accent)] border border-[var(--color-accent)]/20">
              Before / After
            </span>
            <span className="text-[0.65rem] font-mono text-[var(--color-text-tertiary)]">
              {new Date().toLocaleDateString("en-US", { year: "numeric", month: "short", day: "numeric" })}
            </span>
          </div>
          <h1 className="text-[clamp(1.5rem,3.5vw,2.2rem)] font-bold tracking-tight leading-tight">
            Exact Adjustments
          </h1>
          <p className="text-[0.75rem] text-[var(--color-text-tertiary)] mt-1">
            Original: {video_info.original.width}&times;{video_info.original.height} &middot; Edited: {video_info.edited.width}&times;{video_info.edited.height}
          </p>
        </div>
        <button
          onClick={onReset}
          className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg text-sm font-semibold border border-[var(--color-border)] text-[var(--color-text-secondary)] bg-transparent cursor-pointer transition-all hover:border-[var(--color-accent)] hover:text-[var(--color-text-primary)]"
        >
          <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
            <path d="M2 8a6 6 0 0110.47-4M14 2v4h-4M14 8a6 6 0 01-10.47 4M2 14v-4h4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
          New Comparison
        </button>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6">
        {[
          { label: "Edits Found", value: totalEdits, badge: editSeverity.label, color: editSeverity.color },
          { label: "Filters", value: filters.length, color: "var(--color-accent)" },
          { label: "Effects", value: effects.length, color: "var(--color-green)" },
          { label: "Confidence", value: "High", color: "var(--color-teal)" },
        ].map((m, i) => (
          <div key={i} className="rounded-[var(--radius-card)] border border-[var(--color-border)] p-4" style={{ background: "var(--color-bg-card)" }}>
            <span className="text-[0.65rem] font-semibold uppercase tracking-wider text-[var(--color-text-secondary)] block mb-2.5">
              {m.label}
            </span>
            <div className="flex items-center gap-2.5">
              <span className="text-[1.6rem] font-bold leading-none tabular-nums" style={{ color: m.color }}>
                {typeof m.value === "number" ? m.value : m.value}
              </span>
              {m.badge && <span className="text-[0.55rem] font-bold px-2 py-0.5 rounded-full uppercase tracking-wider" style={{ background: `${m.color}20`, color: m.color }}>{m.badge}</span>}
            </div>
          </div>
        ))}
      </div>

      <div className="mb-4">
        <AdjustmentsPanel adjustments={adjustments} />
      </div>

      <div>
        <FilterGrid filters={[...filters, ...effects]} />
      </div>
    </section>
  );
}

// Lazy imports to avoid circular deps
import AdjustmentsPanel from "@/components/AdjustmentsPanel";
import FilterGrid from "@/components/FilterGrid";
