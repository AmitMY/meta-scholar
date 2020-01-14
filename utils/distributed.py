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

"""
docker run -d -p 5672:5672 rabbitmq
docker run -d -p 6379:6379 redis

pip install -U "celery[redis]"
pip install flower
"""


class Distributed:
    def __init__(self, name, master, slaves, module_path):
        self.master = master
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

    def kill(self, servers, what="worker"):
        kill_others = 'ps U $(whoami) | grep \'celery -A .* ' + what + '\' | tr -s \' \' | sed \'s/[ ]\?\([0-9]*\).*/\\1/g\' | xargs kill'

        self.spread(kill_others, servers)

    def kill_slaves(self):
        self.kill(servers=self.slaves)

    def spread(self, cmd: str, servers: list, sync: bool = True):
        for slave in servers:
            print("Spread", cmd, slave)
            self.cmd("ssh " + slave + " \"" + cmd + "\"", sync)

    def spawn_workers(self):
        cmds = self.env_cmd + [self.celery_path + " -A " + self.module_path + " worker --loglevel=info --autoscale=4,1"]
        self.kill_slaves()
        self.spread(cmd=" && ".join(cmds), servers=self.slaves, sync=False)

        return self

    def clear_tasks(self):
        print("Purge queue")
        self.app.control.purge()
        return self

    def run(self, callable, data):
        # Clear Queue
        self.clear_tasks()
        time.sleep(1)

        # Create all distributed tasks in the queue
        print("Creating tasks")
        tasks = [callable.delay(datum) for datum in data]
        t = tqdm(total=len(tasks), unit="task")
        results = ResultSet(tasks, app=self.app)

        start_time = time.time()

        # Wait for all distributed tasks to finish
        last_completed = 0
        while True:
            if time.time() - start_time > 3600: # Will happen every hour
                start_time = time.time()
                self.spawn_workers() # Restart all slaves

            try:
                if results.ready():
                    break
                completed = results.completed_count()
                t.update(completed - last_completed)
                last_completed = completed
            except Exception as e:
                time.sleep(10)
                pass

            time.sleep(1)

        t.update(results.completed_count() - last_completed)

        return self

    def flower(self):
        print("Kill Flower")
        self.kill([self.master], "flower")

        print("Run flower")
        cmds = self.env_cmd + [self.celery_path + " -A " + self.module_path + " flower --port=5555"]
        self.cmd(" && ".join(cmds))

        return self


def cleanup(*args):
    print("Cleaned up")
    if len(PROCESSES) == 0:
        return
    for p in PROCESSES:
        p.kill()
    sys.exit(0)


signal.signal(signal.SIGINT, cleanup)
atexit.register(cleanup)
