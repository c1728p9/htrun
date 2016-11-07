#!/usr/bin/env python
"""
mbed SDK
Copyright (c) 2011-2016 ARM Limited

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


from time import sleep
from conn_primitive import ConnectorPrimitive
from dap_serial import DapSerial


class PyocdConnectorPrimitive(ConnectorPrimitive):
    def __init__(self, name, port, baudrate, config):
        ConnectorPrimitive.__init__(self, name)
        self.port = port
        self.baudrate = int(baudrate)
        self.timeout = 0.01  # 10 milli sec
        self.config = config
        self.target_id = self.config.get('target_id', None)
        self.forced_reset_timeout = config.get('forced_reset_timeout', 1)

        # Values used to call serial port listener...
        self.logger.prn_inf("serial(id=%s, baudrate=%d, timeout=%s)" % (self.target_id, self.baudrate, self.timeout))

        try:
            # TIMEOUT: While creating Serial object timeout is delibrately passed as 0. Because blocking in Serial.read
            # impacts thread and mutliprocess functioning in Python. Hence, instead in self.read() s delay (sleep()) is
            # inserted to let serial buffer collect data and avoid spinning on non blocking read().
            self.serial = DapSerial(self.target_id, baudrate=self.baudrate, timeout=0)
        except Exception as e:
            self.serial = None
            self.LAST_ERROR = "connection lost, serial.Serial(%s, %d, %d): %s" % (self.target_id,
                self.baudrate,
                self.timeout,
                str(e))
            self.logger.prn_err(str(e))
        else:
            self.reset_dev_via_pyocd(delay=self.forced_reset_timeout)

    def reset_dev_via_pyocd(self, delay=1):
        """! Reset device using selected method, calls one of the reset plugins """
        reset_type = self.config.get('reset_type', 'default')
        if not reset_type:
            reset_type = 'default'

        self.logger.prn_inf("reset device using pyocd_serial plugin")
        self.serial.send_break(delay)
        result = True

        self.logger.prn_inf("wait for it...")
        return result

    def read(self, count):
        """! Read data from serial port RX buffer """
        # TIMEOUT: Since read is called in a loop, wait for self.timeout period before calling serial.read(). See
        # comment on serial.Serial() call above about timeout.
        sleep(self.timeout)
        c = str()
        try:
            if self.serial:
                c = self.serial.read(count)
        except Exception as e:
            self.serial = None
            self.LAST_ERROR = "connection lost, serial.read(%d): %s"% (count, str(e))
            self.logger.prn_err(str(e))
        return c

    def write(self, payload, log=False):
        """! Write data to serial port TX buffer """
        try:
            if self.serial:
                self.serial.write(payload)
                if log:
                    self.logger.prn_txd(payload)
        except Exception as e:
            self.serial = None
            self.LAST_ERROR = "connection lost, serial.write(%d bytes): %s" % (len(payload), str(e))
            self.logger.prn_err(str(e))
        return payload

    def flush(self):
        if self.serial:
            self.serial.flush()

    def connected(self):
        return bool(self.serial)

    def error(self):
        return self.LAST_ERROR

    def finish(self):
        if self.serial:
            self.serial.close()

    def __del__(self):
        self.finish()
