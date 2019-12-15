import json
from functools import lru_cache

import cv2
import numpy as np
import imageio

from utils.file_system import temp_name, listdir

BODY_POINTS = ["Nose", "Neck", "RShoulder", "RElbow", "RWrist", "LShoulder", "LElbow", "LWrist", "MidHip",
               "RHip", "RKnee", "RAnkle", "LHip", "LKnee", "LAnkle", "REye", "LEye", "REar", "LEar", "LBigToe",
               "LSmallToe", "LHeel", "RBigToe", "RSmallToe", "RHeel"]

# Based on https://github.com/CMU-Perceptual-Computing-Lab/openpose/raw/master/doc/media/keypoints_pose_25.png
BODY_LIMBS = [
    # Face
    ("Nose", "LEye"),
    ("Nose", "REye"),
    ("Nose", "LEar"),
    ("Nose", "REar"),
    ("Nose", "Neck"),
    # Body
    ("Neck", "RShoulder"),
    ("RShoulder", "RElbow"),
    ("RElbow", "RWrist"),
    ("Neck", "LShoulder"),
    ("LShoulder", "LElbow"),
    ("LElbow", "LWrist"),
    ("Neck", "MidHip"),
    # Legs
    ("MidHip", "RHip"),
    ("RHip", "RKnee"),
    ("RKnee", "RAnkle"),
    ("MidHip", "LHip"),
    ("LHip", "LKnee"),
    ("LKnee", "LAnkle"),
    # Feet
    ("RAnkle", "RHeel"),
    ("RAnkle", "RBigToe"),
    ("RBigToe", "RSmallToe"),
    ("LAnkle", "LHeel"),
    ("LAnkle", "LBigToe"),
    ("LBigToe", "LSmallToe"),
]

# Anatomy guide http://blog.handcare.org/blog/2017/10/26/anatomy-101-finger-joints/
HAND_POINTS = [
    "BASE",
    "T_STT", "T_BCMC", "T_MCP", "T_IP",  # Thumb
    "I_CMC", "I_MCP", "I_PIP", "I_DIP",  # Index
    "M_CMC", "M_MCP", "M_PIP", "M_DIP",  # Middle
    "R_CMC", "R_MCP", "R_PIP", "R_DIP",  # Ring
    "P_CMC", "P_MCP", "P_PIP", "P_DIP",  # Pinky
]

# Based on https://github.com/CMU-Perceptual-Computing-Lab/openpose/raw/master/doc/media/keypoints_hand.png
HAND_LIMBS = [
    ("BASE", "T_STT"), ("BASE", "I_CMC"), ("BASE", "M_CMC"), ("BASE", "R_CMC"), ("BASE", "P_CMC"),  # Base
    ("T_STT", "T_BCMC"), ("T_BCMC", "T_MCP"), ("T_MCP", "T_IP"),  # Thumb
    ("I_CMC", "I_MCP"), ("I_MCP", "I_PIP"), ("I_PIP", "I_DIP"),  # Index
    ("M_CMC", "M_MCP"), ("M_MCP", "M_PIP"), ("M_PIP", "M_DIP"),  # Middle
    ("R_CMC", "R_MCP"), ("R_MCP", "R_PIP"), ("R_PIP", "R_DIP"),  # Ring
    ("P_CMC", "P_MCP"), ("P_MCP", "P_PIP"), ("P_PIP", "P_DIP"),  # Pinky
]

# Based on https://github.com/CMU-Perceptual-Computing-Lab/openpose/raw/master/doc/media/keypoints_face.png
# Border
FACE_BORDER_POINTS = ["FB_" + str(i) for i in range(17)]
FACE_BORDER_LIMBS_LEFT = [("FB_" + str(i), "FB_" + str(i - 1)) for i in reversed(range(1, 9))]
FACE_BORDER_LIMBS_RIGHT = [("FB_" + str(i), "FB_" + str(i + 1)) for i in range(8, 16)]

# Lips
FACE_OUTER_LIPS_POINTS = ["FLO_" + str(i) for i in range(48, 60)]
FACE_OUTER_LIPS_LIMBS = [("FLO_" + str(i), "FLO_" + str(i + 1)) for i in range(48, 60)] + [("FLO_59", "FLO_48")]
FACE_INNER_LIPS_POINTS = ["FLI_" + str(i) for i in range(60, 68)]
FACE_INNER_LIPS_LIMBS = [("FLI_" + str(i), "FLI_" + str(i + 1)) for i in range(60, 8)] + [("FLI_67", "FLI_60")]

# Nose
FACE_NOSE_POINTS = ["FN_" + str(i) for i in range(27, 36)]
FACE_NOSE_BRIDGE_LIMBS = [("FN_" + str(i), "FN_" + str(i + 1)) for i in range(27, 31)]
FACE_NOSE_HORIZONTAL_LIMBS = [("FN_" + str(i), "FN_" + str(i + 1)) for i in range(31, 36)]
FACE_NOSE_LIMBS = FACE_NOSE_BRIDGE_LIMBS + FACE_NOSE_HORIZONTAL_LIMBS + [("FN_30", "FN_33")]

