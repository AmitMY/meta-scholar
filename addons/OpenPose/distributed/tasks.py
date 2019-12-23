import os
from os import path
from os.path import exists

from jsonlines import jsonlines
from tqdm import tqdm

from addons.OpenPose.pose_util import get_directory_person
from utils.dataset import load
from utils.file_system import makedir, listdir

if __name__ == "__main__":
    version = {"version": "BODY_25"}
    directory = "/home/nlp/amit/PhD/meta-scholar/datasets/SLCrawl/versions/SpreadTheSign/OpenPose/BODY_25"
    dataset = load("SLCrawl", version="SpreadTheSign")[:400000]

    poses_dir = path.join(directory, "poses")
    makedir(poses_dir)

    existing = {path.join(poses_dir, d) for d in os.listdir(poses_dir)}
    print("Existing", len(existing))

    new_data = []

    with jsonlines.open("sample.jsonl", mode='w') as writer:
        tasks = 0
        for datum in tqdm(dataset):
            datum["pose_dir"] = path.join(poses_dir, datum["id"])
            if datum["pose_dir"] not in existing:
                tasks += 1
                # pose_distributed.delay(datum)
            else:
                datum["OpenPose"] = {"BODY_25": get_directory_person(datum["pose_dir"])}
                writer.write(datum)



    print("Created", tasks, "tasks")