"""Unit tests for the pure logic (no ffmpeg, no whisper, no GUI windows)."""

import pytest

from autocaption.ass_builder import _inline_color, _style_color, ass_time, build_ass
from autocaption.grouping import group_words
from autocaption.media import _filter_path
from autocaption.srt_builder import build_srt, srt_time
from autocaption.styles import PRESETS
from autocaption.transcribe import Word


def words_from(spec):
    """[(text, start, end), ...] -> [Word, ...]"""
    return [Word(text, start, end) for text, start, end in spec]


# ---------------------------------------------------------------- timestamps


def test_ass_time():
    assert ass_time(0) == "0:00:00.00"
    assert ass_time(3661.234) == "1:01:01.23"
    assert ass_time(-1) == "0:00:00.00"


def test_srt_time():
    assert srt_time(0) == "00:00:00,000"
    assert srt_time(3661.5) == "01:01:01,500"


# -------------------------------------------------------------------- colors


def test_style_color_is_bgr_with_alpha():
    assert _style_color("#FFD700") == "&H0000D7FF"
    assert _style_color("#000000", alpha=128) == "&H80000000"


def test_inline_color_is_bgr():
    assert _inline_color("#FFD700") == "&H00D7FF&"
    assert _inline_color("00FF88") == "&H88FF00&"


# ------------------------------------------------------------------ grouping


def test_group_breaks_on_silence_gap():
    lines = group_words(words_from([("one", 0.0, 0.3), ("two", 1.5, 1.8)]))
    assert [line.text for line in lines] == ["one", "two"]


def test_group_breaks_on_sentence_end():
    lines = group_words(words_from([("Hi.", 0.0, 0.3), ("there", 0.4, 0.6)]))
    assert [line.text for line in lines] == ["Hi.", "there"]


def test_group_respects_max_words():
    spec = [(f"w{i}", i * 0.2, i * 0.2 + 0.15) for i in range(10)]
    lines = group_words(words_from(spec), max_words=4, max_chars=100)
    assert [len(line.words) for line in lines] == [4, 4, 2]


def test_gap_snapping_makes_highlight_contiguous():
    lines = group_words(words_from([("a", 0.0, 0.2), ("b", 0.3, 0.5)]))
    (line,) = lines
    assert line.words[0].end == line.words[1].start == 0.3
    assert line.words[1].end == 0.5  # last word keeps its real end


# ------------------------------------------------------------------ builders


def test_build_srt_one_highlight_per_block():
    lines = group_words(words_from([("one", 0.0, 0.2), ("two", 0.2, 0.4), ("three", 0.4, 0.6)]))
    srt = build_srt(lines, "#FFD700")
    blocks = [b for b in srt.split("\n\n") if b.strip()]
    assert len(blocks) == 3
    for i, block in enumerate(blocks):
        assert block.startswith(f"{i + 1}\n")
        assert block.count("<font") == 1


@pytest.mark.parametrize("preset", sorted(PRESETS))
def test_build_ass_structure(preset):
    lines = group_words(words_from([("hello", 0.0, 0.4), ("world", 0.4, 0.9)]))
    doc = build_ass(lines, PRESETS[preset], 1080, 1920)
    assert "PlayResX: 1080" in doc and "PlayResY: 1920" in doc
    dialogues = [l for l in doc.splitlines() if l.startswith("Dialogue:")]
    assert len(dialogues) == (2 if PRESETS[preset].mode == "pop" else 1)


def test_filter_path_escapes_windows_paths():
    assert _filter_path(r"C:\clips\my video.ass") == "C\\:/clips/my video.ass"


# ----------------------------------------------------------------- gui logic


def test_settings_to_flags_and_style():
    pytest.importorskip("customtkinter")
    from autocaption.gui import DEFAULT_SETTINGS, settings_to_flags, settings_to_style

    flags = settings_to_flags(dict(DEFAULT_SETTINGS))
    assert "--style" in flags and "pop" in flags
    assert "--model" not in flags  # "auto" model label means no flag
    assert "--nvenc" not in flags and "--no-burn" not in flags

    flags = settings_to_flags(dict(DEFAULT_SETTINGS, burn=False, nvenc=True, model_label="small.en - balanced"))
    assert "--no-burn" in flags and "--nvenc" in flags
    assert flags[flags.index("--model") + 1] == "small.en"

    style = settings_to_style(dict(DEFAULT_SETTINGS, highlight_color="#00FF88", style="karaoke"))
    assert style.mode == "karaoke" and style.highlight_color == "#00FF88"
