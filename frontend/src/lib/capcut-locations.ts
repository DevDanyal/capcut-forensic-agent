export const CAPCUT_LOCATIONS: Record<string, { tab: string; path: string }> = {
  Brightness: { tab: "Adjustments", path: "Adjustments \u203A Brightness" },
  Contrast: { tab: "Adjustments", path: "Adjustments \u203A Contrast" },
  Saturation: { tab: "Adjustments", path: "Adjustments \u203A Saturation" },
  Highlights: { tab: "Adjustments", path: "Adjustments \u203A Highlights" },
  Shadows: { tab: "Adjustments", path: "Adjustments \u203A Shadows" },
  Whites: { tab: "Adjustments", path: "Adjustments \u203A Whites" },
  Blacks: { tab: "Adjustments", path: "Adjustments \u203A Blacks" },
  Temperature: { tab: "Adjustments", path: "Adjustments \u203A Temperature" },
  Vibrance: { tab: "Adjustments", path: "Adjustments \u203A Vibrance" },
  Sharpen: { tab: "Adjustments", path: "Adjustments \u203A Sharpen" },
  Sharpness: { tab: "Adjustments", path: "Adjustments \u203A Sharpen" },

  Exposure: { tab: "Settings", path: "Settings \u203A Exposure" },

  Tint: { tab: "Filters", path: "Filters \u203A Color \u203A Tint" },

  "Teal & Orange": { tab: "Filters", path: "Filters \u203A Color \u203A Teal & Orange" },
  "Vintage / Retro": { tab: "Filters", path: "Filters \u203A Vintage" },
  Vintage: { tab: "Filters", path: "Filters \u203A Vintage" },
  "Noir / B&W": { tab: "Filters", path: "Filters \u203A Noir" },
  Noir: { tab: "Filters", path: "Filters \u203A Noir" },
  Dramatic: { tab: "Filters", path: "Filters \u203A Dramatic" },
  "Pastel / Soft": { tab: "Filters", path: "Filters \u203A Pastel" },
  Pastel: { tab: "Filters", path: "Filters \u203A Pastel" },
  "Fade / Film Fade": { tab: "Filters", path: "Filters \u203A Fade" },
  Fade: { tab: "Filters", path: "Filters \u203A Fade" },

  "Glow / Soft Bloom": { tab: "Effects", path: "Effects \u203A Glow" },
  Glow: { tab: "Effects", path: "Effects \u203A Glow" },
  "HDR Look": { tab: "Effects", path: "Effects \u203A HDR Look" },
  HDR: { tab: "Effects", path: "Effects \u203A HDR Look" },
  Grain: { tab: "Effects", path: "Effects \u203A Grain" },
  Vignette: { tab: "Effects", path: "Effects \u203A Vignette" },
};

export function getCapcutLocation(name: string): { tab: string; path: string } | null {
  return CAPCUT_LOCATIONS[name] || null;
}
