import os
import shutil
import ffmpeg
from pathlib import Path


# Prefer the project-local full build, keeping probe and encode versions aligned.
local_bin = Path(__file__).resolve().parent.parent / '.tools' / 'ffmpeg' / 'bin'
executable_suffix = '.exe' if os.name == 'nt' else ''
local_ffmpeg = local_bin / f'ffmpeg{executable_suffix}'
local_ffprobe = local_bin / f'ffprobe{executable_suffix}'
ffmpeg_cmd = str(local_ffmpeg) if local_ffmpeg.is_file() else 'ffmpeg'
ffprobe_cmd = str(local_ffprobe) if local_ffprobe.is_file() else 'ffprobe'

# Configuration
vid_list_file = Path('vid_list.txt')
sub_list_file = Path('sub_list.txt')
output_folder = Path('./Output')
video_encoder = os.environ.get(
    'VIDEO_ENCODER',
    'h264_nvenc' if os.name == 'nt' else 'libx264',
)

# Ensure output directory exists
output_folder.mkdir(parents=True, exist_ok=True)

# Read lists (using pathlib's read_text and splitlines for clean parsing)
try:
    vid_lines = [p.strip() for p in vid_list_file.read_text(encoding='UTF-8').splitlines() if p.strip()]
    sub_lines = [p.strip() for p in sub_list_file.read_text(encoding='UTF-8').splitlines() if p.strip()]
except FileNotFoundError as e:
    print(f"Error: Required list file not found - {e}")
    exit(1)

# Iterate through the files
for v_str, s_str in zip(vid_lines, sub_lines):
    vid_path = Path(v_str)
    sub_path = Path(s_str)

    if not vid_path.exists():
        print(f"Skip: {vid_path.name} does not exist.")
        continue

    print(f"Processing: {vid_path.name}")

    temp_sub = Path(f"temp_sub{sub_path.suffix}")
    shutil.copy(sub_path, temp_sub)

    try:
        # 1. Probe video information
        probe = ffmpeg.probe(str(vid_path), cmd=ffprobe_cmd)
        video_stream = next(s for s in probe['streams'] if s['codec_type'] == 'video')

        # Get original bitrate in bps
        orig_bitrate = int(video_stream.get('bit_rate') or probe['format'].get('bit_rate') or 0)

        # 2. Determine Bitrate Cap (2000k = 2,000,000 bps)
        # If original is lower than 2000k, keep original; otherwise, cap at 2000k.
        if 0 < orig_bitrate < 2000000:
            target_bitrate = f"{int(orig_bitrate / 1000)}k"
            print(f"  -> Low bitrate detected ({target_bitrate}). Keeping original quality.")
        else:
            target_bitrate = "2000k"
            print(f"  -> Capping bitrate at {target_bitrate}.")

        # 3. Define output path
        # Changes extension to .mp4 and places it in the Output folder
        out_file = output_folder / vid_path.with_suffix('.mp4').name

        # 4. FFmpeg Stream Pipeline
        stream = ffmpeg.input(str(vid_path))

        # Hardcode subtitles. Only videos larger than 1080p are scaled down;
        # smaller videos keep their original dimensions and aspect ratio.
        v = stream.video.filter("subtitles", str(temp_sub))
        source_width = int(video_stream['width'])
        source_height = int(video_stream['height'])
        if source_width > 1920 or source_height > 1080:
            v = v.filter(
                "scale",
                1920,
                1080,
                force_original_aspect_ratio="decrease",
                force_divisible_by=2,
            )
            print(
                f"  -> Scaling {source_width}x{source_height} down within "
                "1920x1080 while preserving aspect ratio."
            )
        else:
            print(f"  -> Keeping original dimensions: {source_width}x{source_height}.")
        a = stream.audio

        # Output settings
        ffmpeg.output(
            v, a,
            str(out_file),
            vcodec=video_encoder,
            acodec='aac',
            video_bitrate=target_bitrate,
            pix_fmt='yuv420p'
        ).global_args('-xerror').run(cmd=ffmpeg_cmd, overwrite_output=True)

        print(f"Done: {out_file.name} saved successfully.")

    except Exception as e:
        print(f"Error processing {vid_path.name}: {e}")

    finally:
        temp_sub.unlink(missing_ok=True)
