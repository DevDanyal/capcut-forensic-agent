"use client";

import { useState, useRef } from "react";
import { applyEdits, type ApplyEditsResult, formatDuration } from "@/lib/api";
import AdjustmentsPanel from "./AdjustmentsPanel";
import FilterGrid from "./FilterGrid";

export default function ApplyEditsPanel() {
  const [originalFile, setOriginalFile] = useState<File | null>(null);
  const [referenceFile, setReferenceFile] = useState<File | null>(null);
  const [processing, setProcessing] = useState(false);
  const [result, setResult] = useState<ApplyEditsResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const videoRef = useRef<HTMLVideoElement>(null);

  const handleStart = async () => {
    if (!originalFile || !referenceFile) return;
    setProcessing(true);
    setError(null);
    setResult(null);
    try {
      const data = await applyEdits(originalFile, referenceFile);
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Processing failed");
    } finally {
      setProcessing(false);
    }
  };

  const handleSave = () => {
    if (!result?.video_data) return;
    const link = document.createElement("a");
    link.href = `data:${result.video_mime};base64,${result.video_data}`;
    const name = originalFile?.name?.replace(/\.[^.]+$/, "") || "edited";
    link.download = `${name}_edited.mp4`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const reset = () => {
    setOriginalFile(null);
    setReferenceFile(null);
    setResult(null);
    setError(null);
  };

  return (
    <div className="flex-1 px-4 py-8 max-w-[800px] mx-auto w-full">
      {!result && !processing && (
        <>
          <div className="mb-6">
            <h2 className="text-xl font-bold tracking-tight mb-1">Apply Edits</h2>
            <p className="text-sm text-[var(--color-text-tertiary)]">
              Upload an unedited video and a reference edited video. The edits from the reference will be applied to your original.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-6">
            <UploadBox
              label="Original (Unedited)"
              accept="video/*"
              file={originalFile}
              onFile={setOriginalFile}
            />
            <UploadBox
              label="Reference (Edited)"
              accept="video/*"
              file={referenceFile}
              onFile={setReferenceFile}
            />
          </div>

          <button
            onClick={handleStart}
            disabled={!originalFile || !referenceFile}
            className="w-full py-3 rounded-xl text-sm font-bold text-white bg-[var(--color-accent)] disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer transition-all hover:shadow-[0_0_24px_var(--color-accent-dim)]"
          >
            Apply Edits
          </button>
        </>
      )}

      {processing && (
        <div className="flex flex-col items-center justify-center py-16 gap-4">
          <div className="w-10 h-10 border-2 border-[var(--color-accent)] border-t-transparent rounded-full animate-spin" />
          <p className="text-sm text-[var(--color-text-secondary)]">Processing video...</p>
        </div>
      )}

      {error && (
        <div className="text-center py-16">
          <p className="text-[var(--color-red)] mb-4">{error}</p>
          <button onClick={reset} className="px-5 py-2.5 rounded-lg text-sm font-semibold border border-[var(--color-border)] cursor-pointer">
            Try Again
          </button>
        </div>
      )}

      {result && (
        <div>
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-xl font-bold tracking-tight">Edits Applied</h2>
              <p className="text-sm text-[var(--color-text-tertiary)]">
                Your video has been processed with the detected adjustments
              </p>
            </div>
            <div className="flex gap-2">
              <button
                onClick={reset}
                className="px-4 py-2 rounded-lg text-sm font-semibold border border-[var(--color-border)] cursor-pointer"
              >
                New
              </button>
              <button
                onClick={handleSave}
                className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg text-sm font-bold text-white bg-[var(--color-accent)] cursor-pointer transition-all hover:shadow-[0_0_24px_var(--color-accent-dim)]"
              >
                <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
                  <path d="M13 10v2a1 1 0 01-1 1H4a1 1 0 01-1-1v-2M8 2v8M5 7l3 3 3-3" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
                Save Video
              </button>
            </div>
          </div>

          {result.video_data && (
            <div className="rounded-xl overflow-hidden border border-[var(--color-border)] mb-4 bg-black">
              <video
                ref={videoRef}
                src={`data:${result.video_mime};base64,${result.video_data}`}
                controls
                className="w-full max-h-[400px]"
              />
            </div>
          )}

          <div className="mb-4">
            <AdjustmentsPanel adjustments={result.adjustments} />
          </div>

          <div>
            <FilterGrid filters={[...result.filters, ...result.effects]} />
          </div>
        </div>
      )}
    </div>
  );
}

function UploadBox({ label, accept, file, onFile }: {
  label: string;
  accept: string;
  file: File | null;
  onFile: (f: File | null) => void;
}) {
  const inputRef = useRef<HTMLInputElement>(null);

  return (
    <div
      onClick={() => inputRef.current?.click()}
      className="rounded-xl border-2 border-dashed border-[var(--color-border)] p-6 text-center cursor-pointer transition-all hover:border-[var(--color-accent)]/50 hover:bg-[var(--color-accent-dim)]/30"
    >
      <input
        ref={inputRef}
        type="file"
        accept={accept}
        className="hidden"
        onChange={(e) => {
          const f = e.target.files?.[0];
          if (f) onFile(f);
        }}
      />
      {file ? (
        <div>
          <p className="text-sm font-semibold truncate">{file.name}</p>
          <p className="text-xs text-[var(--color-text-tertiary)] mt-1">
            {(file.size / 1024 / 1024).toFixed(1)} MB
          </p>
        </div>
      ) : (
        <div>
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" className="mx-auto mb-2 opacity-40">
            <path d="M12 4v12M8 12l4 4 4-4M4 16v2a2 2 0 002 2h12a2 2 0 002-2v-2" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
          </svg>
          <p className="text-sm font-medium">{label}</p>
          <p className="text-xs text-[var(--color-text-tertiary)] mt-1">Click to upload</p>
        </div>
      )}
    </div>
  );
}
