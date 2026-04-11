# ffmpeg-tool

A collection of FFmpeg-based utilities for video and subtitle processing.

## Tools

### [addsub-ffmpeg](addsub-ffmpeg/)

Batch-encode video files with hardcoded subtitles. Reads paired video and subtitle lists, burns subtitles into the video, scales to 1080p, and outputs H.264/AAC MP4 files.

**Requirements:** Python >= 3.9, [uv](https://github.com/astral-sh/uv), FFmpeg, NVIDIA GPU (default encoder)

```bash
cd addsub-ffmpeg
uv sync
uv run main.py
```

---

### [sub-converter](sub-converter/)

Batch-convert subtitle files (ASS / SSA / AAS) to SRT. Drop subtitle files into the folder and run the script.

**Requirements:** Python >= 3.9, FFmpeg

```bash
cd sub-converter
python main.py
```

---

### [clip-concat-ffmpeg](clip-concat-ffmpeg/)

Batch-convert and concatenate video clips within subfolders. Scales to a chosen resolution (1080p / 720p / 480p) with a selectable bitrate preset (High / Medium / Low), then merges all clips in each subfolder into a single MP4.

**Requirements:** Python >= 3.9, FFmpeg

```bash
cd clip-concat-ffmpeg
python main.py
```

---

## Requirements (shared)

- FFmpeg installed and available in PATH
