import json
import os
from os import path
import zipfile
from urllib.request import urlretrieve

from utils.file_system import makedir

base = path.dirname(path.abspath(__file__))


def download(version="1.0"):
    versions_dir = path.join(base, "versions")
    makedir(versions_dir)
    version_dir = path.join(versions_dir, version)
    makedir(version_dir)

    header = json.load(open(path.join(base, "header.json")))
    versions = [v for v in header["versions"] if v["version"] == version]
    if len(versions) == 0:
        raise ValueError("Version not found")

    url = versions[0]["url"]

    file_handle, _ = urlretrieve(url)
    with zipfile.ZipFile(file_handle, 'r') as zipObj:
        zipObj.extractall(version_dir)


if __name__ == "__main__":
    download()
