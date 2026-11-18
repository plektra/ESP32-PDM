// SPDX-License-Identifier: MIT
#include "hal.h"

#include <Arduino.h>

#include "pdm_config.h"
#include "pins.h"

namespace hal {

void init() {
  // DEN first: nothing may hold it high (design-notes 6.1 requirement 3).
  digitalWrite(pins::kDen, LOW);
  pinMode(pins::kDen, OUTPUT);

  for (int ch = 0; ch < 4; ch++) {
    digitalWrite(pins::kDrive[ch], LOW);
    pinMode(pins::kDrive[ch], OUTPUT);
    digitalWrite(pins::kPanelLed[ch], LOW);
    pinMode(pins::kPanelLed[ch], OUTPUT);
    // The switch node has its own 4.7 k to GND behind 10 k; no internal pull.
    pinMode(pins::kSwitch[ch], INPUT);
    analogSetPinAttenuation(pins::kIs[ch], ADC_11db);
  }

  pinMode(pins::kSwSense, INPUT);

  // Status LED: plain output, never INPUT_PULLUP (the LED would glow, design-notes 8.7).
  digitalWrite(pins::kStatusLed, LOW);
  pinMode(pins::kStatusLed, OUTPUT);

  // Unused pins get a pull so they do not float (T-0160).
  for (uint8_t pin : pins::kSpare4ch) pinMode(pin, INPUT_PULLDOWN);

  // 11 dB attenuation: calibrated up to about 2.9 V (design-notes 2).
  analogSetPinAttenuation(pins::kModId, ADC_11db);
  analogSetPinAttenuation(pins::kNtc, ADC_11db);
  analogSetPinAttenuation(pins::kVbatSense, ADC_11db);
}

int read_mv(uint8_t pin, int samples) {
  long sum = 0;
  for (int i = 0; i < samples; i++) sum += analogReadMilliVolts(pin);
  return (int)(sum / samples);
}

void sample_is(int mv[4]) {
  digitalWrite(pins::kDen, HIGH);
  delayMicroseconds(pdm::kDenSettleUs);
  for (int ch = 0; ch < 4; ch++) mv[ch] = (int)analogReadMilliVolts(pins::kIs[ch]);
  digitalWrite(pins::kDen, LOW);
}

bool switch_raw(int ch) { return digitalRead(pins::kSwitch[ch]) == HIGH; }
bool sw_supply_present() { return digitalRead(pins::kSwSense) == HIGH; }
void set_drive(int ch, bool on) { digitalWrite(pins::kDrive[ch], on ? HIGH : LOW); }
void set_panel_led(int ch, bool on) { digitalWrite(pins::kPanelLed[ch], on ? HIGH : LOW); }
void set_status_led(bool on) { digitalWrite(pins::kStatusLed, on ? HIGH : LOW); }

}  // namespace hal
