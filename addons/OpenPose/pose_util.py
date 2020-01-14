import base64
import json
from functools import lru_cache

import cv2
import numpy as np
import imageio
from typing import List

from utils.file_system import temp_name, listdir
from utils.pose import BODY_POINTS, HAND_POINTS, FACE_POINTS, BODY_LIMBS, FACE_LIMBS, HAND_LIMBS, color_opacity, \
    point_color, draw_limbs


def raw_to_points(raw, names):
    points = {}
    for i, name in enumerate(names):
        x = raw[i * 3]
        y = raw[i * 3 + 1]
        c = raw[i * 3 + 2]
        if x != 0 and y != 0:
            points[name] = {"x": x, "y": y, "c": c}
    return points


def structure_raw_person(raw):
    person = {
        "body": raw_to_points(raw["pose_keypoints_2d"], BODY_POINTS),
        "hand_left": raw_to_points(raw["hand_left_keypoints_2d"], HAND_POINTS),
        "hand_right": raw_to_points(raw["hand_right_keypoints_2d"], HAND_POINTS),
        "face": raw_to_points(raw["face_keypoints_2d"], FACE_POINTS),
    }

    # Seems like base of the wrist is better in the body model
    if "BASE" in person["hand_left"] and "LWrist" in person["body"]:
        person["hand_left"]["BASE"] = person["body"]["LWrist"]
    if "BASE" in person["hand_right"] and "RWrist" in person["body"]:
        person["hand_right"]["BASE"] = person["body"]["RWrist"]

    return person


def points_compress(obj, points):
    if len(obj) == 0:
        return None

    arr = np.zeros((len(points) * 3), dtype="float16")

    for i, p in enumerate(points):
        if p in obj:
            arr[i * 3 + 0] = obj[p]["x"]
            arr[i * 3 + 1] = obj[p]["y"]
            arr[i * 3 + 2] = obj[p]["c"]

    return base64.b64encode(arr.tobytes()).decode('latin-1')


def points_expand(base64_str, points):
    if base64_str is None:
        return {}

    decoded = base64.b64decode(base64_str)

    arr = np.frombuffer(decoded, dtype="float16")

    obj = {}

    for i, p in enumerate(points):
        x = float(arr[i * 3 + 0])
        y = float(arr[i * 3 + 1])
        c = float(arr[i * 3 + 2])

        if x != 0 and y != 0:
            obj[p] = {"x": x, "y": y, "c": c}

    return obj


def compress(person):
    return {
        "body": points_compress(person["body"], BODY_POINTS),
        "hand_left": points_compress(person["hand_left"], HAND_POINTS),
        "hand_right": points_compress(person["hand_right"], HAND_POINTS),
        "face": points_compress(person["face"], FACE_POINTS),
    }


def compress_frames(frames):
    return [compress(p) for p in frames]


def expand(person):
    return {
        "body": points_expand(person["body"], BODY_POINTS),
        "hand_left": points_expand(person["hand_left"], HAND_POINTS),
        "hand_right": points_expand(person["hand_right"], HAND_POINTS),
        "face": points_expand(person["face"], FACE_POINTS),
    }


def expand_frames(frames):
    return [expand(p) for p in frames]


def get_file_person(f_name: str):
    people = json.load(open(f_name))["people"]
    if len(people) == 0:
        return {
            "body": {},
            "hand_left": {},
            "hand_right": {},
            "face": {},
        }

    return structure_raw_person(people[0])


def get_directory_person(directory: str):
    return [get_file_person(f) for f in listdir(directory, full=True)]


def draw_person(image, person):
    return draw_limbs(image, person, {
        'body': BODY_LIMBS,
        'face': FACE_LIMBS,
        'hand_left': HAND_LIMBS,
        'hand_right': HAND_LIMBS,
    })


def create_video(shape, frames: List[List], fname=None, fps=25):
    blank_image = np.zeros(shape, np.uint8)

    if fname is None:
        fname = temp_name(".mp4")
    writer = imageio.get_writer(fname, fps=fps)
    for frame in frames:
        im = blank_image
        for person in frame:
            im = draw_person(im, person)
        writer.append_data(im)
    writer.close()

    return fname


def create_video_from_directory(directory: str, shape=(320, 320, 3), fname=None):
    return create_video(shape, [[p] for p in get_directory_person(directory)], fname=fname)


if __name__ == "__main__":
    c = points_compress({"RHeel": {"x": 1234.546, "y": 2, "c": 3}}, BODY_POINTS)
    e = points_expand(c, BODY_POINTS)
    print(c)
    print(e)
