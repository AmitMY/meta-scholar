import json
import re
import time
from itertools import chain

from urllib.request import urlopen
from tqdm import tqdm

from datasets.SLCrawl.util import word2chars


def download_HandSpeak(version):
    def clean_text(t):
        return t.replace('\\r\\n', ' ').replace('\\n', ' ').replace('<p>', '').replace('</p>', '').strip()

    def get_fingered_wordslist(url):
        req = str(urlopen(url).read())
        text = str(re.search("var wordList = ([\\s\\S]*?);", req)[1]).replace('\\n', '').replace('\\r', '')
        json_text = re.sub('([{, :])(\\w+)([},:])', '\\1\"\\2\"\\3', text)
        raw = json.loads(json_text)

        for row in raw:
            yield {
                "texts": [{"text": word2chars(row["word"])}],
                "video_url": row["src"]
            }

    def get_words():
        words = json.loads(urlopen(version["url"] + "word/search/app/getlist.php").read())
        for word in tqdm(words):
            if word["signName"] == "":
                continue

            content = None
            while content is None:
                url = version["url"] + "word/search/index.php?id=" + word["signID"]
                try:
                    content = str(urlopen(url).read())
                except:
                    print("HTTP Request Failed", url)
                    time.sleep(2)

            text = re.search('<span itemprop="name">ASL sign for: ([\\s\\S]*?)<\\/span>', content)[1]
            description = re.search('<span itemprop="description">([\\s\\S]*?)<\\/span>', content)[1]
            video = re.search('<video id="mySign" class="v-asl" autoplay ([\\s\\S]*?) src="(.*?)"', content)[2]

            datum = {
                "texts": None,
                "description": clean_text(description),
                "video_url": version["url"] + video
            }
            text = clean_text(text)
            modifier_match = re.search('(.*?) \\((.*?)\\)', text)
            if modifier_match:
                datum["texts"] = [{"text": modifier_match[1], "modifier": modifier_match[2]}]
            else:
                datum["texts"] = [{"text": text}]

            yield datum

    def get_sentences():
        sentences = json.loads(urlopen(version["url"] + "translate/app/getlist.php").read())
        for sentence in tqdm(sentences):
            content = None
            while content is None:
                url = version["url"] + "translate/index.php?id=" + sentence["senID"]
                try:
                    content = str(urlopen(url).read())
                except:
                    print("HTTP Request Failed", url)
                    time.sleep(2)

            search_re = "[\\s\\S]*".join(["<div class=\"dictext\">", "<p>", "Gloss:", "?>(", "?)<\/span",
                                          "?English equivalent:", "?>(", "?)<", "?<p>(", "?)<\\/p>"])

            match = re.search(search_re, content)
            video = re.search('<video id="mySen" autoplay class="v-asl"([\\s\\S]*?) src="(.*?)"', content)[2]

            yield {
                "texts": [{"text": clean_text(match[2])}],
                "gloss": clean_text(match[1]),
                "description": clean_text(match[3]),
                "video_url": version["url"] + video
            }

    finger_words = get_fingered_wordslist(version["url"] + "spell/practice/")
    finger_double_words = get_fingered_wordslist(version["url"] + "spell/practice/double-word/")

    data = chain(finger_words, finger_double_words, get_words(), get_sentences())

    for datum in data:
        d = {"id": re.search("\\/([A-Z|a-z|0-9|\\-| |\\\\|\\(|\\)]*?)\\.mp4", datum["video_url"])[1]}
        for k, v in datum.items():
            d[k] = v
        datum["signer"] = {"gender": "female"}
        datum["sign_language"] = "en.us"
        datum["text_language"] = "English"
        yield d
