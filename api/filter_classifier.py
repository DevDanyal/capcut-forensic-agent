import numpy as np
from typing import Dict, List, Tuple, Optional
from reference_card import FILTER_SIGNATURES

def classify_filters(
    luminance_stats: Dict,
    color_matrix: Dict,
    saturation: Dict,
    edge_analysis: Dict,
    noise_analysis: Dict,
    vignette_analysis: Dict,
    reference_stats: Dict,
) -> List[Dict]:
    detected_filters = []

    params = {}

    mean_diff = luminance_stats["mean"] - (reference_stats.get("mean_luminance", 128))
    params["brightness"] = _map_to_percent(mean_diff, -64, 64, -100, 100)

    std_ratio = luminance_stats["std"] / (reference_stats.get("luminance_std", 74) + 1e-8)
    params["contrast"] = _map_to_percent(std_ratio, 0.3, 2.5, -100, 100)

    sat_ratio = saturation["mean_saturation"] / (reference_stats.get("mean_saturation", 0.2) + 1e-8)
    params["saturation"] = _map_to_percent(sat_ratio, 0.0, 3.0, -100, 100)

    r_b_ratio = color_matrix["r_b_ratio"]
    temp_shift = (r_b_ratio - 1.0) * 50
    params["temperature"] = max(-100, min(100, temp_shift))

    g_r_dev = color_matrix["g_r_ratio_deviation"]
    tint_shift = g_r_dev * 100
    params["tint"] = max(-100, min(100, tint_shift))

    p25 = luminance_stats.get("p25", 64)
    p75 = luminance_stats.get("p75", 192)
    ref_p25 = reference_stats.get("p25", 64)
    ref_p75 = reference_stats.get("p75", 192)

    shadows_diff = p25 - ref_p25
    params["shadows"] = _map_to_percent(shadows_diff, -64, 64, -100, 100)

    highlights_diff = p75 - ref_p75
    params["highlights"] = _map_to_percent(highlights_diff, -64, 64, -100, 100)

    p01 = luminance_stats.get("p01", 0)
    p99 = luminance_stats.get("p99", 255)
    ref_p01 = reference_stats.get("p01", 0)
    ref_p99 = reference_stats.get("p99", 255)

    params["whites"] = _map_to_percent(p99 - ref_p99, -30, 30, -100, 100)
    params["blacks"] = _map_to_percent(p01 - ref_p01, -30, 30, -100, 100)

    params["exposure"] = params["brightness"] * 0.05

    if luminance_stats.get("min", 0) > 15:
        black_lift = luminance_stats["min"]
        params["fade_black_lift"] = _map_to_percent(black_lift, 0, 50, 0, 100)

    lap_var_ratio = edge_analysis["laplacian_variance"] / (reference_stats.get("laplacian_variance", 100) + 1e-8)
    params["sharpness"] = _map_to_percent(lap_var_ratio, 0.3, 3.0, -100, 100)

    noise_std_ratio = noise_analysis["noise_std"] / (reference_stats.get("noise_std", 0.005) + 1e-8)
    params["grain"] = _map_to_percent(noise_std_ratio, 0.0, 10.0, 0, 100)

    center_vs_corner = vignette_analysis.get("center_vs_corner_ratio", 1.0)
    if center_vs_corner > 1.05:
        vignette_strength = (center_vs_corner - 1.0) * 200
        params["vignette"] = max(0, min(100, vignette_strength))

    basic_adjustments = {
        "brightness": params.get("brightness", 0),
        "contrast": params.get("contrast", 0),
        "saturation": params.get("saturation", 0),
        "exposure": params.get("exposure", 0),
        "highlights": params.get("highlights", 0),
        "shadows": params.get("shadows", 0),
        "whites": params.get("whites", 0),
        "blacks": params.get("blacks", 0),
        "temperature": params.get("temperature", 0),
        "tint": params.get("tint", 0),
        "sharpness": params.get("sharpness", 0),
    }

    detected_filters.append({
        "name": "Adjustments",
        "type": "adjustments",
        "parameters": basic_adjustments,
        "confidence": 85,
    })

    style_filters = _detect_style_filters(params, color_matrix, saturation, luminance_stats, edge_analysis, noise_analysis)
    detected_filters.extend(style_filters)

    if params.get("grain", 0) > 8:
        detected_filters.append({
            "name": "Grain",
            "type": "effect",
            "parameters": {"intensity": round(params["grain"], 0)},
            "confidence": min(90, 50 + params["grain"] * 0.5),
        })

    if params.get("vignette", 0) > 10:
        detected_filters.append({
            "name": "Vignette",
            "type": "effect",
            "parameters": {"intensity": round(params["vignette"], 0)},
            "confidence": min(90, 50 + params["vignette"] * 0.5),
        })

    return detected_filters