# Eyebrows
FACE_EYE_POINTS = ["FE_" + str(i) for i in range(36, 48)]
FACE_EYE_LEFT_LIMBS = [("FE_" + str(i), "FE_" + str(i + 1)) for i in range(36, 42)] + [("FE_41", "FE_36")]
FACE_EYE_RIGHT_LIMBS = [("FE_" + str(i), "FE_" + str(i + 1)) for i in range(42, 48)] + [("FE_47", "FE_42")]
FACE_PUPILS_POINTS = ["FP_68", "FP_69"]

# Eyes
FACE_EYEBROWS_POINTS = ["FEB_" + str(i) for i in range(17, 27)]
FACE_EYEBROW_LEFT_LIMBS = [("FEB_" + str(i), "FEB_" + str(i + 1)) for i in range(17, 21)]
FACE_EYEBROW_RIGHT_LIMBS = [("FEB_" + str(i), "FEB_" + str(i + 1)) for i in range(22, 27)]

# Face points, in order
FACE_POINTS = FACE_BORDER_POINTS + FACE_EYEBROWS_POINTS + FACE_NOSE_POINTS + FACE_EYE_POINTS + FACE_OUTER_LIPS_POINTS + FACE_INNER_LIPS_POINTS + FACE_PUPILS_POINTS
FACE_LIMBS = FACE_BORDER_LIMBS_LEFT + FACE_BORDER_LIMBS_RIGHT + FACE_OUTER_LIPS_LIMBS + FACE_INNER_LIPS_LIMBS + FACE_NOSE_LIMBS + FACE_EYEBROW_LEFT_LIMBS + FACE_EYEBROW_RIGHT_LIMBS + FACE_EYE_LEFT_LIMBS + FACE_EYE_RIGHT_LIMBS


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


def get_file_person(f_name: str):
    people = json.load(open(f_name))["people"]
    if len(people) == 0:
        return None

    return structure_raw_person(people[0])


HAND_POINTS_COLOR = [
    [192, 0, 0],
    [192, 192, 0],
    [0, 192, 0],
    [0, 192, 192],
    [0, 0, 192],
    [127, 127, 127]
]


@lru_cache(maxsize=None)
def point_color(part, point):
    if part == "face":
        return (255, 255, 255)  # White
    if part == "body":
        return (255, 0, 0)  # RED

    i = HAND_POINTS.index(point) - 1
    return [x + 35 * (i % 4) for x in HAND_POINTS_COLOR[i // 4]]


def color_opacity(color, opacity):
    return tuple(np.array(color) * opacity)


def draw_person(image, person):
    int_person = json.loads(json.dumps(person))
    image = image.copy()

    limbs = {
        'body': BODY_LIMBS,
        'face': FACE_LIMBS,
        'hand_left': HAND_LIMBS,
        'hand_right': HAND_LIMBS,
    }

    for key, joints in int_person.items():
        for name, joint in joints.items():
            point = (round(joint["x"]), round(joint["y"]))
            color = color_opacity(point_color(key, name), joint["c"])
            if key != 'face' or name in {'FP_68', 'FP_69'}:
                cv2.circle(image, center=point, radius=1 if key == 'face' else 3, color=color, thickness=-1)

        for (p1, p2) in limbs[key]:
            if p1 in joints and p2 in joints:
                point1 = (round(joints[p1]["x"]), round(joints[p1]["y"]))
                point2 = (round(joints[p2]["x"]), round(joints[p2]["y"]))

                base_color = tuple(np.mean([point_color(key, p1), point_color(key, p2)], axis=0))
                color = color_opacity(base_color, (joints[p1]["c"] + joints[p2]["c"]) / 2)

                cv2.line(image, point1, point2, color=color)

    return image


def create_video(shape, person_frames: list, fname=None, fps=25):
    blank_image = np.zeros(shape, np.uint8)

    frames = [draw_person(blank_image, person) for person in person_frames]

    if fname is None:
        fname = temp_name(".mp4")
    writer = imageio.get_writer(fname, fps=fps)
    for person in person_frames:
        writer.append_data(draw_person(blank_image, person))
    writer.close()

    return fname


def create_video_from_directory(directory: str, shape=(320, 320, 3), fname=None):
    person_frames = [get_file_person(f) for f in listdir(directory, full=True)]
    return create_video(shape, person_frames, fname=fname)


if __name__ == "__main__":
    example = "../../datasets/SLCrawl/versions/SpreadTheSign/OpenPose/BODY_25/poses/10013_hr.hr_0/"

    drawn = create_video_from_directory(example, fname="main.mp4")
