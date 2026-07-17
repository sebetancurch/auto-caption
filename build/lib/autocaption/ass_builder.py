"""Generate .ass subtitles with per-word karaoke / pop effects."""

from __future__ import annotations

from .grouping import CaptionLine
from .styles import StylePreset

REF_W, REF_H = 1080, 1920  # reference resolution the preset sizes are tuned for

HEADER_TEMPLATE = """\
[Script Info]
ScriptType: v4.00+
PlayResX: {width}
PlayResY: {height}
ScaledBorderAndShadow: yes
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Caption,{font},{font_size},{primary},{secondary},{outline_color},{back_color},0,0,0,0,100,100,0,0,1,{outline:.1f},{shadow:.1f},5,40,40,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def _style_color(color: str, alpha: int = 0) -> str:
    """'#RRGGBB' -> ASS style colour '&HAABBGGRR' (ASS is blue-green-red ordered)."""
    c = color.lstrip("#")
    r, g, b = c[0:2], c[2:4], c[4:6]
    return f"&H{alpha:02X}{b}{g}{r}".upper()


def _inline_color(color: str) -> str:
    """'#RRGGBB' -> inline override colour '&HBBGGRR&'."""
    c = color.lstrip("#")
    r, g, b = c[0:2], c[2:4], c[4:6]
    return f"&H{b}{g}{r}&".upper()


def ass_time(seconds: float) -> str:
    cs = max(0, round(seconds * 100))
    h, rem = divmod(cs, 360_000)
    m, rem = divmod(rem, 6_000)
    s, cs = divmod(rem, 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def _display(text: str, caps: bool) -> str:
    t = text.upper() if caps else text
    # braces would be parsed as ASS override blocks
    return t.replace("{", "(").replace("}", ")")


def build_ass(
    lines: list[CaptionLine],
    style: StylePreset,
    width: int,
    height: int,
) -> str:
    scale = height / REF_H
    if style.mode == "karaoke":
        # \kf sweeps SecondaryColour -> PrimaryColour as each word is spoken
        primary, secondary = style.highlight_color, style.text_color
    else:
        primary, secondary = style.text_color, style.highlight_color

    header = HEADER_TEMPLATE.format(
        width=width,
        height=height,
        font=style.font,
        font_size=round(style.font_size * scale),
        primary=_style_color(primary),
        secondary=_style_color(secondary),
        outline_color=_style_color(style.outline_color),
        back_color=_style_color("#000000", alpha=128),
        outline=style.outline * scale,
        shadow=style.shadow * scale,
    )

    pos_tag = f"\\pos({width / 2:.0f},{height * style.pos_y:.0f})"
    events: list[str] = []
    for line in lines:
        if style.mode == "karaoke":
            events.append(_karaoke_event(line, style, pos_tag))
        else:
            events.extend(_pop_events(line, style, pos_tag))
    return header + "\n".join(events) + "\n"


def _pop_events(line: CaptionLine, style: StylePreset, pos_tag: str) -> list[str]:
    """One event per word interval; the active word is recolored and pops in."""
    events: list[str] = []
    n = len(line.words)
    highlight = _inline_color(style.highlight_color)
    for i, word in enumerate(line.words):
        fade_in = style.fade_in_ms if i == 0 else 0
        fade_out = style.fade_out_ms if i == n - 1 else 0
        fade = f"\\fad({fade_in},{fade_out})" if fade_in or fade_out else ""

        parts: list[str] = []
        for j, other in enumerate(line.words):
            text = _display(other.text, style.caps)
            if i == j:
                parts.append(
                    f"{{\\c{highlight}"
                    f"\\fscx{style.pop_scale}\\fscy{style.pop_scale}"
                    f"\\t(0,{style.pop_ms},\\fscx100\\fscy100)}}"
                    f"{text}{{\\r}}"
                )
            else:
                parts.append(text)

        events.append(
            f"Dialogue: 0,{ass_time(word.start)},{ass_time(word.end)},Caption,,0,0,0,,"
            f"{{{pos_tag}{fade}}}{' '.join(parts)}"
        )
    return events


def _karaoke_event(line: CaptionLine, style: StylePreset, pos_tag: str) -> str:
    """One event per line; \\kf sweeps the highlight through each word."""
    fade = f"\\fad({style.fade_in_ms},{style.fade_out_ms})"
    parts: list[str] = []
    for word in line.words:
        duration_cs = max(1, round((word.end - word.start) * 100))
        parts.append(f"{{\\kf{duration_cs}}}{_display(word.text, style.caps)}")
    return (
        f"Dialogue: 0,{ass_time(line.start)},{ass_time(line.end)},Caption,,0,0,0,,"
        f"{{{pos_tag}{fade}}}{' '.join(parts)}"
    )
