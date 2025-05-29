from machine import Pin, I2C
from attiny_sensor import ATtinySensor
import time

# Initialize I2C outside the class
i2c = I2C(0, scl=Pin(5), sda=Pin(4), freq=100000)

# Pass I2C to the class
sensor = ATtinySensor(i2c)

while True:
    light, moisture = sensor.read_sensors()
    if light is not None:
        print(f"Light: {light}, Moisture: {moisture}")

    if sensor.check_photogate_triggered():
        print("Photogate event detected!")

    time.sleep(1)
