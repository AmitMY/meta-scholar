# slaves = ["nlp01", "nlp02", "nlp03", "nlp05", "nlp06", "nlp09", "nlp10", "nlp11", "nlp12", "nlp13", "nlp14", "nlp15"]
from utils.distributed import Distributed

slaves = [
    "nlp01",
    "nlp02",
    "nlp03",
    "nlp04",
    "nlp05",
    "nlp06",
    "nlp07",
    "nlp08",
    "nlp09",
    "nlp10",
    "nlp11",
    "nlp12",
    # "nlp13", Can't connect to nlp01
    # "nlp14", Can't connect to nlp01
    "nlp15"
]
distributed = Distributed("NLP", "nlp01", slaves, "")

# ssh -N -f -L localhost:48109:localhost:48109 nlp07
# ssh -N -f -L localhost:5555:localhost:5555 nlp01
