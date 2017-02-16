'''
Created on 12.1.2017

@author: sapejura
'''
import unittest
import xcamserver
from xcamserver.camera_worker import DummyWorker
import json
from xcamserver.socket_server import SocketServer
from tests.base_test import json2dict, check_meta_keys, BaseTest 



class APITestCase(BaseTest):

    def setUp(self):
        super().setUp()

    def test_root(self):
        rv = self.app.get('/')
        assert isinstance(rv.data, bytes)
        assert len(rv.data) != 0

    def test_init(self):
        rv = self.app.get('/init')
        data = json2dict(rv.data)
        check_meta_keys(data)
        assert data['byte order'] == None
        server_addr = xcamserver.socket_server.server_socket.getsockname()
        print(server_addr)
        print(data['stream_address'])
        assert data['stream_address'] == list(server_addr)
        assert data['clients'] == 0
        assert data['data type'] == 'u2'
        assert data['error'] == ''
        assert data['frame_size'] == 163840
        assert data['height'] == 256
        assert data['interleave'] == 'bil'
        assert data['width'] == 320

        assert data['status'] == 'STOPPED'

    def test_start(self):
        rv = self.app.get('/init')
        rv = self.app.get('/start')
        data = json2dict(rv.data)
        check_meta_keys(data)
        assert data['byte order'] == None
        server_addr = xcamserver.socket_server.server_socket.getsockname()
        print(server_addr)
        print(data['stream_address'])
        assert data['stream_address'] == list(server_addr)
        assert data['clients'] == 0
        assert data['data type'] == 'u2'
        assert data['error'] == ''
        assert data['frame_size'] == 163840
        assert data['height'] == 256
        assert data['interleave'] == 'bil'
        assert data['width'] == 320
        assert data['status'] == 'RUNNING'

        rv = self.app.get('/start')
        data = json2dict(rv.data)
        print(data)
        assert len(data['error']) != 0

    def test_stop(self):
        rv = self.app.get('/init')
        rv = self.app.get('/start')
        rv = self.app.get('/stop')
        data = json2dict(rv.data)
        assert data['status'] == 'STOPPED'


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
