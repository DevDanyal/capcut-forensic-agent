export interface VideoInfo {
  filename: string;
  duration_seconds: number;
  fps: number;
  width: number;
  height: number;
  total_frames_analyzed: number;
  aspect_ratio: string;
}

export interface Shot {
  start: number;
  end: number;
  type: string;
}

export interface Transition {
  time: number;
  type: string;
  strength: number;
}

export interface Adjustments {
  [key: string]: number;
}

export interface Filter {
  name: string;
  type: string;
  parameters: Record<string, number>;
  confidence: number;
}

export interface TimelineEntry {
  time: number;
  frame_index: number;
  mean_brightness?: number;
  contrast_level?: number;
  temperature_shift?: number;
  saturation_level?: number;
  transition?: Transition;
  shot_index?: number;
}

export interface AnalysisSummary {
  total_significant_adjustments: number;
  adjustments_list: Adjustments;
  filters_detected: string[];
  total_filters: number;
  estimated_edits_count: number;
}

export interface Analysis {
  video_info: VideoInfo;
  shots: Shot[];
  transitions: Transition[];
  adjustments: Adjustments;
  filters: Filter[];
  effects: Filter[];
  timeline: TimelineEntry[];
  summary: AnalysisSummary;
}

export interface FrameData {
  time: number;
  data: string;
}

export interface AnalysisResult {
  analysis: Analysis;
  frames: FrameData[];
  status: string;
}

const API_BASE =
  typeof window !== "undefined" && window.location.hostname === "localhost"
    ? "http://localhost:5000"
    : "";

export async function analyzeVideo(file: File): Promise<AnalysisResult> {
  const formData = new FormData();
  formData.append("video", file);

  const response = await fetch(`${API_BASE}/api/analyze`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const text = await response.text();
    try {
      const err = JSON.parse(text);
      throw new Error(err.error || "Analysis failed");
    } catch {
      throw new Error(text || "Analysis failed");
    }
  }

  return response.json();
}

export async function analyzeVideoUrl(url: string): Promise<AnalysisResult> {
  const response = await fetch(`${API_BASE}/api/analyze-url`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url }),
  });

  if (!response.ok) {
    const text = await response.text();
    try {
      const err = JSON.parse(text);
      throw new Error(err.error || "Analysis failed");
    } catch {
      throw new Error(text || "Analysis failed");
    }
  }

  return response.json();
}

export function formatDuration(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${s.toString().padStart(2, "0")}`;
}

export interface CompareResult {
  adjustments: Adjustments;
  filters: Filter[];
  effects: Filter[];
  video_info: {
    original: { width: number; height: number; fps: number; frames_analyzed: number };
    edited: { width: number; height: number; fps: number; frames_analyzed: number };
  };
  status: string;
}

export async function compareVideos(original: File, edited: File): Promise<CompareResult> {
  const formData = new FormData();
  formData.append("original", original);
  formData.append("edited", edited);

  const response = await fetch(`${API_BASE}/api/compare`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const text = await response.text();
    try {
      const err = JSON.parse(text);
      throw new Error(err.error || "Comparison failed");
    } catch {
      throw new Error(text || "Comparison failed");
    }
  }

  return response.json();
}

export function capitalize(str: string): string {
  return str.replace(/\b\w/g, (c) => c.toUpperCase());
}
