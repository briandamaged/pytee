
import os
from threading import Thread, Lock, Semaphore
import time



class WRITE:
    def __init__(self, data):
        self.data = data


class EOF:
    pass




class AsyncWriter:

    def __init__(self, fout):
        self.fout      = fout
        self.queue     = []

        self.queue_lock      = Lock()
        self.event_available = Semaphore(0)

        t                    = Thread(target = self.__event_loop)
        t.daemon             = True
        t.start()

    def write(self, data):
        with self.queue_lock:
            self.queue.insert(0, WRITE(data))

        self.event_available.release()

    def eof(self):
        with self.queue_lock:
            self.queue.insert(0, EOF())

        self.event_available.release()

    def __event_loop(self):
        while True:
            self.event_available.acquire()

            with self.queue_lock:
                event = self.queue.pop()

            if isinstance(event, WRITE):
                self.fout.write(event.data)
            else:
                break

        self.fout.close()




def mux(fin, fout_list):
    fout_list = [AsyncWriter(f) for f in fout_list]
    def _mux():
        data = fin.read()
        while data:
            for f in fout_list:
                f.write(data)
            data = fin.read()

        for f in fout_list:
            f.eof()

    t = Thread(target = _mux)
    t.daemon = True
    t.start()


