import numpy as np
from typing import Dict, Tuple, Optional, List

def rgb_to_luminance(frame: np.ndarray) -> np.ndarray:
    return 0.299 * frame[:, :, 0] + 0.587 * frame[:, :, 1] + 0.114 * frame[:, :, 2]

def rgb_to_hsv(frame: np.ndarray) -> np.ndarray:
    import cv2
    return cv2.cvtColor(frame, cv2.COLOR_RGB2HSV)

def analyze_luminance_stats(frame: np.ndarray) -> Dict:
    lum = rgb_to_luminance(frame)
    mean_lum = float(np.mean(lum))
    std_lum = float(np.std(lum))
    hist, _ = np.histogram(lum, bins=256, range=(0, 255))
    hist = hist.astype(float) / hist.sum()

    cumsum = np.cumsum(hist)
    p01 = float(np.searchsorted(cumsum, 0.01) / 255.0 * 100.0)
    p10 = float(np.searchsorted(cumsum, 0.10) / 255.0 * 100.0)
    p25 = float(np.searchsorted(cumsum, 0.25) / 255.0 * 100.0)
    p50 = float(np.searchsorted(cumsum, 0.50) / 255.0 * 100.0)
    p75 = float(np.searchsorted(cumsum, 0.75) / 255.0 * 100.0)
    p90 = float(np.searchsorted(cumsum, 0.90) / 255.0 * 100.0)
    p99 = float(np.searchsorted(cumsum, 0.99) / 255.0 * 100.0)
    bottom_10pct_mean = float(np.mean(lum[lum <= np.percentile(lum, 10)])) if np.any(lum <= np.percentile(lum, 10)) else 0.0
    top_10pct_mean = float(np.mean(lum[lum >= np.percentile(lum, 90)])) if np.any(lum >= np.percentile(lum, 90)) else 255.0

    return {
        "mean": mean_lum,
        "std": std_lum,
        "p01": p01,
        "p10": p10,
        "p25": p25,
        "p50": p50,
        "p75": p75,
        "p90": p90,
        "p99": p99,
        "bottom_10pct_mean": bottom_10pct_mean,
        "top_10pct_mean": top_10pct_mean,
        "min": float(np.min(lum)),
        "max": float(np.max(lum)),
    }

def analyze_color_matrix(frame: np.ndarray) -> Dict:
    r, g, b = frame[:,:,0].astype(float), frame[:,:,1].astype(float), frame[:,:,2].astype(float)

    r_mean = float(np.mean(r))
    g_mean = float(np.mean(g))
    b_mean = float(np.mean(b))

    r_b_ratio = r_mean / (b_mean + 1e-8)
    g_r_ratio_deviation = g_mean / (r_mean + 1e-8) - 0.587 / 0.299
    g_b_ratio = g_mean / (b_mean + 1e-8)
    r_g_ratio = r_mean / (g_mean + 1e-8)

    diff_rb = r_mean - b_mean
    diff_rg = r_mean - g_mean
    diff_bg = b_mean - g_mean

    r_std = float(np.std(r))
    g_std = float(np.std(g))
    b_std = float(np.std(b))

    skin_mask = detect_skin_region(frame)
    skin_mean = np.mean(r[skin_mask]) - np.mean(b[skin_mask]) if np.any(skin_mask) else 0.0

    return {
        "r_mean": r_mean,
        "g_mean": g_mean,
        "b_mean": b_mean,
        "r_b_ratio": float(r_b_ratio),
        "g_r_ratio_deviation": float(g_r_ratio_deviation),
        "g_b_ratio": float(g_b_ratio),
        "r_g_ratio": float(r_g_ratio),
        "diff_rb": float(diff_rb),
        "diff_rg": float(diff_rg),
        "diff_bg": float(diff_bg),
        "r_std": r_std,
        "g_std": g_std,
        "b_std": b_std,
        "skin_tone_isolation": float(skin_mean),
        "skin_ratio": float(np.mean(skin_mask)),
    }

