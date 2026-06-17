import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional

@dataclass
class EffectSignature:
    name: str
    category: str  # 'adjustment', 'filter', 'transition', 'effect'
    description: str
    detection_method: str  # 'histogram', 'color_matrix', 'edge', 'noise', 'motion', 'ml'
    parameters: Dict[str, Tuple[float, float, float]] = field(default_factory=dict)

FILTER_SIGNATURES: Dict[str, EffectSignature] = {
    "brightness": EffectSignature(
        name="Brightness",
        category="adjustment",
        description="Global brightness adjustment",
        detection_method="histogram",
        parameters={
            "mean_luminance_shift": (0, 255, 128),
            "histogram_translation": (0.0, 1.0, 0.5),
        },
    ),
    "contrast": EffectSignature(
        name="Contrast",
        category="adjustment",
        description="Global contrast adjustment",
        detection_method="histogram",
        parameters={
            "luminance_std_ratio": (0.5, 2.0, 1.0),
            "histogram_spread": (0.0, 1.0, 0.5),
        },
    ),
    "saturation": EffectSignature(
        name="Saturation",
        category="adjustment",
        description="Color saturation adjustment",
        detection_method="histogram",
        parameters={
            "mean_saturation_ratio": (0.0, 3.0, 1.0),
            "saturation_std_ratio": (0.0, 3.0, 1.0),
        },
    ),
    "exposure": EffectSignature(
        name="Exposure",
        category="adjustment",
        description="Exposure adjustment (EV)",
        detection_method="histogram",
        parameters={
            "mean_luminance_log": (-3.0, 3.0, 0.0),
            "histogram_shift": (-100, 100, 0),
        },
    ),
    "highlights": EffectSignature(
        name="Highlights",
        category="adjustment",
        description="Highlight region adjustment",
        detection_method="histogram",
        parameters={
            "upper_quartile_shift": (-100, 100, 0),
            "top_10pct_mean_shift": (-100, 100, 0),
        },
    ),
    "shadows": EffectSignature(
        name="Shadows",
        category="adjustment",
        description="Shadow region adjustment",
        detection_method="histogram",
        parameters={
            "lower_quartile_shift": (-100, 100, 0),
            "bottom_10pct_mean_shift": (-100, 100, 0),
        },
    ),
    "whites": EffectSignature(
        name="Whites",
        category="adjustment",
        description="White point adjustment",
        detection_method="histogram",
        parameters={
            "max_luminance_shift": (-100, 100, 0),
            "p99_luminance_shift": (-100, 100, 0),
        },
    ),
    "blacks": EffectSignature(
        name="Blacks",
        category="adjustment",
        description="Black point adjustment",
        detection_method="histogram",
        parameters={
            "min_luminance_shift": (-100, 100, 0),
            "p01_luminance_shift": (-100, 100, 0),
        },
    ),
    "temperature": EffectSignature(
        name="Temperature",
        category="adjustment",
        description="Color temperature (blue/yellow)",
        detection_method="color_matrix",
        parameters={
            "r_b_ratio": (0.5, 2.0, 1.0),
            "b_channel_mean": (-50, 50, 0),
        },
    ),
    "tint": EffectSignature(
        name="Tint",
        category="adjustment",
        description="Color tint (green/magenta)",
        detection_method="color_matrix",
        parameters={
            "g_channel_offset": (-50, 50, 0),
            "g_r_ratio_deviation": (-0.5, 0.5, 0.0),
        },
    ),
    "vibrance": EffectSignature(
        name="Vibrance",
        category="adjustment",
        description="Smart saturation (protects skin tones)",
        detection_method="color_matrix",
        parameters={
            "low_sat_boost": (0.0, 2.0, 1.0),
            "high_sat_attenuation": (0.0, 1.0, 1.0),
        },
    ),
    "sharpness": EffectSignature(
        name="Sharpness",
        category="adjustment",
        description="Edge sharpness enhancement",
        detection_method="edge",
        parameters={
            "edge_strength_ratio": (0.5, 3.0, 1.0),
            "laplacian_variance_ratio": (0.5, 3.0, 1.0),
        },
    ),
    "vignette": EffectSignature(
        name="Vignette",
        category="effect",
        description="Corner darkening effect",
        detection_method="histogram",
        parameters={
            "center_vs_corner_ratio": (0.0, 1.0, 1.0),
            "radial_falloff": (0.0, 1.0, 0.0),
        },
    ),
    "grain": EffectSignature(
        name="Grain",
        category="effect",
        description="Film grain / noise overlay",
        detection_method="noise",
        parameters={
            "noise_std_ratio": (0.0, 0.1, 0.0),
            "high_freq_noise": (0.0, 1.0, 0.0),
        },
    ),
    "fade": EffectSignature(
        name="Fade / Film Fade",
        category="filter",
        description="Faded film look with lifted blacks",
        detection_method="color_matrix",
        parameters={
            "black_lift": (0, 50, 0),
            "contrast_reduction": (0.0, 0.5, 0.0),
            "saturation_reduction": (0.0, 0.5, 0.0),
        },
    ),
    "teal_and_orange": EffectSignature(
        name="Teal & Orange",
        category="filter",
        description="Teal shadows + warm skin tones",
        detection_method="color_matrix",
        parameters={
            "teal_shift_shadows": (0.0, 1.0, 0.0),
            "orange_shift_midtones": (0.0, 1.0, 0.0),
            "skin_isolation": (0.0, 1.0, 0.0),
        },
    ),
    "vintage": EffectSignature(
        name="Vintage / Retro",
        category="filter",
        description="Warm, faded vintage look",
        detection_method="color_matrix",
        parameters={
            "warmth_shift": (0, 30, 0),
            "fade_amount": (0.0, 0.4, 0.0),
            "grain_amount": (0.0, 0.3, 0.0),
            "saturation_reduction": (0.0, 0.4, 0.0),
        },
    ),
    "noir": EffectSignature(
        name="Noir / B&W",
        category="filter",
        description="Black and white with contrast",
        detection_method="color_matrix",
        parameters={
            "desaturation": (0.7, 1.0, 0.0),
            "contrast_increase": (0.0, 0.5, 0.0),
            "red_weight": (0.0, 1.0, 0.299),
            "green_weight": (0.0, 1.0, 0.587),
            "blue_weight": (0.0, 1.0, 0.114),
        },
    ),
    "glow": EffectSignature(
        name="Glow / Soft Bloom",
        category="effect",
        description="Soft glowing highlights",
        detection_method="edge",
        parameters={
            "bloom_intensity": (0.0, 1.0, 0.0),
            "blur_radius": (0, 20, 0),
            "threshold": (0.5, 1.0, 0.8),
        },
    ),
    "dramatic": EffectSignature(
        name="Dramatic",
        category="filter",
        description="High contrast dramatic look",
        detection_method="histogram",
        parameters={
            "contrast_increase": (0.2, 0.8, 0.0),
            "shadow_clip": (0.0, 0.3, 0.0),
            "highlight_clip": (0.0, 0.2, 0.0),
            "saturation_reduction": (0.0, 0.3, 0.0),
        },
    ),
    "pastel": EffectSignature(
        name="Pastel / Soft",
        category="filter",
        description="Soft pastel colors, low contrast",
        detection_method="color_matrix",
        parameters={
            "contrast_reduction": (0.0, 0.4, 0.0),
            "saturation_reduction": (0.0, 0.3, 0.0),
            "brightness_increase": (0, 20, 0),
            "color_shift": (0.0, 0.2, 0.0),
        },
    ),
    "hdr": EffectSignature(
        name="HDR",
        category="effect",
        description="High dynamic range effect",
        detection_method="edge",
        parameters={
            "local_contrast": (0.0, 1.0, 0.0),
            "detail_enhancement": (0.0, 1.0, 0.0),
            "saturation_boost": (0.0, 0.5, 0.0),
        },
    ),
    "speed_ramp": EffectSignature(
        name="Speed Ramp",
        category="transition",
        description="Variable speed playback",
        detection_method="motion",
        parameters={
            "motion_vector_magnitude": (0.0, 2.0, 1.0),
            "time_warp_factor": (0.1, 4.0, 1.0),
        },
    ),
    "reverse": EffectSignature(
        name="Reverse",
        category="transition",
        description="Reversed playback segment",
        detection_method="motion",
        parameters={
            "motion_direction_reversal": (0.0, 1.0, 0.0),
        },
    ),
}

FILTER_NAMES_MAP = {
    "Brightness": "Brightness",
    "Contrast": "Contrast",
    "Saturation": "Saturation",
    "Exposure": "Exposure",
    "Highlights": "Highlights",
    "Shadows": "Shadows",
    "Whites": "Whites",
    "Blacks": "Blacks",
    "Temperature": "Temperature",
    "Tint": "Tint",
    "Vibrance": "Vibrance",
    "Sharpness": "Sharpen",
    "Vignette": "Vignette",
    "Grain": "Grain",
    "Fade / Film Fade": "Fade",
    "Teal & Orange": "Teal & Orange",
    "Vintage / Retro": "Vintage",
    "Noir / B&W": "Noir",
    "Glow / Soft Bloom": "Glow",
    "Dramatic": "Dramatic",
    "Pastel / Soft": "Pastel",
    "HDR": "HDR Look",
    "Speed Ramp": "Speed",
    "Reverse": "Reverse",
}

def get_neutral_reference():
    return {
        "mean_luminance": 128.0,
        "luminance_std": 74.0,
        "mean_saturation": 0.2,
        "r_b_ratio": 1.0,
        "g_channel_offset": 0.0,
        "laplacian_variance": 100.0,
        "noise_std": 0.005,
    }
