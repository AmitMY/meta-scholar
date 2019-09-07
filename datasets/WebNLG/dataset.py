import json
import os
import urllib
from os import path
from urllib.request import urlopen

import jsonlines

from utils.file_system import makedir

base = path.dirname(path.abspath(__file__))


def download_version(version="2"):
    header = json.load(open(path.join(base, "header.json")))
    versions = [v for v in header["versions"] if v["version"] == version]
    if len(versions) == 0:
        raise ValueError("Version not found")

    versions_dir = path.join(base, "versions")
    makedir(versions_dir)
    version_dir = path.join(versions_dir, version)
    makedir(version_dir)

    return download(versions[0], version_dir)


def download(version, directory):
    if version["version"] not in ["2", "2_constrained"]:
        raise ValueError("Downloading this version is not implemented")

    url = version["url"].replace("/tree/", "/raw/") + "/json/webnlg_release_v" + version["version"] + "_"

    lines = 0
    splits = {}

    with jsonlines.open(path.join(directory, "index.jsonl"), mode='w') as writer:
        for split in ["dev", "test", "train"]:
            splits[split] = []
            split_url = url + split + ".json"

            print("Downloading split:", split)
            entries = json.loads(urlopen(split_url).read())["entries"]
            for entry in entries:
                for id, datum in entry.items():
                    writer.write({
                        "id": split + "_" + id,
                        "category": datum["category"],
                        "graph": datum["modifiedtripleset"],
                        "texts": [l["lex"] for l in datum["lexicalisations"]]
                    })

                    splits[split].append(lines)
                    lines += 1

    json.dump(splits, open(path.join(directory, "split.json"), "w"))


if __name__ == "__main__":
    download_version("2")
