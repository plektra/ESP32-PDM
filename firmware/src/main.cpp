// ESP32-PDM firmware, first draft: pdm-4ch in Active mode.
//
// What runs: variant check, panel switch state, bus commands, DEN-pulsed current sense, soft fuse,
// panel LEDs, battery voltage, board temperature, SW_SUPPLY alert, NMEA 2000 switch bank, and a
// serial console on USB for bring-up. Not yet: Wi-Fi / Signal K, OTA, Eco and Sleep modes, PWM,
// pdm-hc2. See firmware/README.md.
// SPDX-License-Identifier: MIT
#include <Arduino.h>
#include <Preferences.h>
#include <esp_mac.h>
#include <math.h>

#include "channel.h"
#include "debounce.h"
#include "hal.h"
#include "n2k.h"
#include "pdm_config.h"
#include "pins.h"
#include "scale.h"
#include "version.h"

using namespace pdm;

namespace {

Variant variant = Variant::Unknown;
Channel channels[4];
Debounce switches[4] = {Debounce(kSwitchQualifyMs), Debounce(kSwitchQualifyMs),
                        Debounce(kSwitchQualifyMs), Debounce(kSwitchQualifyMs)};
Preferences prefs;
uint8_t bank_instance = 0;

float vbat_v = NAN;
float board_temp_c = NAN;
bool sw_supply_alert = false;
bool temp_warning = false;

uint32_t last_tick_ms = 0;
uint32_t last_sense_ms = 0;
uint32_t sense_period_ms = kSensePeriodMs;
uint32_t last_slow_ms = 0;
uint32_t sw_supply_low_ms = 0;

void on_bus_command(int ch, bool on) {
  if (ch >= 0 && ch < 4) channels[ch].set_command(on);
}

uint32_t unique_number() {
  uint8_t mac[6] = {0};
  esp_efuse_mac_get_default(mac);
  return ((uint32_t)mac[3] << 16) | ((uint32_t)mac[4] << 8) | mac[5];
}

// --- every 10 ms: switches, drives, LEDs ----------------------------------------------------------
void tick(uint32_t now, uint32_t dt_ms) {
  const bool blink_on = (now / kFaultBlinkHalfPeriodMs) % 2 == 0;
  for (int ch = 0; ch < 4; ch++) {
    const bool sw = switches[ch].update(hal::switch_raw(ch), dt_ms);
    channels[ch].tick(sw, dt_ms);
    hal::set_drive(ch, channels[ch].drive());
    const Led led = channels[ch].led();
    hal::set_panel_led(ch, led == Led::On || (led == Led::Blink && blink_on));
  }
  // Status LED D7: short flash every 2 s = running; steady blink = a fault or alert is active.
  bool any_fault = sw_supply_alert || temp_warning;
  for (const Channel& c : channels) any_fault = any_fault || c.fault() != Fault::None;
  hal::set_status_led(any_fault ? blink_on : (now % 2000) < 50);
}

// --- every 100 ms (500 ms after a full-scale reading): current sense -----------------------------
void sense(uint32_t dt_ms) {
  int mv[4];
  hal::sample_is(mv);
  bool full_scale = false;
  for (int ch = 0; ch < 4; ch++) {
    channels[ch].on_sense(mv[ch], dt_ms / 1000.0f);
    full_scale = full_scale || mv[ch] >= kIsFullScaleMv;
  }
  // A full-scale reading means a fault current of up to 40 mA runs through RIS while DEN is high
  // (design-notes 6.1), so the next look comes later.
  sense_period_ms = full_scale ? kSenseRetryMs : kSensePeriodMs;
}

// --- every second: supply, temperature, alerts -----------------------------------------------------
void slow(uint32_t dt_ms) {
  vbat_v = vbat_from_mv(hal::read_mv(pins::kVbatSense));
  board_temp_c = ntc_celsius_from_mv(hal::read_mv(pins::kNtc));
  temp_warning = !isnan(board_temp_c) && board_temp_c >= kBoardTempWarnC;

  // SW_SUPPLY missing while the battery is healthy: F4 tripped, D55 open or a short at J5.5
  // (decision 93). An alert only; the panel path does not depend on it.
  if (!hal::sw_supply_present() && vbat_v >= kVbatHealthyV) {
    sw_supply_low_ms += dt_ms;
  } else {
    sw_supply_low_ms = 0;
  }
  sw_supply_alert = sw_supply_low_ms >= kSwSupplyAlertMs;
}

// --- serial console (USB) -------------------------------------------------------------------------
void print_status() {
  Serial.printf("ESP32-PDM %s  %s  bank %u\n", PDM_FW_VERSION, variant_name(variant),
                bank_instance);
  Serial.printf("VS %.1f V  board %.0f C  SW_SUPPLY %s%s\n", vbat_v, board_temp_c,
                hal::sw_supply_present() ? "ok" : "low", sw_supply_alert ? "  ALERT" : "");
  for (int ch = 0; ch < 4; ch++) {
    const Channel& c = channels[ch];
    Serial.printf("ch%d  %s  sw %d  cmd %d  %.2f A  fuse %.0f %%  fault: %s%s\n", ch + 1,
                  c.output_on() ? "ON " : "off", c.sw(), c.command(), c.current_a(),
                  c.fuse_level() * 100.0f, fault_name(c.fault()),
                  c.open_load_off() ? "  (open load)" : "");
  }
}

void handle_console() {
  static char line[32];
  static size_t len = 0;
  while (Serial.available()) {
    const char c = (char)Serial.read();
    if (c != '\n' && c != '\r') {
      if (len < sizeof(line) - 1) line[len++] = c;
      continue;
    }
    line[len] = 0;
    len = 0;
    int n = 0;
    if (sscanf(line, "on %d", &n) == 1 && n >= 1 && n <= 4) {
      channels[n - 1].set_command(true);
    } else if (sscanf(line, "off %d", &n) == 1 && n >= 1 && n <= 4) {
      channels[n - 1].set_command(false);
    } else if (sscanf(line, "bank %d", &n) == 1 && n >= 0 && n <= 252) {
      prefs.putUChar("bank", (uint8_t)n);
      Serial.println("saved; takes effect after a reset");
    } else if (line[0] == 0 || strcmp(line, "status") == 0) {
      print_status();
    } else {
      Serial.println("commands: status | on N | off N | bank N");
    }
  }
}

}  // namespace

