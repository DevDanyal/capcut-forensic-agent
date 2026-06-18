"use client";

import { useState, useRef, type DragEvent } from "react";

interface Props {
  onCompare: (original: File, edited: File) => void;
}

export default function CompareUpload({ onCompare }: Props) {
  const [original, setOriginal] = useState<File | null>(null);
  const [edited, setEdited] = useState<File | null>(null);
  const [dragTarget, setDragTarget] = useState<"original" | "edited" | null>(null);

  const origRef = useRef<HTMLInputElement>(null);
  const editRef = useRef<HTMLInputElement>(null);

  function handleDrop(e: DragEvent, target: "original" | "edited") {
    e.preventDefault();
    setDragTarget(null);
    const file = e.dataTransfer?.files?.[0];
    if (file) {
      if (target === "original") setOriginal(file);
      else setEdited(file);
    }
  }

  function handleFile(e: React.ChangeEvent<HTMLInputElement>, target: "original" | "edited") {
    const file = e.target.files?.[0];
    if (file) {
      if (target === "original") setOriginal(file);
      else setEdited(file);
    }
  }

  function readableSize(bytes: number) {
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  }

  return (
    <div className="flex-1 flex items-center justify-center px-4 py-12">
      <div className="w-full max-w-2xl">
        <div className="text-center mb-8">
          <h2 className="text-xl font-bold mb-2">Before / After Comparison</h2>
          <p className="text-[0.8rem] text-[var(--color-text-tertiary)]">
            Upload the <strong>original unedited</strong> video and the <strong>edited</strong> video to get exact adjustment values.
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-8">
          <DropZone
            label="Original (unedited)"
            file={original}
            dragTarget={dragTarget === "original"}
            onDragOver={() => setDragTarget("original")}
            onDragLeave={() => setDragTarget(null)}
            onDrop={(e) => handleDrop(e, "original")}
            onClick={() => origRef.current?.click()}
            color="var(--color-green)"
          />
          <DropZone
            label="Edited (after effects)"
            file={edited}
            dragTarget={dragTarget === "edited"}
            onDragOver={() => setDragTarget("edited")}
            onDragLeave={() => setDragTarget(null)}
            onDrop={(e) => handleDrop(e, "edited")}
            onClick={() => editRef.current?.click()}
            color="var(--color-accent)"
          />
        </div>

        <input ref={origRef} type="file" accept="video/*" className="hidden" onChange={(e) => handleFile(e, "original")} />
        <input ref={editRef} type="file" accept="video/*" className="hidden" onChange={(e) => handleFile(e, "edited")} />

        <div className="text-center">
          <button
            disabled={!original || !edited}
            onClick={() => original && edited && onCompare(original, edited)}
            className="inline-flex items-center gap-2 px-8 py-3 rounded-xl text-sm font-bold text-white bg-[var(--color-accent)] cursor-pointer transition-all duration-200 hover:shadow-[0_0_32px_var(--color-accent-dim)] disabled:opacity-30 disabled:cursor-not-allowed"
          >
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <path d="M8 2v12M2 8h12" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
            </svg>
            Compare Videos
          </button>
        </div>

        <p className="text-center text-[0.6rem] text-[var(--color-text-tertiary)] mt-4">
          Videos should have the same scene content for accurate comparison.
        </p>
      </div>
    </div>
  );
}

function DropZone({
  label, file, dragTarget, onDragOver, onDragLeave, onDrop, onClick, color,
}: {
  label: string;
  file: File | null;
  dragTarget: boolean;
  onDragOver: () => void;
  onDragLeave: () => void;
  onDrop: (e: DragEvent) => void;
  onClick: () => void;
  color: string;
}) {
  return (
    <div
      onDragOver={(e) => { e.preventDefault(); onDragOver(); }}
      onDragLeave={onDragLeave}
      onDrop={onDrop}
      onClick={onClick}
      className="rounded-[var(--radius-card)] border-2 border-dashed p-6 text-center cursor-pointer transition-all duration-200 hover:border-[var(--color-accent)]/50"
      style={{
        background: dragTarget ? `${color}10` : "var(--color-bg-card)",
        borderColor: file ? color : dragTarget ? color : "var(--color-border)",
      }}
    >
      {file ? (
        <div className="space-y-2">
          <div className="w-10 h-10 rounded-xl mx-auto flex items-center justify-center" style={{ background: `${color}20` }}>
            <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
              <rect x="2" y="2" width="14" height="14" rx="3" stroke={color} strokeWidth="1.5" />
              <path d="M6 6.5v5l5-2.5-5-2.5z" fill={color} />
            </svg>
          </div>
          <p className="text-sm font-semibold truncate max-w-[200px] mx-auto">{file.name}</p>
          <p className="text-[0.6rem] text-[var(--color-text-tertiary)]">{(file.size / (1024 * 1024)).toFixed(1)} MB</p>
        </div>
      ) : (
        <div className="space-y-2">
          <div className="w-10 h-10 rounded-xl mx-auto flex items-center justify-center" style={{ background: `${color}15` }}>
            <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
              <path d="M9 2v14M2 9h14" stroke={color} strokeWidth="1.5" strokeLinecap="round" />
            </svg>
          </div>
          <p className="text-sm font-semibold">{label}</p>
          <p className="text-[0.6rem] text-[var(--color-text-tertiary)]">Click or drag video here</p>
        </div>
      )}
    </div>
  );
}
