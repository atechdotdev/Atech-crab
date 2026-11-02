# Sesame on Atech

![Sesame with an Atech 14-port board on its back](docs/img/cover.png)

The same Sesame (frame, servos, legs and moves) with an **Atech 14-port board** as its brain. The servos
plug straight into the board's ports on jumper wires, with no servo driver board. An Atech screen
in a visor at the front shows Sesame's face, and an Atech motion sensor keeps the walk on course.

Nothing under Sesame's top cover changes. The top cover is replaced by a **deck** that holds the board flat over
the legs and a **lid** that closes it. Both come from Atech Atelier's "Sesame walker".

[Assembly guide (PDF)](docs/sesame_atech_assembly.pdf) · [Assembly video (MP4, 33 s)](docs/sesame_atech_assembly.mp4)

## Status

| What | State |
|---|---|
| Firmware (`firmware/project.yaml`) | Builds with the Atech SDK and runs on the SDK's emulated board: all modules start, every move plays |
| Walking | Run in simulation (emulated board + MuJoCo): the motion sensor holds the walk within about 20° over ten cycles |
| Servo driver (`sg90_pair`) | Has driven an SG90 on a real Atech 14-port board |
| Deck and lid (v3) | Pass Atech Atelier's fit check in CAD. **Not yet printed or assembled** |

Print and test-fit the deck on the frame, with the servos in, before you print more than one set.

## What changes from Sesame

| Sesame | Sesame on Atech |
|---|---|
| ESP32 + distro board (or PCA9685) | Atech 14-port board (ESP32-S3). Servos on ports 2–5, two per port |
| 128×64 OLED | Atech screen module, ports 10+11, in a front visor |
| — | Atech motion sensor (icm40608), port 13: heading hold while walking, 90° turns |
| USB on the ESP32 | Atech USB-C module, port 8, at the back |
| Top cover | Deck (two printed parts, glued) + lid |
| Arduino IDE | `pip install atech`, then `atech upload` |

The moves are Sesame's own. `firmware/make_firmware.py` reads them out of this repository's
[`firmware/movement-sequences.h`](../firmware/movement-sequences.h) and sends each servo the same pulse
Sesame's firmware would (0–180° → 732–2929 µs).

## Parts

**Printed (13):** Sesame's internal frame, bottom cover, femurs L1 L2 R1 R2 and feet L3 L4 R3 R4, plus
deck part 1, deck part 2 and the lid. All 13 are in [`print/stl/`](print/stl/), turned the right way up.

**Hardware:** 8 × SG90 or MG90S servos · Atech 14-port board · Atech USB-C module · Atech motion sensor module ·
Atech screen module with its cable · 6 × M2×8 pan-head screws · 3 × M2×10 countersunk screws ·
male-to-male jumper wires · a 5 V 3 A supply for the servos · superglue (CA).

## Print

Sliced and checked for Bambu Lab printers, PLA Basic, Textured PEI plate, 0.4 mm nozzle, 0.20 mm layers,
tree supports from the build plate only:

| Printer | File(s) in [`print/gcode/`](print/gcode/) | Time |
|---|---|---|
| H2S | `sesame_atech_pla_h2s.gcode.3mf` | 4 h 34 min |
| H2D | `sesame_atech_pla_h2d.gcode.3mf` | 4 h 45 min |
| X2D | `sesame_atech_pla_x2d_plate1` + `_plate2` | 3 h 07 + 1 h 37 |
| P2S | `sesame_atech_pla_p2s_plate1` + `_plate2` | 3 h 41 + 1 h 04 |

