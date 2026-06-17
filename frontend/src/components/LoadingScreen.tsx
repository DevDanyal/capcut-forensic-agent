"use client";

import { useEffect, useState } from "react";

const STEPS = [
  "Extracting frames",
  "Detecting shots",
  "Analyzing color & adjustments",
  "Classifying filters & effects",
  "Building report",
];

export default function LoadingScreen() {
  const [step, setStep] = useState(0);
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    const durations = [800, 1200, 1500, 1000, 600];
    const total = durations.reduce((a, b) => a + b);
    let elapsed = 0;
    let current = 0;

    const interval = setInterval(() => {
      elapsed += 50;
      setProgress(Math.min((elapsed / total) * 100, 95));

      if (current < durations.length && elapsed >= durations.slice(0, current + 1).reduce((a, b) => a + b, 0)) {
        current++;
        setStep(current);
      }

      if (elapsed >= total) clearInterval(interval);
    }, 50);

    return () => clearInterval(interval);
  }, []);

  return (
    <section className="flex-1 flex items-center justify-center px-4">
      <div className="text-center max-w-sm mx-auto">
        <div className="relative w-[120px] h-[120px] mx-auto mb-6">
          <div className="w-full h-full flex items-center justify-center text-[var(--color-accent)] animate-[pulse_2s_ease-in-out_infinite]">
            <svg width="80" height="80" viewBox="0 0 80 80" fill="none">
              <rect
                x="4"
                y="4"
                width="72"
                height="72"
                rx="16"
                stroke="currentColor"
                strokeWidth="2"
              />
              <path
                d="M24 30h32M24 40h32M24 50h24"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
              />
            </svg>
          </div>
          <div
            className="absolute left-[10%] w-[80%] h-[2px] bg-gradient-to-r from-transparent via-[var(--color-accent)] to-transparent rounded-sm shadow-[0_0_12px_var(--color-accent-glow)]"
            style={{ animation: "scan 2s ease-in-out infinite" }}
          />
        </div>

        <h2 className="text-lg font-semibold mb-6">Analyzing Video</h2>

        <div className="flex flex-col gap-2.5 text-left mb-6">
          {STEPS.map((s, i) => (
            <div
              key={s}
              className={`px-4 py-2.5 rounded-lg text-sm border-l-[3px] transition-all duration-300 ${
                i === step
                  ? "bg-[rgba(108,92,231,0.08)] border-l-[var(--color-accent)] text-[var(--color-text-primary)]"
                  : i < step
                  ? "bg-[var(--color-bg-card)] border-l-[var(--color-green)] text-[var(--color-green)]"
                  : "bg-[var(--color-bg-card)] border-l-[var(--color-border)] text-[var(--color-text-tertiary)]"
              }`}
            >
              {s}
              {i < step && <span className="ml-1">✓</span>}
            </div>
          ))}
        </div>

        <div className="h-1 rounded-full bg-[var(--color-bg-card)] overflow-hidden">
          <div
            className="h-full rounded-full bg-gradient-to-r from-[var(--color-accent)] to-[var(--color-green)] transition-[width] duration-300"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>
    </section>
  );
}
