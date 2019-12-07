# python -m addons.OpenPose.distributed.tasks
from os import path

from addons.OpenPose.distributed.pose import pose_distributed
from utils.dataset import load
from utils.file_system import makedir

if __name__ == "__main__":
    version = {"version": "BODY_25"}
    directory = "/home/nlp/amit/PhD/meta-scholar/datasets/SLCrawl/versions/SpreadTheSign/OpenPose/BODY_25"
    dataset = load("SLCrawl", version="SpreadTheSign")[:5000]

    poses_dir = path.join(directory, "poses")
    makedir(poses_dir)

    for datum in dataset:
        datum["pose_dir"] = path.join(directory, "poses", datum["id"])

        pose_distributed.delay(datum)
