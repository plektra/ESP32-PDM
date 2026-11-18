// Host tests for lib/pdm_core. Run: pio test -e native
// SPDX-License-Identifier: MIT
#include <math.h>
#include <unity.h>

#include "channel.h"
#include "debounce.h"
#include "pdm_config.h"
#include "scale.h"
#include "soft_fuse.h"

using namespace pdm;

void setUp() {}
void tearDown() {}

// --- scale ----------------------------------------------------------------------------------------

static void test_variant() {
  TEST_ASSERT_TRUE(variant_from_mod_id_mv(1650) == Variant::Pdm4ch);
  TEST_ASSERT_TRUE(variant_from_mod_id_mv(1055) == Variant::PdmHc2);
  TEST_ASSERT_TRUE(variant_from_mod_id_mv(0) == Variant::Unknown);
  TEST_ASSERT_TRUE(variant_from_mod_id_mv(3300) == Variant::Unknown);
  TEST_ASSERT_TRUE(variant_from_mod_id_mv(1350) == Variant::Unknown);  // between the two
}

static void test_vbat() {
  // 24 V at VS gives 24 / 11 = 2.182 V at the pin.
  TEST_ASSERT_FLOAT_WITHIN(0.05f, 24.0f, vbat_from_mv(2182));
  TEST_ASSERT_FLOAT_WITHIN(0.05f, 12.0f, vbat_from_mv(1091));
}

static void test_ntc() {
  // 10 k NTC against a 10 k pull-up: half of 3.3 V at 25 C.
  TEST_ASSERT_FLOAT_WITHIN(0.2f, 25.0f, ntc_celsius_from_mv(1650));
  // B3380: R(85 C) = 10k * exp(3380 * (1/358.15 - 1/298.15)) = 1.50 k -> 430 mV.
  TEST_ASSERT_FLOAT_WITHIN(1.0f, 85.0f, ntc_celsius_from_mv(430));
  TEST_ASSERT_TRUE(isnan(ntc_celsius_from_mv(0)));
  TEST_ASSERT_TRUE(isnan(ntc_celsius_from_mv(3300)));
}

static void test_profet_current() {
  // design-notes 6.1: BTT6050 4.5 A -> 3.0 mA -> 1.50 V; about 0.33 V/A.
  TEST_ASSERT_FLOAT_WITHIN(0.01f, 4.5f, profet_current_from_mv(1500, kKilisBtt6050));
  TEST_ASSERT_FLOAT_WITHIN(0.01f, 1.0f, profet_current_from_mv(333, kKilisBtt6050));
  // BTT6010 8 A -> 2.05 mA -> 1.03 V.
  TEST_ASSERT_FLOAT_WITHIN(0.05f, 8.0f, profet_current_from_mv(1026, kKilisBtt6010));
}

// --- debounce -------------------------------------------------------------------------------------

static void test_debounce() {
  Debounce d(20);
  TEST_ASSERT_FALSE(d.update(true, 10));  // 10 ms
  TEST_ASSERT_TRUE(d.update(true, 10));   // 20 ms stable
  TEST_ASSERT_TRUE(d.update(false, 10));  // glitch
  TEST_ASSERT_TRUE(d.update(true, 10));
  TEST_ASSERT_TRUE(d.update(false, 10));
  TEST_ASSERT_FALSE(d.update(false, 10));
}

// --- soft fuse ------------------------------------------------------------------------------------

static float trip_time(float current_a, float rated_a, float tau_s, float limit_s) {
  SoftFuse f(rated_a, tau_s);
  const float dt = 0.1f;
  for (float t = dt; t <= limit_s; t += dt) {
    if (f.update(current_a, dt)) return t;
  }
  return -1.0f;
}

static void test_fuse_never_trips_below_rating() {
  TEST_ASSERT_TRUE(trip_time(3.9f, 4.0f, 10.0f, 3600.0f) < 0.0f);
}

static void test_fuse_trip_times() {
  // tau * ln(I^2 / (I^2 - Ir^2)): 3 x -> 1.18 s, 2 x -> 2.88 s, 1.25 x -> 10.2 s.
  TEST_ASSERT_FLOAT_WITHIN(0.15f, 1.18f, trip_time(12.0f, 4.0f, 10.0f, 60.0f));
  TEST_ASSERT_FLOAT_WITHIN(0.15f, 2.88f, trip_time(8.0f, 4.0f, 10.0f, 60.0f));
  TEST_ASSERT_FLOAT_WITHIN(0.3f, 10.2f, trip_time(5.0f, 4.0f, 10.0f, 60.0f));
}

static void test_fuse_cools() {
  SoftFuse f(4.0f, 10.0f);
  while (!f.update(8.0f, 0.1f)) {
  }
  f.reset();
  TEST_ASSERT_TRUE(f.update(8.0f, 0.1f));  // still hot: trips at once
  f.reset();
  for (int i = 0; i < 300; i++) f.update(0.0f, 0.1f);  // 30 s = 3 tau off
  TEST_ASSERT_FALSE(f.tripped());
  TEST_ASSERT_TRUE(f.level() < 0.1f);
}

// --- channel --------------------------------------------------------------------------------------

static const int kMv1A = 333;  // BTT6050, 1 A

