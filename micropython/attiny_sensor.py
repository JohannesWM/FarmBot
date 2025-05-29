from machine import Pin, I2C
import struct

class ATtinySensor:
    CMD_RESET_BASELINE = 0x01
    CMD_SET_THRESHOLD = 0x02

    def __init__(self, i2c, i2c_addr=0x10, interrupt_pin=15):
        self.i2c = i2c
        self.i2c_addr = i2c_addr
        self.interrupt_pin = Pin(interrupt_pin, Pin.IN, Pin.PULL_DOWN)
        self.interrupt_pin.irq(trigger=Pin.IRQ_RISING, handler=self._interrupt_handler)
        self.photogate_triggered_flag = False

    def _interrupt_handler(self, pin):
        self.photogate_triggered_flag = True
        print("Photogate triggered!")

    def read_sensors(self):
        try:
            data = self.i2c.readfrom(self.i2c_addr, 4)
            light, moisture = struct.unpack('<HH', data)
            return light, moisture
        except Exception as e:
            print("I2C read error:", e)
            return None, None

    def send_command(self, cmd, value=None):
        try:
            if value is not None:
                self.i2c.writeto(self.i2c_addr, bytes([cmd, value]))
            else:
                self.i2c.writeto(self.i2c_addr, bytes([cmd]))
        except Exception as e:
            print("I2C write error:", e)

    def reset_baseline(self):
        self.send_command(self.CMD_RESET_BASELINE)

    def set_threshold(self, threshold):
        if 0 <= threshold <= 255:
            self.send_command(self.CMD_SET_THRESHOLD, threshold)
        else:
            print("Threshold must be 0-255")

    def check_photogate_triggered(self):
        triggered = self.photogate_triggered_flag
        self.photogate_triggered_flag = False
        return triggered
