import numpy as np
from typing import List, Dict, Tuple

def detect_shots(frames: List[Tuple[float, np.ndarray]], threshold: float = 30.0) -> List[Dict]:
    shots = []
    if len(frames) < 2:
        if frames:
            shots.append({"start": frames[0][0], "end": frames[-1][0], "type": "scene"})
        return shots

    shot_boundaries = [frames[0][0]]
    for i in range(1, len(frames)):
        diff = frame_difference(frames[i-1][1], frames[i][1])
        if diff > threshold:
            shot_boundaries.append(frames[i][0])

    for t in shot_boundaries:
        shots.append({"start": t, "end": None, "type": "scene"})

    for i in range(len(shots) - 1):
        shots[i]["end"] = shots[i + 1]["start"]
    if shots and shots[-1]["end"] is None:
        shots[-1]["end"] = frames[-1][0]

    return shots

def _ssim_approx(img1: np.ndarray, img2: np.ndarray) -> float:
    C1 = (0.01 * 255) ** 2
    C2 = (0.03 * 255) ** 2
    mu1, mu2 = float(np.mean(img1)), float(np.mean(img2))
    sigma1_sq = float(np.var(img1))
    sigma2_sq = float(np.var(img2))
    sigma12 = float(np.mean((img1 - mu1) * (img2 - mu2)))
    num = (2 * mu1 * mu2 + C1) * (2 * sigma12 + C2)
    den = (mu1 ** 2 + mu2 ** 2 + C1) * (sigma1_sq + sigma2_sq + C2)
    return num / (den + 1e-8)

def frame_difference(frame1: np.ndarray, frame2: np.ndarray) -> float:
    import cv2

    g1 = cv2.cvtColor(frame1, cv2.COLOR_RGB2GRAY)
    g2 = cv2.cvtColor(frame2, cv2.COLOR_RGB2GRAY)

    h1 = cv2.calcHist([g1], [0], None, [64], [0, 256])
    h2 = cv2.calcHist([g2], [0], None, [64], [0, 256])
    cv2.normalize(h1, h1, 0, 1, cv2.NORM_MINMAX)
    cv2.normalize(h2, h2, 0, 1, cv2.NORM_MINMAX)
    hist_diff = cv2.compareHist(h1, h2, cv2.HISTCMP_CHISQR)

    s = _ssim_approx(g1, g2)
    ssim_diff = (1.0 - s) * 100

    mean_diff = float(np.mean(np.abs(g1.astype(float) - g2.astype(float))))

    combined = hist_diff * 0.3 + ssim_diff * 0.5 + mean_diff * 0.2
    return combined

def detect_transitions(frames: List[Tuple[float, np.ndarray]], shot_boundaries: List[float], fps: float = 30) -> List[Dict]:
    transitions = []
    if len(frames) < 4:
        return transitions

    diffs = []
    for i in range(1, len(frames)):
        d = frame_difference(frames[i-1][1], frames[i][1])
        diffs.append((frames[i][0], d))

    window = max(1, int(fps * 0.3))
    for i in range(window, len(diffs) - window):
        local_mean = np.mean([d[1] for d in diffs[i-window:i+window]])
        peak = diffs[i][1]
        if peak > local_mean * 2.5 and peak > 15:
            is_adjacent_to_shot = any(abs(diffs[i][0] - sb) < 0.5 for sb in shot_boundaries)
            if not is_adjacent_to_shot:
                transitions.append({
                    "time": diffs[i][0],
                    "type": "dissolve" if peak < 50 else "cut",
                    "strength": float(min(100, peak / 2)),
                })

    return transitions

def detect_effects_in_transition(transition_frames: List[Tuple[float, np.ndarray]]) -> Dict:
    if len(transition_frames) < 3:
        return {}

    first = transition_frames[0][1]
    last = transition_frames[-1][1]

    diff = np.mean(np.abs(last.astype(float) - first.astype(float)))
    return {"pixel_change_pct": float(min(100, diff / 2.55))}
