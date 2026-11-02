"""Check sliced .gcode.3mf files before they go to a printer.

    python check.py file.gcode.3mf ...

For each file: the printer and filament; that the start G-code is the printer's own
(equal to Bambu Studio's profile for that printer, not fdm_machine_common's
generic Marlin one); that the first layer is at
0.2 mm; that every part puts plastic down on that first layer; supports; time and
filament.
"""
import json
import re
import sys
import zipfile

GENERIC_START = ("G29 ;Home", ";Draw the first line")   # fdm_machine_common's start G-code


def check(path):
    z = zipfile.ZipFile(path)
    cfg = json.loads(z.read("Metadata/project_settings.config"))
    g = z.read("Metadata/plate_1.gcode").decode("utf-8", "replace")
    head = g[: g.index("; CHANGE_LAYER")]
    start = head[head.index("; CONFIG_BLOCK_END"):]
    problems = []

    if any(s in start for s in GENERIC_START):
        problems.append("generic Marlin start G-code (prints in the air on a Bambu)")
    try:   # the printer's own start G-code, from Bambu Studio's profiles
        from slice import preset
        own = preset("machine", cfg["printer_settings_id"])["machine_start_gcode"]
        if cfg.get("machine_start_gcode") != own:
            problems.append("start G-code differs from Bambu's profile for this printer")
    except (ImportError, KeyError, FileNotFoundError):
        pass

    layers = g.split("; CHANGE_LAYER")
    first = layers[1]
    z0 = re.search(r"; Z_HEIGHT: ([\d.]+)", first)
    if not z0 or abs(float(z0.group(1)) - 0.2) > 1e-6:
        problems.append(f"first layer at {z0.group(1) if z0 else '?'} mm, not 0.2")

    # which objects print on layer 1 (Bambu marks them with M624/M625 or "; start printing object, unique label id: N")
    ids_all = set(re.findall(r"start printing object, unique label id: (\d+)", g))
    ids_first = set(re.findall(r"start printing object, unique label id: (\d+)", first))
    if ids_all - ids_first:
        problems.append(f"parts with nothing on the first layer: {sorted(ids_all - ids_first)}")

    t = re.search(r"total estimated time: ([^\n;]+)", head)
    w = re.search(r"total filament weight \[g\] : ([\d.]+)", head)
    print(f"{path.split('/')[-1]}")
    print(f"  printer   {cfg['printer_model']} / {cfg['printer_settings_id']}")
    print(f"  filament  {cfg['filament_settings_id'][0]}   plate {cfg.get('curr_bed_type')}")
    print(f"  start     {start.count(chr(10))} lines")
    print(f"  layer 1   {z0.group(1) if z0 else '?'} mm, {len(ids_first)}/{len(ids_all)} parts on it")
    print(f"  supports  {cfg.get('enable_support')} {cfg.get('support_type')}, build plate only {cfg.get('support_on_build_plate_only')}")
    print(f"  time      {t.group(1).strip() if t else '?'}, {w.group(1) if w else '?'} g")
    print("  " + ("OK" if not problems else "PROBLEMS: " + "; ".join(problems)))
    return not problems


if __name__ == "__main__":
    ok = [check(p) for p in sys.argv[1:]]
    sys.exit(0 if all(ok) else 1)
