// SPDX-License-Identifier: MIT
#include "scale.h"

#include <math.h>
#include <stdlib.h>

namespace pdm {

Variant variant_from_mod_id_mv(int mv) {
  if (abs(mv - kModId4chMv) <= kModIdWindowMv) return Variant::Pdm4ch;
  if (abs(mv - kModIdHc2Mv) <= kModIdWindowMv) return Variant::PdmHc2;
  return Variant::Unknown;
}

const char* variant_name(Variant v) {
  switch (v) {
    case Variant::Pdm4ch: return "pdm-4ch";
    case Variant::PdmHc2: return "pdm-hc2";
    default: return "unknown";
  }
}

float vbat_from_mv(int mv) { return mv * kVbatDividerRatio / 1000.0f; }

float ntc_celsius_from_mv(int mv) {
  if (mv <= 50 || mv >= (int)kVrefMv - 50) return NAN;  // shorted or open
  const float r = kNtcPullup * mv / (kVrefMv - mv);
  const float inv_t = 1.0f / 298.15f + logf(r / kNtcR25) / kNtcBeta;
  return 1.0f / inv_t - 273.15f;
}

float profet_current_from_mv(int mv, float kilis) {
  if (mv < 0) mv = 0;
  return (mv / 1000.0f) / kRisOhm * kilis;
}

}  // namespace pdm
