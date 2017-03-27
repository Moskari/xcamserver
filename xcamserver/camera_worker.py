'''
Created on 13.12.2016

@author: Samuli Rahkonen
'''
import threading
import time
import struct


class BaseWorker():

    def __init__(self):
        self.stream_address = None  # Address to socket server
        self.camera_handler = None  # 'makefile' socket that connects to camera
        self.stop_event = None  # Event to stop camera
        self._capture_thread = None

        self.status = 'CLOSED'
        self._error = ''
        self.frame_size = None
        self.width = None
        self.height = None
        self.interleave = None
        self.byte_order = None
        self.data_type = None

        self._initialized_lock = threading.Lock()
        self._initialized = False

    @property
    def initialized(self):
        with self._initialized_lock:
            return self._initialized

    @initialized.setter
    def initialized(self, val):
        with self._initialized_lock:
            self._initialized = val

    def error(self, *msg_args):
        text = ' '.join(map(lambda x: str(x), msg_args))
        self._error = text + '\n' + self._error

    def has_error(self):
        return self._error != ''

    def clear_error(self):
        self._error = ''

    def get_meta(self):
        return {'status': self.status,
                'error': self._error,
                'stream_address': self.stream_address,
                'frame_size': self.frame_size,
                'width': self.width,
                'height': self.height,
                'interleave': self.interleave,
                'byte order': self.byte_order,
                'data type': self.data_type,
                'clients': 0}  # TODO:


class CameraWorker(BaseWorker):
    '''
    CameraWorker must have only one handler (the socket server) at a time.
    '''

    def __init__(self, camera):
        super().__init__()
        self.cam = camera
        self.stop_event = threading.Event()
        self._capture_thread = threading.Thread(name='camera thread',
                                                target=self._thread,
                                                args=(self.stop_event,))

    def is_alive(self):
        return self._capture_thread.isAlive()

    def set_handler(self, handler, incl_ctrl_frames=False):
        self.cam.set_handler(handler, incl_ctrl_frames)

    def clear_handlers(self):
        self.cam.clear_handlers()

    def init(self):
        try:
            # if self.initialized:
            #     self.status = 'ERROR'
            #     self.error = 'Camera is already initialized.'
            #     raise Exception('Camera is already initialized.')
            if self.status != 'CLOSED' or self.has_error():
                self.close()
            self.cam.open()
            self.height, self.width = self.cam.get_frame_dims()
            self.frame_size = self.cam.get_frame_size()
            self.data_type = 'u%d' % self.cam.get_pixel_size()
            self.interleave = 'bil'
            self.initialized = True
            self.status = 'STOPPED'
        except Exception as e:
            self.error('INIT', repr(e))
            self.initialized = False
            raise

    def close(self):
        if self.is_alive():
            self.stop()
        self.cam.close()
        self.initialized = False
        self.status = 'CLOSED'
        self.clear_error()

    def start(self):
        if self.is_alive():
            self.error('START', 'Camera is already started')
            raise Exception('Camera is already started')
        if not self.initialized:
            self.error('START', 'Camera is not initialized')
            raise Exception('Camera is not initialized')
        self.set_handler(self.camera_handler, incl_ctrl_frames=True)
        self.status = 'STARTING'
        self.stop_event.clear()
        self._capture_thread = threading.Thread(name='camera thread',
                                                target=self._thread,
                                                args=(self.stop_event,))
        self._capture_thread.start()
        if not self.is_alive():
            self.error('START', 'Thread didn\'t start')
            raise Exception('Thread didn\'t start')
        self.status = 'RUNNING'

    def stop(self):
        if not self.is_alive():
            print('No need to stop when worker is not alive')
            return
        self.stop_event.set()
        self._capture_thread.join(5)
        if self.is_alive():
            self.error('STOP', 'Thread didn\'t stop')
            raise Exception('Thread didn\'t stop')
        # self.clear_handlers()
        self.status = 'STOPPED'

    def _thread(self, stop_event):
        print('CameraWorker thread started.')
        try:
            self.cam.start_recording()
            while not stop_event.is_set():
                self.cam.check_thread_exceptions()
            self.cam.stop_recording()
        except ConnectionAbortedError as e:
            # TODO: This potentially messes up metadata (mainly error)
            # because the variable is not thread safe
            print('CameraWorker thread failed')
            error = repr(e)  # '%s(%s): %s' % (str(type(e).__name__), str(e.errno), e.strerror)
            print(error)
            print('Stopping thread...')
            stop_event.set()
            # Connection failed so handler has to be removed to prevent it
            # from messing up next connections
            print('Removing connection handlers from worker.')
            self.clear_handlers()
            self.error('_THREAD', error)
            self.close()
        finally:
            print('CameraWorker thread closed.')


