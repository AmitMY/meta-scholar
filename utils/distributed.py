import atexit
import signal
import socket
import subprocess
import sys
import time
from os import path

from celery import Celery
from celery.result import ResultSet
from tqdm import tqdm

CURRENT_HOST = socket.gethostname()

PROCESSES = []


class Distributed:
    def __init__(self, name, master, slaves, module_path):
        self.slaves = slaves
        self.module_path = module_path

        if master == CURRENT_HOST:
            self.check_queue_port("rabbitmq", 5672)
            self.check_queue_port("redis", 6379)

        self.app = Celery(name, backend='redis://' + master + ":6379", broker='amqp://' + master + ":5672")

        self.env_cmd = [
            "cd " + path.join(path.dirname(path.realpath(__file__)), path.pardir),
        ]

        self.celery_path = sys.executable + " -m celery"

    def check_queue_port(self, service, port):
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('127.0.0.1', port))
        sock.close()
        if result != 0:
            raise Exception("No RabbitMQ found on port " + str(port) + ", run `docker run -d -p " +
                            str(port) + ":" + str(port) + " " + service + "`")

    def cmd(self, cmd: str, sync: bool = False):
        print("Exec", cmd)

        process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                   universal_newlines=True)

        if sync:
            while True:
                line = process.stdout.readline()
                if line:
                    print(line, end='')
                if not line:
                    break

        PROCESSES.append(process)

    def spawn_workers(self):
        kill_others = 'ps U $(whoami) | grep \'celery -A .* worker\' | tr -s \' \' | sed \'s/[ ]\?\([0-9]*\).*/\\1/g\' | xargs kill'
        cmds = self.env_cmd + [self.celery_path + " -A " + self.module_path + " worker --loglevel=info --autoscale=4,1"]

        for slave in self.slaves:
            self.cmd("ssh " + slave + " \"" + kill_others + "\"", True)  # Kill all other celery workers
            self.cmd("ssh " + slave + " '" + " && ".join(cmds) + "'")  # Start a celry worker

        return self

    def run(self, callable, data):
        # Clear Queue
        print("Purge queue")
        self.app.control.purge()
        time.sleep(1)

        # Create all distributed tasks in the queue
        print("Creating tasks")
        tasks = [callable.delay(datum) for datum in data]
        t = tqdm(total=len(tasks), unit="task")
        results = ResultSet(tasks, app=self.app)

        # Wait for all distributed tasks to finish
        last_completed = 0
        while not results.ready():
            completed = results.completed_count()
            t.update(completed - last_completed)
            last_completed = completed
            time.sleep(1)
        t.update(results.completed_count() - last_completed)

        return self

    def flower(self):
        cmds = self.env_cmd + [self.celery_path + " -A " + self.module_path + " flower --port=5555"]
        self.cmd(" && ".join(cmds))

        return self


def cleanup(*args):
    if len(PROCESSES) == 0:
        return
    for p in PROCESSES:
        p.kill()
    sys.exit(0)


signal.signal(signal.SIGINT, cleanup)
atexit.register(cleanup)
