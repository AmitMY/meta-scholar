import sys
import time
from utils.distributed import Distributed

d = Distributed("test", "nlp01", ["nlp03", "nlp04", "nlp05"], "utils.distributed_test")

# Must declare the app in the root level
app = d.app

@app.task(name="distributed_test")
def distributed_test(t):
    return t*t


print("tasks", app.tasks)

if __name__ == "__main__":
    d.spawn_workers()
    d.flower()
    print("task", distributed_test)
    results = d.run(distributed_test, [i for i in range(10000)])
    print(results)