def analyze_saturation(frame: np.ndarray) -> Dict:
    hsv = rgb_to_hsv(frame)
    sat = hsv[:,:,1].astype(float)
    mean_sat = float(np.mean(sat))
    std_sat = float(np.std(sat))

    sat_hist, _ = np.histogram(sat, bins=256, range=(0, 255))
    sat_hist = sat_hist.astype(float) / sat_hist.sum()
    low_sat_energy = float(np.sum(sat_hist[:64]))
    high_sat_energy = float(np.sum(sat_hist[192:]))

    hue = hsv[:,:,0].astype(float)
    hue_std = float(np.std(hue))

    return {
        "mean_saturation": mean_sat / 255.0,
        "std_saturation": std_sat / 255.0,
        "low_sat_energy": low_sat_energy,
        "high_sat_energy": high_sat_energy,
        "hue_std": hue_std,
    }

def analyze_edges(frame: np.ndarray) -> Dict:
    import cv2
    gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY).astype(float)

    laplacian = cv2.Laplacian(gray, cv2.CV_64F)
    lap_var = float(np.var(laplacian))
    lap_mean = float(np.mean(np.abs(laplacian)))

    sobelx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
    sobely = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
    edge_mag = np.sqrt(sobelx**2 + sobely**2)
    edge_mean = float(np.mean(edge_mag))
    edge_std = float(np.std(edge_mag))

    high_freq_edge_ratio = float(np.mean(edge_mag > np.percentile(edge_mag, 90))) if np.any(edge_mag > 0) else 0.0

    return {
        "laplacian_variance": lap_var,
        "laplacian_mean_abs": lap_mean,
        "edge_mean": edge_mean,
        "edge_std": edge_std,
        "high_freq_edge_ratio": high_freq_edge_ratio,
    }

def analyze_noise(frame: np.ndarray, smooth_radius: int = 3) -> Dict:
    import cv2
    gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY).astype(float)
    smoothed = cv2.GaussianBlur(gray, (0, 0), smooth_radius)
    noise = gray - smoothed
    noise_std = float(np.std(noise))
    noise_mean = float(np.mean(np.abs(noise)))

    fft = np.fft.fft2(gray)
    fft_shift = np.fft.fftshift(fft)
    magnitude = np.abs(fft_shift)
    h, w = magnitude.shape
    cy, cx = h // 2, w // 2
    high_freq_mask = np.zeros_like(magnitude, dtype=bool)
    y, x = np.ogrid[:h, :w]
    radius = min(h, w) * 0.3
    high_freq_mask[(y - cy)**2 + (x - cx)**2 > radius**2] = True

    high_freq_energy = float(np.sum(magnitude[high_freq_mask]) / (np.sum(magnitude) + 1e-8))
    total_energy = float(np.sum(magnitude))

    return {
        "noise_std": noise_std / 255.0,
        "noise_mean_abs": noise_mean / 255.0,
        "high_freq_ratio": high_freq_energy,
        "total_freq_energy": total_energy,
    }

def analyze_vignette(frame: np.ndarray) -> Dict:
    gray = rgb_to_luminance(frame)
    h, w = gray.shape
    cy, cx = h / 2, w / 2
    yy, xx = np.ogrid[:h, :w]
    dist = np.sqrt((yy - cy)**2 + (xx - cx)**2)
    max_dist = np.sqrt(cy**2 + cx**2)
    dist_norm = dist / max_dist

    center_mask = dist_norm < 0.3
    corner_mask = dist_norm > 0.85

    if np.any(center_mask) and np.any(corner_mask):
        center_mean = float(np.mean(gray[center_mask]))
        corner_mean = float(np.mean(gray[corner_mask]))
        center_vs_corner = center_mean / (corner_mean + 1e-8)
        falloff = center_mean - corner_mean
        radial_brightness = []
        for r in np.linspace(0, 1, 20):
            ring_mask = (dist_norm >= r - 0.05) & (dist_norm < r + 0.05)
            if np.any(ring_mask):
                radial_brightness.append(float(np.mean(gray[ring_mask])))
            else:
                radial_brightness.append(None)
    else:
        center_vs_corner = 1.0
        falloff = 0.0
        radial_brightness = []

    return {
        "center_vs_corner_ratio": center_vs_corner,
        "falloff": float(falloff),
        "radial_brightness": radial_brightness,
    }

