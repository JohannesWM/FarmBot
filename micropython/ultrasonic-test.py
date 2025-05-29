from machine import Pin, time_pulse_us
import time

# Define pins
trigger = Pin(15, Pin.OUT)
echo = Pin(14, Pin.IN)

def get_distance():
    # Send trigger pulse
    trigger.low()
    time.sleep_us(2)
    trigger.high()
    time.sleep_us(10)
    trigger.low()

    # Measure echo pulse duration
    duration = time_pulse_us(echo, 1, 30000)  # 30ms timeout

    # Calculate distance (cm)
    distance = duration * 0.0343 / 2
    return distance

while True:
    dist = get_distance()
    print("Distance:", dist, "cm")
    time.sleep(1)
