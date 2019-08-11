import json
import os
from os import path
import re
from tempfile import gettempdir

from utils.file_system import save_temp

base = path.dirname(path.abspath(__file__))

# This should make the code work for Python 2 / Python 3
try:
    unicode
except:
    unicode = str


def eval(texts, version="2.1"):
    header = json.load(open(path.join(base, "header.json")))
    versions = [v for v in header["versions"] if v["version"] == version]
    if len(versions) == 0:
        raise ValueError("Version not found")

    url = versions[0]["url"]

    v_file_name = path.join(gettempdir(), header["title"] + header["version"] + ".perl")
    if not path.isfile(v_file_name):
        # TODO download file from URL
        # Add execution permissions
        os.popen("chmod +x " + v_file_name).read()

    if len(texts) == 0:
        return {"BLEU": 0, "BLEU-1": 0, "BLEU-2": 0, "BLEU-3": 0, "BLEU-4": 0}

    hypothesis = [t["hypothesis"] for t in texts]
    references = [t["references"] for t in texts]

    # Pad references
    max_refs = max([len(ref) for ref in references])
    references = [ref + [""] * (max_refs - len(ref)) for ref in references]

    # Split references to files
    ref_paths = [save_temp(list(map(unicode.lower, map(unicode, refs)))) for refs in zip(*references)]

    hypothesis = list(map(unicode.lower, map(unicode, hypothesis)))
    hyp_path = save_temp(hypothesis)

    cmd = v_file_name + " " + " ".join(ref_paths) + " < " + hyp_path
    res = os.popen(cmd).read()

    search = re.search(" (\d*[\.\d]*?), (\d*[\.\d]*?)\/(\d*[\.\d]*?)\/(\d*[\.\d]*?)\/(\d*[\.\d]*?) ", str(res))
    if search:
        scores = list(map(lambda k: float(k), search.groups()))
        return {"BLEU": scores[0], "BLEU-1": scores[1], "BLEU-2": scores[2], "BLEU-3": scores[3], "BLEU-4": scores[4]}

    print(cmd)
    print(search)
    raise Exception(res)


if __name__ == "__main__":
    sen = "A small, sample sentence"
    print(eval([{"hypothesis": sen, "references": [sen]}]))
