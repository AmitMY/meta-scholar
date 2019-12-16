import socket
from celery import Celery

MASTER = socket.gethostname()


def find_free_port():
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("", 0))
    s.listen(1)
    port = s.getsockname()[1]
    s.close()
    return port


class Distributed:
    def __init__(self, name, slaves, module_path):
        self.queue_port = find_free_port()
        self.slaves = slaves
        self.module_path = module_path

        self.init_queue()

        self.app = Celery(name, broker='pyamqp://' + MASTER + ':' + self.queue_port + '//')

    def init_queue(self):
        # docker run -d -p 5462:self.queue_port rabbitmq # Should die on exit
        return self

    def run(self, data):
        # Spawn celery workers on all of the slaves

        # Create all distributed tasks in the queue

        # Wait for all distributed tasks to finish

        # Kill all celery workers

        return self
