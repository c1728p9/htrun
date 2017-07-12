#!/usr/bin/env python
"""
mbed SDK
Copyright (c) 2017-2017 ARM Limited

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

from mbed_host_tests.host_tests_conn_proxy.conn_primitive import ConnectorPrimitive
from subprocess import Popen, PIPE
from threading import Thread
from Queue import Queue, Empty
from time import sleep


class HostConnectorPrimitive(ConnectorPrimitive):
    def __init__(self, name, config):
        ConnectorPrimitive.__init__(self, name)
        self.image_path = config.get('image_path', None)
        self.polling_timeout = int(config.get('polling_timeout', 10))
        self._bp = BufferedProcess(self.image_path)
        self.__program_start()

    def __program_start(self):
        """Start program execution"""
        #self._process = Popen(self.image_path, stdin=PIPE, stdout=PIPE)
        self._bp.start()

    def read(self, count):
        """Read data from the test application's standard out"""
        #print("Read start")
        #data = self._process.stdout.read(count)
        data = self._bp.read(count, 1)
        #print("Read finsihed: %i" % len(data))
        return data

    def write(self, payload, log=False):
        """Write data to the test application's standard in"""
        if log:
            self.logger.prn_txd(payload)
        #print""
        self._bp.write(payload)
        return True

    def flush(self):
        """No flushing needed"""
        pass

    def connected(self):
        """Return True if the application is running, False otherwise"""
        return self._bp.running()#self._process is not None and self._process.returncode is None

    def finish(self):
        """Close the process if it hasn't been closed already"""
#        print("Calling finish")
#        if self._process is None:
#            return
#        if self._process.returncode is not None:
#            return
#        self._process.kill()
#        self._process = None
        self._bp.finish()


class BufferedProcess(object):

    def __init__(self, path):
        self._path = path
        self._reader = Thread(target=self._read_main)
        self._process = None
        self._remainder = ""
        self._rx_buffer = Queue()

    def start(self):
        assert self._process is None
        self._process = Popen(self._path, stdin=PIPE, stdout=PIPE)
        self._reader.start()

    def _read_main(self):
        while self._process.returncode is None:
            data = self._process.stdout.read(1)
            print("Read block: %s" % len(data))
            if len(data) > 0:
                self._rx_buffer.put(data)
                #print("Read data: %s" % data)
            else:
                print("LOOPING WITH 0 BYTES READ!!!!!: %s" % data)
            assert not self._process.stdout.closed
                #assert self._process.stdout.closed or self._process.returncode is not None
                #assert self._process.returncode is not None
                #break
            self._process.poll()

        print("Read thread exiting!!!!!!!!!!!!!!!!!!!!!")

    def read(self, count, timeout=0.001):
        assert self._process is not None
        new_data = self._remainder[0:count]
        self._remainder = self._remainder[count:]
        size_needed = count - len(new_data)
        #print("Need %i read %i" % (size_needed, len(new_data)))
        try:
            while size_needed > 0:
                data = self._rx_buffer.get(True, timeout)
                new_data += data[:size_needed]
                self._remainder = data[size_needed:]
                size_needed = len(new_data) - count
        except Empty:
            pass
        return new_data

    def write(self, data):
        assert self._process is not None
        #print("Writing data: %s, running %s" % (type(data), self.running()))
        try:
            self._process.stdin.write(data)
        except IOError:
            pass
            #self._process.poll()
           # assert self._process.returncode is not None

    def running(self):
        return self._process is not None and self._process.returncode is None

    def finish(self):
        print("Calling finish")
        if self._process is None:
            return
        if self._process.returncode is not None:
            return
        self._process.kill()
        self._reader.join()

#    def __del__(self):
#        self.finish()
