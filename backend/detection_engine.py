import numpy as np
import os
from typing import List, Dict, Tuple, Optional

class DetectionEngine:
    def __init__(self, video_path: str, sample_interval: float = 0.5, max_frames: int = 300):
        self.video_path = video_path
        self.sample_interval = sample_interval
        self.max_frames = max_frames
        self.frames: List[Tuple[float, np.ndarray]] = []
        self.fps = 30.0
        self.duration = 0.0
        self.width = 0
        self.height = 0

    def extract_frames(self) -> bool:
        import os as _os, cv2
        if not _os.path.exists(self.video_path):
            self._error = f"Video file not found: {self.video_path}"
            return False

        file_size = _os.path.getsize(self.video_path)
        if file_size < 100:
            self._error = f"Video file is too small ({file_size} bytes)"
            return False

        cap = cv2.VideoCapture(self.video_path, cv2.CAP_ANY)
        if not cap.isOpened():
            cap = cv2.VideoCapture(self.video_path)
            if not cap.isOpened():
                self._error = "Could not open video file. The file may be corrupted, use an unsupported codec, or the URL may not point to a direct video file."
                return False

        self.fps = cap.get(cv2.CAP_PROP_FPS)
        if self.fps <= 0 or self.fps > 1000:
            self.fps = 30.0
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.duration = total_frames / self.fps if total_frames > 0 else 0
        self.width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        if self.width <= 0 or self.height <= 0:
            ret, test_frame = cap.read()
            if ret:
                self.height, self.width = test_frame.shape[:2]
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            else:
                self._error = "Could not read video frames"
                cap.release()
                return False

        frame_interval = max(1, int(self.fps * self.sample_interval))
        sample_count = 0

        frame_idx = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            if frame_idx % frame_interval == 0:
                timestamp = frame_idx / self.fps
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                self.frames.append((timestamp, rgb))
                sample_count += 1
                if sample_count >= self.max_frames:
                    break

            frame_idx += 1

        cap.release()

        if len(self.frames) == 0:
            self._error = "No frames could be extracted. Unsupported video codec."
            return False

        if self.duration <= 0 and len(self.frames) > 0:
            self.duration = len(self.frames) * self.sample_interval

        return True

    def analyze(self) -> Dict:
        from shot_detection import detect_shots, detect_transitions
        from color_analysis import (
            analyze_luminance_stats, analyze_color_matrix, analyze_saturation,
            analyze_edges, analyze_noise, analyze_vignette,
            estimate_histogram_parameters, estimate_color_parameters,
            estimate_saturation_parameters,
        )
        from filter_classifier import classify_filters
        from reference_card import compute_dynamic_reference, get_neutral_reference

        analysis = {
            "video_info": self._get_video_info(),
            "shots": [],
            "transitions": [],
            "adjustments": {},
            "filters": [],
            "effects": [],
            "timeline": [],
            "summary": {},
        }

        if len(self.frames) < 2:
            return analysis

        shots = detect_shots(self.frames)
        analysis["shots"] = shots

        all_lum_stats = []
        all_color_matrix = []
        all_saturation = []
        all_edge = []
        all_noise = []
        all_vignette = []

        for ts, frame in self.frames:
            lum_stats = analyze_luminance_stats(frame)
            color_mat = analyze_color_matrix(frame)
            sat = analyze_saturation(frame)
            edge = analyze_edges(frame)
            noise = analyze_noise(frame)
            vig = analyze_vignette(frame)

            all_lum_stats.append(lum_stats)
            all_color_matrix.append(color_mat)
            all_saturation.append(sat)
            all_edge.append(edge)
            all_noise.append(noise)
            all_vignette.append(vig)

        avg_lum = _average_dicts(all_lum_stats)
        avg_color = _average_dicts(all_color_matrix)
        avg_sat = _average_dicts(all_saturation)
        avg_edge = _average_dicts(all_edge)
        avg_noise = _average_dicts(all_noise)
        avg_vig = _average_dicts(all_vignette)

        ref = compute_dynamic_reference(self.frames, all_lum_stats, all_color_matrix,
                                         all_saturation, all_edge, all_noise, all_vignette)

        hist_params = estimate_histogram_parameters(
            {"mean": ref["mean_luminance"], "std": ref["luminance_std"],
             "p25": ref["p25"], "p75": ref["p75"], "p01": ref["p01"], "p99": ref["p99"],
             "top_10pct_mean": ref["top_10pct_mean"], "bottom_10pct_mean": ref["bottom_10pct_mean"],
             "min": ref["min"]},
            avg_lum,
        )
        color_params = estimate_color_parameters(
            {"g_r_ratio_deviation": ref.get("g_r_ratio_deviation", 0.0), "r_b_ratio": ref.get("r_b_ratio", 1.0)},
            avg_color,
        )
        sat_params = estimate_saturation_parameters(
            {"mean_saturation": ref["mean_saturation"],
             "low_sat_energy": ref.get("low_sat_energy", 0.5),
             "mid_sat_energy": ref.get("mid_sat_energy", 0.5),
             "high_sat_energy": ref.get("high_sat_energy", 0.05)},
            avg_sat,
        )

        lap_var_ratio = avg_edge["laplacian_variance"] / max(ref["laplacian_variance"], 1)
        adjustments_raw = {
            "brightness": hist_params.get("brightness", 0),
            "contrast": hist_params.get("contrast", 0),
            "saturation": sat_params.get("saturation", 0),
            "exposure": hist_params.get("exposure", 0),
            "highlights": hist_params.get("highlights", 0),
            "shadows": hist_params.get("shadows", 0),
            "whites": hist_params.get("whites", 0),
            "blacks": hist_params.get("blacks", 0),
            "temperature": round(color_params.get("temperature", 0), 0),
            "tint": round(color_params.get("tint", 0), 0),
            "vibrance": round(sat_params.get("vibrance", 0), 0),
            "sharpness": round(_map_from_ratio(lap_var_ratio, 0.5, 2.5, 0, 100), 0),
        }
        adjustments = adjustments_raw
        analysis["adjustments"] = adjustments

        all_detected = classify_filters(avg_lum, avg_color, avg_sat, avg_edge, avg_noise, avg_vig, ref)
        analysis["filters"] = [d for d in all_detected if d.get("type") != "effect"]
        analysis["effects"] = [d for d in all_detected if d.get("type") == "effect"]

        transitions = detect_transitions(self.frames, [s["start"] for s in shots], self.fps)
        analysis["transitions"] = transitions

        timeline = self._build_timeline(all_lum_stats, all_color_matrix, all_saturation, all_edge, shots, transitions)
        analysis["timeline"] = timeline

        analysis["summary"] = self._build_summary(adjustments, analysis["filters"])

        return analysis

    def _get_video_info(self) -> Dict:
        filename = os.path.basename(self.video_path)
        return {
            "filename": filename,
            "duration_seconds": round(self.duration, 2),
            "fps": round(self.fps, 2),
            "width": self.width,
            "height": self.height,
            "total_frames_analyzed": len(self.frames),
            "aspect_ratio": f"{self.width}:{self.height}",
        }

    def _build_timeline(
        self,
        all_lum: List[Dict],
        all_color: List[Dict],
        all_sat: List[Dict],
        all_edge: List[Dict],
        shots: List[Dict],
        transitions: List[Dict],
    ) -> List[Dict]:
        timeline = []
        segment_duration = self.duration / max(len(self.frames), 1)

        def _find_transition(ts: float) -> Dict:
            for t in transitions:
                if abs(t["time"] - ts) < 0.3:
                    return t
            return None

        for i, (ts, frame) in enumerate(self.frames):
            entry = {
                "time": round(ts, 2),
                "frame_index": i,
            }

            if i < len(all_lum):
                lum = all_lum[i]
                entry["mean_brightness"] = round(lum["mean"], 1)
                entry["contrast_level"] = round(lum["std"], 1)

            if i < len(all_color):
                cm = all_color[i]
                entry["temperature_shift"] = round((cm["r_b_ratio"] - 1.0) * 50, 1)

            if i < len(all_sat):
                s = all_sat[i]
                entry["saturation_level"] = round(s["mean_saturation"] * 100, 1)

            tr = _find_transition(ts)
            if tr:
                entry["transition"] = tr

            for si, shot in enumerate(shots):
                if shot["start"] <= ts <= shot.get("end", ts):
                    entry["shot_index"] = si
                    break

            timeline.append(entry)

        return timeline

    def _build_summary(self, adjustments: Dict, filters: List[Dict]) -> Dict:
        significant_adjustments = {k: v for k, v in adjustments.items() if abs(v) > 5}
        applied_filters = [f for f in filters if f.get("confidence", 0) > 40]

        return {
            "total_significant_adjustments": len(significant_adjustments),
            "adjustments_list": significant_adjustments,
            "filters_detected": [f["name"] for f in applied_filters],
            "total_filters": len(applied_filters),
            "estimated_edits_count": len(significant_adjustments) + len(applied_filters),
        }

    def get_representative_frame(self, timestamp: float) -> Optional[np.ndarray]:
        closest = min(self.frames, key=lambda f: abs(f[0] - timestamp))
        if abs(closest[0] - timestamp) < 1.0:
            return closest[1]
        return None

    def get_all_frames(self) -> List[Tuple[float, np.ndarray]]:
        return self.frames

