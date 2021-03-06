from os import path
import os
from os.path import exists
from urllib.request import URLopener

from jsonlines import jsonlines
from tqdm import tqdm

from addons.OpenPose.pose_util import get_directory_person, compress_frames
from utils.distributed_nlp_cluster import distributed
from utils.docker import Docker
from utils.file_system import makedir
from utils.gpu import get_empty_gpu

distributed.module_path = "addons.OpenPose.addon"
app = distributed.app  # Must declare the app in the root level

DOCKER_NAME = "openpose"


def clean_dockers():
    distributed.spread(Docker.kill_cmd(DOCKER_NAME), distributed.slaves)


@app.task(name="OpenPose_pose_video")
def pose_video(datum):
    if not exists(datum['video']):
        try:
            URLopener().retrieve(datum["video_url"], datum["video"])
        except Exception as e:
            makedir(datum["pose_dir"]) # Empty directory

    if not exists(datum["pose_dir"]):
        gpu = get_empty_gpu()

        # Create Container
        container_id = Docker.create_container(DOCKER_NAME, "-it -v " + datum["video"] + ":/video.mp4")

        def remove_container():
            Docker.remove_container(container_id)

        try:
            # Start Container
            Docker.start_container(container_id)

            cmd = "./build/examples/openpose/openpose.bin --video /video.mp4 --model_pose BODY_25 --display 0 --render_pose 0 --write_json /out/ --hand --face --num_gpu 1 "
            cmd += " --num_gpu_start " + str(gpu)
            Docker.exec_container(container_id, "bash -c 'cd /openpose && " + cmd + "'")

            # Copy files
            Docker.cp_container_directory(container_id, datum["pose_dir"], "/out/")
        except Exception as e:
            remove_container()
            raise e
        finally:
            remove_container()

    return True


def download(version, directory: str, dataset: list):
    if version["version"] != "BODY_25":
        raise ValueError("Running this addon version is not implemented")

    poses_dir = path.join(directory, "poses")
    makedir(poses_dir)

    Docker.verify_image_exists(DOCKER_NAME)

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

        distributed.clear_tasks()
        distributed.kill_slaves()
        clean_dockers()
        distributed.spawn_workers().flower()
        distributed.run(pose_video, missing_data[:50000])
        distributed.kill_slaves()
        clean_dockers()

    with jsonlines.open(path.join(directory, "index.jsonl"), mode='w') as writer:
        for datum in tqdm(dataset):
            writer.write({
                "id": datum["id"],
                "poses": compress_frames(get_directory_person(datum["pose_dir"]))
            })
