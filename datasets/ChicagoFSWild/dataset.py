import csv
import json
import sys
from collections import defaultdict
from os import path, remove, popen, system, removedirs
import jsonlines
import tarfile
import wget
from tqdm import tqdm

from datasets.SLCrawl.util import word2chars
from utils.dataset import load
from utils.file_system import makedir


def download(version, directory: str):
    # First check if FFMPEG is installed
    ffmpeg_path = "/".join(sys.executable.split("/")[:-1] + ["ffmpeg"])
    if not path.exists(ffmpeg_path):
        raise Exception("Missing ffmpeg! Looked in '" + ffmpeg_path + "' - please run 'conda install ffmpeg'")

    dataset_directory = path.join(directory, "dataset")
    if not path.exists(dataset_directory):
        dataset_file = path.join(directory, "dataset.tgz")
        if not path.exists(dataset_file):
            print("Downloading Archive")
            wget.download(version["url"], dataset_file)

        print("Extracting Archive")
        tar = tarfile.open(dataset_file)
        tar.extractall(path=dataset_directory)
        tar.close()

        remove(dataset_file)

    archive_directory = path.join(dataset_directory, version["version"]) \
        if version["version"] == "ChicagoFSWild" else dataset_directory

    frames_directory = path.join(archive_directory, "frames")
    if not path.exists(frames_directory):
        print("Extracting Frames Archive")
        tar = tarfile.open(path.join(archive_directory, version["version"] + "-Frames.tgz"))
        tar.extractall(path=frames_directory)
        tar.close()

    if version["version"] == "ChicagoFSWildPlus":
        frames_directory = path.join(frames_directory, version["version"])

    videos_directory = path.join(directory, "videos")
    makedir(videos_directory)

    splits = defaultdict(list)
    data = []

    if version["version"] == "ChicagoFSWild":
        print("Note! While ChicagoFSWild contains hand bounding boxes, we do not load them at this time.")

    with open(path.join(archive_directory, version["version"] + ".csv")) as csv_file:
        csv_data = csv.reader(csv_file, delimiter=',')
        next(csv_data)  # Ignore the header
        for i, row in tqdm(enumerate(csv_data)):
            # As this ID will be used for file naming, lets make it work by default
            datum_id = row[1].replace("/", "-").replace("_(youtube)", "").replace("_(nad)", "")

            # Convert Frames to a video
            datum_frames = path.join(frames_directory, row[1])
            datum_video = path.join(videos_directory, datum_id + ".mp4")
            if not path.exists(datum_video):
                cmd = ffmpeg_path + " -framerate 24 -hide_banner -loglevel panic -i \"" + datum_frames + "/%04d.jpg\" " + datum_video + ""
                status = system(cmd)
                if int(status) != 0:
                    print(cmd)
                    raise Exception("FFMPEG Status " + str(status))

            data.append({
                "id": datum_id,
                "texts": [
                    {"text": row[7]}
                ],
                "gloss": word2chars(row[7]),
                "description": row[9],
                "video_url": row[2],
                "video": datum_video,
                "timing": {
                    "start": row[3],
                },
                "sign_language": "en.us",
                "text_language": "en",
                "signer": {
                    "name": row[-1]
                },
                "metadata": {
                    "frames": row[4],
                    "width": int(row[5]),
                    "height": int(row[6])
                }
            })

            splits[row[10]].append(i)


    with jsonlines.open(path.join(directory, "index.jsonl"), mode='w') as writer:
        for datum in data:
            writer.write(datum)

    json.dump(dict(splits), open(path.join(directory, "split.json"), "w"))


if __name__ == "__main__":
    # dataset = load("ChicagoFSWild", version="ChicagoFSWild", addons=[{"name": "OpenPose"}])
    dataset = load("ChicagoFSWild", version="ChicagoFSWildPlus", addons=[{"name": "OpenPose"}])
    print(dataset[0])
