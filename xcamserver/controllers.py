'''
Created on 13.12.2016

@author: Samuli Rahkonen
'''
import flask
import xcamserver
from xcamserver import app
from xcamserver import worker_ctx, \
                       socket_server
# from xcamserver.sockets import create_socket_thread
import socket
import threading
from xcamserver.socket_server import SocketServer


def meta2json(data):
    return flask.jsonify(**data)


@app.route('/', methods=['GET'])
def root_msg():
    return '' + \
        'REST API\n' + \
        'Every command returns metadata json.\n' + \
        '-------\n' + \
        '/init  ; POST Initializes camera and sets up server for streaming.\n' + \
        '/start ; POST Starts the camera and begins streaming data to socket.\n' + \
        '/stop  ; POST Stops the camera.\n' + \
        '/close ; POST Closes camera and server.\n' + \
        '/meta  ; GET  Returns current state and camera properties in json.\n' + \
        '-------\n' + \
        'METADATA fields:\n' + \
        '-------\n' + \
        'byte order     ; Byte order of data words. 1 for MSB first and 0 for LSB.\n' + \
        'data type      ; String for stream pixel data type. I.e. u2 = unsigned 16 bit int.\n' + \
        'error          ; Error description string, otherwise nul\n' + \
        'frame_size     ; Size of frame in bytes.\n' + \
        'height         ; Height of the image in pixels.\n' + \
        'width          ; Width of the image in pixels.\n' + \
        'interleave     ; How data is interleaved in case of spectral data. bil, bsq or bip. For line scanner it is bil.\n' + \
        'status         ; Current status of the server. CLOSED, STOPPED, STARTING, RUNNING.\n' + \
        'stream_address ; Address to the stream.\n'


@app.route('/init', methods=['GET', 'POST'])
def init_worker():
    with worker_ctx() as worker:
        try:
            worker.init()
            xcamserver.socket_server.init()
            xcamserver.socket_server.data_size = worker.frame_size
            # if xcamserver.socket_server is None:
            #     xcamserver.socket_server = SocketServer()
            server_addr = xcamserver.socket_server.server_socket.getsockname()
            # Connect to SocketServer
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect(server_addr)
            client_addr = client_socket.getsockname()

            # Socket server listens the camera worker
            xcamserver.socket_server.camera_addr = client_addr

            # Camera writes data to the socket
            connection = client_socket.makefile(mode='wb')
            worker.camera_handler = connection
            worker.stream_address = server_addr

            xcamserver.socket_server.run()
        except Exception as e:
            print('%s' % str(repr(e)))
        finally:
            return meta2json(worker.get_meta())


@app.route('/close', methods=['GET', 'POST'])
def close_worker():
    with worker_ctx() as worker:
        try:
            worker.close()
        finally:
            return meta2json(worker.get_meta())


@app.route('/start', methods=['POST', 'GET'])
def start_worker():
    print('Starting worker')
    # Contexts are for preventing overlapping accesses to resources
    with worker_ctx() as worker:
        # if not worker.initialized:
        #     print('Worker is not initialized. Call /init before calling /start')
        #     worker.status = 'ERROR'
        #     worker.error = 'Worker is not initialized. Call /init before calling /start'
        #     return get_metadata()
        try:
            # worker.set_handler(worker.camera_handler)
            worker.start()
        except:
            return meta2json(worker.get_meta())
        else:
            print('Worker is starting.')
            return meta2json(worker.get_meta())


'''
def _create_socket(server_socket):
    try:
        # with worker_ctx():
        # Wait for a connection to the socket
        print('Server socket is waiting a connection...')
        client_socket, client_addr = server_socket.accept()
        print('...accepted client address: %s' % str(client_addr))

        # Make the socket a file like object
        connection = client_socket.makefile(mode='wb')
        # print('Makefile done')
        with worker_ctx() as worker:
            worker.status = 'STARTING'
            # if not worker.cam.enabled():
            worker.client_address = client_addr
            worker.set_handler(connection)
            print('Worker is starting')
            worker.start()
        # print('Started')
    except Exception as e:
        print('Exception', e)
        raise
'''


@app.route('/stop', methods=['POST', 'GET'])
def stop_worker():
    with worker_ctx() as worker:
        try:
            worker.stop()
        except:
            pass
        finally:
            return meta2json(worker.get_meta())


@app.route('/close', methods=['POST', 'GET'])
def close():
    with worker_ctx() as worker:
        try:
            worker.close()
            xcamserver.socket_server.close()
        except:
            pass
        finally:
            return meta2json(worker.get_meta())


@app.route('/meta', methods=['GET'])
def get_metadata():
    with worker_ctx() as worker:
        try:
            data = worker.get_meta()
        except:
            pass
        finally:
            return meta2json(data)


def shutdown_server():
    func = flask.request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()


@app.route('/shutdown', methods=['GET', 'POST'])
def shutdown():
    import time
    time.sleep(1)
    shutdown_server()
    xcamserver.socket_server.close()
    return 'Server shutting down...'
