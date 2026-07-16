"""Command line interface: media in -> karaoke-captioned video + subtitle files out."""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import replace
from pathlib import Path

from . import media
from .ass_builder import build_ass
from .grouping import group_words
from .srt_builder import build_srt
from .styles import PRESETS
from .transcribe import transcribe

POSITIONS = {"high": 0.32, "mid": 0.50, "low": 0.68}
FONTS_DIR = Path(__file__).resolve().parent.parent / "fonts"


def _hex_color(value: str) -> str:
    v = value.lstrip("#")
    if not re.fullmatch(r"[0-9a-fA-F]{6}", v):
        raise argparse.ArgumentTypeError(f"expected a hex color like #FFD700, got {value!r}")
    return f"#{v.upper()}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="autocaption",
        description="Generate animated karaoke captions for shorts/reels. "
        "Outputs a burned-in video plus .ass and DaVinci-compatible .srt files.",
    )
    parser.add_argument("input", help="video or audio file")
    parser.add_argument("--style", choices=sorted(PRESETS), default="pop",
                        help="caption style preset (default: pop)")
    parser.add_argument("--model", default=None,
                        help="whisper model (default: medium.en on GPU, small.en on CPU)")
    parser.add_argument("--device", choices=["auto", "cuda", "cpu"], default="auto")
    parser.add_argument("--language", default="en", help="audio language, or 'auto' to detect")
    parser.add_argument("--highlight-color", type=_hex_color, default=None, metavar="HEX")
    parser.add_argument("--font", default=None, help="font name (default: bundled Anton)")
    parser.add_argument("--font-size", type=int, default=None,
                        help="size at the 1080x1920 reference scale")
    parser.add_argument("--caps", action=argparse.BooleanOptionalAction, default=None,
                        help="UPPERCASE the captions (default: on)")
    parser.add_argument("--words-per-line", type=int, default=4)
    parser.add_argument("--max-chars", type=int, default=18)
    parser.add_argument("--position", choices=sorted(POSITIONS), default="low")
    parser.add_argument("--no-burn", action="store_true", help="only write subtitle files")
    parser.add_argument("--no-srt", action="store_true", help="skip the DaVinci .srt export")
    parser.add_argument("--nvenc", action="store_true", help="encode with NVIDIA NVENC (faster)")
    parser.add_argument("-o", "--output", default=None, help="output video path")
    args = parser.parse_args(argv)

    input_path = Path(args.input).expanduser().resolve()
    if not input_path.is_file():
        parser.error(f"input file not found: {input_path}")

    style = PRESETS[args.style]
    overrides = {"pos_y": POSITIONS[args.position]}
    if args.highlight_color:
        overrides["highlight_color"] = args.highlight_color
    if args.font:
        overrides["font"] = args.font
    if args.font_size:
        overrides["font_size"] = args.font_size
    if args.caps is not None:
        overrides["caps"] = args.caps
    style = replace(style, **overrides)

    language = None if args.language == "auto" else args.language
    words = transcribe(input_path, model_name=args.model, device=args.device, language=language)
    if not words:
        print("No speech detected - nothing to caption.", file=sys.stderr)
        return 1

    lines = group_words(words, max_words=args.words_per_line, max_chars=args.max_chars)
    print(f"[captions] {len(lines)} caption lines, style '{style.name}'")

    size = media.probe_video_size(input_path)
    if size is None:
        print("[captions] audio-only input: writing subtitle files sized for 1080x1920")
    width, height = size if size else (1080, 1920)

    ass_path = input_path.with_suffix(".ass")
    ass_path.write_text(build_ass(lines, style, width, height), encoding="utf-8")
    print(f"[out] {ass_path}")

    if not args.no_srt:
        srt_path = input_path.with_suffix(".davinci.srt")
        srt_path.write_text(build_srt(lines, style.highlight_color), encoding="utf-8")
        print(f"[out] {srt_path}")

    if size is not None and not args.no_burn:
        out_path = (
            Path(args.output).expanduser().resolve()
            if args.output
            else input_path.with_name(input_path.stem + ".captioned.mp4")
        )
        fontsdir = FONTS_DIR if FONTS_DIR.is_dir() else None
        print(f"[burn] rendering {out_path.name} ...")
        media.burn_subtitles(input_path, ass_path, out_path, fontsdir=fontsdir, nvenc=args.nvenc)
        print(f"[out] {out_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
