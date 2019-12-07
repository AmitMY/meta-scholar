from os import path
import os
import multiprocessing
from os.path import exists
from random import randint, shuffle
from urllib.request import URLopener
import getpass

from GPUtil import GPUtil
from tqdm import tqdm

from utils.file_system import makedir

GPUs = len(GPUtil.getGPUs())
user = getpass.getuser()


def pose_video(datum):
    if not exists(datum['video']):
        try:
            URLopener().retrieve(datum["video_url"], datum["video"])
        except Exception as e:
            print("Download Failed", datum)
            return False

    if not exists(datum["pose_dir"]):
        # Create Container
        d_create = "nvidia-docker create -it --rm -v " + datum["video"] + ":/video.mp4 --workdir /openpose amitmy/openpose"
        print(d_create)
        container_id = os.popen(d_create).read().strip()

        # Start Container
        d_start = "docker start " + container_id
        print(d_start)
        os.system(d_start)

        # Exec openpose
        cmd = "./build/examples/openpose/openpose.bin --video /video.mp4 --model_pose BODY_25 --display 0 --render_pose 0 --write_json /out/ --hand --face --num_gpu 1 "
        cmd += " --num_gpu_start " + str(randint(0, GPUs - 1))
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

    for datum in dataset:
        datum["pose_dir"] = path.join(directory, "poses", datum["id"])

    for datum in tqdm(dataset):
        pose_video(datum)

    # processes = min(GPUs * 2, multiprocessing.cpu_count() - 1)
    # processes = 1
    # pool = multiprocessing.Pool(processes)
    # list(tqdm(pool.imap(pose_video, dataset), total=len(dataset[:1])))

    raise Exception("Didn't return anything")
    # with jsonlines.open(path.join(directory, "index.jsonl"), mode='w') as writer:
    #     for row in res:
    #         writer.write(row)
