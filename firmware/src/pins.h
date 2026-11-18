// Pin map, from docs/ARCHITECTURE.md "Pin map (ESP32-S3)". Change it there first (a /system
// decision), then here. SPDX-License-Identifier: MIT
#pragma once
#include <stdint.h>

namespace pins {

// Shared by both boards
constexpr uint8_t kModId = 1;       // ADC1: variant ID
constexpr uint8_t kNtc = 9;         // ADC1: NTC TH1
constexpr uint8_t kVbatSense = 10;  // ADC1: VS / 11
constexpr uint8_t kSwSense = 12;    // digital: high = SW_SUPPLY present (decision 93)
constexpr uint8_t kStatusLed = 13;  // D7, high = on; internal pull-up must stay off
constexpr uint8_t kSwitch[4] = {14, 15, 16, 21};  // panel switch state, high = closed
constexpr uint8_t kCanTx = 17;
constexpr uint8_t kCanRx = 18;
constexpr uint8_t kPanelLed[4] = {38, 39, 40, 41};  // LED sinks, high = LED on

// pdm-4ch
constexpr uint8_t kIs[4] = {2, 3, 4, 5};      // ADC1: current sense IS1-IS4
constexpr uint8_t kDrive[4] = {6, 7, 8, 11};  // RTC GPIOs: channel IN, diode-OR with the switches
constexpr uint8_t kDen = 33;                  // diagnostics enable, all four channels
constexpr uint8_t kSpare4ch[] = {34, 35, 36, 37, 42};  // IO34 spare; IO35-37, IO42 on unfitted J6

// IO3 (IS2) is a strapping pin held low by the sense network. Never burn eFuse
// EFUSE_STRAP_JTAG_SEL (decision 66).

}  // namespace pins
