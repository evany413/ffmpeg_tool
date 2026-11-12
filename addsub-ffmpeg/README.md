# addsub-ffmpeg

Batch-encode video files with hardcoded subtitles using FFmpeg. Reads a list of video and subtitle file pairs, burns the subtitles into the video, scales oversized videos down within 1080p while preserving their aspect ratio, and outputs H.264/AAC MP4 files.

## Requirements

- Windows 10 or later, Linux, or macOS

## Setup

Run the setup script once after cloning the repository. It installs FFmpeg and
`uv`, then creates the Python environment with `uv sync`.

### Windows

```powershell
powershell -ExecutionPolicy Bypass -File .\setup.ps1
```

The Windows setup downloads the Gyan FFmpeg full build into
`.tools/ffmpeg/bin/` at the repository root. It does not modify the system
FFmpeg installation. Use `-ForceFfmpeg` to download it again. The archive is
verified against its pinned SHA-256 checksum.

### Linux and macOS

```bash
chmod +x setup.sh
./setup.sh
```

Linux and macOS also install portable FFmpeg and FFprobe binaries into
`.tools/ffmpeg/bin/`; no system package manager or administrator access is
required. Linux x86-64/ARM64 and macOS Intel/Apple Silicon are supported. Use
`./setup.sh --force-ffmpeg` to download them again. Downloads are verified
against pinned SHA-256 checksums. All platforms currently use FFmpeg 9.0.2.

## Usage

1. Add video file names (one per line) to `vid_list.txt`
2. Add the corresponding subtitle file names (one per line) to `sub_list.txt`
3. Run:

```bash
uv run main.py
```

Output files are saved to the `Output/` folder with `.mp4` extension.

Encoding stops on FFmpeg errors. A failed encode may leave a partial output
file; do not use it as a completed video.

## Notes

- Video and subtitle lists are matched line-by-line, so order matters.
- Subtitle filenames with special characters (brackets, apostrophes, etc.) are handled automatically.
- Bitrate is capped at 2000k. If the source bitrate is lower, the original is preserved.
- Windows defaults to NVIDIA `h264_nvenc`; Linux and macOS default to CPU
  `libx264`. Set the `VIDEO_ENCODER` environment variable to override it:
  - NVIDIA: `h264_nvenc`
  - AMD: `h264_amf`
  - Intel: `h264_qsv`
  - CPU: `libx264`
