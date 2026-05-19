from __future__ import annotations

_LIGHT: dict[str, str] = {
    # Structure
    "bg":             "#F4F4F5",
    "surface":        "#FFFFFF",
    "surface_alt":    "#FAFAFA",
    "text":           "#111827",
    "text_secondary": "#374151",
    "muted":          "#6B7280",
    "placeholder":    "#D1D5DB",
    "border":         "#E5E7EB",
    "border_soft":    "#F3F4F6",
    # Amber — quotes, primary CTA
    "amber":          "#B45309",
    "amber_dark":     "#92400E",
    "amber_light":    "#FEF3C7",
    "amber_ring":     "rgba(180,83,9,0.10)",
    # Blue — reports
    "blue":           "#1D4ED8",
    "blue_dark":      "#1E3A8A",
    "blue_light":     "#DBEAFE",
    "blue_ring":      "rgba(29,78,216,0.08)",
    # Green — success, connected
    "green":          "#059669",
    "green_light":    "#D1FAE5",
    "green_text":     "#065F46",
    "green_ring":     "rgba(5,150,105,0.08)",
    # Red — danger, destructive
    "red":            "#DC2626",
    "red_light":      "#FEE2E2",
    "red_text":       "#991B1B",
    # Purple — AI / Groq
    "purple":         "#7C3AED",
    "purple_light":   "#F5F3FF",
    "purple_ring":    "rgba(124,58,237,0.08)",
    # Teal — section templates
    "teal":           "#0D9488",
    "teal_light":     "#CCFBF1",
    "teal_ring":      "rgba(13,148,136,0.08)",
}

_DARK: dict[str, str] = {
    "bg":             "#111827",
    "surface":        "#1F2937",
    "surface_alt":    "#18202E",
    "text":           "#F9FAFB",
    "text_secondary": "#E5E7EB",
    "muted":          "#9CA3AF",
    "placeholder":    "#4B5563",
    "border":         "#374151",
    "border_soft":    "#2D3748",
    "amber":          "#D97706",
    "amber_dark":     "#B45309",
    "amber_light":    "#451A03",
    "amber_ring":     "rgba(217,119,6,0.15)",
    "blue":           "#3B82F6",
    "blue_dark":      "#1D4ED8",
    "blue_light":     "#1E3A5F",
    "blue_ring":      "rgba(59,130,246,0.15)",
    "green":          "#10B981",
    "green_light":    "#064E3B",
    "green_text":     "#A7F3D0",
    "green_ring":     "rgba(16,185,129,0.15)",
    "red":            "#EF4444",
    "red_light":      "#450A0A",
    "red_text":       "#FCA5A5",
    "purple":         "#8B5CF6",
    "purple_light":   "#2E1065",
    "purple_ring":    "rgba(139,92,246,0.15)",
    "teal":           "#14B8A6",
    "teal_light":     "#042F2E",
    "teal_ring":      "rgba(20,184,166,0.15)",
}

# Live reference — swap via activate()
current: dict[str, str] = _LIGHT

# Badge colors per semantic color name
ICON_BADGE: dict[str, tuple[str, str]] = {
    "amber":  ("amber_light",  "amber"),
    "blue":   ("blue_light",   "blue"),
    "green":  ("green_light",  "green"),
    "purple": ("purple_light", "purple"),
    "teal":   ("teal_light",   "teal"),
    "gray":   ("border_soft",  "muted"),
}

STATUS_PALETTE: dict[str, tuple[str, str, str]] = {
    # state → (bg_token, text_token, dot_token)
    "ok":   ("green_light", "green_text", "green"),
    "warn": ("amber_light", "amber_dark", "amber"),
    "off":  ("border_soft", "muted",      "placeholder"),
}


def activate(mode: str) -> None:
    """Switch the live theme.  Call before constructing any widget."""
    global current
    current = _DARK if mode == "dark" else _LIGHT
