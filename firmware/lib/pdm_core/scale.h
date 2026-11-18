// Conversions from ADC millivolts to physical values. No hardware access.
// SPDX-License-Identifier: MIT
#pragma once
#include "pdm_config.h"

namespace pdm {

enum class Variant : uint8_t { Unknown = 0, Pdm4ch, PdmHc2 };

// MOD_ID pin voltage -> board variant. 0 V, 3.3 V and anything outside the windows are Unknown.
Variant variant_from_mod_id_mv(int mv);
const char* variant_name(Variant v);

// VBAT_SENSE pin voltage -> volts at VS.
float vbat_from_mv(int mv);

// NTC pin voltage -> degrees C. Returns NAN for an open or shorted sensor.
float ntc_celsius_from_mv(int mv);

// pdm-4ch IS pin voltage -> load current in amperes.
float profet_current_from_mv(int mv, float kilis);

}  // namespace pdm
