import json
import os
import urllib
from os import path
import zipfile
from urllib.request import urlretrieve
import csv

from tqdm import tqdm
from utils.file_system import makedir, listdir

base = path.dirname(path.abspath(__file__))


def download(version="1.02"):
    versions_dir = path.join(base, "versions")
    makedir(versions_dir)
    version_dir = path.join(versions_dir, version)
    makedir(version_dir)

    header = json.load(open(path.join(base, "header.json")))
    versions = [v for v in header["versions"] if v["version"] == version]
    if len(versions) == 0:
        raise ValueError("Version not found")

    print("The PIG dataset requires authentication, which is granted to everyone who requests it.")
    print("You can register in: http://beam.kisarazu.ac.jp/~saito/research/PianoFingeringDataset/register.php")
    print("")

    username = input("Insert your username:")
    password = input("Insert your password:")

    url = versions[0]["url"]

    # Make further requests authenticated
    password_mgr = urllib.request.HTTPPasswordMgrWithDefaultRealm()
    password_mgr.add_password(None, url, username, password)
    handler = urllib.request.HTTPBasicAuthHandler(password_mgr)
    urllib.request.install_opener(urllib.request.build_opener(handler))

    raw_dir = path.join(version_dir, "raw")
    makedir(raw_dir)

    file_handle, _ = urlretrieve(url)
    with zipfile.ZipFile(file_handle, 'r') as zipObj:
        zipObj.extractall(raw_dir)

    print("Download done")

    dataset = []

    raw_dataset_dir = path.join(raw_dir, os.listdir(raw_dir)[0])

    metadata = csv.reader(open(path.join(raw_dataset_dir, "List.csv"), 'r'))
    next(metadata)
    metadata_id = {int(r[0]): r for r in metadata}

    fingering_dir = path.join(raw_dataset_dir, "FingeringFiles")
    for file in tqdm(listdir(fingering_dir, full=False)):
        file_id, tagger_id = map(int, file.split("_")[0].split("-"))
        mata = metadata_id[file_id]

        datum = {
            "piece": mata[2],
            "composer": mata[1],
            "tagger": mata[5 + tagger_id],
            "#bars": int(mata[3]),
            "#notes": int(mata[4]),
            "notes": []
        }

        f = open(path.join(fingering_dir, file), "r")
        notes = [r.split() for r in f.read().splitlines()[1:]]
        f.close()

        for note in notes:
            datum["notes"].append({
                "on_event": {
                    "time": float(note[1]),
                    "velocity": int(note[4])
                },
                "off_event": {
                    "time": float(note[2]),
                    "velocity": int(note[5])
                },
                "spelled_pitch": note[3],
                "midi_pitch": 0,
                "channel": int(note[6]),
                "fingers": [{"finger": abs(f), "hand": "right" if f > 0 else "left"}
                            for f in [int(f) for f in note[7].strip('_').split("_")]]

            })

        dataset.append(datum)

    json.dump({"data": dataset}, open(path.join(version_dir, "index.json"), "w"))


if __name__ == "__main__":
    download()
