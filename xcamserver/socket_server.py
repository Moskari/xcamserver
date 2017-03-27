'''
Created on 28.12.2016

@author: sapejura
'''
import threading
import socket
import select
import queue
from xcamserver.framebuffer import FrameQueue
# from xcamserver import worker_ctx, dummy_worker


class SocketServer():

    def __init__(self):
        self.stop_event = threading.Event()
        self.thread = threading.Thread(name='socket thread',
                                       target=self._thread,
                                       args=(self.stop_event,))
        self._data_size = 4096  # Size of data chunks read from camera
        self._frame_size = None  # Size of frame read from camera
        self.camera_addr = None
        self.camera_socket = None  # Connection to camera which we are reading

        self.server_socket = None

    def init(self, frame_size):
        self.close()
        self._frame_size = frame_size
        print('Creating new socket...')
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.settimeout(60)
        self.server_socket.bind(('localhost', 0))
        # self.server_socket.setblocking(1)
        # server_socket.bind(('localhost', 8000))
        server_addr = self.server_socket.getsockname()
        print('...binded...')
        print('...picked server address: %s...' % str(server_addr))
        self.server_socket.listen(100)
        # print('...server socket is listening max 10 connection.')

    def run(self):
        if self.is_alive():
            raise Exception('Socket server is already online')
        self.inputs = [self.server_socket]
        self.outputs = []
        self.stop_event.clear()
        self.thread.start()

    def stop(self):
        if self.is_alive():
            self.stop_event.set()
            self.thread.join(10)
            if self.is_alive():
                raise Exception('Socket server didn\'t stop.')
            for sock in self.outputs:
                try:
                    sock.close()
                except:
                    print('Could not close socket', sock)
            for sock in self.inputs:
                try:
                    sock.close()
                except:
                    print('Could not close socket', sock)
        else:
            raise Exception('Can\'t stop socket server. Server is already stopped.')

    def close(self):
        if self.is_alive():
            self.stop()
        if self.server_socket:
            self.server_socket.close()
        if self.camera_socket:
            self.camera_socket.close()

    def is_alive(self):
        return self.thread.isAlive()

    def _thread(self, stop_event):
        # TODO: Exception handling
        # TODO: This will definitely stackoverflow if there are no clients ever. Queue needs buffered replacement
        # print('server_socket:', self.server_socket.getsockname(), 'client_socket:', self.camera_addr)
        queues = {}  # Every outgoing socket gets its own send and receive queues
        while True:
            # Wait for sockets
            (sread, swrite, sexc) = select.select(self.inputs, self.outputs, [], 1)
            # Exit thread
            if stop_event.is_set():
                self.inputs.clear()
                self.outputs.clear()
                break
            # Check incoming connections
            self._handle_read_reqs(queues, sread, swrite, sexc)
            # Write received camera data to outgoing sockets which are ready
            self._handle_write_reqs(queues, sread, swrite, sexc)
        print('Socket server closed')

    def _remove_socket(self, sock, queues, sread, swrite, sexc):
        sock_addr, peer_addr = None, None
        try:
            sock_addr = sock.getsockname()
        except:
            pass
        try:
            peer_addr = sock.getpeername()
        except:
            pass
        queues.pop(sock)
        if sock in self.inputs:
            self.inputs.remove(sock)
        if sock in self.outputs:
            self.outputs.remove(sock)
        if sock in sread:
            sread.remove(sock)
        if sock in swrite:
            swrite.remove(sock)
        if sock in sexc:
            sexc.remove(sock)
        sock.close()
        print('Closed connection to', peer_addr, 'from', sock_addr)

    def _handle_read_reqs(self, queues, sread, swrite, sexc):

        for sock in sread:
            if sock == self.server_socket:
                # A "readable" server socket is ready to accept a connection
                connection, client_address = sock.accept()
                print('new client registration from', client_address)
                connection.setblocking(0)
                if client_address == self.camera_addr:  # Camera connection
                    self._add_camera_sock(connection)
                else:
                    self._add_client_sock(connection, queues)
            elif sock == self.camera_socket:  # Camera is sending data
                self._recv_from_camera(sock, queues)
            else:
                error = self._recv_from_client(sock, queues)
                if error:
                    self._remove_socket(sock, queues, sread, swrite, sexc)
                    continue

    def _add_camera_sock(self, connection):
        print('It is the camera.')
        self.camera_socket = connection
        self.inputs.append(connection)

    def _add_client_sock(self, connection, queues):
        print('It is a new client application:', connection.getpeername())
        # Add the socket to outgoing sockets
        # if sock not in self.outputs:
        #     self.outputs.append(connection)
        self.inputs.append(connection)
        # Give the socket its own data queue because sockets
        # can be available for sending at different times
        if connection not in queues.keys():
            # Outgoing data and control frames
            tx_q = FrameQueue(self._frame_size + 4)  # timestamp is 4 bytes
            # Incoming control frames
            rx_q = FrameQueue(4)
            rx_q.set_mode(b'\x02')  # Cares only about the newest control frames
            queues[connection] = (tx_q, rx_q)

    def _recv_from_camera(self, sock, queues):
        data = sock.recv(self._data_size)
        if data:
            for tx_q, _ in queues.values():
                tx_q.put(data)
        else:
            pass

    def _recv_from_client(self, sock, queues):
        print('Connection from', sock.getpeername())
        msg_size = 4
        try:
            data = sock.recv(msg_size)
        except (ConnectionAbortedError,
                ConnectionResetError) as e:
            return True
        else:
            if data == b'':
                # Client disconnects
                print('Removing socket', sock.getpeername(), 'from listened inputs and outputs, closing connection.')
                return True
            else:
                print('Received ctrl data:', data, 'from client', sock.getpeername())
                # print('Received something unexpected from,', sock.getpeername(), 'Data:', data)
                tx_q, rx_q = queues[sock]
                rx_q.put(data)
                if rx_q.buffer_size() >= msg_size:
                    msg = rx_q.get(4)
                    print('Received full ctrl package:', msg)
                    # print(msg[0:1])
                    tx_q.set_mode(msg[0:1])
                    if sock not in self.outputs:
                        self.outputs.append(sock)
        return False

    def _handle_write_reqs(self, queues, sread, swrite, sexc):
        for sock in swrite:
            # data = message_queue.get_nowait()
            tx_q, _ = queues[sock]
            data = tx_q.get()
            if len(data) == 0:
                pass
            else:
                try:
                    sent_data = 0
                    # print('Sending data to socket', s.getsockname())
                    while(sent_data < len(data)):
                        sent_data += sock.send(data[sent_data:])
                        # print('Sent', sent_data, 'bytes')
                    # print('Sent data to socket', sock.getpeername())
                except (ConnectionResetError,
                        ConnectionAbortedError,
                        ConnectionRefusedError) as e:
                    sock_addr = sock.getpeername()
                    print('Connection to', sock_addr, 'lost')
                    print('%s(%s): %s' % (type(e).__name__, str(e.errno), e.strerror))
                    self._remove_socket(sock, queues, sread, swrite, sexc)
                    continue

