from machine import I2C, Pin
from attinyServoI2C import AttinyServoI2C
import time

i2c = I2C(0, scl=Pin(1), sda=Pin(0), freq=100000)
servo_ctrl = AttinyServoI2C(i2c)

print("I2C devices found:", servo_ctrl.scan())

servo_ctrl.move_servo(0, 180, 15)
time.sleep(3)
servo_ctrl.move_servo(0, 0, 30)
