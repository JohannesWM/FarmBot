#include <Wire.h>

// === Pin Definitions ===
#define PHOTOGATE_PIN PIN_PA6     // PA6
#define MOISTURE_PIN PIN_PA3      // PA3
#define INTERRUPT_PIN PIN_PA7     // PA7

#define I2C_ADDRESS 0x10     // I2C address of this slave
#define INTERRUPT_PULSE_MS 50 // Duration of interrupt pulse

// === I2C Command Codes ===
#define CMD_RESET_BASELINE  0x01
#define CMD_SET_THRESHOLD   0x02

// === Configuration ===
#define BASELINE_SAMPLES    100     // Number of samples for light baseline averaging

// === Global Variables ===
uint16_t lightBase = 0;
uint8_t threshold = 2;  // Default threshold
volatile bool photogateTriggered = false;

void setup() {
  pinMode(INTERRUPT_PIN, OUTPUT);
  digitalWrite(INTERRUPT_PIN, LOW);

  Wire.begin(I2C_ADDRESS);
  Wire.onRequest(onI2CRequest);
  Wire.onReceive(onI2CReceive);

  delay(100); // Allow sensor to settle
  calibrateLightBaseline();
}

void loop() {
  uint16_t lightValue = analogRead(PHOTOGATE_PIN);

  // Check for photogate trigger
  if (abs((int)lightValue - (int)lightBase) > threshold) {
    if (!photogateTriggered) {
      sendInterruptPulse();
      photogateTriggered = true;
    }
  } else {
    photogateTriggered = false;
  }

  delay(25); // Basic debounce + reduce CPU usage
}

// === Interrupt Pulse Output ===
void sendInterruptPulse() {
  digitalWrite(INTERRUPT_PIN, HIGH);
  delay(INTERRUPT_PULSE_MS);
  digitalWrite(INTERRUPT_PIN, LOW);
}

// === I2C Data Send Handler ===
void onI2CRequest() {
  uint16_t light = analogRead(PHOTOGATE_PIN);
  uint16_t moisture = analogRead(MOISTURE_PIN);

  Wire.write((uint8_t*)&light, sizeof(light));
  Wire.write((uint8_t*)&moisture, sizeof(moisture));
}

// === I2C Command Receive Handler ===
void onI2CReceive(int len) {
  if (len < 1) return;

  uint8_t command = Wire.read();

  switch (command) {
    case CMD_RESET_BASELINE:
      calibrateLightBaseline();
      break;

    case CMD_SET_THRESHOLD:
      if (Wire.available()) {
        threshold = Wire.read();  // New threshold value
      }
      break;

    default:
      // Unknown command
      break;
  }
}

// === Baseline Calibration ===
void calibrateLightBaseline() {
  uint32_t total = 0;
  for (uint8_t i = 0; i < BASELINE_SAMPLES; i++) {
    total += analogRead(PHOTOGATE_PIN);
    delay(5);  // Let ADC settle between reads
  }
  lightBase = total / BASELINE_SAMPLES;
}
