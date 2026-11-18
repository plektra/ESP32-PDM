// Soft fuse: a first-order thermal model of the load current.
//
//   d(level)/dt = ((I / I_rated)^2 - level) / tau        trips when level >= 1
//
// A current at or below the rating never trips. Above it the trip time is
// tau * ln(I^2 / (I^2 - I_rated^2)): 1.2 s at 3 x rated, 2.9 s at 2 x, 10 s at 1.25 x with tau = 10 s.
// The level falls with the same time constant, so a load that has just tripped cannot be
// switched straight back on at full heat.
//
// This is an alarm and load-shedding aid. It is not a circuit breaker: the wiring still needs its
// own fuse or breaker (design-notes 8).
// SPDX-License-Identifier: MIT
#pragma once

namespace pdm {

class SoftFuse {
 public:
  SoftFuse(float rated_a, float tau_s) : rated_a_(rated_a), tau_s_(tau_s) {}

  void configure(float rated_a, float tau_s) {
    rated_a_ = rated_a;
    tau_s_ = tau_s;
  }

  // Feed one current sample covering dt_s seconds. Returns true when the fuse is tripped.
  bool update(float current_a, float dt_s);

  // Heat fraction, 0..1 and above. 1 = trip level.
  float level() const { return level_; }
  bool tripped() const { return tripped_; }
  float rated_a() const { return rated_a_; }

  // Clears the trip flag. The heat level stays and keeps decaying through update().
  void reset() { tripped_ = false; }

 private:
  float rated_a_;
  float tau_s_;
  float level_ = 0.0f;
  bool tripped_ = false;
};

}  // namespace pdm
