import json

from utils.file_system import listdir
from utils.pose import HAND_POINTS, draw_limbs, HAND_LIMBS


def hand_from_raw(hand):
    return {name:  {"x": hand[i][0], "y": hand[i][1], "z": hand[i][2]} for i, name in enumerate(HAND_POINTS)}

def draw_hands(image, hands):
    hands_obj = {"hand"+ str(i): hand for i, hand in enumerate(hands)}

    return draw_limbs(image, hands_obj, { k: HAND_LIMBS for k in hands_obj.keys() })


def get_file_hands(f_name: str):
    content = open(f_name, "r").read()

    if content == "":
        print("File", f_name, "empty content")
        return []

    return json.loads(content)

def get_directory_hands(directory):
    return [get_file_hands(f) for f in listdir(directory, full=True)]