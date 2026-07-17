# Contributing

Bug reports, feature ideas, and pull requests are all welcome!

## Dev setup

```bash
git clone https://github.com/sebetancurch/auto-caption
cd auto-caption
python -m venv .venv
# Windows: .venv\Scripts\activate     macOS/Linux: source .venv/bin/activate
pip install -e .[dev]
```

You'll also need [FFmpeg](https://ffmpeg.org/download.html) on your PATH for
burn-in and previews (`winget install Gyan.FFmpeg` / `brew install ffmpeg` /
`sudo apt install ffmpeg`).

## Running tests

```bash
pytest
```

CI runs the same tests on Windows, macOS, and Linux.

## Ideas that would make good PRs

- New style presets in `autocaption/styles.py` (they're small dataclasses —
  see how `pop` and `karaoke` are built in `autocaption/ass_builder.py`)
- Word-level correction UI (edit the transcript before rendering)
- Translations of the GUI
