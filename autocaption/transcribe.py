"""Speech-to-text with word-level timestamps via faster-whisper."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Word:
    text: str
    start: float
    end: float


def _default_model(device: str, language: str | None) -> str:
    size = "medium" if device == "cuda" else "small"
    return f"{size}.en" if language == "en" else size


def transcribe(
    media_path: str | Path,
    model_name: str | None = None,
    device: str = "auto",
    language: str | None = "en",
    verbose: bool = True,
) -> list[Word]:
    """Transcribe an audio or video file into one Word per spoken word.

    device="auto" tries CUDA first and falls back to CPU int8 — GPU inference
    needs cuBLAS/cuDNN DLLs that are not installed by default on Windows.
    """
    attempts: list[tuple[str, str]] = []
    if device in ("auto", "cuda"):
        attempts.append(("cuda", "float16"))
    if device in ("auto", "cpu"):
        attempts.append(("cpu", "int8"))

    last_error: Exception | None = None
    for i, (dev, compute_type) in enumerate(attempts):
        name = model_name or _default_model(dev, language)
        try:
            if verbose:
                print(f"[transcribe] loading model '{name}' on {dev} ({compute_type})...")
            return _run(media_path, name, dev, compute_type, language, verbose)
        except Exception as error:  # CUDA/CTranslate2 failures surface here
            last_error = error
            if i + 1 < len(attempts):
                print(f"[transcribe] {dev} failed ({error}); falling back...", file=sys.stderr)
    raise last_error  # type: ignore[misc]


def _run(
    media_path: str | Path,
    model_name: str,
    device: str,
    compute_type: str,
    language: str | None,
    verbose: bool,
) -> list[Word]:
    from faster_whisper import WhisperModel

    model = WhisperModel(model_name, device=device, compute_type=compute_type)
    segments, info = model.transcribe(
        str(media_path),
        language=language,
        word_timestamps=True,
        vad_filter=True,
    )
    words: list[Word] = []
    for segment in segments:
        if verbose:
            print(f"  [{segment.start:6.2f}s] {segment.text.strip()}")
        for w in segment.words or []:
            text = w.word.strip()
            if text:
                words.append(Word(text=text, start=float(w.start), end=float(w.end)))
    if verbose:
        print(f"[transcribe] {len(words)} words (language: {info.language})")
    return words
