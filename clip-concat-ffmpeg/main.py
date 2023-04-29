# use ffmpeg to convert video to 1080p or 720p
# and then concat all videos in subfolder

import os
import ffmpeg

resolutions = ['1080p', '720p', '480p']


def create_test_case():
    folders = ['fc2-ppv-1473962', 'fc2-ppv-1473963', 'fc2-ppv-1473964']
    # create folders
    for folder in folders:
        os.mkdir(folder)
        # create 3 test videos in each folder with sequence number
        for i in range(3):
            video_name = folder + '-' + str(i + 1) + '.mp4'
            open(folder + '/' + video_name, 'w').close()


def convert_and_concat(folder, videos, resolution):
    # create output folder
    if not os.path.exists(f"{folder.path}/output"):
        os.mkdir(f"{folder.path}/output")

    streams = []
    for video in videos:
        # convert video to 1080p or 720p
        input = ffmpeg.input(video)

        if resolution == 0:
            v = input.video.filter('scale', 1920, 1080, force_original_aspect_ratio='decrease').filter('pad', w=1920, h=1080, x='(ow-iw)/2', y='(oh-ih)/2').filter('setsar', 1)
            a = input.audio
        elif resolution == 1:
            v = input.video.filter('scale', 1280, 720, force_original_aspect_ratio='decrease').filter('pad', w=1280, h=720, x='(ow-iw)/2', y='(oh-ih)/2').filter('setsar', 1)
            a = input.audio
        elif resolution == 2:
            v = input.video.filter('scale', 854, 480, force_original_aspect_ratio='decrease').filter('pad', w=854, h=480, x='(ow-iw)/2', y='(oh-ih)/2').filter('setsar', 1)
            a = input.audio

        # add to stream list
        streams.append(v)
        streams.append(a)

    # concat streams
    # [v0][0:a:0][v1][1:a:0][v2][2:a:0]concat=n=3:v=1:a=1[v][a]" -map "[v]" -map "[a]" output.mp4
    joined = ffmpeg.concat(*streams, v=1, a=1).node
    v = joined[0]
    a = joined[1]
    out = ffmpeg.output(v, a, f"{folder.path}/output/{folder.name}.mp4", vsync='vfr', vcodec='libx264', acodec='aac', strict='experimental')
    out.run()


def main():
    # create_test_case()

    jobs = []

    # get all subfolders
    subfolders = [f for f in os.scandir('.') if f.is_dir()]

    # get all videos in subfolders
    for folder in subfolders:
        # get all videos(mp4, mkv) in subfolder
        videos = [f.path for f in os.scandir(folder) if f.is_file() and (f.path.endswith('.mp4') or f.path.endswith('.mkv'))]
        videos.sort()

        # convert videos to user choose resolution
        print(f"Choose resolution for {folder.name}: ")
        for idx, res in enumerate(resolutions):
            print(f"{idx + 1}. {res}")
        resolution = 0
        try:
            resolution = int(input('Enter resolution: ')) - 1
            if resolution < 0 or resolution > 2:
                print('Invalid resolution')
                exit()
        except ValueError:
            print('Invalid input')
            exit()

        jobs.append((folder, videos, resolution))

    # convert videos to 1080p, 720p or 480p
    for job in jobs:
        print(f"Converting {job[0].name} to {resolutions[job[2]]}...")
        convert_and_concat(job[0], job[1], job[2])


if __name__ == "__main__":
    main()
