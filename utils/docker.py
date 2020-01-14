import os

import subprocess

from utils.file_system import makedir


class Docker:
    @staticmethod
    def kill_cmd(name: str):
        return " | ".join([
            "docker ps -a",
            "awk '{ print \$1,\$2 }'",
            "grep " + name,
            "awk '{print \$1 }'",
            "xargs -I {} docker rm -f {}"
        ])

    @staticmethod
    def verify_image_exists(name: str):
        cmd = "docker image inspect " + name + " >/dev/null 2>&1 && echo yes || echo no"
        exists = os.popen(cmd).read().strip()
        if exists == "no":
            raise Exception("Docker image '" + name + "' doesn't exist on this machine")

    @staticmethod
    def start_container(container_id: str):
        d_start = "docker start " + container_id
        print(d_start)
        status = os.system(d_start)
        if int(status) != 0:
            raise Exception("Start Status " + str(status))

    @staticmethod
    def exec_container(container_id: str, cmd: str):
        d_exec = "docker exec " + container_id + " " + cmd
        print(d_exec)
        proc = subprocess.Popen(d_exec, stdout=subprocess.PIPE, shell=True)
        (out, err) = proc.communicate()
        print("Exec out", out)

        if err is not None:
            raise Exception("Exec Error " + str(err))

    @staticmethod
    def cp_container_directory(container_id: str, local_dir: str, docker_dir: str):
        makedir(local_dir)
        d_cp = "nvidia-docker cp " + container_id + ":" + docker_dir + ". " + local_dir
        print(d_cp)
        status = os.system(d_cp)
        if int(status) != 0:
            raise Exception("CP Status " + str(status))

    @staticmethod
    def create_container(name: str, options: str = ''):
        d_create = "nvidia-docker create " + options + " " + name
        print(d_create)
        container_id = os.popen(d_create).read().strip()
        print("Creation Output", container_id)
        return container_id

    @staticmethod
    def remove_container(container_id: str):
        d_wait = "docker rm -f " + container_id
        print(d_wait)
        os.system(d_wait)
