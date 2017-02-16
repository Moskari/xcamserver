'''
Created on 13.12.2016

@author: Samuli Rahkonen
'''
import xcamserver
from xcamserver import app, socket_server
from xcamserver.camera_worker import DummyWorker, CameraWorker
from xcamserver.socket_server import SocketServer
# from xcamserver import socketio
#import socket

# Uncomment to debug/test without real camera
# xcamserver._worker = DummyWorker()
# xcamserver._worker.interval = 1/60

xcamserver.socket_server = SocketServer()
app.run(threaded=True, use_reloader=False)
# socketio.run(app)

# app.run(debug=True)
