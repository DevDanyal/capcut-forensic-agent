"use client";

import { useState, useRef, type DragEvent } from "react";

interface Props {
  onFile: (file: File) => void;
  onUrl: (url: string) => void;
}

export default function UploadZone({ onFile, onUrl }: Props) {
  const [dragging, setDragging] = useState(false);
  const [mode, setMode] = useState<"upload" | "url">("upload");
  const [urlInput, setUrlInput] = useState("");
  const [selectedFile, setSelectedFile] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const allowed = [
    "video/mp4",
    "video/quicktime",
    "video/x-msvideo",
    "video/x-matroska",
    "video/webm",
    "video/x-ms-wmv",
    "video/x-flv",
    "video/avi",
    "video/mpeg",
  ];

  const handleFile = (file: File) => {
    if (
      !allowed.includes(file.type) &&
      !file.name.match(/\.(mp4|mov|avi|mkv|webm|wmv|flv|m4v)$/i)
    ) {
      alert("Unsupported file type. Please upload MP4, MOV, AVI, MKV, or WebM.");
      return;
    }
    if (file.size > 1024 * 1024 * 1024) {
      alert("File too large. Maximum size is 1GB.");
      return;
    }
    onFile(file);
  };

  const handleDrop = (e: DragEvent) => {
    e.preventDefault();
    setDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  };

  const handleUrlSubmit = () => {
    const url = urlInput.trim();
    if (!url) {
      alert("Please enter a video URL");
      return;
    }
    if (!url.match(/^https?:\/\//i)) {
      alert("Please enter a valid URL starting with http:// or https://");
      return;
    }
    onUrl(url);
  };

  return (
    <section className="flex-1 flex items-center justify-center px-4 py-20">
      <div className="text-center max-w-lg mx-auto w-full">
        <svg
          width="64"
          height="64"
          viewBox="0 0 64 64"
          fill="none"
          className="mx-auto mb-4 text-[var(--color-accent)]"
        >
          <rect
            x="8"
            y="8"
            width="48"
            height="48"
            rx="12"
            stroke="currentColor"
            strokeWidth="2.5"
            opacity="0.3"
          />
          <path
            d="M24 28l8-8 8 8M32 20v24"
            stroke="currentColor"
            strokeWidth="2.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>

        <h1 className="text-[clamp(1.6rem,4vw,2.4rem)] font-extrabold tracking-tight mb-2">
          Analyze Any Video
        </h1>
        <p className="text-[var(--color-text-secondary)] text-sm mb-8 max-w-sm mx-auto">
          Upload a video or paste a link — get a complete forensic breakdown of
          every effect, filter, and adjustment used
        </p>

        {/* Mode Toggle */}
        <div className="flex bg-[var(--color-bg-elevated)] rounded-xl p-1 mb-6 w-fit mx-auto border border-[var(--color-border)]">
          <button
            onClick={() => setMode("upload")}
            className={`px-5 py-2 rounded-lg text-sm font-medium transition-all ${
              mode === "upload"
                ? "bg-[var(--color-accent)] text-white"
                : "text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)]"
            }`}
          >
            Upload File
          </button>
          <button
            onClick={() => setMode("url")}
            className={`px-5 py-2 rounded-lg text-sm font-medium transition-all ${
              mode === "url"
                ? "bg-[var(--color-accent)] text-white"
                : "text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)]"
            }`}
          >
            Video URL
          </button>
        </div>

        {mode === "upload" ? (
          <>
            <div
              onDragOver={(e) => {
                e.preventDefault();
                setDragging(true);
              }}
              onDragLeave={() => setDragging(false)}
              onDrop={handleDrop}
              className={`relative border-2 border-dashed rounded-2xl py-12 px-6 cursor-pointer transition-all duration-300 ${
                dragging
                  ? "border-[var(--color-accent)] bg-[rgba(108,92,231,0.05)] shadow-[0_0_40px_var(--color-accent-glow)]"
                  : "border-[var(--color-border)] bg-[var(--color-bg-elevated)] hover:border-[var(--color-accent)]"
              }`}
            >
              <input
                ref={inputRef}
                type="file"
                onChange={(e) => {
                  const file = e.target.files?.[0];
                  if (file) {
                    setSelectedFile(file.name);
                    handleFile(file);
                  }
                }}
                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10"
              />
              <div className="flex flex-col items-center gap-2 text-[var(--color-text-secondary)] text-sm pointer-events-none">
                <svg
                  width="40"
                  height="40"
                  viewBox="0 0 40 40"
                  fill="none"
                  className="text-[var(--color-accent)]"
                >
                  <path
                    d="M20 28V12M12 20l8-8 8 8"
                    stroke="currentColor"
                    strokeWidth="2.5"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>
                <span>
                  Drop video here or{" "}
                  <strong className="text-[var(--color-accent)]">browse</strong>
                </span>
                <small className="text-[var(--color-text-tertiary)] text-xs">
                  MP4, MOV, AVI, MKV, WebM &bull; Max 1GB
                </small>
              </div>
            </div>
            <div className="flex gap-2 justify-center mt-4 flex-wrap">
              {["MP4", "MOV", "AVI", "MKV", "WebM", "WMV", "FLV", "M4V"].map((fmt) => (
                <span
                  key={fmt}
                  className="text-[0.7rem] font-medium px-2.5 py-1 rounded-full bg-[var(--color-bg-card)] text-[var(--color-text-tertiary)] border border-[var(--color-border)]"
                >
                  {fmt}
                </span>
              ))}
            </div>
            {selectedFile && (
              <p className="text-xs text-[var(--color-accent)] mt-3">
                Selected: {selectedFile}
              </p>
            )}
          </>
        ) : (
          <div className="bg-[var(--color-bg-elevated)] rounded-2xl p-6 border border-[var(--color-border)]">
            <div className="flex flex-col items-center gap-2 text-[var(--color-text-secondary)] text-sm mb-4">
              <svg
                width="40"
                height="40"
                viewBox="0 0 40 40"
                fill="none"
                className="text-[var(--color-accent)]"
              >
                <path
                  d="M12 12h16v16H12z"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinejoin="round"
                />
                <path
                  d="M20 16v8M16 20h8"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                />
              </svg>
              <span>Paste a direct video URL</span>
            </div>
            <div className="flex gap-2">
              <input
                type="url"
                value={urlInput}
                onChange={(e) => setUrlInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleUrlSubmit()}
                placeholder="https://example.com/video.mp4"
                className="flex-1 px-4 py-3 rounded-xl bg-[var(--color-bg-card)] border border-[var(--color-border)] text-sm text-[var(--color-text-primary)] placeholder-[var(--color-text-tertiary)] outline-none focus:border-[var(--color-accent)] transition-colors"
              />
              <button
                onClick={handleUrlSubmit}
                disabled={!urlInput.trim()}
                className="px-6 py-3 rounded-xl bg-[var(--color-accent)] text-white text-sm font-semibold disabled:opacity-40 disabled:cursor-not-allowed hover:opacity-90 transition-opacity whitespace-nowrap"
              >
                Analyze
              </button>
            </div>
            {urlInput.includes('tiktok.com') && (
              <p className="text-xs text-[var(--color-orange)] mt-2">
                TikTok videos often can&apos;t be downloaded via URL. Use <strong>Upload File</strong> instead — save the video to your device first.
              </p>
            )}
            {!urlInput.includes('tiktok.com') && (
              <p className="text-xs text-[var(--color-text-tertiary)] mt-3">
                Supports YouTube, direct MP4/MOV/AVI/MKV/WebM links &bull; Max 500MB
              </p>
            )}
          </div>
        )}
      </div>
    </section>
  );
}
