# clip-concat-ffmpeg

Batch-convert and concatenate video clips within subfolders. Scales to a chosen resolution with a selectable bitrate preset, then merges all clips in each subfolder into a single MP4.

## Requirements

- Python >= 3.9
- FFmpeg installed and available in PATH

## Usage

1. Place each group of clips into its own subfolder:

```
clip-concat-ffmpeg/
├── episode1/
│   ├── clip1.mp4
│   ├── clip2.mp4
│   └── clip3.mkv
└── episode2/
    ├── clip1.mp4
    └── clip2.mp4
```

2. Run:

```bash
python main.py
```

3. Follow the prompts to select resolution and bitrate for each folder. Press **Enter** to accept the default.

Output files are saved to `<subfolder>/output/<subfolder-name>.mp4`.

## Options

### Resolution

| # | Resolution |
|---|------------|
| 1 | 1080p (default) |
| 2 | 720p |
| 3 | 480p |

### Bitrate Preset

| # | Preset | 1080p | 720p | 480p |
|---|--------|-------|------|------|
| 1 | High   | 8000k | 5000k | 2500k |
| 2 | Medium | 4000k | 2500k | 1500k |
| 3 | Low (default) | 2000k | 1200k | 800k |

## Notes

- Clips within each subfolder are concatenated in alphabetical order.
- Supported input formats: `.mp4`, `.mkv`
- To change the video encoder, edit the `VCODEC` option in `main.py`:
  - CPU: `libx264` (default, cross-platform)
  - NVIDIA: `h264_nvenc`
  - AMD: `h264_amf`
  - Intel: `h264_qsv`
