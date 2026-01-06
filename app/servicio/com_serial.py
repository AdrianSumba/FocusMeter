import serial
import time

PUERTO = "/dev/ttyACM0"
BAUDIOS = 115200

class SerialManager:
    def __init__(self):
        self.serial = None
        self.last_send = 0

    def connect(self):
        try:
            self.serial = serial.Serial(PUERTO, BAUDIOS, timeout=1)
            time.sleep(2)
        except serial.SerialException:
            self.serial = None

    def send(self, value):
        if self.serial is None:
            self.connect()
            return

        now = time.time()
        if now - self.last_send >= 4:
            try:
                self.serial.write(f"<{value}>\n".encode())
                self.last_send = now
            except serial.SerialException:
                try:
                    self.serial.close()
                except Exception:
                    pass
                self.serial = None
