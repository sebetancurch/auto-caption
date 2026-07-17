"""FFmpeg/ffprobe helpers: discovery, probing, subtitle burn-in."""

from __future__ import annotations

import glob
import os
import shutil
import subprocess
import sys
from pathlib import Path

FFMPEG_INSTALL_HINT = {
    "win32": "winget install Gyan.FFmpeg",
    "darwin": "brew install ffmpeg",
}.get(sys.platform, "sudo apt install ffmpeg  (or your distro's equivalent)")


class FFmpegNotFound(RuntimeError):
    pass


def find_tool(name: str) -> str:
    path = shutil.which(name)
    if path:
        return path
    candidates: list[str] = []
    if sys.platform == "win32":
        # a fresh winget install may not be on this shell's PATH yet
        candidates.append(os.path.expandvars(rf"%LOCALAPPDATA%\Microsoft\WinGet\Links\{name}.exe"))
        candidates += glob.glob(
            os.path.expandvars(
                rf"%LOCALAPPDATA%\Microsoft\WinGet\Packages\Gyan.FFmpeg*\ffmpeg-*\bin\{name}.exe"
            )
        )
    elif sys.platform == "darwin":
        candidates += [f"/opt/homebrew/bin/{name}", f"/usr/local/bin/{name}"]
    for candidate in candidates:
        if os.path.isfile(candidate):
            return candidate
    raise FFmpegNotFound(f"{name} not found. Install it with:  {FFMPEG_INSTALL_HINT}")


def probe_video_size(media_path: str | Path) -> tuple[int, int] | None:
    """Return (width, height) of the video stream, or None for audio-only input."""
    result = subprocess.run(
        [
            find_tool("ffprobe"), "-v", "error", "-select_streams", "v:0",
            "-show_entries", "stream=width,height:stream_disposition=attached_pic",
            "-of", "csv=p=0", str(media_path),
        ],
        capture_output=True,
        text=True,
    )
    line = result.stdout.strip().splitlines()[0].strip() if result.stdout.strip() else ""
    if result.returncode != 0 or not line:
        return None
    fields = line.split(",")
    try:
        width, height = int(fields[0]), int(fields[1])
        attached_pic = int(fields[2]) if len(fields) > 2 else 0
    except (ValueError, IndexError):
        return None
    if attached_pic:  # e.g. cover art embedded in an mp3
        return None
    return width, height


def _filter_path(path: str | Path) -> str:
    """Escape a Windows path for use inside an ffmpeg filter argument."""
    return str(path).replace("\\", "/").replace(":", "\\:")


def burn_subtitles(
    video: str | Path,
    ass_path: str | Path,
    output: str | Path,
    fontsdir: str | Path | None = None,
    nvenc: bool = False,
) -> None:
    vf = f"ass=filename='{_filter_path(ass_path)}'"
    if fontsdir:
        vf += f":fontsdir='{_filter_path(fontsdir)}'"
    if nvenc:
        vcodec = ["-c:v", "h264_nvenc", "-preset", "p5", "-cq", "19"]
    else:
        vcodec = ["-c:v", "libx264", "-crf", "18", "-preset", "medium"]
    subprocess.run(
        [
            find_tool("ffmpeg"), "-y", "-hide_banner", "-loglevel", "error", "-stats",
            "-i", str(video), "-vf", vf, *vcodec,
            "-c:a", "copy", "-movflags", "+faststart", str(output),
        ],
        check=True,
    )
