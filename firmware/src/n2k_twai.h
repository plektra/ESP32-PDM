// CAN driver for the NMEA2000 library on the ESP32-S3, using the ESP-IDF TWAI driver.
// (The library's own NMEA2000_esp32 driver is written for the original ESP32 only.)
// SPDX-License-Identifier: MIT
#pragma once
#include <NMEA2000.h>
#include <driver/gpio.h>

class N2kTwai : public tNMEA2000 {
 public:
  N2kTwai(gpio_num_t tx, gpio_num_t rx) : tx_(tx), rx_(rx) {}

  // Call regularly: restarts the controller after bus-off.
  void poll();

 protected:
  bool CANOpen() override;
  bool CANSendFrame(unsigned long id, unsigned char len, const unsigned char* buf,
                    bool wait_sent = true) override;
  bool CANGetFrame(unsigned long& id, unsigned char& len, unsigned char* buf) override;

 private:
  gpio_num_t tx_;
  gpio_num_t rx_;
  bool open_ = false;
};
