from machine import Pin, ADC
import sys
import uselect
from termreader import TermReader
import motor
from pins import *
from constants import *
from attiny_sensor import ATtinySensor
from ultrasonic import UltrasonicSensor
from attinyServoI2C import AttinyServoI2C

button = machine.Pin(FORCE_STOP, machine.Pin.IN, machine.Pin.PULL_UP)
if button.value() == 0:
    print("stopped")
    sys.exit()


# MM per step 0.01262195
# 82169

stepperX = motor.StepperController(0, step_pin=STEP_PIN_X, dir_pin=DIR_PIN_X, enable_pin=ENABLE_PIN_X, stopper_pin=STOPPER_PIN_X, max_speed=MAX_SPEED, acceleration=ACCELERATION)
stepperY = motor.StepperController(1, step_pin=STEP_PIN_Y, dir_pin=DIR_PIN_Y, enable_pin=ENABLE_PIN_Y, stopper_pin=STOPPER_PIN_Y, max_speed=MAX_SPEED, acceleration=ACCELERATION)
stepperZ = motor.StepperController(2, step_pin=STEP_PIN_Z, dir_pin=DIR_PIN_Z, enable_pin=ENABLE_PIN_Z, stopper_pin=STOPPER_PIN_Z, max_speed=MAX_SPEED, acceleration=ACCELERATION)

axes = {"x": stepperX, "y": stepperY, "z": stepperZ}
homing_axes_queue = []
current_homing_axis = None

i2c = I2C(0, scl=Pin(SCL_PIN), sda=Pin(SDA_PIN))
sensor = ATtinySensor(i2c)
servo_12 = AttinyServoI2C(i2c, slave_addr=0x12)  # Lettuce, Mesculin, Sensor
servo_13 = AttinyServoI2C(i2c, slave_addr=0x13)  # Spinach, Carrots

pump_relay = Pin(PUMP_RELAY_PIN, Pin.OUT)
pump_relay.value(0)  # Start with pump off

temp_sensor_adc = ADC(Pin(TEMP_SENSOR_PIN))

