// Input qualifier: the state changes only after the raw input has been stable for a set time.
// SPDX-License-Identifier: MIT
#pragma once
#include <stdint.h>

namespace pdm {

class Debounce {
 public:
  explicit Debounce(uint32_t qualify_ms, bool initial = false)
      : qualify_ms_(qualify_ms), state_(initial), candidate_(initial) {}

  // Call at a regular interval. Returns the qualified state.
  bool update(bool raw, uint32_t dt_ms) {
    if (raw == state_) {
      candidate_ = state_;
      stable_ms_ = 0;
    } else {
      if (raw != candidate_) {
        candidate_ = raw;
        stable_ms_ = 0;
      }
      stable_ms_ += dt_ms;
      if (stable_ms_ >= qualify_ms_) {
        state_ = raw;
        stable_ms_ = 0;
      }
    }
    return state_;
  }

  bool state() const { return state_; }

 private:
  uint32_t qualify_ms_;
  uint32_t stable_ms_ = 0;
  bool state_;
  bool candidate_;
};

}  // namespace pdm
