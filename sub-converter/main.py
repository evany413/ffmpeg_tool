import subprocess
from pathlib import Path

INPUT_DIR = Path(__file__).parent
OUTPUT_DIR = INPUT_DIR / "Output"
SUPPORTED_EXTENSIONS = {'.ass', '.ssa', '.aas', '.ssa'}

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

sub_files = [
    f for f in INPUT_DIR.iterdir()
    if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS
]

if not sub_files:
    print("No subtitle files found (.ass / .ssa / .aas). Drop them into this folder and re-run.")
else:
    for sub in sub_files:
        out_file = OUTPUT_DIR / sub.with_suffix('.srt').name
        print(f"Converting: {sub.name} -> {out_file.name}")
        try:
            result = subprocess.run(
                ['ffmpeg', '-y', '-i', str(sub), str(out_file)],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                print(f"  Done: {out_file.name}")
            else:
                print(f"  Error: {result.stderr.strip()}")
        except FileNotFoundError:
            print("  Error: ffmpeg not found. Make sure ffmpeg is installed and in PATH.")
            break

print("\nFinished.")
