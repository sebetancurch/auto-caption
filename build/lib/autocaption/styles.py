"""Caption style presets."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class StylePreset:
    name: str
    mode: str  # "pop" | "karaoke"
    font: str = "Anton"
    font_size: int = 130  # at the 1080x1920 reference resolution
    text_color: str = "#FFFFFF"
    highlight_color: str = "#FFD700"
    outline_color: str = "#000000"
    outline: float = 4.0
    shadow: float = 1.5
    caps: bool = True
    pos_y: float = 0.68  # vertical position as a fraction of frame height
    fade_in_ms: int = 80
    fade_out_ms: int = 40
    pop_scale: int = 115  # % size the active word pops in from
    pop_ms: int = 60


PRESETS: dict[str, StylePreset] = {
    "pop": StylePreset(name="pop", mode="pop"),
    "karaoke": StylePreset(name="karaoke", mode="karaoke"),
}
