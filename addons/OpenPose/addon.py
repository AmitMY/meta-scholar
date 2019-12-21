import time
from os import path
import os
import multiprocessing
from os.path import exists
from random import randint, shuffle
from urllib.request import URLopener
import getpass

from GPUtil import GPUtil
from tqdm import tqdm

from utils.distributed import Distributed
from utils.file_system import makedir

GPUs = len(GPUtil.getGPUs())
user = getpass.getuser()

slaves = ["nlp02", "nlp07", "nlp08", "nlp09"]
d = Distributed("OpenPose", "nlp01", slaves, "addons.OpenPose.addon")
app = d.app  # Must declare the app in the root level

"""
Test it out
nvidia-docker run -it -v /home/nlp/amit/PhD/meta-scholar/utils/../datasets/SLCrawl/versions/SpreadTheSign/videos/20259_lt-lt_0.mp4:/video.mp4 --workdir /openpose openpose /bin/bash
./build/examples/openpose/openpose.bin --video /video.mp4 --model_pose BODY_25 --display 0 --render_pose 0 --write_json /out/ --hand --face --num_gpu 1  --num_gpu_start 1
"""


@app.task(name="OpenPose_pose_video")
def pose_video(datum):
    if not exists(datum['video']):
        try:
            URLopener().retrieve(datum["video_url"], datum["video"])
        except Exception as e:
            print("Download Failed", datum)
            return False

    if not exists(datum["pose_dir"]):
        # Create Container
        d_create = "nvidia-docker create -it -v " + datum["video"] + ":/video.mp4 --workdir /openpose openpose"
        print(d_create)
        container_id = os.popen(d_create).read().strip()
        print("Creation Output", container_id)

        # Start Container
        d_start = "docker start " + container_id
        print(d_start)
        os.system(d_start)

        # Exec openpose
        # gpu = GPUtil.getFirstAvailable(order='first', maxLoad=0.1, maxMemory=0.1, attempts=10, interval=30)[0]
        # gpu = randint(0, GPUs - 1)
        gpus = None
        while gpus is None or len(gpus) == 0:
            if gpus is not None:
                time.sleep(10)
            gpus = GPUtil.getFirstAvailable(order='memory', maxLoad=1, maxMemory=0.1)

        cmd = "./build/examples/openpose/openpose.bin --video /video.mp4 --model_pose BODY_25 --display 0 --render_pose 0 --write_json /out/ --hand --face --num_gpu 1 "
        cmd += " --num_gpu_start " + str(gpus[0])
        d_exec = "docker exec " + container_id + " bash -c 'cd /openpose && " + cmd + "'"
        print(d_exec)
        status = os.system(d_exec)
        if int(status) != 0:
            raise Exception("Status " + str(status))

        # Copy files
        makedir(datum["pose_dir"])
        d_cp = "nvidia-docker cp " + container_id + ":/out/. " + datum["pose_dir"]
        print(d_cp)
        os.system(d_cp)

        # Shut down and remove container
        d_wait = "nvidia-docker rm -f " + container_id
        print(d_wait)
        os.system(d_wait)

    return True


def download(version, directory: str, dataset: list):
    if version["version"] != "BODY_25":
        raise ValueError("Running this addon version is not implemented")

    shuffle(dataset)

    poses_dir = path.join(directory, "poses")
    makedir(poses_dir)

    # TODO check if openpose image exists on server

    for datum in dataset:
        datum["pose_dir"] = path.join(directory, "poses", datum["id"])
        # pose_video(datum)

    d.spawn_workers().flower()
    d.run(pose_video, dataset[:50000])

    # processes = min(GPUs * 2, multiprocessing.cpu_count() - 1)
    # processes = 1
    # pool = multiprocessing.Pool(processes)
    # list(tqdm(pool.imap(pose_video, dataset), total=len(dataset[:1])))

    raise Exception("Didn't return anything")
    # with jsonlines.open(path.join(directory, "index.jsonl"), mode='w') as writer:
    #     for row in res:
    #         writer.write(row)
