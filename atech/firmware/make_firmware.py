"""Write project.yaml: Sesame's poses and gaits on an Atech 14-port board.

    python make_firmware.py [--sequences path/to/movement-sequences.h]

The moves are read straight out of Sesame's firmware/movement-sequences.h (Apache-2.0,
Dorian Todd): each run...() function is played through - its
setServoAngle() calls, delays, loops and nested runStandPose() - and stored as keyframes.
The firmware plays them without blocking, sends each servo the pulse Sesame's own
firmware would (0..180 deg -> 732..2929 us), and draws Pip's face for each move.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
SEQUENCES = HERE.parents[1] / "firmware" / "movement-sequences.h"   # this repository's Sesame moves
ORDER = ("R1", "R2", "L1", "L2", "R4", "R3", "L3", "L4")
FRAME_DELAY = 100        # Sesame's frameDelay, ms
WALK_CYCLES = 10         # Sesame's walkCycles
TURN_CYCLES = 2          # one "left"/"right" unit; the firmware repeats it to make 90 deg
# the moves this firmware knows, and the face each gets (Pip's moods: 1 awake, 2 happy,
# 3 love, 4 surprised, 5 focused, 6 dizzy, 0 asleep)
MOVES = {"rest": 0, "stand": 1, "wave": 2, "dance": 3, "swim": 2, "point": 1, "pushup": 5,
         "bow": 2, "cute": 3, "freaky": 6, "worm": 6, "shake": 2, "shrug": 4, "dead": 0,
         "crab": 5, "walk": 5, "back": 5, "left": 5, "right": 5}
FUNCS = {"rest": "runRestPose", "stand": "runStandPose", "wave": "runWavePose", "dance": "runDancePose",
         "swim": "runSwimPose", "point": "runPointPose", "pushup": "runPushupPose", "bow": "runBowPose",
         "cute": "runCutePose", "freaky": "runFreakyPose", "worm": "runWormPose", "shake": "runShakePose",
         "shrug": "runShrugPose", "dead": "runDeadPose", "crab": "runCrabPose", "walk": "runWalkPose",
         "back": "runWalkBackward", "left": "runTurnLeft", "right": "runTurnRight"}


def _bodies(src: str) -> dict[str, str]:
    out = {}
    for m in re.finditer(r"inline void (\w+)\([^)]*\)\s*\{", src):
        i, depth = m.end(), 1
        while depth:
            depth += {"{": 1, "}": -1}.get(src[i], 0)
            i += 1
        out[m.group(1)] = src[m.end():i - 1]
    return out


def play(name: str, bodies: dict[str, str], walk_cycles: int = WALK_CYCLES) -> list[tuple[int, dict[str, int]]]:
    """Run a Sesame move function symbolically: [(hold_ms, {servo: deg}), ...]."""
    frames: list[tuple[int, dict[str, int]]] = []
    pending: dict[str, int] = {}

    def flush(ms):
        nonlocal pending
        frames.append((ms, pending))
        pending = {}

    def run(body: str):
        tok = re.compile(r"for\s*\(int i\s*=\s*0;\s*i\s*<\s*(\w+);\s*i\+\+\)\s*\{|setServoAngle\((\w+),\s*(\d+)\)"
                         r"|delayWithFace\((\d+)\)|pressingCheck\([^,]+,\s*frameDelay\)|runStandPose\((\d?)\)"
                         r"|for \(int i = 0; i < 8; i\+\+\) setServoAngle\(i, (\d+)\)")
        i = 0
        while True:
            m = tok.search(body, i)
            if m is None:
                return
            if m.group(0).startswith("for (int i = 0; i < 8; i++) setServoAngle"):
                pending.update({s: int(m.group(6)) for s in ORDER})
                i = m.end()
            elif m.group(1) is not None:
                n = walk_cycles if m.group(1) == "walkCycles" else int(m.group(1))
                j, depth = m.end(), 1
                while depth:
                    depth += {"{": 1, "}": -1}.get(body[j], 0)
                    j += 1
                for _ in range(n):
                    run(body[m.end():j - 1])
                i = j
            elif m.group(2) is not None:
                pending[m.group(2)] = int(m.group(3))
                i = m.end()
            elif m.group(4) is not None:
                flush(int(m.group(4)))
                i = m.end()
            elif m.group(0).startswith("pressingCheck"):
                flush(FRAME_DELAY)
                i = m.end()
            else:      # runStandPose(...)
                run(bodies["runStandPose"])
                i = m.end()

    run(bodies[FUNCS[name]])
    flush(FRAME_DELAY * 3)    # let the last pose settle
    return [(ms, f) for ms, f in frames if f or ms]


MODULES_ATELIER = """name: atech_crab
board: 14port
# Sesame (Dorian Todd's eight-servo quadruped, Apache-2.0) with an Atech 14-port board:
# Atech Atelier's "Sesame walker" (Atelier 0.1.3). Sesame's frame, servos and legs are
# unchanged; a deck in place of its top cover holds the board flat over the legs, its centre
# 8 mm ahead of the hip axes. The servos (MG90S, 180 deg) plug straight into the ports on
# jumper wires, two per port, run under the board through the spine:
#   port 2: L1 (front-left hip) on Line A, L3 (its knee) on Line B
#   port 3: R1 / R3 (front-right)    port 4: L2 / L4 (rear-left)    port 5: R2 / R4 (rear-right)
# Red wires to the port's +5V, brown to GND, orange to the line. +12V is next to +5V:
# check which end of the header is +12V on your board before you wire anything.
# Feed the servos from a 5 V 3 A supply (Sesame's buck converter), grounds joined.
# USB-C module on port 8. The screen sits on a cable from ports 10+11, upright in the front
# visor, its connector edge down (the firmware turns the image 180 deg); the motion sensor
# on port 13.
modules_path: ./my_modules
modules:
  - {id: sg90_pair,  instance: fl,    port: 2}
  - {id: sg90_pair,  instance: fr,    port: 3}
  - {id: sg90_pair,  instance: bl,    port: 4}
  - {id: sg90_pair,  instance: br,    port: 5}
  - {id: st7735_tft, instance: face,  ports: [10, 11]}
  - {id: icm40608,   instance: imu,   port: 13}
