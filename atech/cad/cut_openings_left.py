"""v4: the v3 wire openings on the -X side as well (ports 10-13), cut into the v3 print STLs.

The same boxes as opening_boxes() in sesame_atech_wired.py (PORT_Y_LEFT). The print STLs
were cut as meshes: print_to_model.json maps each print STL into the model frame.

python cut_openings_left.py v3_stl_dir out_dir print_to_model.json
"""
import json, sys
import numpy as np
import trimesh

PORT_Y = {10: (-45.82, -30.18), 11: (-25.82, -10.18), 12: (-5.82, 9.82), 13: (14.18, 29.82)}
X_OUT, X_IN = -45.0, -35.8        # the side wall only (-38..-36): the lid-screw boss at (-33.3, -2.5) stands 0.5 mm inside it
SLOT_Z = (79.45, 86.65)
LEAD_W, LEAD_Z0 = 8.0, 75.95
LEAD_SHIFT = {12: 2.0}            # port 12's notch 2 mm back, clear of the boss (y -4.7..-0.3)


def boxes():
    out = []
    for n, (y0, y1) in PORT_Y.items():
        out.append(("port%d" % n, (X_OUT, X_IN, y0 - 0.5, y1 + 0.5) + SLOT_Z))
        yc = (y0 + y1) / 2 + LEAD_SHIFT.get(n, 0.0)
        out.append(("sg90_%d" % n, (X_OUT, X_IN, yc - LEAD_W / 2, yc + LEAD_W / 2, LEAD_Z0, SLOT_Z[0] + 0.1)))
    return out


def cutter():
    return trimesh.boolean.union([trimesh.creation.box(bounds=[[x0, y0, z0], [x1, y1, z1]])
                                  for _, (x0, x1, y0, y1, z0, z1) in boxes()], engine="manifold")


if __name__ == "__main__":
    src, dst, maps = sys.argv[1], sys.argv[2], json.load(open(sys.argv[3]))
    for key, name in (("part1", "deck_part1_plate.stl"), ("lid", "lid_print_upside_down.stl")):
        M = np.array(maps[key])
        m = trimesh.load(f"{src}/{name}")
        m.apply_transform(M)                                   # print -> model frame
        before = m.volume
        m = trimesh.boolean.difference([m, cutter()], engine="manifold")
        m.apply_transform(np.linalg.inv(M))                    # back to print orientation
        m.export(f"{dst}/{name}")
        print(f"{name}: removed {before - m.volume:.1f} mm3, watertight {m.is_watertight}, bodies {len(m.split(only_watertight=False))}")