def _detect_style_filters(params: Dict, color_matrix: Dict, saturation: Dict, luminance_stats: Dict, edge_analysis: Dict = None, noise_analysis: Dict = None) -> List[Dict]:
    detected = []

    black_lift = params.get("fade_black_lift", 0)
    contrast = params.get("contrast", 0)
    sat = params.get("saturation", 0)
    temp = params.get("temperature", 0)
    grain = params.get("grain", 0)

    if black_lift > 20 and contrast < -10 and sat < -10:
        detected.append({
            "name": "Fade",
            "type": "filter",
            "parameters": {
                "intensity": round(min(100, black_lift * 1.5), 0),
                "fade_amount": round(black_lift / 50 * 100, 0),
            },
            "confidence": 70,
        })

    if temp > 15 and sat > 15 and grain > 5:
        detected.append({
            "name": "Vintage",
            "type": "filter",
            "parameters": {
                "warmth": round(temp, 0),
                "intensity": round((temp + sat + grain) / 6, 0),
            },
            "confidence": 65,
        })

    r_b = color_matrix["r_b_ratio"]
    r_g = color_matrix["r_g_ratio"]
    skin_ratio = color_matrix.get("skin_ratio", 0)
    skin_tone = color_matrix.get("skin_tone_isolation", 0)

    teal_orange = False
    teal_confidence = 0
    if r_b > 1.25 and r_g > 1.1 and color_matrix.get("diff_bg", 0) < -8:
        if skin_ratio > 0.05:
            teal_orange = True
            teal_confidence = 65
        elif abs(skin_tone) < 5:
            teal_orange = True
            teal_confidence = 50
    if teal_orange:
        detected.append({
            "name": "Teal & Orange",
            "type": "filter",
            "parameters": {
                "intensity": round(min(100, (r_b - 1.0) * 80), 0),
                "teal_shadows": round(abs(color_matrix.get("diff_bg", 0)) / 2, 0),
            },
            "confidence": teal_confidence,
        })

    if luminance_stats.get("std", 74) > 100 and contrast > 40 and sat < -5:
        detected.append({
            "name": "Dramatic",
            "type": "filter",
            "parameters": {
                "intensity": round(min(100, (contrast + abs(sat)) / 2), 0),
            },
            "confidence": 65,
        })

    if contrast < -20 and sat < -20 and params.get("brightness", 0) > 10:
        detected.append({
            "name": "Pastel",
            "type": "filter",
            "parameters": {
                "intensity": round(min(100, abs(contrast) * 0.5 + abs(sat) * 0.5), 0),
            },
            "confidence": 55,
        })

    desaturation = 1.0 - saturation["mean_saturation"] / 0.2 if saturation["mean_saturation"] < 0.15 else 0.0
    if desaturation > 0.7:
        detected.append({
            "name": "Noir",
            "type": "filter",
            "parameters": {
                "intensity": round(desaturation * 100, 0),
                "desaturation": round(desaturation * 100, 0),
            },
            "confidence": 75,
        })

    if edge_analysis:
        lap_var = edge_analysis.get("laplacian_variance", 100.0)
        ref_lap_var = 100.0
        lap_var_ratio = lap_var / (ref_lap_var + 1e-8)
        high_freq_edge = edge_analysis.get("high_freq_edge_ratio", 0)

        if lap_var_ratio > 1.8 and contrast > 20:
            detected.append({
                "name": "HDR Look",
                "type": "effect",
                "parameters": {
                    "intensity": round(min(100, (lap_var_ratio - 1.0) * 60), 0),
                },
                "confidence": 50,
            })

        if high_freq_edge > 0.3 and lap_var_ratio > 1.5:
            bloom = min(100, (high_freq_edge - 0.3) * 150 + (lap_var_ratio - 1.0) * 30)
            if bloom > 10:
                detected.append({
                    "name": "Glow",
                    "type": "effect",
                    "parameters": {"intensity": round(bloom, 0)},
                    "confidence": 55,
                })

    return detected

def _map_to_percent(val: float, in_min: float, in_max: float, out_min: float, out_max: float) -> float:
    if abs(in_max - in_min) < 1e-8:
        return 0.0
    t = (val - in_min) / (in_max - in_min)
    result = out_min + t * (out_max - out_min)
    return round(max(out_min, min(out_max, result)), 0)

def estimate_confidence(filter_name: str, params: Dict, frame_count: int) -> float:
    if filter_name == "Adjustments":
        return 85.0
    base = 50.0
    non_zero = sum(1 for v in params.values() if abs(v) > 5)
    base += non_zero * 5
    base += min(frame_count / 30, 20)
    return min(95, base)
