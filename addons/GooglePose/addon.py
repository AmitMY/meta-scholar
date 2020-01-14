from os import path
import os
from os.path import exists

from jsonlines import jsonlines
from tqdm import tqdm

from addons.GooglePose.pose_util import get_directory_hands
from utils.dataset import load
from utils.distributed_nlp_cluster import distributed
from utils.docker import Docker
from utils.file_system import makedir

distributed.module_path = "addons.GooglePose.addon"
app = distributed.app  # Must declare the app in the root level

DOCKER_NAME = "google-pose"


def clean_dockers():
    distributed.spread(Docker.kill_cmd(DOCKER_NAME), distributed.slaves)


@app.task(name="GooglePose_pose_video")
def pose_video(datum):
    if not exists(datum['video']):
        raise Exception("Video doesn't exist")

    if not exists(datum["pose_dir"]):
        # Create Container
        container_id = Docker.create_container(DOCKER_NAME, "-it -v " + datum["video"] + ":/video.mp4")

        def remove_container():
            Docker.remove_container(container_id)

        try:
            Docker.start_container(container_id)  # Start Container
            Docker.exec_container(container_id, "python /api/pose_video.py")  # Pose video
            Docker.cp_container_directory(container_id, datum["pose_dir"], "/out/")  # Copy files
            remove_container() # Remove container
        except Exception as e:
            remove_container() # Remove container
            raise e


    return True


def download(version, directory: str, dataset: list):
    if version["version"] != "Mediapipe":
        raise ValueError("Running this addon version is not implemented")

    poses_dir = path.join(directory, "poses")
    makedir(poses_dir)

    Docker.verify_image_exists(DOCKER_NAME)

    should_cleanup = False
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

        print(missing_data)

        should_cleanup = True
        print("Done", len(dataset) - len(missing_data), "/", len(dataset), "tasks")

        # should_cleanup = False
        # for datum in tqdm(missing_data):
        #     pose_video(datum)

        distributed.clear_tasks()
        distributed.kill_slaves()
        clean_dockers()
        distributed.spawn_workers().flower()
        distributed.run(pose_video, missing_data[:50000])

    if should_cleanup:
        distributed.kill_slaves()
        clean_dockers()

    with jsonlines.open(path.join(directory, "index.jsonl"), mode='w') as writer:
        for datum in tqdm(dataset):
            writer.write({
                "id": datum["id"],
                "poses": get_directory_hands(datum["pose_dir"])
            })


if __name__ == "__main__":
    load("ChicagoFSWild", version="ChicagoFSWild", addons=[{"name": "GooglePose"}])
    # load("SLCrawl", version="SpreadTheSign", addons=[{"name": "GooglePose"}])
    # load('SLCrawl', version='SpreadTheSign', addons=[{"name": "OpenPose"}, {"name": "GooglePose"}])