"""


GLOBALS_HEAD = r"""
// ---- the servos: Sesame's channel order, each on its port line ----
enum { R1, R2, L1, L2, R4, R3, L3, L4 };
static Sg90Pair* const PAIR[8] = {&fr, &br, &fl, &bl, &br, &fr, &fl, &bl};
static const uint8_t LINE[8]   = {0,   0,   0,   0,   1,   1,   1,   1};
static int8_t subtrim[8] = {0, 0, 0, 0, 0, 0, 0, 0};
static uint8_t servoDeg[8];
static int rawDeg[8];                 // what the move asked for, before steering
// Sesame's mapping: 0..180 deg -> 732..2929 us (its MIN_PULSE / MAX_PULSE)
static void writeServo(uint8_t ch, float deg) {
  deg = constrain(deg + subtrim[ch], 0.0f, 180.0f);
  servoDeg[ch] = (uint8_t)(deg + 0.5f);
  PAIR[ch]->writeUs(LINE[ch], 732 + (int)(deg * (2929 - 732) / 180.0f + 0.5f));
}

// Steering. Sesame's walk on its own drifts to the left (in MuJoCo, on Sesame's own model
// too). While walking, the IMU's heading scales the hips' stroke: u > 0 lengthens the left
// hips' stroke and shortens the right ones', turning right. u = bias + kp * error + ki * its integral.
static bool steerOn = false;
static float steerU = 0.0f;
static const float STEER_KP = 4.0f, STEER_KI = 2.0f, STEER_BIAS = 0.15f;
static float steerI = 0.0f;
static const uint8_t HIP_CENTER[8] = {135, 45, 45, 135, 0, 0, 0, 0};
static const uint8_t HIP_LO[8] = {45, 0, 0, 45, 0, 0, 0, 0}, HIP_HI[8] = {180, 135, 135, 180, 0, 0, 0, 0};
static void steerHips() {
  for (int ch = R1; ch <= L2; ch++) {
    float sc = (ch == R1 || ch == R2) ? 1.0f - steerU : 1.0f + steerU;
    float d = steerOn ? HIP_CENTER[ch] + (rawDeg[ch] - HIP_CENTER[ch]) * sc : rawDeg[ch];
    writeServo(ch, constrain(d, (float)HIP_LO[ch], (float)HIP_HI[ch]));
  }
}
static void setServoAngle(uint8_t ch, int deg) {
  rawDeg[ch] = deg;
  if (ch <= L2) steerHips(); else writeServo(ch, deg);
}

