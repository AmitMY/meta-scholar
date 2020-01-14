import sys
from os import path
import jsonlines

from hand_speak import download_HandSpeak
from spread_the_sign import download_SpreadTheSign
from finger_spell import download_FingerSpell


def download(version, directory):
    if version["version"] == "HandSpeak":
        res = download_HandSpeak(version)
    elif version["version"] == "SpreadTheSign":
        res = download_SpreadTheSign(directory)
    elif version["version"] == "FingerSpell":
        res = download_FingerSpell(version, directory)
    else:
        raise ValueError("Downloading this version is not implemented")

    with jsonlines.open(path.join(directory, "index.jsonl"), mode='w') as writer:
        for row in res:
            writer.write(row)
