from machine import Pin
import time

# Define stopper input pins
STOPPER_X = Pin(6, Pin.IN, Pin.PULL_UP)
STOPPER_Y = Pin(7, Pin.IN, Pin.PULL_UP)
STOPPER_Z = Pin(8, Pin.IN, Pin.PULL_UP)

def read_stoppers():
    # Adjust logic depending on how your stopper works: LOW when pressed or HIGH?
    # This example assumes LOW = triggered
    stopper_x_triggered = STOPPER_X.value() == 0
    stopper_y_triggered = STOPPER_Y.value() == 0
    stopper_z_triggered = STOPPER_Z.value() == 0

    print("Stopper X:", stopper_x_triggered)
    print("Stopper Y:", stopper_y_triggered)
    print("Stopper Z:", stopper_z_triggered)

# Loop to continuously check stopper states
while True:
    read_stoppers()
    time.sleep(0.5)
