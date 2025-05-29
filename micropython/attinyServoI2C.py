class AttinyServoI2C:
    def __init__(self, i2c, slave_addr=0x12):
        self.i2c = i2c
        self.slave_addr = slave_addr

    def move_servo(self, index, angle, delay_ms):
        if not (0 <= index <= 3):
            raise ValueError("Servo index must be 0-3")
        if not (0 <= angle <= 180):
            raise ValueError("Angle must be 0-180")
        if not (1 <= delay_ms <= 255):
            raise ValueError("Delay must be 1-255 ms")
        buf = bytes([index, angle, delay_ms])
        self.i2c.writeto(self.slave_addr, buf)

    def scan(self):
        return self.i2c.scan()
