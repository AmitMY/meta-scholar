import json
from os import path
from urllib.request import urlopen
import jsonlines


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
