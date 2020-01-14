import time
from GPUtil import GPUtil


def get_empty_gpu() -> int:
    # Get a GPU
    gpus = None
    sleeps = 0
    while gpus is None or len(gpus) == 0:
        if gpus is not None:
            time.sleep(10)
            sleeps += 1

            if sleeps > 10:
                raise Exception("No available GPU to allocate")
        try:
            gpus = GPUtil.getFirstAvailable(order='random', maxLoad=0.05, maxMemory=0.05)
        except:
            gpus = []

    return gpus[0]