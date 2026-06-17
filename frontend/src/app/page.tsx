"use client";

import { useState } from "react";
import { analyzeVideo, analyzeVideoUrl, type AnalysisResult } from "@/lib/api";
import UploadZone from "@/components/UploadZone";
import LoadingScreen from "@/components/LoadingScreen";
import ResultsDashboard from "@/components/ResultsDashboard";

export default function Home() {
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleFile = async (file: File) => {
    setUploading(true);
    setError(null);
    setResult(null);
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
    try {
      const data = await analyzeVideoUrl(url);
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Analysis failed");
    } finally {
      setUploading(false);
    }
  };

  const reset = () => {
    setResult(null);
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
        {!uploading && !result && <UploadZone onFile={handleFile} onUrl={handleUrl} />}
        {uploading && !result && <LoadingScreen />}
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
      </main>

      <footer className="text-center py-6 text-[var(--color-text-tertiary)] text-xs border-t border-[var(--color-border)]">
        CapCut Forensic Agent &mdash; AI-Powered Video Analysis
      </footer>
    </>
  );
}
