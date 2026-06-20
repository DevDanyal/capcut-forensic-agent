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

function isLocal(): boolean {
  return typeof window !== "undefined" && window.location.hostname === "localhost";
}

async function uploadFileToBlob(file: File): Promise<string> {
  const { uploadVideoToBlob } = await import("@/lib/blob-upload/upload");
  const result = await uploadVideoToBlob(file);
  return result.url;
}

async function apiPost<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    const text = await response.text();
    try {
      const err = JSON.parse(text);
      throw new Error(err.error || "Request failed");
    } catch {
      throw new Error(text || "Request failed");
    }
  }
  return response.json();
}

async function apiUpload<T>(path: string, formData: FormData): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    body: formData,
  });
  if (!response.ok) {
    const text = await response.text();
    try {
      const err = JSON.parse(text);
      throw new Error(err.error || "Request failed");
    } catch {
      throw new Error(text || "Request failed");
    }
  }
  return response.json();
}

export async function analyzeVideo(file: File): Promise<AnalysisResult> {
  if (!isLocal()) {
    const blobUrl = await uploadFileToBlob(file);
    return apiPost<AnalysisResult>("/api/analyze-blob", { blob_url: blobUrl });
  }

  const formData = new FormData();
  formData.append("video", file);
  return apiUpload<AnalysisResult>("/api/analyze", formData);
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
  if (!isLocal()) {
    const [origBlobUrl, editBlobUrl] = await Promise.all([
      uploadFileToBlob(original),
      uploadFileToBlob(edited),
    ]);
    return apiPost<CompareResult>("/api/compare-blob", {
      original_blob_url: origBlobUrl,
      edited_blob_url: editBlobUrl,
    });
  }

  const formData = new FormData();
  formData.append("original", original);
  formData.append("edited", edited);
  return apiUpload<CompareResult>("/api/compare", formData);
}

export function capitalize(str: string): string {
  return str.replace(/\b\w/g, (c) => c.toUpperCase());
}

export interface ApplyEditsResult {
  status: string;
  adjustments: Adjustments;
  filters: Filter[];
  effects: Filter[];
  download_token?: string;
  result_blob_url?: string;
  video_size: number;
  video_mime: string;
}

export async function applyEdits(original: File, reference: File): Promise<ApplyEditsResult> {
  if (!isLocal()) {
    const [origBlobUrl, refBlobUrl] = await Promise.all([
      uploadFileToBlob(original),
      uploadFileToBlob(reference),
    ]);
    return apiPost<ApplyEditsResult>("/api/apply-edits-blob", {
      original_blob_url: origBlobUrl,
      reference_blob_url: refBlobUrl,
    });
  }

  const formData = new FormData();
  formData.append("original", original);
  formData.append("reference", reference);
  return apiUpload<ApplyEditsResult>("/api/apply-edits", formData);
}
