import argparse
import importlib.util
import json
from collections import defaultdict
from os import path
from os.path import exists

from jsonlines import jsonlines

from utils.file_system import makedir

base_path = path.dirname(path.realpath(__file__))


def load(dataset, version=None, split=False):
    dataset_path = path.join(base_path, "../datasets/" + dataset)
    spec = importlib.util.spec_from_file_location("dataset", path.join(dataset_path, 'dataset.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    # Verify version
    header = json.load(open(path.join(dataset_path, "header.json")))
    if version is None:
        versions = [header["versions"][0]]
    else:
        versions = [v for v in header["versions"] if v["version"] == version]

    if len(versions) == 0:
        raise ValueError("Version not found")

    versions_dir = path.join(dataset_path, "versions")
    makedir(versions_dir)
    version_dir = path.join(versions_dir, versions[0]["version"])
    if not exists(version_dir):
        makedir(version_dir)
        # module.download(versions[0], version_dir)
    module.download(versions[0], version_dir)

    # Load dataset and splits
    data = list(jsonlines.open(path.join(version_dir, 'index.jsonl')))
    for key, props in header["data"].items():
        if props["type"] == "file":
            for datum in data:
                datum["key"] = path.join(version_dir, datum["key"])

    if not split:
        return data
    else:
        splits = defaultdict(list)
        for s, ids in json.load(open(path.join(version_dir, 'split.json'))).items():
            splits[s] = [data[i] for i in ids]
        return dict(splits)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--dataset', help="Dataset ID", required=True)
    parser.add_argument('-v', '--version', help="Version ID", default=None)
    args = parser.parse_args()

    load(args.dataset, args.version)
