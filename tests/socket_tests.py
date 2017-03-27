'''
Created on 26.1.2017

@author: sapejura
'''
import unittest
from tests.base_test import json2dict, check_meta_keys, BaseTest
import xcamserver
from xcamserver.camera_worker import DummyWorker
from xcamserver.socket_server import SocketServer
import requests
import socket
import json
import time
import struct
import threading
import queue


def init(addr):
    print('INIT')
    r = requests.post(addr + "/init", timeout=5)
    print(r.status_code, r.reason)
    print(r.text)
    resp = r.json()
    if resp['status'] != 'STOPPED':
        print('status is not STOPPED, it\'s %s' % resp['status'])
        return


def start(addr):
    print('START')
    r = requests.post(addr + "/start", timeout=5)
    print(r.status_code, r.reason)
    print(r.text)
    if r.status_code is 200 and r.reason == 'OK':
        return r.json()
    else:
        return None


class SocketTest(BaseTest):

    def setUp(self):
        super().setUp()
        xcamserver._worker.interval = 1/60
        # self.addr = "http://127.0.0.1:5000"
        resp = json2dict(self.app.post('/init').data)
        # resp = init(self.addr)
        self.socket_addr = resp['stream_address']
        if self.socket_addr is None:
            print('Received data didn\'t have socket address')
            raise Exception('Did not receive socket address')
        self.data_type = resp['data type']
        self.frame_size = resp['frame_size']

    def create_socket(self):
        print('CONNECTING TO SOCKET %s:%s' % tuple(self.socket_addr))
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.setblocking(1)
        # client_socket.settimeout(15)
        client_socket.connect(tuple(self.socket_addr))
        print('CONNECTED')
        return client_socket
    '''
    def test_single_socket_stream(self):
        # Connect to server stream socket
        num_of_frames = 512
        xcamserver._worker.interval = 0.01

        cs = self.create_socket().makefile(mode='rb')
        # Start camera
        self.app.post('/start')
        # resp = start(self.addr)
        if self.socket_addr is None:
            print('Received data didn\'t have socket address')
            raise Exception('Did not receive socket address')
        try:
            for i in range(num_of_frames):
                received = cs.read(self.frame_size)
                expected = struct.pack('B', (i + 1) % 256) * self.frame_size
                # print(received)
                print('.', end='', flush=True)
                # assert received == expected, \
                if received != expected:
                    print('Expected %s \n\nReceived %s' % (expected, received))
                    raise Exception('Incorrect data!')
                # print(connection.read(163840))
            print('OK!\n', end='')
        except:
            raise
        finally:
            print('Closing connection...')
            cs.close()
            print('...closed.')
    '''

    def create_socket_client(self, id, mode, thread_exceptions, num_of_frames):

        def client_thread(thread_num, s, mode):
            print('Client thread %d %s starting...' % (thread_num, s.getsockname()))
            try:
                # num_of_frames = 512
                # cs = s.makefile(mode='wrb')
                # time.sleep(5)
                # cs.write(b'\x00\x00\x00\x00')
                # Value \x01 for mode sets the server to send this socket all data
                # value \x02 sets server to send the newest full frame
                s.sendall(struct.pack('B', mode) + b'\x00\x00\x00')
                print('Client thread %d sent msg' % thread_num)
                received = bytearray()
                for i in range(num_of_frames):
                    # received = cs.read(self.frame_size)
                    while len(received) < self.frame_size + 4:  # 4 is length of timestamp
                        received.extend(s.recv(4096))
                    remaining = received[self.frame_size + 4:]
                    received = received[:self.frame_size + 4]
                    # expected = struct.pack('B', (i + 1) % 256) * self.frame_size
                    val = (i + 1) % 256
                    vals = [val] * self.frame_size
                    expected = struct.pack('I%sB' % self.frame_size, i, *vals)
                    print('beginning', received[:20])
                    print('end', received[-20:])
                    # print(len(received))
                    # print(received)
                    # print('.', end='', flush=True)
                    if received != expected:
                        # print('Expected %s \n\nReceived %s' % (expected, received))
                        # Find index where the frame data goes wrong first time
                        # print(received)
                        index = -1
                        first_expected = None
                        first_received = None
                        for x in range(len(received)):
                            first_expected = expected[x]
                            first_received = received[x]
                            if first_received != first_expected:
                                index = x
                                break
                        raise Exception('Thread %d: Incorrect data! Client address=%s, Frame num=%d, length=%d. First difference at %d. Expected=%s, received=%s' % (thread_num, str(s.getsockname()), i, len(received), index, str(first_expected), str(first_received)))
                    received = remaining
                    # print(connection.read(163840))
                # print('OK!\n', end='')
            except Exception as e:
                print('Thread %d:' % thread_num, repr(e))
                thread_exceptions.put((thread_num, e))
            finally:
                print('Thread %d: Closing connection...' % thread_num)
                # cs.close()
                s.close()
                print('...closed.')

        s = self.create_socket()
        # print(s.getsockname())
        # cs = s.makefile(mode='rb')
        client = threading.Thread(name='client_thread_%d' % id,
                                  target=client_thread,
                                  args=(id, s, mode))
        return client

    def check_thread_exceptions(self, exception_queue):
        # Get the error messages from clients
        exceptions = []
        try:
            while True:
                exceptions.append(exception_queue.get(block=False))
        except queue.Empty:
            pass
        error = '\n'.join('Exception at thread %d: %s' % (thread_id, str(repr(exc))) for thread_id, exc in exceptions)

        if error:
            raise Exception(error)
        else:
            print('No errors')

    def test_single_fast_socket_stream(self):
        num_of_clients = 1
        frames = 512
        xcamserver._worker.interval = 1/120  # roughly 120 fps

        thread_exceptions = queue.Queue()
        clients = []
        for client_number in range(num_of_clients):
            client = self.create_socket_client(client_number, 1, thread_exceptions, frames)
            clients.append(client)

        # Start camera
        self.app.post('/start')

        for client in clients:
            client.start()

        for client in clients:
            client.join()
        self.check_thread_exceptions(thread_exceptions)

    def test_multiple_fast_socket_streams(self):
        num_of_clients = 3
        frames = 512
        xcamserver._worker.interval = 1/120  # roughly 120 fps

        thread_exceptions = queue.Queue()
        clients = []
        for client_number in range(num_of_clients):
            client = self.create_socket_client(client_number, 1, thread_exceptions, frames)
            clients.append(client)

        # Start camera
        self.app.post('/start')

        for client in clients:
            client.start()

        for client in clients:
            client.join()
        self.check_thread_exceptions(thread_exceptions)
    
    def test_multiple_slow_socket_streams(self):
        num_of_clients = 10
        frames = 20
        xcamserver._worker.interval = 1/10  # roughly 10 fps

        thread_exceptions = queue.Queue()
        clients = []
        for client_number in range(num_of_clients):
            client = self.create_socket_client(client_number, 1, thread_exceptions, frames)
            clients.append(client)

        # Start camera
        self.app.post('/start')

        for client in clients:
            client.start()

        for client in clients:
            client.join()
        self.check_thread_exceptions(thread_exceptions)


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
