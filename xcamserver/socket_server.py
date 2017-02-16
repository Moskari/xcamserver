'''
Created on 28.12.2016

@author: sapejura
'''
import threading
import socket
import select
import queue
# from xcamserver import worker_ctx, dummy_worker


class SocketServer():

    def __init__(self):
        self.stop_event = threading.Event()
        self.thread = threading.Thread(name='socket thread',
                                       target=self._thread,
                                       args=(self.stop_event,))
        self.data_size = 1024
        self.camera_addr = None
        self.camera_socket = None  # Connection to camera which we are reading

        self.server_socket = None

    def init(self,):
        self.close()
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
        queues = {}  # Every outgoing socket gets its own send queue

        while True:
            # Wait for sockets
            (sread, swrite, sexc) = select.select(self.inputs, self.outputs, [], 1)
            # Exit thread
            if stop_event.is_set():
                self.inputs.clear()
                self.outputs.clear()
                break
            # Check incoming connections
            for sock in sread:
                if sock == self.server_socket:
                    # A "readable" server socket is ready to accept a connection
                    connection, client_address = sock.accept()
                    print('new client registration from', client_address)
                    connection.setblocking(0)
                    if client_address == self.camera_addr:  # Camera connection
                        print('It is the camera.')
                        self.camera_socket = connection
                        self.inputs.append(connection)
                    else:
                        print('It is a new client application.')
                        # Add the socket to outgoing sockets
                        if sock not in self.outputs:
                            self.outputs.append(connection)
                        # Give the socket its own data queue because sockets
                        # can be available for sending at different times
                        if sock not in queues.keys():
                            queues[connection] = queue.Queue()
                elif sock == self.camera_socket:  # Camera is sending data
                    data = sock.recv(self.data_size)
                    if data:
                        # print('Received data from camera. Size:', len(data))
                        for q in queues.values():
                            q.put(data)
                    else:
                        pass
                        # print('No data from camera. Remove connection', sock.getsockname())
                        # self.inputs.remove(sock)
                else:
                    # Client disconnects
                    print('Connection from', sock.getsockname())
                    data = sock.recv(self.data_size)
                    if data:
                        print('Received something unexpected from,', sock.getsockname(), 'Data:', data)
                    else:
                        self.inputs.remove(sock)
                        sock.close()
                        # queues.pop(sock)
                        print('Removed socket', sock.getsockname(), 'from listened inputs')
            # Write received camera data to outgoing sockets which are ready
            for sock in swrite:
                try:
                    # data = message_queue.get_nowait()
                    data = queues[sock].get_nowait()
                except queue.Empty:
                    pass
                    # No messages waiting so stop checking for writability.
                    # print('Queue is empty')
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
                        queues.pop(sock)
                        sock.close()
                        self.outputs.remove(sock)
                        print('Closed connection to', sock_addr)
        print('Socket server closed')
