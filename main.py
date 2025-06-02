import serial
import time
import ast
from find_serial import serial_ports

# -----------
# X-length ~ 82000
# Moisture-sensor-wet: 275
# -----------

ports = serial_ports()

# Filter out Bluetooth ports
ports = [port for port in ports if "bluetooth" not in port.lower()]
if not ports:
    raise Exception("No suitable serial ports found (after filtering Bluetooth). Please connect the device and try again.")

# Print available serial ports
print("Available serial ports:")
for port in ports:
    print(port)

print("Connecting to the first available port...")

# Open serial port with short timeout for non-blocking reads
# The timeout=0.1 here applies to individual ser.readline() calls
ser = serial.Serial(ports[0], 9600, timeout=0.1)

def wait_till_string(escape_string: str, timeout_seconds: float = 30.0, debug=False) -> None:
    """
    Waits until a specific string is found in the serial input,
    with a timeout for the entire waiting operation.

    Args:
        escape_string (str): The string to look for.
        timeout_seconds (float): The maximum time to wait for the string, in seconds.
                                 Defaults to 30.0 seconds.
        debug (bool): If True, prints received data and status messages.

    Raises:
        TimeoutError: If the escape_string is not found within the specified timeout.
    """
    start_time = time.time()  # Record the start time
    loop = True
    while loop:
        # Check if timeout has been reached
        if time.time() - start_time > timeout_seconds:
            if debug:
                print(f"Timeout occurred after {timeout_seconds} seconds.")
            raise TimeoutError(f"Timeout: '{escape_string}' not received within {timeout_seconds} seconds.")

        rec = str(ser.readline())  # This readline respects the ser.timeout=0.1

        if debug:
            if rec:  # Only print if something was actually received
                # if 
                print(f"Received: {rec.strip()}")  # .strip() for cleaner debug output

        if escape_string in rec:  # Using 'in' is often more robust than find() != -1
            loop = False
        else:
            pass  # Keep looping if string not found

    if debug:
        print(f"Exiting wait_till_string. Found: '{escape_string}'")

moisture_wet = 275

try:
    ser.write(b'IN')

    time.sleep(1)
    recv = str(ser.readlines())  # This readline also respects ser.timeout=0.1

    # Using 'in' for checking presence is often more Pythonic
    if "Recv" not in recv:
        raise Exception(f"Pico did not receive the command. Received: '{recv.strip()}'")

    # Add a timeout parameter to your function calls
    wait_till_string("Axis X homed.", timeout_seconds=120.0, debug=True)

    ser.write(b'MO')
    moisture_zero = str(ser.readlines()).replace("b", "").replace("'", "\"")
    lst = ast.literal_eval(moisture_zero)
    moisture_zero = lst[len(list(lst)) - 1]
    print(f"Moisture_zero: {int(moisture_zero)}")
    moisture_denom = int(moisture_zero) - moisture_wet

    ser.write(b'MVX,41000;MVY,13000;MVZ,140000;MD')
    time.sleep(1)
    ser.readlines()

    time.sleep(45)

    ser.write(b'MO')
    moisture = str(ser.readlines()).replace("b", "").replace("'", "\"")
    lst = ast.literal_eval(moisture)
    moisture = lst[len(list(lst)) - 1]
    print(f"Moisture: {int(moisture)}")

    # Ensure float division for accuracy
    raw_percent_wet = (float(moisture_zero) - float(moisture)) / float(moisture_denom)

    # Clamp the value between 0.0 (0% wet, i.e., fully dry) and 1.0 (100% wet)
    # This handles cases where current_moisture is outside the calibrated range.
    clamped_percent_wet = max(0.0, min(1.0, raw_percent_wet))

    print(f"Moisture percent wet: {clamped_percent_wet * 100:.2f}%")

    ser.write(b'MVZ,-40000') # go back up

    time.sleep(20) # TODO make sure this is accurate

    ser.write(b'MU;MVZ,40000') # going to plant seed

    time.sleep(20)

    ser.write(b'MVZ,-20000')

    time.sleep(8)

    ser.write(b'MVX,10000')

    time.sleep(4)

    ser.write(b'PU')

    input("Press enter to stop water...")

    ser.write(b'PD;MVX,-10000') # we not going back 'too' low because we want to show people seeds dropping

    time.sleep(10)

    ser.write(b'SD0')

    time.sleep(8)

    input("Press Enter to home...")

    # ser.write(b'MVZ,-40000')

    # time.sleep(25)

    ser.write(b'HM')

except TimeoutError as te:
    print(f"Operation timed out: {te}")
    ser.close()  # Ensure port is closed on timeout
except Exception as e:
    print(f"An error occurred: {e}")
    ser.close()  # Ensure port is closed on other exceptions

# This ensures the port is closed even if no exceptions occur
finally:
    if ser.is_open:
        ser.close()
        print("Serial port closed.")