import sys
from os import path

import subprocess

ffmpeg_path = "/".join(sys.executable.split("/")[:-1] + ["ffmpeg"])


class FFmpeg:

    @staticmethod
    def check_installed():
        if not path.exists(ffmpeg_path):
            raise Exception("Missing ffmpeg! Looked in '" + ffmpeg_path + "' - please run 'conda install ffmpeg'")

    @staticmethod
    def video_from_frames(frames_dir, number_length, output_video):
        if frames_dir[-1] != "/":
            frames_dir += "/"

        pattern = "\"" + frames_dir + "%0" + str(number_length) + "d.jpg\""
        cmd = ffmpeg_path + " -framerate 24 -hide_banner -loglevel panic -i " + pattern + " " + output_video

        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
        (out, err) = proc.communicate()

        if err is not None:
            raise Exception("FFmpeg Error " + str(err))
