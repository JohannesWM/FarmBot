from machine import Pin, time_pulse_us
import time

class UltrasonicSensor:
    def __init__(self, trig_pin, echo_pin):
        self.trig = Pin(trig_pin, Pin.OUT)
        self.echo = Pin(echo_pin, Pin.IN)

    def read_distance_cm(self):
        # Send trigger pulse
        self.trig.low()
        time.sleep_us(2)
        self.trig.high()
        time.sleep_us(10)
        self.trig.low()

        try:
            duration = time_pulse_us(self.echo, 1, 30000)  # Wait for echo high
            distance = (duration / 2) / 29.1  # Convert to cm
            return round(distance, 2)
        except OSError:
            return None
