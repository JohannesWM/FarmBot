from machine import I2C, Pin
from ads1x15 import ADS1115

i2c = I2C(1, scl=Pin(3), sda=Pin(2))
print(i2c.scan())

GAIN = 2  # +/- 2.048V
ads = ADS1115(i2c, gain=GAIN)

def raw_to_percentage(raw_value, raw_empty, raw_full):
    if raw_value < raw_full:
        raw_value = raw_full
    elif raw_value > raw_empty:
        raw_value = raw_empty
    
    percentage = ((raw_empty - raw_value) / (raw_empty - raw_full)) * 100
    return percentage

raw_empty = 29000
raw_full = 6300

while True:
    raw_value = ads.read(0)
    
    percentage = raw_to_percentage(raw_value, raw_empty, raw_full)
    print(f"Raw Value: {raw_value}, Percentage: {percentage:.2f} %")