void setup() {
  hal::init();
  Serial.begin(115200);

  variant = variant_from_mod_id_mv(hal::read_mv(pins::kModId, 32));
  if (variant != Variant::Pdm4ch) return;  // loop() only blinks; no pin is driven

  prefs.begin("pdm", false);
  bank_instance = prefs.getUChar("bank", 0);

  for (Channel& c : channels) c.configure(kKilisBtt6050, kRatedCurrentBtt6050A, kSoftFuseTauS);
  n2k::begin(bank_instance, unique_number(), on_bus_command);
  last_tick_ms = last_sense_ms = last_slow_ms = millis();
}

void loop() {
  const uint32_t now = millis();

  if (variant != Variant::Pdm4ch) {
    // Unknown board or pdm-hc2 (not supported yet): fast blink, outputs left to the panel switches.
    hal::set_status_led((now / 100) % 2 == 0);
    if (now - last_slow_ms >= 2000) {
      last_slow_ms = now;
      Serial.printf("ESP32-PDM %s: board variant '%s' is not supported, MOD_ID %d mV\n",
                    PDM_FW_VERSION, variant_name(variant), hal::read_mv(pins::kModId, 32));
    }
    delay(10);
    return;
  }

  if (now - last_tick_ms >= kTickMs) {
    tick(now, now - last_tick_ms);
    last_tick_ms = now;
  }
  if (now - last_sense_ms >= sense_period_ms) {
    sense(now - last_sense_ms);
    last_sense_ms = now;
  }
  if (now - last_slow_ms >= 1000) {
    slow(now - last_slow_ms);
    last_slow_ms = now;
  }

  n2k::ChannelReport reports[4];
  for (int ch = 0; ch < 4; ch++) {
    const Channel& c = channels[ch];
    reports[ch].state = c.output_on() ? n2k::ItemState::On
                        : c.fault() != Fault::None ? n2k::ItemState::Error
                                                   : n2k::ItemState::Off;
    reports[ch].current_a = c.current_a();
  }
  n2k::loop(reports, vbat_v);

  handle_console();
  delay(1);
}
