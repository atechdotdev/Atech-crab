// Two hobby servos (SG90 / MG90S) on one Atech port, on jumper wires.
// Each servo uses one of the chip's 8 LEDC channels at 50 Hz: 8 servos per project at most.
#pragma once
#include <Arduino.h>

class Sg90Pair {
 public:
  Sg90Pair(int pinA, int pinB);
  void begin();
  void write(int which, float deg);       // 0..180
  void writeUs(int which, int us);        // 400..3000
  void detach(int which);
  float read(int which) const;

 private:
  int pin_[2];
  int ch_[2];
  float deg_[2];
};
