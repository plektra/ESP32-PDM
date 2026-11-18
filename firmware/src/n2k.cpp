// SPDX-License-Identifier: MIT
#include "n2k.h"

#include <Arduino.h>
#include <N2kMessages.h>
#include <math.h>

#include "n2k_twai.h"
#include "pins.h"
#include "version.h"

namespace n2k {

namespace {

N2kTwai bus((gpio_num_t)pins::kCanTx, (gpio_num_t)pins::kCanRx);

const unsigned long kTransmitPgns[] PROGMEM = {127501L, 127751L, 0};
const unsigned long kReceivePgns[] PROGMEM = {127502L, 0};

constexpr uint32_t kStatusPeriodMs = 2500;
constexpr uint32_t kDcPeriodMs = 1500;

uint8_t bank = 0;
CommandHandler on_command = nullptr;
ItemState last_state[4] = {ItemState::Off, ItemState::Off, ItemState::Off, ItemState::Off};
uint32_t last_status_ms = 0;
uint32_t last_dc_ms = 0;
bool send_status_now = true;

void handle_msg(const tN2kMsg& msg) {
  if (msg.PGN != 127502L) return;
  unsigned char target;
  tN2kBinaryStatus status;
  if (!ParseN2kSwitchbankControl(msg, target, status)) return;
  if (target != bank) return;
  for (int ch = 0; ch < 4; ch++) {
    // Items are numbered from 1. "Unavailable" means "leave this one alone".
    const tN2kOnOff item = N2kGetStatusOnBinaryStatus(status, ch + 1);
    if (item == N2kOnOff_On && on_command) on_command(ch, true);
    if (item == N2kOnOff_Off && on_command) on_command(ch, false);
  }
  send_status_now = true;  // answer with the new state
}

void send_status(const ChannelReport reports[4]) {
  tN2kBinaryStatus status;
  N2kResetBinaryStatus(status);
  for (int ch = 0; ch < 4; ch++) {
    N2kSetStatusBinaryOnStatus(status, (tN2kOnOff)reports[ch].state, ch + 1);
  }
  tN2kMsg msg;
  SetN2kBinaryStatus(msg, bank, status);
  bus.SendMsg(msg);
}

void send_dc(const ChannelReport reports[4], float vbat_v) {
  for (int ch = 0; ch < 4; ch++) {
    // Proposed numbering: DC instance = bank x 4 + channel, so two boards do not collide.
    const unsigned char instance = (unsigned char)(bank * 4 + ch);
    const double current = isnan(reports[ch].current_a) ? N2kDoubleNA : reports[ch].current_a;
    const double voltage = isnan(vbat_v) ? N2kDoubleNA : vbat_v;
    tN2kMsg msg;
    SetN2kDCVoltageCurrent(msg, instance, voltage, current, 0xff);
    bus.SendMsg(msg);
  }
}

}  // namespace

void begin(uint8_t bank_instance, uint32_t unique_number, CommandHandler handler) {
  bank = bank_instance;
  on_command = handler;

  // Load equivalency 1 = 50 mA from NET-S (docs/ARCHITECTURE.md `can` row: 49.3 mA worst case,
  // to be measured on the first prototype).
  bus.SetProductInformation("00000001", 100, "ESP32-PDM 4ch", PDM_FW_VERSION, "rev A", 1);
  // Class 30 = Electrical Distribution, function 140 = Load Controller: from memory of the NMEA
  // class and function list, to be checked. 2046 is not a registered manufacturer code; a
  // product needs its own (open item).
  bus.SetDeviceInformation(unique_number & 0x1FFFFF, 140, 30, 2046);
  bus.SetMode(tNMEA2000::N2km_ListenAndNode, 35);
  bus.EnableForward(false);
  bus.ExtendTransmitMessages(kTransmitPgns);
  bus.ExtendReceiveMessages(kReceivePgns);
  bus.SetMsgHandler(handle_msg);
  bus.Open();
}

void loop(const ChannelReport reports[4], float vbat_v) {
  bus.poll();
  bus.ParseMessages();

  const uint32_t now = millis();
  for (int ch = 0; ch < 4; ch++) {
    if (reports[ch].state != last_state[ch]) {
      last_state[ch] = reports[ch].state;
      send_status_now = true;
    }
  }
  if (send_status_now || now - last_status_ms >= kStatusPeriodMs) {
    send_status(reports);
    last_status_ms = now;
    send_status_now = false;
  }
  if (now - last_dc_ms >= kDcPeriodMs) {
    send_dc(reports, vbat_v);
    last_dc_ms = now;
  }
}

}  // namespace n2k
