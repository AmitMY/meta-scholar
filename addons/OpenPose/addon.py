import time
from os import path
import os
import multiprocessing
from os.path import exists
from random import randint, shuffle
from urllib.request import URLopener
import getpass

from GPUtil import GPUtil
from jsonlines import jsonlines
from tqdm import tqdm

from addons.OpenPose.pose_util import get_directory_person, compress_OpenPose
from utils.distributed import Distributed
from utils.file_system import makedir

GPUs = len(GPUtil.getGPUs())
user = getpass.getuser()

# slaves = ["nlp01", "nlp02", "nlp03", "nlp05", "nlp06", "nlp09", "nlp10", "nlp11", "nlp12", "nlp13", "nlp14", "nlp15"]
slaves = [
    # "nlp01",
    "nlp02",
    "nlp03",
    "nlp04",
    # "nlp05", Amir
    "nlp06",
    "nlp07",
    "nlp08",
    "nlp09",
    "nlp10",
    "nlp11",
    "nlp12",
    # "nlp13", Can't connect to nlp01
    # "nlp14", Can't connect to nlp01
    "nlp15"
]
d = Distributed("OpenPose", "nlp01", slaves, "addons.OpenPose.addon")
app = d.app  # Must declare the app in the root level

"""
Test it out
nvidia-docker run -it -v /home/nlp/amit/PhD/meta-scholar/utils/../datasets/SLCrawl/versions/SpreadTheSign/videos/20259_lt-lt_0.mp4:/video.mp4 --workdir /openpose openpose /bin/bash
./build/examples/openpose/openpose.bin --video /video.mp4 --model_pose BODY_25 --display 0 --render_pose 0 --write_json /out/ --hand --face --num_gpu 1  --num_gpu_start 1
"""


def clean_dockers():
    d.spread(
        "docker ps -a | awk '{ print \$1,\$2 }' | grep openpose | awk '{print \$1 }' | xargs -I {} docker rm -f {}",
        d.slaves)


@app.task(name="OpenPose_pose_video")
def pose_video(datum):
    if not exists(datum['video']):
        try:
            URLopener().retrieve(datum["video_url"], datum["video"])
        except Exception as e:
            print("Download Failed", datum)
            return False

    if not exists(datum["pose_dir"]):
        # Get a GPU
        gpus = None
        sleeps = 0
        while gpus is None or len(gpus) == 0:
            if gpus is not None:
                time.sleep(10)
                sleeps += 1

                if sleeps > 10:
                    raise Exception("No available GPU to allocate")
            try:
                gpus = GPUtil.getFirstAvailable(order='random', maxLoad=0.05, maxMemory=0.05)
            except:
                gpus = []

        # Create Container
        d_create = "nvidia-docker create -it -v " + datum["video"] + ":/video.mp4 --workdir /openpose openpose"
        print(d_create)
        container_id = os.popen(d_create).read().strip()
        print("Creation Output", container_id)

        def remove_container():
            d_wait = "docker rm -f " + container_id
            print(d_wait)
            os.system(d_wait)

        try:
            # Start Container
            d_start = "docker start " + container_id
            print(d_start)
            status = os.system(d_start)
            if int(status) != 0:
                raise Exception("Start Status " + str(status))

            cmd = "./build/examples/openpose/openpose.bin --video /video.mp4 --model_pose BODY_25 --display 0 --render_pose 0 --write_json /out/ --hand --face --num_gpu 1 "
            cmd += " --num_gpu_start " + str(gpus[0])
            d_exec = "docker exec " + container_id + " bash -c 'cd /openpose && " + cmd + "'"
            print(d_exec)
            status = os.system(d_exec)
            if int(status) != 0:
                raise Exception("Exec Status " + str(status))

            # Copy files
            makedir(datum["pose_dir"])
            d_cp = "nvidia-docker cp " + container_id + ":/out/. " + datum["pose_dir"]
            print(d_cp)
            status = os.system(d_cp)
            if int(status) != 0:
                raise Exception("CP Status " + str(status))
        except Exception as e:
            remove_container()
            raise e
        finally:
            remove_container()

    return True


def download(version, directory: str, dataset: list):
    if version["version"] != "BODY_25":
        raise ValueError("Running this addon version is not implemented")

    shuffle(dataset)

    poses_dir = path.join(directory, "poses")
    makedir(poses_dir)

    # TODO check if openpose image exists on server

    while True:
        existing = {path.join(poses_dir, di) for di in os.listdir(poses_dir)}
        missing_data = []
        for datum in dataset:
            datum["pose_dir"] = path.join(poses_dir, datum["id"])
            if datum["pose_dir"] not in existing:
                missing_data.append(datum)

        # Break when finished
        if len(missing_data) == 0:
            break

        print("Done", len(dataset) - len(missing_data), "/", len(dataset), "tasks")

        d.clear_tasks()
        d.kill(d.slaves)
        clean_dockers()
        d.spawn_workers().flower()
        d.run(pose_video, missing_data[:50000])
        d.kill(d.slaves)
        clean_dockers()

    with jsonlines.open(path.join(directory, "index.jsonl"), mode='w') as writer:
        for datum in tqdm(dataset):
            writer.write({
                "id": datum["id"],
                "poses": [compress_OpenPose(p) for p in get_directory_person(datum["pose_dir"])]
            })


if __name__ == "__main__":
    d.clear_tasks()
    clean_dockers()
    d.kill(d.slaves)
