#include <Wire.h>
#include <Servo.h>

#define I2C_SLAVE_ADDRESS 0x13
#define NUM_SERVOS 2

Servo servos[NUM_SERVOS];
const uint8_t servoPins[NUM_SERVOS] = {1, 4};
int currentAngles[NUM_SERVOS] = {0, 0}; // Start at neutral
int targetAngles[NUM_SERVOS] = {0, 0};
int delays[NUM_SERVOS] = {0, 0};

bool moveRequested[NUM_SERVOS] = {false, false};

void receiveEvent(int numBytes) {
  if (Wire.available() < 3) return;

  uint8_t servoIndex = Wire.read();
  uint8_t targetAngle = Wire.read();
  uint8_t stepDelay = Wire.read();

  if (servoIndex < NUM_SERVOS && targetAngle <= 180) {
    targetAngles[servoIndex] = targetAngle;
    delays[servoIndex] = stepDelay;
    moveRequested[servoIndex] = true;
  }
}

void setup() {
  for (uint8_t i = 0; i < NUM_SERVOS; i++) {
    servos[i].attach(servoPins[i]);
    servos[i].write(currentAngles[i]);
  }

  Wire.begin(I2C_SLAVE_ADDRESS);
  Wire.onReceive(receiveEvent);
}

void loop() {
  for (uint8_t i = 0; i < NUM_SERVOS; i++) {
    if (moveRequested[i]) {
      int &current = currentAngles[i];
      int target = targetAngles[i];
      int delayMs = delays[i];

      if (current != target) {
        current += (target > current) ? 1 : -1;
        servos[i].write(current);
        delay(delayMs);
      } else {
        moveRequested[i] = false;
      }
    }
  }
}