// ---- Sesame's moves as keyframes: {hold ms, n, servo, deg, servo, deg, ...}, ... , -1 ----
%MOVES%

// ---- the IMU: tilt and heading, for the face and the readout ----
static float rollF = 0, pitchF = 0, yaw = 0;
static void sense(float dt) {
  float ax = imu.readAccelX(), ay = imu.readAccelY(), az = imu.readAccelZ();
  float gx = imu.readGyroX() * DEG_TO_RAD, gy = imu.readGyroY() * DEG_TO_RAD, gz = imu.readGyroZ() * DEG_TO_RAD;
  float rollA = atan2f(-ax, az), pitchA = atan2f(ay, sqrtf(ax * ax + az * az));
  rollF = 0.97f * (rollF + gy * dt) + 0.03f * rollA;
  pitchF = 0.97f * (pitchF + gx * dt) + 0.03f * pitchA;
  yaw += gz * dt;
}
"""

SETUP = r"""
face.setRotation(%ROT%);   // %ROTWHY%
imu.calibrateGyro();
for (int i = 0; i < 8; i++) setServoAngle(i, STAND[i]);
"""

LOOP = r"""
// A show: wake up, then Sesame's moves one after the other. `atech send spider_go <move>`
// plays one move now (rest, stand, wave, dance, walk, back, left, right, ...).
static const char* SHOW[] = {"stand", "wave", "walk", "left", "walk", "dance", "crab", "right",
                             "pushup", "cute", "bow", "shake", "stand"};
static const int NSHOW = sizeof(SHOW) / sizeof(SHOW[0]);
static int showAt = -1, move = -1;
static const int16_t* kf = nullptr;
static unsigned long nextKey = 0, t0 = millis(), moveStart = 0;
static EveryTimer faceT, report, senseT;
static String queued = "";
static float steerYaw0 = 0.0f;
static int turnRepeats = 0;
float t = (millis() - t0) / 1000.0f;

if (atech_action == "spider_go") {
  if (moveIndex(atech_value.c_str()) >= 0) { queued = atech_value; atechDone(); }
}
if (senseT.ready(10)) {
  sense(0.01f);
  if (steerOn) {     // heading hold while walking
    float e = yaw - steerYaw0;
    steerI = constrain(steerI + e * 0.01f, -0.1f, 0.1f);
    steerU = constrain(STEER_BIAS + STEER_KP * e + STEER_KI * steerI, -0.4f, 0.4f);
    steerHips();
  }
}

// pick the next move
if (kf == nullptr && millis() - t0 > 2500) {
  int next = -1;
  if (queued.length()) { next = moveIndex(queued.c_str()); queued = ""; }
  else if (showAt + 1 < NSHOW) next = moveIndex(SHOW[++showAt]);
  if (next >= 0) {
    move = next; kf = MOVE_DATA[move]; nextKey = millis(); moveStart = millis();
    steerOn = (move == moveIndex("walk"));
    steerYaw0 = yaw; steerI = 0.0f;
    Serial.printf("{\"type\":\"event\",\"payload\":{\"event_type\":\"state\",\"key\":\"spider_move\",\"value\":\"%s\"}}\n", MOVE_NAMES[move]);
#ifdef HAS_VOICE
    if (move == moveIndex("wave") || move == moveIndex("dance")) voice.playRTTTL("hi:d=16,o=6,b=180:c,e,g,c7");
    else voice.playNote(NOTE_G5, 60);
#endif
  }
}
// play keyframes
while (kf != nullptr && (long)(millis() - nextKey) >= 0) {
  if (kf[0] < 0) {
    // a turn is done when the IMU has counted 90 degrees: play it again until then (6 units at most)
    bool turn = move == moveIndex("left") || move == moveIndex("right");
    if (turn && fabsf(yaw - steerYaw0) < radians(85) && ++turnRepeats < 6) { kf = MOVE_DATA[move]; continue; }
    turnRepeats = 0;
    kf = nullptr; steerOn = false; steerHips(); break;
  }
  int hold = kf[0], n = kf[1];
  for (int i = 0; i < n; i++) setServoAngle(kf[2 + 2 * i], kf[3 + 2 * i]);
  kf += 2 + 2 * n;
  nextKey += hold;
}

