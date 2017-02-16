'''
Created on 27.1.2017

@author: sapejura
'''
import unittest
import xcamserver
from xcamserver.camera_worker import DummyWorker
import json
from xcamserver.socket_server import SocketServer


def check_meta_keys(d):
    assert 'byte order' in d
    assert 'stream_address' in d
    assert 'clients' in d
    assert 'data type' in d
    assert 'error' in d
    assert 'frame_size' in d
    assert 'height' in d
    assert 'interleave' in d
    assert 'status' in d
    assert 'width' in d


def json2dict(j):
    return json.loads(j.decode("utf-8"))


class BaseTest(unittest.TestCase):

    def setUp(self):
        xcamserver.app.config['TESTING'] = True
        xcamserver._worker = DummyWorker()
        xcamserver.socket_server = SocketServer()
        self.app = xcamserver.app.test_client()

    def tearDown(self):
        with xcamserver.worker_ctx() as worker:
            worker.close()
        xcamserver.socket_server.close()