def _average_dicts(dicts: List[Dict]) -> Dict:
    if not dicts:
        return {}
    result = {}
    keys = dicts[0].keys()
    for k in keys:
        vals = [d[k] for d in dicts if k in d and isinstance(d[k], (int, float))]
        if vals:
            result[k] = float(np.mean(vals))
        else:
            result[k] = dicts[0][k]
    return result

def _map_from_ratio(ratio: float, in_min: float, in_max: float, out_min: float, out_max: float) -> float:
    ratio = max(in_min, min(in_max, ratio))
    t = (ratio - in_min) / (in_max - in_min + 1e-8)
    result = out_min + t * (out_max - out_min)
    return max(out_min, min(out_max, result))

def _load_sample_frames(video_path: str, max_frames: int = 15, resize: int = 360) -> Tuple[List[Tuple[float, np.ndarray]], float, int, int]:
    import cv2
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Could not open video: {video_path}")
    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps <= 0 or fps > 1000:
        fps = 30.0
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    step = max(1, total // max_frames) if total > 0 else 1
    frames = []
    idx = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if idx % step == 0:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w = rgb.shape[:2]
            if max(h, w) > resize:
                scale = resize / max(h, w)
                rgb = cv2.resize(rgb, (0, 0), fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
            frames.append((idx / fps, rgb))
            if len(frames) >= max_frames:
                break
        idx += 1
    cap.release()
    return frames, fps, width, height

def _load_aligned_frames(orig_path: str, edit_path: str, max_frames: int = 30) -> Tuple[List[Tuple[float, np.ndarray]], List[Tuple[float, np.ndarray]], float, float, int, int, int, int]:
    import cv2

    def _open(path):
        cap = cv2.VideoCapture(path)
        if not cap.isOpened():
            raise ValueError(f"Could not open video: {path}")
        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps <= 0 or fps > 1000:
            fps = 30.0
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        return cap, fps, total, w, h

    cap_o, fps_o, total_o, ow, oh = _open(orig_path)
    cap_e, fps_e, total_e, ew, eh = _open(edit_path)

    dur_o = total_o / fps_o if total_o > 0 else 0
    dur_e = total_e / fps_e if total_e > 0 else 0
    dur_min = min(dur_o, dur_e)

    timestamps = []
    step = dur_min / max_frames
    for i in range(max_frames):
        timestamps.append(i * step)

    orig_out, edit_out = [], []
    for t in timestamps:
        frame_idx_o = int(t * fps_o)
        cap_o.set(cv2.CAP_PROP_POS_FRAMES, frame_idx_o)
        ret_o, f_o = cap_o.read()
        if not ret_o:
            continue
        rgb_o = cv2.cvtColor(f_o, cv2.COLOR_BGR2RGB)

        frame_idx_e = int(t * fps_e)
        cap_e.set(cv2.CAP_PROP_POS_FRAMES, frame_idx_e)
        ret_e, f_e = cap_e.read()
        if not ret_e:
            continue
        rgb_e = cv2.cvtColor(f_e, cv2.COLOR_BGR2RGB)

        orig_out.append((t, rgb_o))
        edit_out.append((t, rgb_e))

    cap_o.release()
    cap_e.release()
    return orig_out, edit_out, fps_o, fps_e, ow, oh, ew, eh

def compare_videos(original_path: str, edited_path: str) -> Dict:
    from color_analysis import (
        analyze_luminance_stats, analyze_color_matrix, analyze_saturation,
        analyze_edges, analyze_noise, analyze_vignette,
        estimate_histogram_parameters, estimate_color_parameters,
        estimate_saturation_parameters,
    )
    from filter_classifier import classify_filters

    orig_frames, edit_frames, orig_fps, edit_fps, orig_w, orig_h, edit_w, edit_h = _load_aligned_frames(
        original_path, edited_path, max_frames=30
    )

    if len(orig_frames) == 0 or len(edit_frames) == 0:
        missing = "original" if len(orig_frames) == 0 else "edited"
        raise ValueError(f"Could not extract any frames from the {missing} video.")

    def _process(frames):
        lum = [analyze_luminance_stats(f) for _, f in frames]
        col = [analyze_color_matrix(f) for _, f in frames]
        sat = [analyze_saturation(f) for _, f in frames]
        edg = [analyze_edges(f) for _, f in frames]
        noi = [analyze_noise(f) for _, f in frames]
        vig = [analyze_vignette(f) for _, f in frames]
        return _average_dicts(lum), _average_dicts(col), _average_dicts(sat), _average_dicts(edg), _average_dicts(noi), _average_dicts(vig)

    orig_lum, orig_col, orig_sat, orig_edg, orig_noi, _ = _process(orig_frames)
    edit_lum, edit_col, edit_sat, edit_edg, edit_noi, _ = _process(edit_frames)

    ref = {
        "mean": orig_lum["mean"], "std": orig_lum["std"],
        "mean_luminance": orig_lum["mean"], "luminance_std": orig_lum["std"],
        "p25": orig_lum.get("p25", orig_lum["mean"] - orig_lum["std"]),
        "p75": orig_lum.get("p75", orig_lum["mean"] + orig_lum["std"]),
        "p01": orig_lum.get("p01", 0), "p99": orig_lum.get("p99", 255),
        "top_10pct_mean": orig_lum.get("top_10pct_mean", orig_lum["mean"] + orig_lum["std"] * 1.5),
        "bottom_10pct_mean": orig_lum.get("bottom_10pct_mean", orig_lum["mean"] - orig_lum["std"] * 0.8),
        "min": orig_lum.get("min", 0),
    }

    hist_params = estimate_histogram_parameters(ref, edit_lum)
    color_params = estimate_color_parameters(
        {"g_r_ratio_deviation": orig_col.get("g_r_ratio_deviation", 0.0),
         "r_b_ratio": orig_col.get("r_b_ratio", 1.0)}, edit_col,
    )
    sat_params = estimate_saturation_parameters(
        {"mean_saturation": orig_sat["mean_saturation"],
         "low_sat_energy": orig_sat.get("low_sat_energy", 0.5),
         "mid_sat_energy": orig_sat.get("mid_sat_energy", 0.5),
         "high_sat_energy": orig_sat.get("high_sat_energy", 0.05)}, edit_sat,
    )

    adjustments_raw = {
        "brightness": hist_params.get("brightness", 0),
        "contrast": hist_params.get("contrast", 0),
        "saturation": sat_params.get("saturation", 0),
        "exposure": hist_params.get("exposure", 0),
        "highlights": hist_params.get("highlights", 0),
        "shadows": hist_params.get("shadows", 0),
        "whites": hist_params.get("whites", 0),
        "blacks": hist_params.get("blacks", 0),
        "temperature": round(color_params.get("temperature", 0), 0),
        "tint": round(color_params.get("tint", 0), 0),
        "vibrance": round(sat_params.get("vibrance", 0), 0),
        "sharpness": round(_map_from_ratio(edit_edg["laplacian_variance"] / max(orig_edg.get("laplacian_variance", 100), 1), 0.5, 2.5, 0, 100), 0),
    }
    adjustments = _compensate_interactions(adjustments_raw)

    filters_ref = {**ref,
        "mean_saturation": orig_sat["mean_saturation"],
        "noise_std": orig_noi["noise_std"],
        "laplacian_variance": orig_edg["laplacian_variance"],
        "low_sat_energy": orig_sat.get("low_sat_energy", 0.5),
        "mid_sat_energy": orig_sat.get("mid_sat_energy", 0.5),
        "high_sat_energy": orig_sat.get("high_sat_energy", 0.05),
    }
    filters_detected = classify_filters(edit_lum, edit_col, edit_sat, edit_edg, edit_noi, {}, filters_ref)

    return {
        "adjustments": adjustments,
        "filters": [d for d in filters_detected if d.get("type") != "effect"],
        "effects": [d for d in filters_detected if d.get("type") == "effect"],
        "video_info": {
            "original": {"width": orig_w, "height": orig_h, "fps": round(orig_fps, 2), "frames_analyzed": len(orig_frames)},
            "edited": {"width": edit_w, "height": edit_h, "fps": round(edit_fps, 2), "frames_analyzed": len(edit_frames)},
        },
    }

def _compensate_interactions(adj: Dict[str, float]) -> Dict[str, float]:
    out = dict(adj)
    for k in out:
        if k == "exposure":
            out[k] = max(-5, min(5, out[k]))
        elif k == "vibrance":
            out[k] = max(-100, min(100, out[k]))
        elif k == "sharpness":
            out[k] = max(0, min(100, out[k]))
        else:
            out[k] = max(-100, min(100, out[k]))
    return out