if (faceT.ready(80)) {
  float blink = (fmodf(t, 3.7f) < 0.15f) ? 1.0f : 0.0f;
  int mood = (move < 0) ? ((t < 1.2f) ? 0 : 1) : MOVE_MOOD[move];
  if (kf == nullptr && move >= 0) mood = 1;
  bool tipped = fabsf(rollF) > 1.0f || fabsf(pitchF) > 1.0f;
  if (tipped) mood = 4;
  float gx = (mood == 1) ? 0.6f * sinf(t * 1.3f) : 0.0f;
  drawFace(mood, gx, mood == 5 ? -0.3f : 0.0f, blink, t);
  switch (mood) {
    case 0: glowAll(0, 0, 10); break;
    case 2: case 3: glowAll(51, 10, 30); break;
    case 5: glowAll(0, 40, 20); break;
    case 6: glowAll(30, 0, 40); break;
    default: glowAll(10, 30, 40);
  }
}
if (report.ready(100)) {
  Serial.printf("{\"type\":\"event\",\"payload\":{\"event_type\":\"sensor\",\"key\":\"spider_state\",\"value\":{\"roll\":%.3f,\"pitch\":%.3f,\"yaw\":%.3f,\"deg\":[%d,%d,%d,%d,%d,%d,%d,%d]}}}\n",
                rollF, pitchF, yaw, servoDeg[0], servoDeg[1], servoDeg[2], servoDeg[3], servoDeg[4], servoDeg[5], servoDeg[6], servoDeg[7]);
}
"""


LANDSCAPE_FACE = r"""
// ============================ the face (upright, in the visor) =================
// The screen stands upright at the front, its long side across: a landscape face.
// 0 asleep, 1 awake, 2 happy, 3 love, 4 surprised, 5 focused (walking), 6 dizzy
static void drawFace(int mood, float gx, float gy, float blink, float t) {
  const uint16_t BG = 0x0841, EYE = 0xAFFF, PUPIL = 0x0841, PINK = 0xFB56, WARM = 0xFD20;
  face.fillScreen(BG);
  int ex[2] = {52, 108};
  int ey = 34;
  for (int e = 0; e < 2; e++) {
    int x = ex[e] + (int)(gx * 8), y = ey + (int)(gy * 6);
    if (mood == 0) {
      face.fillRoundRect(x - 15, y + 4, 30, 5, 2, EYE);
    } else if (mood == 2) {
      face.fillCircle(x, y + 8, 15, EYE); face.fillCircle(x, y + 14, 14, BG); face.fillRect(x - 16, y + 8, 33, 14, BG);
    } else if (mood == 3) {
      int sz = 8 + (int)(2 * sinf(t * 12));
      face.fillCircle(x - sz / 2, y - 2, sz / 2 + 1, PINK); face.fillCircle(x + sz / 2, y - 2, sz / 2 + 1, PINK);
      face.fillTriangle(x - sz - 1, y, x + sz + 1, y, x, y + sz + 4, PINK);
    } else if (mood == 4) {
      face.fillCircle(x, y, 16, EYE); face.fillCircle(x, y, 6, PUPIL);
    } else if (mood == 6) {
      for (int r = 3; r <= 14; r += 4) {
        float a0 = t * 9.0f + r * 0.5f;
        face.drawCircle(x + (int)(2 * cosf(a0)), y + (int)(2 * sinf(a0)), r, EYE);
      }
    } else {
      int h = max(4, (int)(36 * (1.0f - blink)));
      if (mood == 5) h = min(h, 22);
      face.fillRoundRect(x - 14, y - h / 2, 28, h, min(12, h / 2), EYE);
      if (h > 12) { face.fillCircle(x + (int)(gx * 5), y + (int)(gy * 5), 6, PUPIL); face.fillCircle(x + (int)(gx * 5) - 2, y + (int)(gy * 5) - 2, 2, EYE); }
      if (mood == 5) { int sg = e == 0 ? 1 : -1; face.fillTriangle(x - 15, y - 20 + 4 * sg, x + 15, y - 20 - 4 * sg, x + 14 * sg, y - 14, WARM); }
    }
  }
  if (mood != 0 && mood != 6) { face.fillRoundRect(24, 56, 16, 6, 3, PINK); face.fillRoundRect(120, 56, 16, 6, 3, PINK); }
  if (mood == 0) face.drawCircle(80, 64, 4, EYE);
  else if (mood == 4) face.fillCircle(80, 66, 6, EYE);
  else if (mood == 6) { face.drawLine(68, 66, 75, 61, EYE); face.drawLine(75, 61, 85, 69, EYE); face.drawLine(85, 69, 92, 64, EYE); }
  else { face.fillCircle(80, 58, 9, EYE); face.fillRect(70, 48, 21, 11, BG); }
  if (mood == 0) {
    int zy = 22 - (int)(fmodf(t, 1.5f) * 6);
    for (int k = 0; k < 2; k++) { int x0 = 130 + 9 * k, y0 = zy - 7 * k, w = 5 + 2 * k;
      face.drawLine(x0, y0, x0 + w, y0, EYE); face.drawLine(x0 + w, y0, x0, y0 + w, EYE); face.drawLine(x0, y0 + w, x0 + w, y0 + w, EYE); }
  }
  face.display();
}

