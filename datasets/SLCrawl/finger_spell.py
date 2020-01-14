import string
from os import path

from urllib.request import urlretrieve

import cv2
import numpy as np
from tqdm import tqdm

from addons.FFmpeg.ffmpeg_utils import FFmpeg
from utils.dataset import load
from utils.file_system import temp_name, temp_dir, makedir


def download_FingerSpell(version, directory):
    FFmpeg.check_installed()

    letters = ['rest'] + list(string.ascii_lowercase)

    animated = {
        "j": temp_name(".jpg"),
        "z": temp_name(".jpg")
    }

    for l, f in list(animated.items()):
        urlretrieve(version["url"] + l+"-begin_"+l+"-end.jpg", f)
        animated[l] = cv2.imread(f)

    videos_path = path.join(directory, "videos")
    makedir(videos_path)

    for l1 in tqdm(letters):
        for l2 in tqdm(letters):
            is_l2_animated = l2 in animated
            is_l1_animated = l1 in animated

            text = (l1 + l2).replace("rest", "")
            gloss ="" if l1 == l2 == "rest" else l2 + "#" if l1 == "rest" else "#" + l1 if l2 == "rest" else "#" + l1 + "# #" + l2 + "#"

            download_l1 = l1
            download_l2 = l2
            if is_l2_animated:
                download_l2 = download_l2 + "-begin"
            if is_l1_animated:
                download_l1 = download_l1 + "-end"

            full_url = version["url"] + download_l1 + "_" + download_l2 + ".jpg"

            video_path = path.join(videos_path, text + ".mp4")
            if not path.exists(video_path):
                temp = temp_name(".jpg")
                urlretrieve(full_url, temp)
                img = cv2.imread(temp)

                if is_l2_animated and not is_l1_animated:
                    img = np.concatenate((img, animated[l2]))
                if is_l1_animated and not is_l2_animated:
                    img = np.concatenate((animated[l1], img))

                imgs = img.reshape((int(img.shape[0] / 256), 256, 256, 3))

                temp_dir_name = temp_dir()
                for i, im in enumerate(imgs):
                    cv2.imwrite(temp_dir_name + str(i).zfill(2) + ".jpg", im)

                FFmpeg.video_from_frames(temp_dir_name, 2, video_path)

            yield {
                "id": text if text != "" else "rest",
                "texts": [{"text": text}],
                "gloss": gloss,
                "video": video_path,
                "video_url": full_url,
                "sign_language": "en.us",
                "text_language": "English",
                "metadata": {
                    "width": 256,
                    "height": 256
                }
            }


if __name__ == "__main__":
    load("SLCrawl", version="FingerSpell", addons=[{"name": "GooglePose"}])