def detect_skin_region(frame: np.ndarray) -> np.ndarray:
    import cv2
    hsv = cv2.cvtColor(frame, cv2.COLOR_RGB2HSV)
    lower = np.array([0, 20, 60])
    upper = np.array([30, 150, 255])
    mask1 = cv2.inRange(hsv, lower, upper)
    lower2 = np.array([150, 20, 60])
    upper2 = np.array([179, 150, 255])
    mask2 = cv2.inRange(hsv, lower2, upper2)
    return (mask1 | mask2).astype(bool)

def estimate_histogram_parameters(ref_stats: Dict, cur_stats: Dict) -> Dict:
    def lerp(val, src_range, dst_range):
        t = (val - src_range[0]) / (src_range[1] - src_range[0] + 1e-8)
        return dst_range[0] + t * (dst_range[1] - dst_range[0])

    params = {}
    mean_diff = cur_stats["mean"] - ref_stats["mean"]
    params["brightness"] = lerp(mean_diff, (-70, 70), (-100, 100))

    std_ratio = cur_stats["std"] / (ref_stats["std"] + 1e-8)
    params["contrast"] = lerp(std_ratio, (0.2, 3.0), (-100, 100))

    shadows_diff = cur_stats["p25"] - ref_stats.get("p25", 64)
    params["shadows"] = lerp(shadows_diff, (-45, 45), (-100, 100))

    highlights_diff = cur_stats["p75"] - ref_stats.get("p75", 192)
    params["highlights"] = lerp(highlights_diff, (-45, 45), (-100, 100))

    whites_diff = cur_stats.get("p99", 255) - ref_stats.get("p99", 255)
    params["whites"] = lerp(whites_diff, (-25, 25), (-100, 100))

    blacks_diff = cur_stats.get("p01", 0) - ref_stats.get("p01", 0)
    params["blacks"] = lerp(blacks_diff, (-25, 25), (-100, 100))

    top_pct = cur_stats.get("top_10pct_mean", 255)
    ref_top = ref_stats.get("top_10pct_mean", 255)
    top_diff = top_pct - ref_top
    exposure_from_highlights = lerp(top_diff, (-50, 50), (-5, 5))
    params["exposure"] = exposure_from_highlights

    min_val = cur_stats.get("min", 0)
    ref_min = ref_stats.get("min", 0)
    if min_val > ref_min + 5:
        params["fade_black_lift"] = lerp(min_val - ref_min, (0, 50), (0, 100))

    return params

def estimate_color_parameters(ref_matrix: Dict, cur_matrix: Dict) -> Dict:
    params = {}

    r_b_ratio_cur = cur_matrix["r_b_ratio"]
    r_b_ratio_ref = 1.0
    temp_shift = (r_b_ratio_cur - r_b_ratio_ref) * 100
    params["temperature"] = max(-100, min(100, temp_shift))

    g_r_dev = cur_matrix["g_r_ratio_deviation"] - (ref_matrix.get("g_r_ratio_deviation", 0.0))
    tint_shift = g_r_dev * 150
    params["tint"] = max(-100, min(100, tint_shift))

    return params

def estimate_saturation_parameters(ref_sat: Dict, cur_sat: Dict) -> Dict:
    params = {}
    sat_ratio = cur_sat["mean_saturation"] / (ref_sat.get("mean_saturation", 0.2) + 1e-8)
    params["saturation"] = max(-100, min(100, (sat_ratio - 1.0) * 80))

    low_sat_ratio = cur_sat["low_sat_energy"] / (ref_sat.get("low_sat_energy", 0.5) + 1e-8)
    high_sat_ratio = cur_sat["high_sat_energy"] / (ref_sat.get("high_sat_energy", 0.05) + 1e-8)

    vibrance = 0.0
    if low_sat_ratio < 0.85 and sat_ratio > 1.05:
        vibrance = (1.0 - low_sat_ratio) * 120
    elif high_sat_ratio > 1.5 and sat_ratio > 1.1:
        vibrance = (high_sat_ratio - 1.0) * -60
    if vibrance > 0:
        params["vibrance"] = max(0, min(100, vibrance))

    return params