class DummyWorker(BaseWorker):

    def __init__(self, interval=0.5):
        '''
        Constructor for DummyWorker that simulates a real CameraWorker
        for testing purposes.
        @param interval: Float for specifying time between simulated frames
        '''
        super().__init__()
        self.handlers = []
        self.stop_event = threading.Event()
        self._capture_thread = threading.Thread(name='dummy camera thread',
                                                target=self._thread,
                                                args=(self.stop_event,))
        self.interval = interval

    def is_alive(self):
        return self._capture_thread.isAlive()

    def set_handler(self, handler, incl_ctrl_frames=False):
        self.handlers.append((handler, incl_ctrl_frames))

    def clear_handlers(self):
        self.handlers.clear()

    def init(self):
        if self.status != 'CLOSED':
            self.close()
        self.initialized = True
        self.height = 256
        self.width = 320
        self.frame_size = 163840
        self.data_type = 'u2'
        self.interleave = 'bil'

        self.status = 'STOPPED'

    def close(self):
        if self.is_alive():
            self.stop()
        self.initialized = False
        self.status = 'CLOSED'
        self.clear_error()

    def start(self):
        if self.is_alive():
            self.error('Camera is already started')
            raise Exception('Camera is already started')
        if not self.initialized:
            self.error('Camera is not initialized')
            raise Exception('Camera is not initialized')
        # self.handlers.append(self.camera_handler)
        self.set_handler(self.camera_handler, incl_ctrl_frames=True)
        self.status = 'STARTING'
        self.stop_event.clear()
        self._capture_thread = threading.Thread(name='dummy camera thread',
                                                target=self._thread,
                                                args=(self.stop_event,))
        self._capture_thread.start()
        if not self.is_alive():
            self.error('Thread didn\'t start')
            raise Exception('Thread didn\'t start')
        self.status = 'RUNNING'

    def stop(self):
        if not self.is_alive():
            print('No need to stop when worker is not alive')
            return
        self.stop_event.set()
        self._capture_thread.join(5)
        if self.is_alive():
            self.error('Thread didn\'t stop')
            raise Exception('Thread didn\'t stop')
        self.handlers.clear()
        self.status = 'STOPPED'

    def _thread(self, stop_event):
        print('DummyWorker thread started.')
        try:
            i = 0
            while not stop_event.is_set():
                # i = (i + 1) % 256
                val = (i + 1) % 256
                vals = [val] * self.frame_size
                dummy_data = struct.pack('%sB' % self.frame_size, *vals)
                # dummy_data = struct.pack('B', i) * self.frame_size
                for h, incl_ctrl_frame in self.handlers:
                    if incl_ctrl_frame:
                        h.write(struct.pack('I', i))
                    h.write(dummy_data)
                    # print('Wrote to handler.')
                    time.sleep(self.interval)
                i += 1
        except ConnectionAbortedError as e:
            # TODO: This potentially messes up metadata (mainly status and error)
            # because the variable is not thread safe
            error = repr(e)  # '%s(%s): %s' % (str(type(e).__name__), str(e.errno), e.strerror)
            print(error)
            print('Stopping thread...')
            stop_event.set()
            # Connection failed so handler has to be removed to prevent it
            # from messing up next connections
            print('Removing connection handler from worker.')
            self.clear_handlers()
            self.error(error)
        print('DummyWorker thread closed.')
