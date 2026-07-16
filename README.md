# auto-caption

Free, local, CapCut-style karaoke captions for shorts/reels — no subscriptions, no
watermarks, no uploads. Feed it a video (or audio) file and it:

1. Transcribes the speech with **word-level timestamps** (faster-whisper, runs locally)
2. Groups the words into short caption lines tuned for 9:16 vertical video
3. Generates an **.ass** subtitle file with per-word karaoke animations
4. **Burns the captions into the video** with FFmpeg (libass) — plus it always writes
   the subtitle files in case you'd rather finish in an editor

```
autocaption clip.mp4
   → clip.captioned.mp4   final video with animated captions
   → clip.ass             the animated subtitles (imports into DaVinci/mpv/etc.)
   → clip.davinci.srt     karaoke SRT for DaVinci Resolve's subtitle track
```

## Setup (once)

```powershell
winget install Gyan.FFmpeg        # already done on this machine
python -m venv .venv
.\.venv\Scripts\pip install -e .
```

The first run downloads the Whisper model (~500 MB for `small.en`) to
`~\.cache\huggingface`; after that everything is offline.

## Usage

```powershell
.\.venv\Scripts\autocaption.exe clip.mp4                     # default "pop" style
.\.venv\Scripts\autocaption.exe clip.mp4 --style karaoke
.\.venv\Scripts\autocaption.exe clip.mp4 --highlight-color 00FF88 --position mid
.\.venv\Scripts\autocaption.exe podcast.mp3                  # audio → subtitle files only
```

Or just **drag & drop a video onto `drop_video_here.bat`**.

### Styles

| Style     | Look |
|-----------|------|
| `pop` (default) | Full phrase on screen; the spoken word flashes yellow and does a quick scale "pop" — the classic CapCut/TikTok look |
| `karaoke` | Full phrase on screen; the highlight color sweeps smoothly through each word as it's spoken, karaoke-lyrics style |

### Options

| Flag | Meaning (default) |
|------|-------------------|
| `--style pop\|karaoke` | caption style (`pop`) |
| `--model NAME` | whisper model (`medium.en` on GPU, `small.en` on CPU); try `medium.en` for tougher audio |
| `--device auto\|cuda\|cpu` | inference device (`auto`, falls back to CPU) |
| `--language XX` | audio language, `auto` to detect (`en`) |
| `--highlight-color HEX` | active-word color (`#FFD700`) |
| `--font NAME` | font (bundled **Anton**; any installed font name works) |
| `--font-size N` | size at 1080x1920 reference scale (`130`) |
| `--caps / --no-caps` | UPPERCASE captions (on) |
| `--words-per-line N` / `--max-chars N` | line length limits (`4` / `18`) |
| `--position high\|mid\|low` | vertical placement (`low` ≈ 68% down, clear of TikTok UI) |
| `--no-burn` | only write subtitle files |
| `--no-srt` | skip the DaVinci `.srt` |
| `--nvenc` | encode with NVIDIA NVENC (much faster export) |
| `-o PATH` | output video path (`<input>.captioned.mp4`) |

## Using the files in DaVinci Resolve instead

- **`.davinci.srt`** — import into a subtitle track (`File → Import → Subtitle`). It
  contains one block per spoken word with the active word wrapped in a `<font color>`
  tag, so the highlight jumps word-to-word on playback (Resolve parses these tags;
  most other editors strip them). Style the track in the Inspector, and add a Text+
  animation or Dynamic Zoom on top for motion.
- **`.ass`** — keeps the full animations; useful for mpv/VLC preview or re-burning
  later with `ffmpeg -i in.mp4 -vf "ass=subs.ass:fontsdir=fonts" out.mp4`.

## GPU (optional)

Transcription works fine on CPU (a 60 s short takes a few seconds with `small.en`).
To run Whisper on the GPU, the CUDA runtime DLLs are needed:

```powershell
.\.venv\Scripts\pip install nvidia-cublas-cu12 nvidia-cudnn-cu12
```

then add the two DLL folders to `PATH` before running:

```powershell
$env:PATH = ".venv\Lib\site-packages\nvidia\cublas\bin;.venv\Lib\site-packages\nvidia\cudnn\bin;$env:PATH"
```

`--device auto` tries CUDA first and falls back to CPU automatically, so this is
never required. (Note: very new GPU generations can also hit CTranslate2 wheel lag —
the fallback covers that case too.)
