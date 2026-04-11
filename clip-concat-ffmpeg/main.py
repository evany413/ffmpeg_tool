import ffmpeg
from pathlib import Path

RESOLUTIONS = {
    0: (1920, 1080),
    1: (1280, 720),
    2: (854, 480),
}
RESOLUTION_LABELS = ['1080p', '720p', '480p']

# Bitrate presets per resolution index [1080p, 720p, 480p]
BITRATE_PRESETS = {
    'High':   ['8000k', '5000k', '2500k'],
    'Medium': ['4000k', '2500k', '1500k'],
    'Low':    ['2000k', '1200k',  '800k'],
}
BITRATE_LABELS = list(BITRATE_PRESETS.keys())

VCODEC = 'libx264'      # CPU (cross-platform)
# VCODEC = 'h264_nvenc' # NVIDIA GPU
# VCODEC = 'h264_amf'   # AMD GPU
# VCODEC = 'h264_qsv'   # Intel GPU


def scale_filter(stream, w, h):
    return (
        stream.video
        .filter('scale', w, h, force_original_aspect_ratio='decrease')
        .filter('pad', w=w, h=h, x='(ow-iw)/2', y='(oh-ih)/2')
        .filter('setsar', 1)
    )


def convert_and_concat(folder: Path, videos: list, resolution: int, bitrate: str):
    output_dir = folder / 'output'
    output_dir.mkdir(parents=True, exist_ok=True)

    w, h = RESOLUTIONS[resolution]
    streams = []
    for video in videos:
        inp = ffmpeg.input(str(video))
        streams.append(scale_filter(inp, w, h))
        streams.append(inp.audio)

    joined = ffmpeg.concat(*streams, v=1, a=1).node
    ffmpeg.output(
        joined[0], joined[1],
        str(output_dir / f"{folder.name}.mp4"),
        vsync='vfr',
        vcodec=VCODEC,
        acodec='aac',
        video_bitrate=bitrate,
    ).run(overwrite_output=True)


def prompt_choice(prompt, labels, default: int = 0):
    for idx, label in enumerate(labels):
        marker = ' (default)' if idx == default else ''
        print(f"  {idx + 1}. {label}{marker}")
    try:
        raw = input(prompt).strip()
        if raw == '':
            return default
        choice = int(raw) - 1
        if choice not in range(len(labels)):
            print('Invalid choice.')
            return None
        return choice
    except ValueError:
        print('Invalid input.')
        return None


def main():
    cwd = Path('.')
    subfolders = [f for f in cwd.iterdir() if f.is_dir() and f.name != 'output']

    if not subfolders:
        print('No subfolders found.')
        return

    jobs = []
    for folder in subfolders:
        videos = sorted(f for f in folder.iterdir() if f.is_file() and f.suffix.lower() in {'.mp4', '.mkv'})

        if not videos:
            print(f"Skip: {folder.name} has no video files.")
            continue

        print(f"\n[{folder.name}] Choose resolution:")
        resolution = prompt_choice('Enter resolution: ', RESOLUTION_LABELS, default=0)
        if resolution is None:
            return

        print(f"\n[{folder.name}] Choose bitrate preset:")
        bitrate_idx = prompt_choice('Enter bitrate: ', [
            f"{label} ({BITRATE_PRESETS[label][resolution]})" for label in BITRATE_LABELS
        ], default=2)
        if bitrate_idx is None:
            return

        bitrate = BITRATE_PRESETS[BITRATE_LABELS[bitrate_idx]][resolution]
        jobs.append((folder, videos, resolution, bitrate))

    for folder, videos, resolution, bitrate in jobs:
        print(f"\nConverting {folder.name} -> {RESOLUTION_LABELS[resolution]}, {bitrate}...")
        convert_and_concat(folder, videos, resolution, bitrate)
        print(f"Done: {folder.name}")


if __name__ == "__main__":
    main()
