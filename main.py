from machine import Pin
import sys
import uselect
from termreader import TermReader
import motor
from pins import *
from constants import *

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

def process_command(command):
    commands = command.split(";")
    for cmd in commands:
        command_type = cmd[:2]
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
        
        elif command_type == "ST": # Stauts
            status_dict = {}
            for key, axis in axes.items():
                status_dict[key.upper()] = {
                    "enabled": axis.enabled,
                    "moving": axis.running,
                    "displacement": axis.displacement,
                }
            print(status_dict)
        
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
