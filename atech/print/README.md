# 3D Printing Guide

Atech-crab is 13 printed parts: Sesame's internal frame, bottom cover and eight leg parts, unchanged, plus a new
**deck** (two parts, glued) and **lid** that hold the Atech board. Print everything in **PLA**.

> [!NOTE]
> **Not printed yet.** The deck and lid pass Atech Atelier's fit check in CAD, but nobody has printed and
> assembled them. Print one set and test-fit the deck on the frame, with the servos in, before you print more.

## Bambu Lab printers: ready to print

Each file in [`gcode/`](gcode/) is sliced and checked. Open it in Bambu Studio or Bambu Handy and send it.

| Printer | File(s) | Time | PLA |
| ------- | ------- | ---- | --- |
| H2S | [`atech_crab_pla_h2s.gcode.3mf`](gcode/atech_crab_pla_h2s.gcode.3mf) | 4 h 35 min | 139 g |
| H2D | [`atech_crab_pla_h2d.gcode.3mf`](gcode/atech_crab_pla_h2d.gcode.3mf) | 4 h 46 min | 139 g |
| X2D | [`atech_crab_pla_x2d_plate1.gcode.3mf`](gcode/atech_crab_pla_x2d_plate1.gcode.3mf) + [`_plate2`](gcode/atech_crab_pla_x2d_plate2.gcode.3mf) | 3 h 08 min + 1 h 37 min | 97 g + 42 g |
| P2S | [`atech_crab_pla_p2s_plate1.gcode.3mf`](gcode/atech_crab_pla_p2s_plate1.gcode.3mf) + [`_plate2`](gcode/atech_crab_pla_p2s_plate2.gcode.3mf) | 3 h 41 min + 1 h 04 min | 117 g + 22 g |

- **H2S / H2D:** all 13 parts on one plate. The H2D file uses one nozzle (Bambu Studio's nozzle 1); the printer
  shows which before it starts.
- **X2D / P2S:** the parts need two plates on a 256 mm bed. Print both files.
- All files: Bambu PLA Basic, **Textured PEI plate**, 0.4 mm nozzle.

<img src="../docs/img/print/plate_h2s.png" alt="All 13 parts on the H2S plate" width="45%">

Each file carries the printer's own Bambu start G-code (`check.py` compares it with Bambu Studio's profile for
that printer), its first layer is at 0.2 mm, and every part lays plastic on it. **Watch the first layer anyway:**
it should go down on the plate with every part and its brim. If the nozzle draws in the air, stop the print.

## Other printers: slice the STLs

All 13 STLs are in [`stl/`](stl/), already the right way up: load them and don't rotate them.

### Recommended settings

* **Material:** PLA / PLA+
* **Layer height:** 0.20 mm, 0.4 mm nozzle
* **Wall loops:** 2
* **Infill:** 15 %, gyroid
* **Supports:** tree, **from the build plate only**, threshold 40°, so nothing grows inside the servo pockets
* **Brim:** auto

These are the settings of the Bambu files above. Sesame's own guide
([`hardware/printing`](../../hardware/printing/README.md)) prints its parts at 8–10 % honeycomb infill with no
supports; either works for Sesame's parts.

### Parts

| Part | From | Qty | STL | Print orientation |
| ---- | ---- | --- | --- | ----------------- |
| Joint R1, R2, R3, R4 | Sesame | 1 each | [R1](stl/R1-v117.stl) · [R2](stl/R2-v117.stl) · [R3](stl/R3-v117.stl) · [R4](stl/R4-v117.stl) | as in the STL |
| Joint L1, L2, L3, L4 | Sesame | 1 each | [L1](stl/L1-v117.stl) · [L2](stl/L2-v117.stl) · [L3](stl/L3-v117.stl) · [L4](stl/L4-v117.stl) | as in the STL |
| Internal frame | Sesame | 1 | [Internal-Frame-v121.stl](stl/Internal-Frame-v121.stl) | as in the STL |
| Bottom cover | Sesame | 1 | [Bottom-Cover-v121.stl](stl/Bottom-Cover-v121.stl) | as in the STL |
| Deck part 1 (plate) | Atech-crab | 1 | [deck_part1_plate.stl](stl/deck_part1_plate.stl) | floor down, walls up |
| Deck part 2 (spine and head) | Atech-crab | 1 | [deck_part2_spine_and_head.stl](stl/deck_part2_spine_and_head.stl) | as in the STL |
| Lid | Atech-crab | 1 | [lid_print_upside_down.stl](stl/lid_print_upside_down.stl) | **upside down**: the top on the plate |

Sesame's parts are the same meshes as [`hardware/printing/stl`](../../hardware/printing/stl/), laid flat at the
origin. Sesame's **top cover is not printed**: the deck and lid replace it.

**Re-slice for a Bambu printer** (macOS, Bambu Studio installed): `python slice.py out_dir [h2s h2d x2d p2s]`.
It uses Bambu Studio's own printer profiles, so the start G-code is the printer's own.
**Check a sliced file:** `python check.py file.gcode.3mf ...`

## The wire openings (v4)

The deck and lid have an opening at every servo port, **on both sides**: ports 2–5 on the right (+X) and ports
10–13 on the left (−X). Each opening is half in the lid and half in the deck:

- **A slot** at each port, 16.6 × 7.2 mm, so the jumpers go straight out of the header.
- **An 8 mm notch** under each slot, down to the gap under the board: the SG90 leads come up the spine, run under
  the board and leave here. An SG90 plug (7.6 × 2.6 mm) fits through.
- **USB-C** (port 8, at the back): the opening reaches 5 mm lower, through the seam.

On the left side a lid-screw post stands just inside the wall behind port 12's slot, so port 12's notch sits 2 mm
further back than the others.

| Left (ports 10–13) | Right (ports 2–5) |
| --- | --- |
| <img src="../docs/img/print/openings_left.jpg" alt="Wire openings on the left side"> | <img src="../docs/img/print/openings_right.jpg" alt="Wire openings on the right side"> |

The openings are open at the seam, so neither the deck nor the lid needs support for them.

## After printing

1. Remove the brims and the tree supports.
2. Glue deck part 2 (spine and head) under deck part 1 with superglue (CA). The 0.6 mm lip fits the recess, so it
   only goes one way.
3. Continue with the [assembly guide (PDF)](../docs/atech_crab_assembly.pdf).

**Screws:** 6 × M2×8 pan-head (4 hold the deck to the frame, from inside; 2 hold the bottom cover) and
3 × M2×10 countersunk (the lid).

## Versions

| Version | Date | Changed |
| ------- | ---- | ------- |
| v4 | 2026-11-03 | Slots and lead notches on the left side too (ports 10–13). Deck part 1 and the lid only. |
| v3 | 2026-11-02 | Wire openings on the right side (ports 2–5), USB-C opening 5 mm lower. |

The CAD is [`../cad/sesame_atech_wired.py`](../cad/sesame_atech_wired.py) (Atech Atelier, FreeCAD). The v4
left-side openings were cut into the v3 print STLs with
[`../cad/cut_openings_left.py`](../cad/cut_openings_left.py), using the same boxes as the CAD.
