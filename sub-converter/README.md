# sub-converter

Batch-convert subtitle files (ASS / SSA / AAS) to SRT using FFmpeg. Drop subtitle files into this folder and run the script — converted `.srt` files are saved to `Output/`.

## Requirements

- Python >= 3.9
- FFmpeg installed and available in PATH

## Usage

1. Drop one or more subtitle files into this folder (`sub-converter/`)
2. Run:

```bash
python main.py
```

Converted `.srt` files are saved to the `Output/` folder with the same filename.

## Supported Input Formats

| Extension | Format |
|-----------|--------|
| `.ass`    | Advanced SubStation Alpha |
| `.ssa`    | SubStation Alpha |
| `.aas`    | Alternative SubStation Alpha |

## Notes

- Files already in SRT format do not need conversion.
- Existing output files are overwritten automatically (`-y` flag).
- FFmpeg must be installed and accessible from the command line.