static void test_channel_bus_command() {
  Channel c;
  c.tick(false, 10);
  TEST_ASSERT_FALSE(c.output_on());
  TEST_ASSERT_TRUE(c.led() == Led::Off);
  c.set_command(true);
  c.tick(false, 10);
  TEST_ASSERT_TRUE(c.drive());
  TEST_ASSERT_TRUE(c.output_on());
  TEST_ASSERT_TRUE(c.led() == Led::On);
  c.on_sense(kMv1A, 0.1f);
  TEST_ASSERT_FLOAT_WITHIN(0.01f, 1.0f, c.current_a());
  c.set_command(false);
  c.tick(false, 10);
  TEST_ASSERT_FALSE(c.output_on());
}

static void test_channel_switch_needs_no_drive() {
  Channel c;
  c.tick(true, 10);
  TEST_ASSERT_TRUE(c.output_on());
  TEST_ASSERT_FALSE(c.drive());  // the switch works in hardware; firmware adds nothing
  TEST_ASSERT_TRUE(c.led() == Led::On);
}

static void test_channel_overload_latches_and_clears() {
  Channel c;
  c.set_command(true);
  c.tick(false, 10);
  // 8 A = 2 x rated (2.66 V, below full scale): trips after about 2.9 s.
  int n = 0;
  while (c.fault() == Fault::None && n < 100) {
    c.on_sense(8 * kMv1A, 0.1f);
    n++;
  }
  TEST_ASSERT_TRUE(c.fault() == Fault::Overload);
  TEST_ASSERT_INT_WITHIN(2, 29, n);
  TEST_ASSERT_FALSE(c.drive());
  TEST_ASSERT_FALSE(c.output_on());
  TEST_ASSERT_TRUE(c.command());  // the request is remembered, the drive is held off
  TEST_ASSERT_TRUE(c.led() == Led::Blink);

  // Nothing retries by itself.
  for (int i = 0; i < 600; i++) {
    c.tick(false, 10);
    c.on_sense(0, 0.1f);
  }
  TEST_ASSERT_TRUE(c.fault() == Fault::Overload);

  // Off, then on again: cleared.
  c.set_command(false);
  TEST_ASSERT_TRUE(c.fault() == Fault::None);
  c.set_command(true);
  c.tick(false, 10);
  TEST_ASSERT_TRUE(c.output_on());
}

static void test_channel_switch_fault() {
  Channel c;
  c.set_command(true);
  c.tick(false, 10);
  c.on_sense(3000, 0.1f);  // fault current: 6 mA x 500 ohm
  c.on_sense(3000, 0.5f);
  TEST_ASSERT_TRUE(c.fault() == Fault::None);  // could still be a start current
  TEST_ASSERT_TRUE(isnan(c.current_a()));
  c.on_sense(3000, 0.5f);
  TEST_ASSERT_TRUE(c.fault() == Fault::SwitchFault);
  TEST_ASSERT_FALSE(c.drive());
}

static void test_channel_start_current_is_not_a_fault() {
  Channel c;
  c.set_command(true);
  c.tick(false, 10);
  c.on_sense(3000, 0.1f);
  c.on_sense(3000, 0.5f);
  c.on_sense(kMv1A, 0.5f);  // settled
  c.on_sense(3000, 0.1f);
  c.on_sense(3000, 0.5f);
  TEST_ASSERT_TRUE(c.fault() == Fault::None);
  TEST_ASSERT_TRUE(c.drive());
}

static void test_channel_fault_with_switch_closed() {
  Channel c;
  c.tick(true, 10);
  for (int i = 0; i < kSwitchFaultSamples; i++) c.on_sense(3000, 0.5f);
  TEST_ASSERT_TRUE(c.fault() == Fault::SwitchFault);
  TEST_ASSERT_TRUE(c.output_on());  // firmware cannot open the hardware path
  TEST_ASSERT_TRUE(c.led() == Led::Blink);
  c.tick(false, 10);  // switch opened: acknowledged
  TEST_ASSERT_TRUE(c.fault() == Fault::None);
  TEST_ASSERT_FALSE(c.output_on());
}

static void test_channel_open_load_off_is_a_warning() {
  Channel c;
  c.set_command(true);
  c.tick(false, 10);
  c.on_sense(kMv1A, 0.1f);
  c.set_command(false);
  c.tick(false, 10);
  c.on_sense(3000, 0.1f);  // right after switch-off: not diagnosed yet
  TEST_ASSERT_FALSE(c.open_load_off());
  for (int i = 0; i < 50; i++) c.tick(false, 10);  // 500 ms off
  c.on_sense(3000, 0.1f);
  TEST_ASSERT_TRUE(c.open_load_off());
  TEST_ASSERT_TRUE(c.fault() == Fault::None);
  TEST_ASSERT_TRUE(c.led() == Led::Off);
  c.on_sense(0, 0.1f);
  TEST_ASSERT_FALSE(c.open_load_off());
}

int main(int, char**) {
  UNITY_BEGIN();
  RUN_TEST(test_variant);
  RUN_TEST(test_vbat);
  RUN_TEST(test_ntc);
  RUN_TEST(test_profet_current);
  RUN_TEST(test_debounce);
  RUN_TEST(test_fuse_never_trips_below_rating);
  RUN_TEST(test_fuse_trip_times);
  RUN_TEST(test_fuse_cools);
  RUN_TEST(test_channel_bus_command);
  RUN_TEST(test_channel_switch_needs_no_drive);
  RUN_TEST(test_channel_overload_latches_and_clears);
  RUN_TEST(test_channel_switch_fault);
  RUN_TEST(test_channel_start_current_is_not_a_fault);
  RUN_TEST(test_channel_fault_with_switch_closed);
  RUN_TEST(test_channel_open_load_off_is_a_warning);
  return UNITY_END();
}
