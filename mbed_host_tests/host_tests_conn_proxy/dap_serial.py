from pyOCD.pyDAPAccess import DAPAccess
import time


class DapSerial(object):
    COMMAND_CONFIG = 1
    COMMAND_RESET = 2
    COMMAND_READ_WRITE = 3

    _MAX_PAYLOAD = 61

    def __init__(self, board_id, baudrate=9600, timeout=None):
        self._baud = baudrate
        self._config = []
        self._read_timeout = timeout
        self._write_timeout = None
        self._tx_data = []
        self._rx_data = []
        self._id = board_id
        self._dap = DAPAccess.get_device(self._id)
        self._dap.open()
        self.baudrate = baudrate

    def write(self, data):
        start = time.time()
        self._tx_data.extend(list(bytearray(data)))

        while len(self._tx_data) > 0:
            size_to_send = len(self._tx_data)
            if size_to_send > self._MAX_PAYLOAD:
                size_to_send = self._MAX_PAYLOAD
            payload = [self._MAX_PAYLOAD, size_to_send]
            payload.extend(list(bytearray(self._tx_data[:size_to_send])))
            ret = self._dap.vendor(self.COMMAND_READ_WRITE, payload)
            size_read = ret[0]
            size_sent = ret[1]
            self._rx_data.extend(ret[2:2 + size_read])
            self._tx_data = self._tx_data[size_sent:]
            if (self._write_timeout is not None and
                    time.time() - start > self._write_timeout):
                self._tx_data = []
                break

    def read(self, size, timeout=None):
        start = time.time()
        while len(self._rx_data) < size:
            data = [self._MAX_PAYLOAD, 0]
            ret = self._dap.vendor(self.COMMAND_READ_WRITE, data)
            size_read = ret[0]
            serial_data = ret[2:2 + size_read]
            self._rx_data.extend(serial_data)
            if (self._read_timeout is not None and
                    time.time() - start > self._read_timeout):
                break
        data = self._rx_data[:size]
        self._rx_data = self._rx_data[size:]
        return str(bytearray(data))

    def flush(self):
        # Write flushes before it returns
        pass

    @property
    def baudrate(self):
        return self._baud

    @baudrate.setter
    def baudrate(self, value):
        self._baud = value
        self._update_config()
        self._dap.vendor(self.COMMAND_CONFIG, self._config)

    def send_break(self, duration=0.25):
        self._dap.vendor(self.COMMAND_RESET, [1])
        time.sleep(duration)
        self._dap.vendor(self.COMMAND_RESET, [0])

    def close(self):
        self._dap.close()

    def _update_config(self):
        self._config = [
            (self._baud >> 0) & 0xFF,
            (self._baud >> 8) & 0xFF,
            (self._baud >> 16) & 0xFF,
            (self._baud >> 24) & 0xFF,
            8,  # DataBits
            0,  # Parity
            0,  # StopBits
            0,  # FlowControl
        ]
