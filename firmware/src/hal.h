// Board access for pdm-4ch: GPIO, ADC and the DEN-pulsed current sense.
// SPDX-License-Identifier: MIT
#pragma once
#include <stdint.h>

namespace hal {

// Puts every pin in its safe state: drives low, DEN low, LEDs off. Call first in setup().
void init();

// Calibrated pin voltage in millivolts, averaged over `samples` conversions.
int read_mv(uint8_t pin, int samples = 8);

// Raises DEN, waits for the sense outputs to settle, reads IS1-IS4 once each and drops DEN.
// DEN is high for well under 2 ms per call and never between calls (design-notes 6.1).
void sample_is(int mv[4]);

bool switch_raw(int ch);
bool sw_supply_present();
void set_drive(int ch, bool on);
void set_panel_led(int ch, bool on);
void set_status_led(bool on);

}  // namespace hal
