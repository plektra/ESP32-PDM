// SPDX-License-Identifier: MIT
#include "n2k_twai.h"

#include <driver/twai.h>
#include <string.h>

bool N2kTwai::CANOpen() {
  if (open_) return true;
  twai_general_config_t g = TWAI_GENERAL_CONFIG_DEFAULT(tx_, rx_, TWAI_MODE_NORMAL);
  g.tx_queue_len = 40;
  g.rx_queue_len = 40;
  twai_timing_config_t t = TWAI_TIMING_CONFIG_250KBITS();  // NMEA 2000 bit rate
  twai_filter_config_t f = TWAI_FILTER_CONFIG_ACCEPT_ALL();
  if (twai_driver_install(&g, &t, &f) != ESP_OK) return false;
  if (twai_start() != ESP_OK) {
    twai_driver_uninstall();
    return false;
  }
  open_ = true;
  return true;
}

bool N2kTwai::CANSendFrame(unsigned long id, unsigned char len, const unsigned char* buf,
                           bool /*wait_sent*/) {
  if (!open_ || len > 8) return false;
  twai_message_t m = {};
  m.extd = 1;
  m.identifier = id;
  m.data_length_code = len;
  memcpy(m.data, buf, len);
  // No blocking: when the queue is full the library keeps the frame and tries again.
  return twai_transmit(&m, 0) == ESP_OK;
}

bool N2kTwai::CANGetFrame(unsigned long& id, unsigned char& len, unsigned char* buf) {
  if (!open_) return false;
  twai_message_t m;
  while (twai_receive(&m, 0) == ESP_OK) {
    if (!m.extd || m.rtr) continue;  // NMEA 2000 uses 29-bit data frames only
    id = m.identifier;
    len = m.data_length_code > 8 ? 8 : m.data_length_code;
    memcpy(buf, m.data, len);
    return true;
  }
  return false;
}

void N2kTwai::poll() {
  if (!open_) return;
  twai_status_info_t s;
  if (twai_get_status_info(&s) != ESP_OK) return;
  if (s.state == TWAI_STATE_BUS_OFF) {
    twai_initiate_recovery();  // ends in the stopped state
  } else if (s.state == TWAI_STATE_STOPPED) {
    twai_start();
  }
}
