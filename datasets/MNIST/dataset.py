import json
import string
import zipfile
from collections import defaultdict
from os import path
from urllib.request import urlretrieve

import jsonlines
import numpy as np
from PIL import Image
from tqdm import tqdm

from utils.file_system import makedir, temp_dir


def download_digits(images_dir):
    from keras.datasets import mnist
    mnist_data = mnist.load_data()

    for split, (x, y) in zip(["train", "test"], mnist_data):
        split_dir = path.join(images_dir, split)
        makedir(split_dir)

        for i, (image, label) in enumerate(zip(x, y)):
            f_name = str(label) + "_" + str(i) + ".png"
            Image.fromarray(image).save(path.join(split_dir, f_name))

            yield split, {
                "label": str(label),
                "image": "/".join([split, f_name])
            }


def download_sign_language(version, images_dir):
    labels = string.ascii_lowercase

    temp = temp_dir()

    file_handle, _ = urlretrieve(version["url"])
    with zipfile.ZipFile(file_handle, 'r') as zipObj:
        zipObj.extractall(temp)

    for split in ["train", "test"]:
        split_dir = path.join(images_dir, split)
        makedir(split_dir)

        csv = [[int(r) for r in row.split(",")]
               for row in open(path.join(temp, "sign_mnist_" + split + ".csv")).readlines()[1:]]
        for i, row in enumerate(csv):
            label = labels[row.pop(0)]
            image = np.array(row, dtype=np.uint8).reshape((28, 28))

            f_name = label + "_" + str(i) + ".png"
            Image.fromarray(image).save(path.join(split_dir, f_name))

            yield split, {
                "label": label,
                "image": "/".join([split, f_name])
            }


def download(version, directory):
    images_dir = path.join(directory, "images")
    makedir(images_dir)

    if version["version"] == "digits":
        res = download_digits(images_dir)
    elif version["version"] == "sign-language":
        res = download_sign_language(version, images_dir)
    else:
        raise ValueError("Downloading this version is not implemented")

    splits = defaultdict(list)

    with jsonlines.open(path.join(directory, "index.jsonl"), mode='w') as writer:
        for i, (split, row) in tqdm(enumerate(res)):
            splits[split].append(i)
            row["image"] = "images/" + row["image"]
            writer.write(row)

    json.dump(splits, open(path.join(directory, 'split.json'), "w"))
