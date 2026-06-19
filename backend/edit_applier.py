import numpy as np
import cv2
import os
from typing import Dict

def apply_adjustments_to_frame(frame: np.ndarray, adj: Dict) -> np.ndarray:
    img = frame.astype(float)

    exposure = adj.get("exposure", 0)
    if abs(exposure) > 0.1:
        ev = 2.0 ** (exposure * 0.2)
        img = img * ev

    brightness = adj.get("brightness", 0)
    if abs(brightness) > 1:
        img = img + brightness * 0.5

    contrast = adj.get("contrast", 0)
    if abs(contrast) > 1:
        factor = 1.0 + contrast * 0.005
        mean = 128.0
        img = mean + (img - mean) * factor

    highlights = adj.get("highlights", 0)
    if abs(highlights) > 1:
        mask = img > 128
        boost = (img - 128) / 128.0 * highlights * 0.3
        img[mask] = img[mask] + boost[mask]

    shadows = adj.get("shadows", 0)
    if abs(shadows) > 1:
        mask = img < 128
        boost = (128 - img) / 128.0 * shadows * 0.3
        img[mask] = img[mask] + boost[mask]

    whites = adj.get("whites", 0)
    if abs(whites) > 1:
        mask = img > 200
        boost = (img - 200) / 55.0 * whites * 0.5
        img[mask] = img[mask] + boost[mask]

    blacks = adj.get("blacks", 0)
    if abs(blacks) > 1:
        mask = img < 55
        boost = (55 - img) / 55.0 * blacks * 0.5
        img[mask] = img[mask] + boost[mask]

    img = np.clip(img, 0, 255)

    temperature = adj.get("temperature", 0)
    tint = adj.get("tint", 0)
    if abs(temperature) > 1 or abs(tint) > 1:
        r = img[:, :, 0].copy()
        g = img[:, :, 1].copy()
        b = img[:, :, 2].copy()
        if abs(temperature) > 1:
            r = r * (1.0 + temperature * 0.003)
            b = b * (1.0 - temperature * 0.003)
        if abs(tint) > 1:
            g = g * (1.0 + tint * 0.0025)
        img[:, :, 0] = np.clip(r, 0, 255)
        img[:, :, 1] = np.clip(g, 0, 255)
        img[:, :, 2] = np.clip(b, 0, 255)

    saturation = adj.get("saturation", 0)
    vibrance = adj.get("vibrance", 0)
    if abs(saturation) > 1 or abs(vibrance) > 1:
        hsv = cv2.cvtColor(img.astype(np.uint8), cv2.COLOR_RGB2HSV).astype(float)
        sat_factor = 1.0 + saturation * 0.01
        if abs(vibrance) > 1:
            low_sat_mask = hsv[:, :, 1] < 80
            vib_boost = (1.0 - hsv[:, :, 1] / 255.0) * vibrance * 0.003
            sat_factor = sat_factor + vib_boost * low_sat_mask.astype(float)
        hsv[:, :, 1] = np.clip(hsv[:, :, 1] * sat_factor, 0, 255)
        img = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2RGB).astype(float)

    sharpness = adj.get("sharpness", 0)
    if abs(sharpness) > 2:
        strength = sharpness / 100.0
        blurred = cv2.GaussianBlur(img, (0, 0), 1.5)
        img = img + (img - blurred) * strength
        img = np.clip(img, 0, 255)

    return img.astype(np.uint8)


def apply_edits_to_video(input_path: str, output_path: str, adjustments: Dict, target_fps: float = None):
    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        raise ValueError(f"Could not open video: {input_path}")

    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps <= 0 or fps > 1000:
        fps = 30.0
    if target_fps and target_fps > 0:
        fps = target_fps

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    frame_idx = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        processed = apply_adjustments_to_frame(rgb, adjustments)
        processed_bgr = cv2.cvtColor(processed, cv2.COLOR_RGB2BGR)
        out.write(processed_bgr)
        frame_idx += 1

    cap.release()
    out.release()

    return frame_idx > 0
