// SPDX-License-Identifier: MIT
#include "soft_fuse.h"

#include <math.h>

namespace pdm {

bool SoftFuse::update(float current_a, float dt_s) {
  if (rated_a_ <= 0.0f || tau_s_ <= 0.0f || dt_s <= 0.0f) return tripped_;
  const float ratio = current_a / rated_a_;
  const float target = ratio * ratio;
  // Exact step of the first-order model, stable for any dt.
  level_ = target + (level_ - target) * expf(-dt_s / tau_s_);
  // Trips only while the current is above the rating, so a hot fuse that is cooling down after a
  // reset does not trip again by itself.
  if (level_ >= 1.0f && target >= 1.0f) tripped_ = true;
  return tripped_;
}

}  // namespace pdm
