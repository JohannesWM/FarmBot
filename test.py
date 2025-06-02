import serial
import time
import ast


# -----------
# X-length ~ 82000
# Moisture-sensor-wet: 275
# -----------

# Open serial port with short timeout for non-blocking reads
# The timeout=0.1 here applies to individual ser.readline() calls
ser = serial.Serial('/dev/cu.usbmodem1414401', 9600, timeout=0.1)


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
                print(f"Received: {rec.strip()}")  # .strip() for cleaner debug output

        if escape_string in rec:  # Using 'in' is often more robust than find() != -1
            loop = False
        else:
            pass  # Keep looping if string not found

    if debug:
        print(f"Exiting wait_till_string. Found: '{escape_string}'")

moisture_wet = 275

try:
    ser.write(b'EN')

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