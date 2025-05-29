#include <Wire.h>
#include <Servo.h>

#define I2C_SLAVE_ADDRESS 0x12

Servo servos[4];
const uint8_t servoPins[4] = {0, 1, 4, 5};
int currentAngles[4] = {0, 0, 0, 0}; // Default starting position

uint8_t recvBuffer[3];
uint8_t recvIndex = 0;

void receiveEvent(int numBytes) {
  while (Wire.available()) {
    if (recvIndex < 3) {
      recvBuffer[recvIndex++] = Wire.read();
    } else {
      Wire.read(); // Discard any extras
    }
  }

  if (recvIndex == 3) {
    uint8_t servoIndex = recvBuffer[0];
    uint8_t targetAngle = recvBuffer[1];
    uint8_t stepDelay = recvBuffer[2];

    if (servoIndex < 4 && targetAngle <= 180) {
      smoothMove(servoIndex, targetAngle, stepDelay);
    }

    recvIndex = 0;
  }
}

void smoothMove(uint8_t index, uint8_t target, uint8_t delayMs) {
  int current = currentAngles[index];
  if (current == target) return;

  int step = (target > current) ? 1 : -1;

  for (int angle = current; angle != target; angle += step) {
    servos[index].write(angle);
    delay(delayMs);
  }

  servos[index].write(target); // Final position
  currentAngles[index] = target;
}

void setup() {
  for (uint8_t i = 0; i < 4; i++) {
    servos[i].attach(servoPins[i]);
    servos[i].write(currentAngles[i]); // Set initial angle
  }

  Wire.begin(I2C_SLAVE_ADDRESS);
  Wire.onReceive(receiveEvent);
}

void loop() {
  // Nothing here, all handled via I2C receive
}