def process_command(command):
    commands = command.split(";")
    for cmd in commands:
        command_type = cmd[:2]
        if not command_type:
            continue
        arguments = cmd[2:].split(",") if cmd[2:] else []        
        
        if command_type == "MV": # Move
            axis = arguments[0]
            steps = int(arguments[1])
            if axis == "X":
                axes["x"].start(steps)
            elif axis == "Y":
                axes["y"].start(steps)
            elif axis == "Z":
                axes["z"].start(steps)
            else:
                print(f"Unknown axis: {axis}")
            
        elif cmd == "HM": # Home
            if len(homing_axes_queue) == 0:
                homing_axes_queue.extend(["x", "y", "z"])
                
        elif cmd == "PS": # Position status
            displacements = {key: axis.displacement for key, axis in axes.items()}
            print(displacements)
            
        elif command_type == "ST": # Stop
            axes["x"].stop()
            axes["y"].stop()
            axes["z"].stop()
            
        elif command_type == "EN": # Enable
            if arguments:
                axis = arguments[0]
                if axis == "X":
                    axes["x"].enable_motor()
                elif axis == "Y":
                    axes["y"].enable_motor()
                elif axis == "Z":
                    axes["z"].enable_motor()
                else:
                    print(f"Unknown axis: {axis}")
            else:
                axes["x"].enable_motor()
                axes["y"].enable_motor()
                axes["z"].enable_motor()
                print("All motors enabled.")
                
        elif command_type == "DI": # Disable
            if arguments:
                axis = arguments[0]
                if axis == "X":
                    axes["x"].disable_motor()
                elif axis == "Y":
                    axes["y"].disable_motor()
                elif axis == "Z":
                    axes["z"].disable_motor()
                else:
                    print(f"Unknown axis: {axis}")
            else:
                axes["x"].disable_motor()
                axes["y"].disable_motor()
                axes["z"].disable_motor()
                print("All motors disabled.")
        
        elif command_type == "MS": # Max speed
            if len(arguments) == 1:
                speed = int(arguments[0])
                axes["x"].max_speed = speed
                axes["y"].max_speed = speed
                axes["z"].max_speed = speed
                print(f"Max speed set to {speed} for all axes.")
            elif len(arguments) == 2:
                # If axis is provided, apply to specific axis
                axis = arguments[0]
                speed = int(arguments[1])
                if axis == "X":
                    axes["x"].max_speed = speed
                elif axis == "Y":
                    axes["y"].max_speed = speed
                elif axis == "Z":
                    axes["z"].max_speed = speed
                else:
                    print(f"Unknown axis: {axis}")
            else:
                print("Invalid arguments for MS command.")
           
        elif command_type == "AC":
            if len(arguments) == 1:
                acceleration = int(arguments[0])
                axes["x"].acceleration = acceleration
                axes["y"].acceleration = acceleration
                axes["z"].acceleration = acceleration
                print(f"Acceleration set to {acceleration} for all axes.")
            elif len(arguments) == 2:
                axis = arguments[0]
                acceleration = int(arguments[1])
                if axis == "X":
                    axes["x"].acceleration = acceleration
                elif axis == "Y":
                    axes["y"].acceleration = acceleration
                elif axis == "Z":
                    axes["z"].acceleration = acceleration
                else:
                    print(f"Unknown axis: {axis}")
            else:
                print("Invalid arguments for AC command.")
                
        elif command_type == "IN": # Initiliaze
            for axis in axes.values():
                axis.max_speed = MAX_SPEED
                axis.acceleration = ACCELERATION
            homing_axes_queue.extend(["x", "y", "z"])
            print("System initialized: All settings reset to defaults and axes homed.")
        
        elif command_type == "DF": # Default
            for axis in axes.values():
                axis.max_speed = MAX_SPEED
                axis.acceleration = ACCELERATION
            
            print("Defaults reset for all axes.")
        
        elif command_type == "VS": # Vector State
            status_dict = {}
            for key, axis in axes.items():
                status_dict[key.upper()] = {
                    "enabled": axis.enabled,
                    "moving": axis.running,
                    "displacement": axis.displacement,
                }
            print(status_dict)
         
        elif command_type == "MO":  # Moisture
            _, moisture = sensor.read_sensors()
            if moisture is not None:
                print(moisture)
            else:
                print("Moisture sensor read failed.")

        elif command_type == "RB":  # Reset baseline
            sensor.reset_baseline()
            print("Sensor baseline reset.")

        elif command_type == "TH":  # Set threshold
            if arguments:
                try:
                    threshold = int(arguments[0])
                    sensor.set_threshold(threshold)
                    print(f"Threshold set to {threshold}")
                except ValueError:
                    print("Invalid threshold value.")
            else:
                print("Threshold value required.")

        elif command_type == "PT":  # Photogate triggered?
            if sensor.check_photogate_triggered():
                print("Photogate was triggered.")
            else:
                print("No photogate event.")
    
        elif command_type == "US":  # Ultrasonic sensor read
            distance = ultrasonic.read_distance_cm()
            if distance is not None:
                print(distance)
            else:
                print("Ultrasonic read failed.")

        elif command_type == "SD":  # Seed Dispense
            if not arguments:
                print("Seed index required. Use 0:Spinach, 1:Carrots, 2:Lettuce, 3:Mesculin")
                return

            try:
                seed_index = int(arguments[0])
                if seed_index == 0:  # Spinach
                    servo_13.move_servo(0, 180, 15)
                    time.sleep(5)
                    servo_13.move_servo(0, 0, 5)
                elif seed_index == 1:  # Carrots
                    servo_13.move_servo(1, 180, 15)
                    time.sleep(5)
                    servo_13.move_servo(1, 0, 5)
                elif seed_index == 2:  # Lettuce
                    servo_12.move_servo(1, 180, 15)
                    time.sleep(5)
                    servo_12.move_servo(1, 0, 5)
                elif seed_index == 3:  # Mesculin
                    servo_12.move_servo(0, 180, 15)
                    time.sleep(5)
                    servo_12.move_servo(0, 0, 5)
                else:
                    print("Invalid seed index. Must be 0-3.")
            except Exception as e:
                print(f"Seed dispense error: {e}")

        elif command_type == "MU":  # Moisture Up
            try:
                servo_12.move_servo(2, 180, 15)
                print("Moisture sensor raised.")
            except Exception as e:
                print(f"Moisture Up error: {e}")

        elif command_type == "MD":  # Moisture Down
            try:
                servo_12.move_servo(2, 0, 15)
                print("Moisture sensor lowered.")
            except Exception as e:
                print(f"Moisture Down error: {e}")
        
        elif command_type == "PU":  # Pump ON
            pump_relay.value(1)
            print("Pump turned ON.")

        elif command_type == "PD":  # Pump OFF
            pump_relay.value(0)
            print("Pump turned OFF.")
    
        elif command_type == "TP":  # Temperature analog sensor
            raw = temp_sensor_adc.read_u16()
            voltage = (raw / 65535.0) * 3.3  # Convert ADC to voltage (assuming 3.3V reference)
            temperature_c = (voltage - 0.5) * 100  # TMP36 formula
            print(f"Temperature: {temperature_c:.2f} °C")
        
        else:
            print(f"Unknown command: {cmd}")


print("Ready for serial commands...")
term_reader = TermReader(sys.stdin.buffer)
while True:
    # Force Stop
    if button.value() == 0:
        print("stopped")
        sys.exit()

    text = term_reader.read().strip()
    if text:
        print("Recv:", text)
        process_command(text)
        
    if homing_axes_queue and not current_homing_axis:
        current_homing_axis = homing_axes_queue.pop(0)
        axis = axes[current_homing_axis]
        axis.calibration_mode = True
        axis.enable_motor()
        axis.set_direction(True)
        axis.spin(999999, 5000)
        print(f"Homing axis {current_homing_axis.upper()}...")

    if current_homing_axis:
        axis = axes[current_homing_axis]
        axis.calibrate_step()
        if not axis.calibration_mode:
            print(f"Axis {current_homing_axis.upper()} homed.")
            current_homing_axis = None
