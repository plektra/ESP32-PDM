// NMEA 2000 side of the PDM: a switch bank.
//   PGN 127501 Binary Status Report   sent every 2.5 s and at once when a state changes
//   PGN 127502 Switch Bank Control    received: sets the bus command of each named channel
//   PGN 127751 DC Voltage/Current     sent every 1.5 s per channel: VS and the load current
// SPDX-License-Identifier: MIT
#pragma once
#include <stdint.h>

namespace n2k {

enum class ItemState : uint8_t { Off = 0, On = 1, Error = 2 };

struct ChannelReport {
  ItemState state;
  float current_a;  // NAN = not available
};

// Called for each channel a 127502 message names (index 0-3).
typedef void (*CommandHandler)(int channel, bool on);

// unique_number: 21 bits that differ between boards (from the MAC address).
void begin(uint8_t bank_instance, uint32_t unique_number, CommandHandler handler);

// Call every loop. `reports` holds the four channels, vbat_v the supply voltage.
void loop(const ChannelReport reports[4], float vbat_v);

}  // namespace n2k
