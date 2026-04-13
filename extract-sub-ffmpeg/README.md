# extract-sub-ffmpeg

Extract subtitle streams from MKV files while preserving their original format and styling (ASS, SSA, SRT, VTT, PGS, etc.).

## Usage

1. Drop one or more `.mkv` files into this folder
2. Run the script:

```bash
python main.py
```

3. Extracted subtitles are saved to `Output/`

## Output naming

```
<video_stem>.<language>[.<title>].<ext>
```

| MKV stream | Output file |
|---|---|
| `movie.mkv` — jpn ASS titled "Signs & Songs" | `movie.jpn.Signs_&_Songs.ass` |
| `movie.mkv` — eng SRT (no title) | `movie.eng.srt` |
| `episode01.mkv` — chi SSA | `episode01.chi.ssa` |

If two streams share the same language and title, a numeric suffix is appended (`movie.eng.1.srt`, `movie.eng.2.srt`, …).

## Supported formats

| Codec | Output extension | Notes |
|---|---|---|
| ASS / SSA | `.ass` / `.ssa` | Full styling preserved |
| SubRip | `.srt` | |
| WebVTT | `.vtt` | |
| mov_text | `.srt` | |
| PGS (Blu-ray) | `.sup` | Bitmap, copied as-is |
| DVD subtitle | `.sub` | Bitmap, copied as-is |
| DVB subtitle | `.sub` | Bitmap, copied as-is |

All streams are extracted with `-c:s copy` — no re-encoding, no style loss.

## Requirements

- Python >= 3.9
- FFmpeg (with `ffprobe`) available in PATH
