import ffmpeg
import os
from pathlib import Path

vid_list = []
sub_list = []
output_folder = './Output/'

# read video list
with open('vid_list.txt', 'r', encoding='UTF-8') as file:
    while (line := file.readline().rstrip()):
        vid_list.append(line)
        print(line)

# read subtitle list
with open('sub_list.txt', 'r', encoding='UTF-8') as file:
    while (line := file.readline().rstrip()):
        sub_list.append(line)
        print(line)

size = len(vid_list)
# iterate through the files
for i in range(size):
    vid = vid_list[i]
    sub = sub_list[i]

    # determine file extension
    name, ext = os.path.splitext(vid)

    # check file exist or not
    try:
        with open(vid):
            pass
        
        # create output folder
        Path(output_folder).mkdir(parents=True, exist_ok=True)

        in_stream = ffmpeg.input(vid)
        v = in_stream.video.filter("subtitles", sub)
        a = in_stream.audio

        ffmpeg.output(v, a, output_folder + name + '.mp4', vcodec='libx264', acodec='aac').run()
        print("Finished converting {}".format(vid))

    except IOError:
        print("{} not exists.".format(vid))
