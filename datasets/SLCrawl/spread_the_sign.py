import itertools
import json
import multiprocessing
import re
import time
from itertools import chain
from multiprocessing.pool import Pool
from os import path
from os.path import exists
from urllib.error import HTTPError

from urllib.request import urlopen, Request
from tqdm import tqdm

# Requests Cache
from utils.dataset import load
from utils.file_system import makedir

reqs_cache = {}

URL = "https://www.spreadthesign.com/"


def chunks(l, n):
    c = []
    for i in range(0, len(l), n):
        c.append(l[i:i + n])
    return c


def get_word(lang, wid, sign=0):
    url = URL + lang + "/word/" + str(wid) + "/w/" + str(sign)

    if url not in reqs_cache:
        req = Request(url)
        req.add_header('X-Requested-With', 'XMLHttpRequest')

        try:
            reqs_cache[url] = str(urlopen(req).read())
        except HTTPError as e:
            raise e

    return reqs_cache[url]


def get_word_languages(wid):
    try:
        res = get_word("en.gb", wid)
        return re.findall("data-set=\"#search-last-to-lang:(.*?)\"", res)
    except HTTPError as e:
        if str(e) != "HTTP Error 404: Not Found" and \
                not str(e).startswith(
                    "HTTP Error 302: The HTTP server returned a redirect error that would lead to an infinite loop."):
            print("error", URL + "/word/" + str(wid), e)
            raise e

        return None


def index_words(directory, pool, processes):
    words_index_path = path.join(directory, "words_index.json")
    words = json.load(open(words_index_path)) if exists(words_index_path) else {}
    # max_i = max([int(i) for i in words.keys()])
    #
    # parallel = (200 // processes) * processes
    # print("parallel", parallel, "requests")
    # for word_id in tqdm(iter(range(1, 9999999, parallel))):
    #     if word_id + parallel < max_i:
    #         continue
    #
    #     ids = list(range(word_id, word_id + parallel))
    #     languages = list(pool.imap(get_word_languages, ids))
    #
    #     if all([l is None for l in languages]):
    #         break
    #
    #     for i, l in zip(ids, languages):
    #         if l is not None:
    #             words[i] = l
    #
    #     json.dump(words, open(words_index_path, "w"))

    return words


def get_video(params):
    wid, lang = params
    try:
        res = get_word(lang, wid)
    except:
        return []

    # Get word
    text = re.findall("<h2>[\\s\\S]*?<\\/span>([\\s\\S]*?)<", res)[0].replace('\\n', '').strip()
    # Get description
    description = re.findall('result-description">([\\s\\S]*?)<\\/div', res)
    description = description[0].replace('\\n', '').strip() if len(description) > 0 else None
    # Alternatives
    alternatives = [res] + [get_word(lang, wid, i) for i in range(1, len(re.findall('<li.*?>', res)))]
    alternatives = [re.findall('<video[\\s\\S]*?src="(.*?)"', alt) for alt in alternatives]
    alternatives = list(itertools.chain.from_iterable(alternatives))

    return [{
        "id": str(wid) + "_" + str(lang) + "_" + str(i),
        "texts": [{"text": text}],
        "description": description,
        "video_url": url,
        "video": "videos/" + str(wid) + "_" + str(lang).replace(".", "-") + "_" + str(i) + ".mp4",
        "sign_language": lang
    } for i, url in enumerate(alternatives)]


def download_SpreadTheSign(directory):
    makedir(path.join(directory, "videos"))

    # Initialize MultiProcessing Pool
    processes = multiprocessing.cpu_count() - 1
    pool = Pool(processes)

    # First gets the list of words and their languages
    print("Indexing SpreadTheSign...")
    words = index_words(directory, pool, processes)

    # For every ID and language, get the metadata
    print("Getting metadata for each sign...")
    data_index_path = path.join(directory, "data_index.json")
    data = json.load(open(data_index_path)) if exists(data_index_path) else []
    existing = {"_".join(d["id"].split("_")[:-1]) for d in data}

    videos = [(i, l) for i, languages in words.items() for l in languages if str(i) + "_" + str(l) not in existing]

    for chunk in tqdm(chunks(videos, processes * 10)):
        data += list(itertools.chain.from_iterable(pool.imap(get_video, list(chunk))))
        json.dump(data, open(data_index_path, "w"), indent=2)

    return data

if __name__ == "__main__":
    load("SLCrawl", version="SpreadTheSign", addons=[{"name": "OpenPose"}])