'''
Created on 13.12.2016

@author: Samuli Rahkonen
'''
from flask import Flask
from contextlib import contextmanager
app = Flask(__name__)
app.config.update(dict(
    DEBUG=False)
)
# from flask_socketio import SocketIO
# socketio = SocketIO(app)

from xcamserver.camera_worker import CameraWorker  # , DummyWorker
from xevacam import camera
# import socket

cam = camera.XevaCam(calibration='C:\\MyTemp\\envs\\xevacam\\Lib\\site-packages\\3ms_196_xeneth3.xca')
camera_worker = CameraWorker(cam)
# dummy_worker = DummyWorker()
_worker = camera_worker

import threading
worker_lock = threading.Lock()


@contextmanager
def worker_ctx():
    '''
    Context for preventing multiple request threads accessing the worker at
    the same time.
    '''
    try:
        worker_lock.acquire()
        yield _worker
        # yield worker
    finally:
        worker_lock.release()
'''
worker_socket = None  # Socket for camera.
worker_socket_thread = None
socket_lock = threading.Lock()


@contextmanager
def socket_ctx():
    try:
        socket_lock.acquire()
        yield worker_socket_thread
    finally:
        socket_lock.release()
'''

from xcamserver.socket_server import SocketServer
socket_server = None


from xcamserver import controllers  # Import order matters
