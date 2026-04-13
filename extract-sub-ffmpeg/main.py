import subprocess
import json
from pathlib import Path

# Configuration
script_dir    = Path(__file__).parent
output_folder = script_dir / 'Output'

# Codec -> file extension mapping (preserves original format and styling)
CODEC_EXT = {
    'ass':            '.ass',
    'ssa':            '.ssa',
    'subrip':         '.srt',
    'webvtt':         '.vtt',
    'mov_text':       '.srt',
    'dvd_subtitle':   '.sub',
    'hdmv_pgs_subtitle': '.sup',
    'dvb_subtitle':   '.sub',
    'text':           '.txt',
}

def probe(path: Path) -> dict:
    result = subprocess.run(
        ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_streams', str(path)],
        capture_output=True, text=True, encoding='utf-8'
    )
    return json.loads(result.stdout)


def get_subtitle_streams(probe_data: dict) -> list[dict]:
    return [s for s in probe_data.get('streams', []) if s.get('codec_type') == 'subtitle']


def extract_subtitle(vid_path: Path, stream_index: int, codec_name: str, out_path: Path):
    """Extract a single subtitle stream from vid_path into out_path."""
    cmd = [
        'ffmpeg', '-y',
        '-i', str(vid_path),
        '-map', f'0:{stream_index}',
        '-c:s', 'copy',   # Copy codec as-is to preserve format/styling
        str(out_path)
    ]

    # bitmap-based subtitles (PGS / DVD) can't be text-extracted, copy as-is
    if codec_name in ('hdmv_pgs_subtitle', 'dvd_subtitle', 'dvb_subtitle'):
        pass  # copy is already correct

    result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip())


def main():
    output_folder.mkdir(parents=True, exist_ok=True)

    mkv_files = sorted(script_dir.glob('*.mkv'))

    if not mkv_files:
        print("No MKV files found in the script directory.")
        return

    for vid_path in mkv_files:

        print(f"\nProcessing: {vid_path.name}")

        try:
            probe_data = probe(vid_path)
        except Exception as e:
            print(f"  Error probing file: {e}")
            continue

        sub_streams = get_subtitle_streams(probe_data)

        if not sub_streams:
            print("  No subtitle streams found.")
            continue

        print(f"  Found {len(sub_streams)} subtitle stream(s).")

        for sub in sub_streams:
            idx        = sub['index']
            codec      = sub.get('codec_name', 'unknown')
            tags       = sub.get('tags', {})
            lang       = tags.get('language', 'und')
            title      = tags.get('title', '').replace(' ', '_')
            ext        = CODEC_EXT.get(codec, f'.{codec}')

            # Build output filename: <video_stem>.<lang>[.<title>].<ext>
            stem = vid_path.stem
            name_parts = [stem, lang]
            if title:
                name_parts.append(title)
            out_name = '.'.join(name_parts) + ext
            out_path = output_folder / out_name

            # Avoid overwriting if multiple streams share same lang+title
            counter = 1
            while out_path.exists():
                name_parts_c = [stem, lang]
                if title:
                    name_parts_c.append(title)
                name_parts_c.append(str(counter))
                out_path = output_folder / ('.'.join(name_parts_c) + ext)
                counter += 1

            print(f"  [{idx}] {codec} / {lang}{' / ' + title if title else ''} -> {out_path.name}")

            try:
                extract_subtitle(vid_path, idx, codec, out_path)
                print(f"       Saved: {out_path.name}")
            except Exception as e:
                print(f"       Error: {e}")

    print("\nDone.")


if __name__ == '__main__':
    main()
