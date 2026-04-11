# addsub-ffmpeg

Batch-encode video files with hardcoded subtitles using FFmpeg. Reads a list of video and subtitle file pairs, burns the subtitles into the video, scales to 1080p, and outputs H.264/AAC MP4 files.

## Requirements

- Python >= 3.9
- [uv](https://github.com/astral-sh/uv)
- FFmpeg installed and available in PATH
- An NVIDIA GPU (uses `h264_nvenc` by default; see below to change encoder)

## Setup

```bash
uv sync
```

## Usage

1. Add video file names (one per line) to `vid_list.txt`
2. Add the corresponding subtitle file names (one per line) to `sub_list.txt`
3. Run:

```bash
uv run main.py
```

Output files are saved to the `Output/` folder with `.mp4` extension.

## Notes

- Video and subtitle lists are matched line-by-line, so order matters.
- Subtitle filenames with special characters (brackets, apostrophes, etc.) are handled automatically.
- Bitrate is capped at 2000k. If the source bitrate is lower, the original is preserved.
- To change the video encoder, edit the `vcodec` option in `main.py`:
  - NVIDIA: `h264_nvenc`
  - AMD: `h264_amf`
  - Intel: `h264_qsv`
  - CPU: `libx264`
