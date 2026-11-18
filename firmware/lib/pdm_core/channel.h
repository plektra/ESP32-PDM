// One output channel: who asks for it, what the current sense says, what the panel LED shows.
//
// Proposed behaviour for decision 20 (open until the owner rules in /system firmware):
//
//   Output on        = panel switch closed (hardware path, invariant 1) OR firmware drive.
//   Firmware drive   = bus command on AND no latched fault.
//   Panel LED        = on while the output is on, blinking while a fault is latched, else off.
//
//   Fault            Detected by                               Firmware action
//   Overload         soft fuse trips on the measured current    drive off, latched
//   SwitchFault      IS at full scale while the output is on,   drive off, latched
//                    3 samples in a row (short, current limit,
//                    overtemperature)
//   open load (off)  IS at full scale while the output is off   warning flag only, no latch, no blink
//
//   A latched fault clears when the output is asked off and on again: the panel switch is opened,
//   or the bus commands the channel off. Nothing retries by itself.
//
// The firmware cannot switch off an output that a closed panel switch holds on. Then the fault is
// only shown and reported; the BTT6050's own protection and the wiring fuse do the protecting.
// SPDX-License-Identifier: MIT
#pragma once
#include <stdint.h>

#include "soft_fuse.h"

namespace pdm {

enum class Fault : uint8_t { None = 0, Overload, SwitchFault };
enum class Led : uint8_t { Off = 0, On, Blink };

const char* fault_name(Fault f);

class Channel {
 public:
  Channel();

  void configure(float kilis, float rated_a, float tau_s);

  // Bus command (NMEA 2000 PGN 127502, later Signal K). Off also clears a latched fault.
  void set_command(bool on);

  // Call every tick with the qualified panel switch state.
  void tick(bool sw, uint32_t dt_ms);

  // Call with each IS sample (millivolts at the pin) and the time since the previous sample.
  void on_sense(int is_mv, float dt_s);

  bool command() const { return command_; }
  bool sw() const { return sw_; }
  bool drive() const { return command_ && fault_ == Fault::None; }
  bool output_on() const { return sw_ || drive(); }
  Fault fault() const { return fault_; }
  bool open_load_off() const { return open_load_off_; }
  // Last measured load current in amperes; NAN while the sense pin shows a fault current.
  float current_a() const { return current_a_; }
  float fuse_level() const { return fuse_.level(); }
  Led led() const;

 private:
  void latch(Fault f);
  void clear_fault();

  SoftFuse fuse_;
  float kilis_;
  float current_a_ = 0.0f;
  uint32_t off_ms_ = 0;  // time since the output went off, saturating
  Fault fault_ = Fault::None;
  bool command_ = false;
  bool sw_ = false;
  bool open_load_off_ = false;
  uint8_t full_scale_count_ = 0;
};

}  // namespace pdm
