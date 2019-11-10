from os import path
import jsonlines

from handspeak import download_HandSpeak


def download(version, directory):
    if version["version"] == "HandSpeak":
        res = download_HandSpeak(version)
    else:
        raise ValueError("Downloading this version is not implemented")

    with jsonlines.open(path.join(directory, "index.jsonl"), mode='w') as writer:
        for row in res:
            writer.write(row)
