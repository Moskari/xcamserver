'''
Created on 15.2.2017

@author: sapejura
'''
import io
import threading
import struct


class FrameQueue(io.IOBase):

    def __init__(self, frame_size):
        super().__init__()
        self.queue_lock = threading.Lock()
        self._queue = bytearray()
        self._store_mode = 0
        self.frame_size = frame_size
        # self.remaining = bytearray()
        # self.memview = memoryview(self.remaining)

    def readable(self):
        return True

    def writable(self):
        return True

    def put(self, b):
        self._queue.extend(b)
        return len(b)

    def get(self, n=-1):
        '''
        Depending on the FrameQueue mode this method returns
        different bytearray.

        mode 1:
          makes the queue FIFO and returns n bytes from it.
          n=-1 returns everything.
        mode 2:
          makes the queue LILO and returns the last full
          'frame_size' bytes frame. Otherwise returns b''.
        '''
        if self._store_mode == 1:
            if n < 0:
                b = self._queue[:]
                del self._queue[:]
            else:
                b = self._queue[:n]
                del self._queue[:n]
        elif self._store_mode == 2:
            # Returns the last full frame and
            # removes it and everything come before that
            l = len(self._queue)
            frames = int(l/self.frame_size)
            start = max((frames-1)*self.frame_size, 0)
            end = start + self.frame_size
            if l >= end-start:
                b = self._queue[start:end]
                del self._queue[:end]
            else:
                b = b''
        else:
            b = b''
        return b

    def set_mode(self, byte):
        m = struct.unpack('B', byte)[0]
        if m in [0, 1, 2]:
            self._store_mode = m
        else:
            raise Exception('Illegal mode parameter.')

    def buffer_size(self):
        return len(self._queue)

    def is_empty(self):
        size = len(self._queue)
        return size == 0

    def clear_queue(self):
        self._queue = bytearray()
