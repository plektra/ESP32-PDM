// ESP32-PDM firmware - constants that come from the hardware design.
// Each value names its source in the repo. SPDX-License-Identifier: MIT
#pragma once
#include <stdint.h>

namespace pdm {

constexpr int kMaxChannels = 4;

// --- Variant ID on MOD_ID (decision 14, docs/ARCHITECTURE.md "Boards") -------------------------
// 10 k pull-up to 3.3 V, variant resistor to GND: 4-ch 10 k = 1.65 V, HC2 4.7 k = 1.05 V.
constexpr int kModId4chMv = 1650;
constexpr int kModIdHc2Mv = 1055;
constexpr int kModIdWindowMv = 150;  // proposed; the two nominal values are 595 mV apart

// --- Battery voltage (decisions 18, 38) ---------------------------------------------------------
// VBAT_SENSE divider 220 k / 22 k: pin voltage x 11, full scale about 32 V.
constexpr float kVbatDividerRatio = 11.0f;

// --- NTC TH1 (decision 18): 10 k B3380 to GND, 10 k pull-up to 3.3 V ------------------------------
constexpr float kNtcR25 = 10000.0f;
constexpr float kNtcBeta = 3380.0f;
constexpr float kNtcPullup = 10000.0f;
constexpr float kVrefMv = 3300.0f;

// --- pdm-4ch current sense (design-notes 6.1, T-0107) --------------------------------------------
// IL = VIS / RIS x kILIS. RIS = 2 x 1 k in parallel. kILIS is stored per channel because a
// BTT6010 build (kILIS 3900) may return later; the first version is all BTT6050 (decision 103).
constexpr float kRisOhm = 500.0f;
constexpr float kKilisBtt6050 = 1500.0f;
constexpr float kKilisBtt6010 = 3900.0f;

// A reading at or above this is "full scale": a fault current IIS(FAULT) >= 6 mA (3.0 V in 500 ohm)
// or a load far above the rating (2.8 V = 8.4 A on a BTT6050). Normal maximum is 1.63 V at 4.5 A.
// The ADC is calibrated up to about 2.9 V. Above 8.4 A the soft fuse therefore never sees the
// current: the channel is switched off at once as a switch fault.
constexpr int kIsFullScaleMv = 2800;  // proposed
// A switch fault latches after this many full-scale samples in a row while the output is on, so
// a start current above 8.4 A (motor, lamp, capacitor) does not switch the channel off. With the
// retry period below this is 1.0-1.5 s. Proposed; the pump start test (decision 100) decides.
constexpr int kSwitchFaultSamples = 3;

// --- Timing ---------------------------------------------------------------------------------------
constexpr uint32_t kTickMs = 10;             // inputs, LEDs
constexpr uint32_t kSwitchQualifyMs = 20;    // design-notes 5: "qualify inputs (e.g. 20 ms stable)"
constexpr uint32_t kSensePeriodMs = 100;     // IS sampling, Active mode (proposed)
constexpr uint32_t kSenseRetryMs = 500;      // IS sampling after a full-scale reading (proposed)
// Wait between DEN rising and the first conversion. UNVERIFIED: the BTT6050 sense settling time
// (tsIS) is not in docs/part-facts/C534868.md yet; read it from the datasheet or measure it at
// bring-up (bring-up.md 7.4) and correct this value.
constexpr uint32_t kDenSettleUs = 500;

// --- Soft fuse defaults (proposed, set per output later) ----------------------------------------
constexpr float kRatedCurrentBtt6050A = 4.0f;  // docs/ARCHITECTURE.md budget: 4 A at 2 oz copper
constexpr float kSoftFuseTauS = 10.0f;         // 3 x rated trips after about 1.2 s

// --- Alerts ---------------------------------------------------------------------------------------
// SW_SENSE low only counts while the battery is healthy (decision 93). SW_SENSE reads low below
// about 8.5 V at the battery, so the alert is armed with margin above that.
constexpr float kVbatHealthyV = 10.0f;        // proposed
constexpr uint32_t kSwSupplyAlertMs = 2000;   // proposed
constexpr float kBoardTempWarnC = 85.0f;      // proposed; NTC sits at U13's tab

// --- Panel LED (decision 20): on = output on, blinking = fault ----------------------------------
constexpr uint32_t kFaultBlinkHalfPeriodMs = 250;  // 2 Hz (proposed)

}  // namespace pdm
