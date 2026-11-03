ATECH-CRAB - PRINT FILES (v3, 2026-11-02)

gcode/: sliced and checked, PLA Basic, Textured PEI plate, 0.4 mm nozzle, 0.20 mm
layers, 2 walls, 15 % gyroid infill, tree supports from the build plate only, auto brim.

  H2S   atech_crab_pla_h2s.gcode.3mf          4 h 34 min   140 g   all 13 parts
  H2D   atech_crab_pla_h2d.gcode.3mf          4 h 45 min   140 g   all 13 parts
        (one nozzle: Bambu Studio's nozzle 1; the printer shows which before it starts)
  X2D   atech_crab_pla_x2d_plate1.gcode.3mf   3 h 07 min    98 g   6 parts
        atech_crab_pla_x2d_plate2.gcode.3mf   1 h 37 min    42 g   7 parts
  P2S   atech_crab_pla_p2s_plate1.gcode.3mf   3 h 41 min   118 g   8 parts
        atech_crab_pla_p2s_plate2.gcode.3mf   1 h 04 min    22 g   5 parts

On a 256 mm bed (X2D, P2S) the parts need two plates: print both files.

Each file carries the printer's own Bambu start G-code (check.py compares it with
Bambu Studio's profile for that printer), its first layer is at 0.2 mm, and every part
lays plastic on it. Watch the first layer anyway: if the nozzle draws in the air, stop.

stl/: all 13 parts, already the right way up.
  Sesame (Dorian Todd, Apache-2.0): Internal-Frame, Bottom-Cover, L1-L4, R1-R4
  (the same meshes as hardware/printing/stl, laid flat at the origin)
  Atech Atelier "Sesame walker", v3: deck_part1_plate, deck_part2_spine_and_head,
  lid_print_upside_down

v3 adds the wire openings to deck part 1 and the lid: the USB-C opening reaches 5 mm
lower, through the seam; a slot at each servo port (2-5), half lid and half deck; and
an 8 mm notch under each slot for the servo leads.

Re-slice (macOS, Bambu Studio installed):  python slice.py out_dir [h2s h2d x2d p2s]
Check a sliced file:                       python check.py file.gcode.3mf ...

Not printed yet: test-fit the deck on the frame, with the servos in, before you print
a second set.