Other printers: slice the STLs yourself, or run `print/slice.py` (it uses Bambu Studio's own printer
profiles, so the start G-code is the printer's own) and `print/check.py`.

## Assemble

The [PDF](docs/sesame_atech_assembly.pdf) has each step with pictures. In short:

1. Build Sesame's base as in the [build guide](../docs/build-guide/README.md), but leave the bottom cover off.
2. Glue deck part 2 under deck part 1 (the lip only fits one way).
3. Feed the servo leads up the deck's spine, and screw the deck on from inside the frame (4 × M2×8).
4. Battery, bottom cover (2 × M2×8).
5. Board on the four posts, USB-C module on port 8, motion sensor on port 13, screen in the visor cabled to ports 10+11.
6. Wire the servos (below).
7. Lid (3 × M2×10 countersunk).

## Wire

| Port | Leg | Line A (pin 5) | Line B (pin 6) |
|---|---|---|---|
| 2 | front left | L1 hip | L3 knee |
| 3 | front right | R1 hip | R3 knee |
| 4 | back left | L2 hip | L4 knee |
| 5 | back right | R2 hip | R4 knee |

Each port is a 6-pin header: 1 +12 V, 2 +5 V, 3 +3.3 V, 4 GND, 5 line A, 6 line B. Run the signal and GND
jumpers out through the slot at each port. Power the servos from the 5 V supply (red to +, brown to −), and
join the supply's − to a port's GND.

> **+12 V sits next to +5 V, and which end of the header is pin 1 is not marked.** Measure before you wire:
> with the board on USB, the pin reading 3.3 V is pin 3, and its neighbour that beeps to the USB-C shell is GND
> (pin 4). Never connect pin 1 to a servo.

![The slots at ports 2–5](docs/img/s6_slots.png)

## Software

```bash
pip install atech
cd atech/firmware
atech validate .
atech upload .                 # builds and flashes over USB; the first build downloads the ESP32 compiler
atech check                    # which modules answered
```

About 2.5 s after it starts, the robot stands up and plays a show: wave, walk, turn left, walk, dance, crab,
turn right, push-ups, cute, bow, shake, stand. **Hold it off the table, or give it room, the first time.**

Play any move from the laptop:

```bash
atech send spider_go walk      # rest stand wave dance swim point pushup bow cute freaky
                               # worm shake shrug dead crab walk back left right
atech monitor                  # spider_move, and spider_state (roll, pitch, yaw, servo angles) 10 times a second
```

From Python:

```python
from atech import Board

with Board.connect() as board:
    board.call("spider_go", "wave")
    for event in board.events(keys=["spider_move"]):
        print("now playing", event.value)
```

`left` and `right` repeat until the motion sensor has counted 85° (six times at most), and `walk` steers by
the sensor's heading.

**New moves:** edit `firmware/movement-sequences.h` (by hand or with
[Sesame Studio](https://github.com/dorianborian/sesame-studio)), then

```bash
python atech/firmware/make_firmware.py   # writes atech/firmware/project.yaml
atech upload atech/firmware
```

To test without a robot: `atech emulate atech/firmware --seconds 10` runs the same firmware on an emulated board.

## Files

```
atech/
├── firmware/
│   ├── project.yaml            the firmware: modules, ports, code (written by make_firmware.py)
│   ├── make_firmware.py        Sesame's movement-sequences.h -> project.yaml
│   └── my_modules/sg90_pair/   two hobby servos per port, 50 Hz LEDC (8 servos per board)
├── print/
│   ├── stl/                    all 13 parts, print orientation
│   ├── gcode/                  sliced for H2S, H2D, X2D, P2S (PLA)
│   ├── slice.py, check.py      re-slice with Bambu Studio's profiles; check a sliced file
│   └── README.txt
├── cad/
│   ├── sesame_atech_wired.py   the deck and lid (Atech Atelier, FreeCAD), with the wire openings
│   └── review.png
└── docs/
    ├── sesame_atech_assembly.pdf
    ├── sesame_atech_assembly.mp4
    └── img/
```

## Credits

- **Sesame** by Dorian Todd ([dorianborian/sesame-robot](https://github.com/dorianborian/sesame-robot)),
  Apache-2.0: the frame, servos, legs and moves.
- **Deck and lid**: Atech Atelier's "Sesame walker" 0.1.3, with wire openings added (v3).
- **Firmware**: built with the [Atech SDK](https://github.com/atechdotdev/python-sdk).
