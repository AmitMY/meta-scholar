import json
import os
import urllib
from os import path
from urllib.request import urlopen

from utils.file_system import makedir

base = path.dirname(path.abspath(__file__))


def download(version="2"):
    if version not in ["2", "2_constrained"]:
        raise ValueError("Downloading this version is not implemented")

    versions_dir = path.join(base, "versions")
    makedir(versions_dir)
    version_dir = path.join(versions_dir, version)
    makedir(version_dir)

    header = json.load(open(path.join(base, "header.json")))
    versions = [v for v in header["versions"] if v["version"] == version]
    if len(versions) == 0:
        raise ValueError("Version not found")

    url = versions[0]["url"].replace("/tree/", "/raw/") + "/json/webnlg_release_v" + version + "_"

    dataset = {}
    splits = {}

    for split in ["dev", "test", "train"]:
        splits[split] = []
        split_url = url + split + ".json"

        entries = json.loads(urlopen(split_url).read())["entries"]
        for entry in entries:
            for id, datum in entry.items():
                datum_id = split + "_" + id
                dataset[datum_id] = {
                    "category": datum["category"],
                    "graph": datum["modifiedtripleset"],
                    "texts": [l["lex"] for l in datum["lexicalisations"]]
                }
                splits[split].append(datum_id)

    json.dump({"data": dataset}, open(path.join(version_dir, "index.json"), "w"))
    json.dump(splits, open(path.join(version_dir, "split.json"), "w"))

    print("Download done")


if __name__ == "__main__":
    download()
