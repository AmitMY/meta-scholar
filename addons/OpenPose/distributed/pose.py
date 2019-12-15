"""
tmux new -s celery
conda activate meta-scholar
cd ~/PhD/meta-scholar
celery -A addons.OpenPose.distributed.pose worker --loglevel=info --autoscale=2,1
celery -A addons.OpenPose.distributed.pose flower --port=5555
"""
#
#
# celery -A addons.OpenPose.distributed.pose control shutdown
from celery import Celery

from addons.OpenPose.addon import pose_video

app = Celery('pose_tasks', broker='amqp://dsigpu01')


@app.task
def pose_distributed(datum):
    return pose_video(datum)