static void glowAll(uint8_t, uint8_t, uint8_t) {}
"""


def moves_cpp(bodies) -> str:
    lines, names = [], list(MOVES)
    for name in names:
        data = []
        # a turn is stored as 2 of Sesame's cycles: the firmware repeats it until the IMU
        # has counted 90 degrees
        cycles = TURN_CYCLES if name in ("left", "right") else WALK_CYCLES
        for ms, f in play(name, bodies, cycles):
            data += [ms, len(f)]
            for s, d in f.items():
                data += [ORDER.index(s), d]
        data.append(-1)
        lines.append(f"static const int16_t MOVE_{name.upper()}[] = {{{', '.join(map(str, data))}}};")
    lines.append(f"static const int16_t* const MOVE_DATA[] = {{{', '.join('MOVE_' + n.upper() for n in names)}}};")
    lines.append(f"static const char* const MOVE_NAMES[] = {{{', '.join(chr(34) + n + chr(34) for n in names)}}};")
    lines.append(f"static const uint8_t MOVE_MOOD[] = {{{', '.join(str(MOVES[n]) for n in names)}}};")
    lines.append(f"static const int NMOVES = {len(names)};")
    stand = dict(play("stand", bodies)[0][1])
    lines.append(f"static const uint8_t STAND[8] = {{{', '.join(str(stand[s]) for s in ORDER)}}};")
    lines.append("static int moveIndex(const char* n) { for (int i = 0; i < NMOVES; i++) if (!strcmp(n, MOVE_NAMES[i])) return i; return -1; }")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description="Write project.yaml: Sesame's moves for the Atech 14-port board.")
    ap.add_argument("--sequences", type=Path, default=SEQUENCES)
    args = ap.parse_args()
    bodies = _bodies(args.sequences.read_text())
    glob = GLOBALS_HEAD.replace("%MOVES%", moves_cpp(bodies)) + LANDSCAPE_FACE

    def block(s):
        return "\n".join("    " + line if line else "" for line in s.strip("\n").splitlines())

    # the visor holds the screen connector edge down: turned 180 deg
    setup = SETUP.replace("%ROT%", "1").replace("%ROTWHY%", "connector edge down in the visor")
    text = (MODULES_ATELIER + "code:\n  globals: |\n" + block(glob) + "\n  setup: |\n" + block(setup)
            + "\n  loop: |\n" + block(LOOP) + "\n")
    (HERE / "project.yaml").write_text(text)
    for n in ("stand", "walk", "left"):
        fr = play(n, bodies)
        print(f"{n}: {len(fr)} keyframes, {sum(ms for ms, _ in fr) / 1000:.1f} s")
    print("wrote project.yaml")


if __name__ == "__main__":
    main()
