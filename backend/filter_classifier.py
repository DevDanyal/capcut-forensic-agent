from typing import Dict, List, Optional

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

    mean_diff = luminance_stats["mean"] - (reference_stats.get("mean_luminance", 118))
    params["brightness"] = _map_to_percent(mean_diff, -50, 50, -100, 100)

    std_ratio = luminance_stats["std"] / (reference_stats.get("luminance_std", 58) + 1e-8)
    params["contrast"] = _map_to_percent(std_ratio, 0.5, 2.0, -100, 100)

    sat_ratio = saturation["mean_saturation"] / (reference_stats.get("mean_saturation", 0.22) + 1e-8)
    params["saturation"] = _map_to_percent(sat_ratio, 0.0, 2.0, -100, 100)

    r_b_ratio = color_matrix["r_b_ratio"]
    ref_r_b = reference_stats.get("r_b_ratio", 1.0)
    params["temperature"] = max(-100, min(100, (r_b_ratio - ref_r_b) * 200))

    g_r_dev = color_matrix["g_r_ratio_deviation"]
    ref_g_r_dev = reference_stats.get("g_r_ratio_deviation", 0.0)
    params["tint"] = max(-100, min(100, (g_r_dev - ref_g_r_dev) * 300))

    p25 = luminance_stats.get("p25", luminance_stats["mean"] - luminance_stats["std"])
    p75 = luminance_stats.get("p75", luminance_stats["mean"] + luminance_stats["std"])
    ref_p25 = reference_stats.get("p25", reference_stats["mean_luminance"] - reference_stats["luminance_std"])
    ref_p75 = reference_stats.get("p75", reference_stats["mean_luminance"] + reference_stats["luminance_std"])

    shadows_diff = p25 - ref_p25
    params["shadows"] = _map_to_percent(shadows_diff, -50, 60, -100, 100)

    highlights_diff = p75 - ref_p75
    params["highlights"] = _map_to_percent(highlights_diff, -60, 50, -100, 100)

    p01 = luminance_stats.get("p01", luminance_stats["mean"] - luminance_stats["std"] * 1.5)
    p99 = luminance_stats.get("p99", luminance_stats["mean"] + luminance_stats["std"] * 1.5)
    ref_p01 = reference_stats.get("p01", reference_stats["mean_luminance"] - reference_stats["luminance_std"] * 1.2)
    ref_p99 = reference_stats.get("p99", reference_stats["mean_luminance"] + reference_stats["luminance_std"] * 1.2)

    params["whites"] = _map_to_percent(p99 - ref_p99, -30, 30, -100, 100)
    params["blacks"] = _map_to_percent(p01 - ref_p01, -20, 20, -100, 100)

    params["exposure"] = _map_to_percent(mean_diff, -60, 60, -5, 5)

    ref_min = reference_stats.get("min", reference_stats.get("p01", 5))
    if luminance_stats.get("min", 0) > ref_min + 5:
        black_lift = luminance_stats["min"] - ref_min
        params["fade_black_lift"] = _map_to_percent(black_lift, 0, 50, 0, 100)

    lap_var_ratio = edge_analysis["laplacian_variance"] / (reference_stats.get("laplacian_variance", 100) + 1e-8)
    params["sharpness"] = _map_to_percent(lap_var_ratio, 0.5, 2.5, 0, 100)

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
    brightness = params.get("brightness", 0)

    if black_lift > 20 and sat < -5:
        detected.append({
            "name": "Fade",
            "type": "filter",
            "parameters": {
                "intensity": round(min(100, black_lift * 1.2), 0),
                "fade_amount": round(black_lift / 50 * 100, 0),
            },
            "confidence": 70,
        })

    if temp > 15 and sat < -5 and brightness > 5:
        detected.append({
            "name": "Vintage",
            "type": "filter",
            "parameters": {
                "warmth": round(temp, 0),
                "intensity": round(min(100, (temp + abs(sat)) / 2), 0),
            },
            "confidence": 65,
        })

    r_b = color_matrix["r_b_ratio"]
    r_g = color_matrix["r_g_ratio"]
    skin_ratio = color_matrix.get("skin_ratio", 0)

    teal_orange = False
    teal_confidence = 0
    diff_bg = color_matrix.get("diff_bg", 0)
    if r_b > 1.15 and r_g > 1.05 and diff_bg < -5:
        teal_orange = True
        teal_confidence = 60 if skin_ratio > 0.03 else 50
    if teal_orange:
        detected.append({
            "name": "Teal & Orange",
            "type": "filter",
            "parameters": {
                "intensity": round(min(100, (r_b - 1.0) * 100), 0),
                "teal_shadows": round(abs(diff_bg) / 2, 0),
            },
            "confidence": teal_confidence,
        })

    if luminance_stats.get("std", 58) > luminance_stats.get("mean", 118) * 0.8 and contrast > 30 and sat < -5:
        detected.append({
            "name": "Dramatic",
            "type": "filter",
            "parameters": {
                "intensity": round(min(100, (contrast + abs(sat)) / 2), 0),
            },
            "confidence": 60,
        })

    if contrast < -15 and sat < -15 and brightness > 5:
        detected.append({
            "name": "Pastel",
            "type": "filter",
            "parameters": {
                "intensity": round(min(100, abs(contrast) * 0.5 + abs(sat) * 0.5), 0),
            },
            "confidence": 55,
        })

    ref_sat = 0.22
    desaturation = 1.0 - saturation["mean_saturation"] / ref_sat if saturation["mean_saturation"] < ref_sat * 0.6 else 0.0
    if desaturation > 0.6:
        detected.append({
            "name": "Noir",
            "type": "filter",
            "parameters": {
                "intensity": round(desaturation * 100, 0),
            },
            "confidence": 70,
        })

    if edge_analysis:
        lap_var = edge_analysis.get("laplacian_variance", 100.0)
        ref_lap_var = 100.0
        lap_var_ratio = lap_var / (ref_lap_var + 1e-8)
        high_freq_edge = edge_analysis.get("high_freq_edge_ratio", 0)

        if lap_var_ratio > 1.5 and contrast > 15:
            detected.append({
                "name": "HDR Look",
                "type": "effect",
                "parameters": {
                    "intensity": round(min(100, (lap_var_ratio - 1.0) * 50), 0),
                },
                "confidence": 50,
            })

        if high_freq_edge > 0.25 and lap_var_ratio > 1.3:
            bloom = min(100, (high_freq_edge - 0.25) * 120 + (lap_var_ratio - 1.0) * 25)
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
