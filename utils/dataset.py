import argparse
import json
from collections import defaultdict
from os import path
from os.path import exists
from jsonlines import jsonlines
import logging

try:
    from utils.file_system import makedir
except ImportError:
    from file_system import makedir


def modular_import(module_name, module_path):
    try:
        import importlib.util

        spec = importlib.util.spec_from_file_location(module_name, module_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    except ImportError:
        import imp
        module = imp.load_source(module_name, module_path)

    return module


base_path = path.dirname(path.realpath(__file__))


def download(directory: str, version, module_path: str, dataset=None):
    makedir(directory)
    version_dir = path.join(directory, version["version"])
    index_path = path.join(version_dir, 'index.jsonl')
    if not exists(version_dir) or not exists(index_path):
        makedir(version_dir)
        module = modular_import("module", module_path)
        if dataset is None:
            module.download(version, version_dir)
        else:
            module.download(version, version_dir, dataset)

    data = list(jsonlines.open(index_path))

    return version_dir, data


def load_header(header_path: str, version: str = None):
    header = json.load(open(header_path))
    if version is None:
        versions = [header["versions"][0]]
    else:
        versions = [v for v in header["versions"] if v["version"] == version]

    if len(versions) == 0:
        raise ValueError("Version not found")

    return header, versions[0]


def format_data(header, version_dir, data):
    # Manage data types
    for key, props in header["data"].items():
        if props["type"] == "file":
            for datum in data:
                if key in datum:
                    datum[key] = path.join(version_dir, datum[key])


def load_addon(addon: str, version: str, dataset, dataset_version_dir: str):
    logging.info("Loading addon %s, version %s" % (addon, version))

    addon_path = path.join(base_path, "../addons/" + addon)

    header, version = load_header(path.join(addon_path, "header.json"), version)
    logging.debug("Loading version %s" % version)

    # Download addon
    addon_dir = path.join(dataset_version_dir, addon)
    version_dir, data = download(addon_dir, version, path.join(addon_path, 'addon.py'), dataset)
    format_data(header, version_dir, data)

    # Load addon
    return header, data


def index_by(data, index_key):
    index = defaultdict(list)
    for d in data:
        index[d[index_key]].append(d)
    return index


def load(dataset: str, version: str = None, split=False, addons=[]):
    logging.info("Loading dataset %s, version %s" % (dataset, version))

    dataset_path = path.join(base_path, "../datasets/" + dataset)

    # Verify version
    header, version = load_header(path.join(dataset_path, "header.json"), version)
    logging.debug("Loading version %s" % version)

    # Download dataset
    versions_dir = path.join(dataset_path, "versions")
    version_dir, data = download(versions_dir, version, path.join(dataset_path, 'dataset.py'))
    format_data(header, version_dir, data)
    logging.debug("Data Length %d" % len(data))

    # Load addons
    for addon in addons:
        addon_version = addon["version"] if "version" in addon else None
        a_header, a_data = load_addon(addon["name"], addon_version, data, version_dir)

        indexed_data = index_by(data, a_header["join_on"])
        for d in a_data:
            for datum in indexed_data[d[a_header["join_on"]]]:
                datum[addon["name"]] = d

        # Add fields to schema
        header["data"][addon["name"]] = a_header["data"]

    # Load splits
    if not split:
        return data
    else:
        splits = defaultdict(list)
        for s, ids in json.load(open(path.join(version_dir, 'split.json'))).items():
            splits[s] = [data[i] for i in ids]
        return dict(splits)


if __name__ == "__main__":
    # parser = argparse.ArgumentParser()
    # parser.add_argument('-d', '--dataset', help="Dataset ID", required=True)
    # parser.add_argument('-v', '--version', help="Version ID", default=None)
    # args = parser.parse_args()
    #
    # load(args.dataset, args.version)
    logging.basicConfig(level=logging.DEBUG)
    load("SLCrawl", version="SpreadTheSign", addons=[{"name": "OpenPose"}])
