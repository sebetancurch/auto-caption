"""DaVinci Resolve-compatible karaoke SRT (word highlight via <font> tags).

Standard SRT has no animation support, but DaVinci's subtitle engine parses
<font color> tags. One block per spoken word, with only the active word
wrapped in a tag, makes the highlight jump from word to word on playback.
"""

from __future__ import annotations

from .grouping import CaptionLine


def srt_time(seconds: float) -> str:
    ms = max(0, round(seconds * 1000))
    h, rem = divmod(ms, 3_600_000)
    m, rem = divmod(rem, 60_000)
    s, ms = divmod(rem, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def build_srt(lines: list[CaptionLine], highlight_color: str = "#FFD700") -> str:
    blocks: list[str] = []
    index = 1
    for line in lines:
        for i, word in enumerate(line.words):
            parts = [
                f'<font color="{highlight_color}">{other.text}</font>' if i == j else other.text
                for j, other in enumerate(line.words)
            ]
            blocks.append(
                f"{index}\n{srt_time(word.start)} --> {srt_time(word.end)}\n{' '.join(parts)}\n"
            )
            index += 1
    return "\n".join(blocks)
