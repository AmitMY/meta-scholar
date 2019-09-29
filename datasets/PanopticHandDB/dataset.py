import json
import math
import os
import string
import zipfile
from collections import defaultdict
from os import path
from shutil import copyfile
from urllib.request import urlretrieve

import jsonlines
import numpy as np
from PIL import Image
from tqdm import tqdm

from utils.file_system import makedir, temp_dir


def download_manual(version, images_dir):
    temp = temp_dir()

    file_handle, _ = urlretrieve(version["url"])
    with zipfile.ZipFile(file_handle, 'r') as zipObj:
        zipObj.extractall(temp)

    labels_dir = path.join(temp, "hand_labels")

    for split in ["train", "test"]:
        original_split_dir = path.join(labels_dir, "manual_" + split)

        split_dir = path.join(images_dir, split)
        makedir(split_dir)

        files = sorted([f for f in os.listdir(original_split_dir) if f.endswith('.json')])
        for file in files:
            content = json.load(open(path.join(original_split_dir, file), "r"))

            fname = file.replace(".json", ".jpg")

            # Crop image
            all_x, all_y, _ = zip(*content["hand_pts"])
            size = round(max(max(all_x) - min(all_x), max(all_y) - min(all_y)) / 2)

            x = min(all_x) - size
            y = min(all_y) - size

            im = Image.open(path.join(original_split_dir, fname))
            crop = im.crop((x, y, x + 4 * size, y + 4 * size))
            crop.save(path.join(split_dir, fname))

            yield split, {
                "image": "/".join(["images", split, fname]),
                "hand": "left" if content["is_left"] else "right",
                "pose": [(x1 - x, y1 - y, z) for x1, y1, z in content["hand_pts"]]
            }


def download_synthetic(version, images_dir):
    temp = temp_dir()
    temp = "C:\\Users\\Amit\\AppData\\Local\\Temp\\tmpx6quakap\\"
    # file_handle, _ = urlretrieve(version["url"])
    # with zipfile.ZipFile(file_handle, 'r') as zipObj:
    #     zipObj.extractall(temp)

    labels_dir = path.join(temp, "hand_labels_synth")

    for split in ['synth1', 'synth2', 'synth3', 'synth4']:
        original_split_dir = path.join(labels_dir, split)

        split_dir = path.join(images_dir, split)
        makedir(split_dir)

        files = sorted([f for f in os.listdir(original_split_dir) if f.endswith('.json')])
        for file in files:
            content = json.load(open(path.join(original_split_dir, file), "r"))
            fname = file.replace(".json", ".jpg")

            copyfile(path.join(original_split_dir, fname), path.join(split_dir, fname))

            yield split, {
                "image": "/".join(["images", split, fname]),
                "hand": "left" if content["is_left"] else "right",
                "pose": content["hand_pts"]
            }


def download(version, directory):
    images_dir = path.join(directory, "images")
    makedir(images_dir)

    if version["version"] == "manual":
        res = download_manual(version, images_dir)
    elif version["version"] == "synthetic":
        res = download_synthetic(version, images_dir)
    else:
        raise ValueError("Downloading this version is not implemented")

    splits = defaultdict(list)

    with jsonlines.open(path.join(directory, "index.jsonl"), mode='w') as writer:
        for i, (split, row) in tqdm(enumerate(res)):
            splits[split].append(i)
            writer.write(row)

    json.dump(splits, open(path.join(directory, 'split.json'), "w"))
