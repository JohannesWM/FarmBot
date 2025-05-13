import utime
import rp2
import math
from machine import Pin

@rp2.asm_pio(set_init=rp2.PIO.OUT_LOW)
def stepperPIO():
  pull()
  mov(y, osr) # steps

  pull()  # get delay, but keep it in osr
 
  label("step")
  mov(x, osr)  # get delay from OSR
  set(pins, 1)
  label("delay")
  set(pins, 0)
  jmp(x_dec, "delay")
  
  irq(rel(0))
  # pull()
  mov(isr, y)
  
  jmp(y_dec, "step")
  
  
  
class StepperController:
    def __init__(self, id, step_pin, dir_pin, enable_pin, stopper_pin, max_speed, acceleration, frequency=25000000):
        """
        Initialize the StepperController.
        
        :param pin: The GPIO pin connected to the stepper motor driver.
        :param max_speed: Maximum speed in steps per second.
        :param acceleration: Acceleration in steps per second squared.
        """
        self.max_speed = max_speed
        self.acceleration = acceleration
        self.frequency = frequency
        self.id = id
        self.step_pin = Pin(step_pin, Pin.OUT)
        self.enable_pin = Pin(enable_pin, Pin.OUT)
        self.stopper_pin = Pin(stopper_pin, Pin.IN, Pin.PULL_UP)
        self.sm = rp2.StateMachine(self.id, stepperPIO, freq=self.frequency, set_base=step_pin)
        self.dir_pin = Pin(dir_pin, Pin.OUT)
        self.sm.irq(self._on_step_completion)
        self.sm.active(0)
        self.running = False
        self.speed = self.acceleration
        self.start_time = utime.ticks_ms()
        self.enable_pin.value(0)
        self.enable = True
        self.mode = "acceleration"
        self.displacement = 0
        self.calibration_mode = False
        self.home_found = False
        self.back_off = False
        self.direction = 1
        self.slow_approach = False

    def _on_step_completion(self, sm):
        """
        Callback triggered when the StateMachine finishes a step.
        """
        
        sm.exec("push(noblock)")
        if self.sm.rx_fifo():
            steps = self.sm.get()

        deltasteps = self.steps-steps
        self.steps -= deltasteps
        if self.direction:
            self.displacement += deltasteps
        else:
            self.displacement -= deltasteps
        
        if self.steps <= 0:
            self.sm.active(0)
            self.running = False
        
        if self.mode == "acceleration":
            current_time = utime.ticks_ms()
            elapsed_time = current_time - self.start_time
                
            if elapsed_time >= 100:
                if self.total_steps-self.steps < self.steps_to_max_speed:
                    self.speed = min(self.speed+self.acceleration//10, self.achievable_max_speed)
                    #print("accelerating", self.speed)
                elif self.steps < self.steps_to_max_speed:
                    self.speed = max(self.speed-self.acceleration//10, self.acceleration)
                    #print("Decelerating", self.speed)
                else:
                    self.speed = self.achievable_max_speed
                    #print("Max speed", self.speed)
                
                self.start_time = utime.ticks_ms()
            
                if self.speed <= 0:
                    self.speed = self.acceleration
                self.delay = self.speed_to_delay(self.speed)
                
                # Update speed
                self.sm.put(self.delay)
                sm.exec("pull()")

    def speed_to_delay(self, speed):
        """
        Convert speed in steps per second to delay.
        
        :param speed: Speed in steps per second.
        :return: Delay in microseconds.
        """
        delay = self.frequency // speed
        return delay // 2
    
    def calculate_steps_to_max_speed(self):
        time_to_max_speed = (self.achievable_max_speed - self.acceleration) / self.acceleration
        
        distance = self.acceleration * time_to_max_speed + 0.5 * self.acceleration * time_to_max_speed ** 2
        
        return distance
    
    def time_to_reach_max_speed_with_initial_velocity(self):
        time_to_max_speed = (self.max_speed - self.acceleration) / self.acceleration
        
        return time_to_max_speed

    
    def start(self, steps):
        self.mode = "acceleration"
        self.speed = self.acceleration
        self.steps = abs(steps)
        if steps < 0:
            self.set_direction(True)
        else:
            self.set_direction(False)
        self.total_steps = self.steps
        self.running = True
        self.start_time = utime.ticks_ms()
        self.achievable_max_speed = self.max_speed
        self.steps_to_max_speed = self.calculate_steps_to_max_speed()
        
        if self.steps_to_max_speed*2 > self.total_steps:
            self.achievable_max_speed = round(math.sqrt(self.acceleration**2 + self.acceleration * self.total_steps))
            # print("adjusting max speed due to limited motor steps to", self.achievable_max_speed)
            self.steps_to_max_speed = self.calculate_steps_to_max_speed()
        
        self.sm.active(1)
        self.sm.put(self.steps)
        self.delay = self.speed_to_delay(self.speed)
        self.sm.put(self.delay)
        
    def enable_motor(self):
        self.enable = True
        self.enable_pin.value(0)
        
    def disable_motor(self):
        self.enable = False
        self.enable_pin.value(1)
        
    def set_direction(self, clockwise):
        self.direction = clockwise
        self.dir_pin.value(clockwise)
        
    def spin(self, steps, speed):
        self.mode = "home"
        self.steps = steps
        self.running = True
        self.delay = self.speed_to_delay(speed)
        self.sm.active(1)
        self.sm.put(self.steps)
        self.sm.put(self.delay)
        
    def _reset_state_machine(self):
        """
        Fully reset the state machine to ensure it does not continue spinning next time.
        """
        self.sm.active(0)
        self.sm = rp2.StateMachine(self.id, stepperPIO, freq=self.frequency, set_base=self.step_pin)
        self.sm.irq(self._on_step_completion)
            
    def calibrate_step(self):
        if self.calibration_mode:
            if self.stopper_pin.value() == 0 and not self.back_off and not self.slow_approach:
                # print(f"Axis {self.id}: Stopped at stopper, backing off...")
                self.sm.active(0)
                self._reset_state_machine()
                self.set_direction(False)  # Reverse direction
                utime.sleep(.5)
                self.back_off = True
                self.displacement = 0
                self.spin(2000, 3000)
            
            elif self.back_off and not self.running:
                # print(f"Axis {self.id}: Backed off, re-approaching slowly...")
                self.set_direction(True)
                utime.sleep(.57)
                self.slow_approach = True
                self.back_off = False
                self.spin(9999999, 500)
            
            elif self.slow_approach and self.stopper_pin.value() == 0:
                # print(f"Axis {self.id}: Homing complete.")
                self.sm.active(0)
                self.running = False
                self.calibration_mode = False
                self.slow_approach = False
                self.home_found = True
                self._reset_state_machine()
                self.steps = 0
                self.displacement = 0
                
    def stop(self):
        self.sm.active(0)
        self.running = False
        self._reset_state_machine()