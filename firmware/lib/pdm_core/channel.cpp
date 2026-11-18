// SPDX-License-Identifier: MIT
#include "channel.h"

#include <math.h>

#include "pdm_config.h"
#include "scale.h"

namespace pdm {

namespace {
// After the output goes off, IS is not used for the open-load-in-OFF diagnosis for this long
// (design-notes 6.1 requirement 4). UNVERIFIED: tsIS(FAULT_OL_OFF) has not been read from the
// BTT6050 datasheet (docs/part-facts/C534868.md); with a load connected the output also needs
// time to discharge. Proposed until measured.
constexpr uint32_t kOffDiagHoldMs = 300;
}  // namespace

const char* fault_name(Fault f) {
  switch (f) {
    case Fault::Overload: return "overload";
    case Fault::SwitchFault: return "switch fault";
    default: return "none";
  }
}

Channel::Channel() : fuse_(kRatedCurrentBtt6050A, kSoftFuseTauS), kilis_(kKilisBtt6050) {}

void Channel::configure(float kilis, float rated_a, float tau_s) {
  kilis_ = kilis;
  fuse_.configure(rated_a, tau_s);
}

void Channel::latch(Fault f) {
  if (fault_ == Fault::None) fault_ = f;
}

void Channel::clear_fault() {
  fault_ = Fault::None;
  fuse_.reset();
}

void Channel::set_command(bool on) {
  if (!on) clear_fault();
  command_ = on;
}

void Channel::tick(bool sw, uint32_t dt_ms) {
  const bool was_on = output_on();
  if (sw_ && !sw) clear_fault();  // switch opened: the fault is acknowledged
  sw_ = sw;
  if (output_on()) {
    off_ms_ = 0;
  } else {
    if (was_on) off_ms_ = 0;
    if (off_ms_ < 0xFFFF0000u) off_ms_ += dt_ms;
  }
}

void Channel::on_sense(int is_mv, float dt_s) {
  const bool full_scale = is_mv >= kIsFullScaleMv;

  if (output_on()) {
    open_load_off_ = false;
    if (full_scale) {
      current_a_ = NAN;
      if (full_scale_count_ < 255) full_scale_count_++;
      if (full_scale_count_ >= kSwitchFaultSamples) latch(Fault::SwitchFault);
      return;
    }
    full_scale_count_ = 0;
    current_a_ = profet_current_from_mv(is_mv, kilis_);
    if (fuse_.update(current_a_, dt_s)) latch(Fault::Overload);
    return;
  }

  full_scale_count_ = 0;
  // Output off: the fuse model cools down; IS only tells open load (or a short to battery).
  fuse_.update(0.0f, dt_s);
  current_a_ = 0.0f;
  if (off_ms_ >= kOffDiagHoldMs) open_load_off_ = full_scale;
}

Led Channel::led() const {
  if (fault_ != Fault::None) return Led::Blink;
  return output_on() ? Led::On : Led::Off;
}

}  // namespace pdm
