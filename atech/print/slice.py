"""Slice the Sesame-on-Atech parts for Bambu printers with the full system profiles.

Bambu keeps each printer's start/end G-code in separate "template" profiles. Loading
only `Bambu Lab H2S 0.4 nozzle.json` into the CLI falls back to fdm_machine_common's
generic Marlin start G-code (G28, G29, a purge line at X10), which skips the Bambu
homing and Z probing: the printer then starts printing in the air. This script resolves
each profile's `inherits` chain itself, merges the template G-codes in, and hands the
CLI flat profiles.

    python slice.py out_dir [printer ...]     # printers: h2s h2d x2d p2s x1c
"""
import json
import pathlib
import subprocess
import sys
import tempfile

APP = pathlib.Path("/Applications/BambuStudio.app/Contents")
CLI = APP / "MacOS/BambuStudio"
PROFILES = APP / "Resources/profiles/BBL"
HERE = pathlib.Path(__file__).parent
STL = sorted((HERE / "stl").glob("*.stl"))

PRINTERS = {
    "h2s": ("Bambu Lab H2S 0.4 nozzle", "0.20mm Standard @BBL H2S", "@BBL H2S"),
    "h2d": ("Bambu Lab H2D 0.4 nozzle", "0.20mm Standard @BBL H2D", "@BBL H2D"),
    "x2d": ("Bambu Lab X2D 0.4 nozzle", "0.20mm Standard @BBL X2D", "@BBL X2D"),
    "p2s": ("Bambu Lab P2S 0.4 nozzle", "0.20mm Standard @BBL P2S", "@BBL P2S"),
    "x1c": ("Bambu Lab X1 Carbon 0.4 nozzle", "0.20mm Standard @BBL X1C", "@BBL X1C"),
}
FILAMENTS = {"pla": "Bambu PLA Basic", "petg": "Bambu PETG Basic"}
JOBS = [("h2s", "pla"), ("h2d", "pla"), ("x2d", "pla"), ("p2s", "pla")]   # the printers we have; PLA only

# Supports where the parts need them: tree, from the build plate only, so no support
# grows on a part's own surface (the servo pockets stay clean).
PRINT_OVERRIDES = {
    "enable_support": "1",
    "support_type": "tree(auto)",
    "support_on_build_plate_only": "1",
    "support_threshold_angle": "40",
    "brim_type": "auto_brim",
    "wall_loops": "2",
    "sparse_infill_density": "15%",
    "sparse_infill_pattern": "gyroid",
    "curr_bed_type": "Textured PEI Plate",   # the default Cool Plate refuses PETG
}


def _index(kind):
    out = {}
    for f in (PROFILES / kind).glob("*.json"):
        try:
            d = json.loads(f.read_text())
        except ValueError:
            continue
        if "name" in d:
            out[d["name"]] = d
    return out


def resolve(index, name):
    d = index[name]
    base = resolve(index, d["inherits"]) if d.get("inherits") else {}
    return {**base, **d}


def preset(kind, system_name, extra=None):
    """The system profile with its `inherits` chain resolved and, for a printer, its
    G-code templates merged in. It keeps the system name and `from: system`: the CLI
    matches the process's `compatible_printers` against the printer by that name."""
    index = _index(kind)
    d = resolve(index, system_name)
    if kind == "machine":
        for tname, t in index.items():
            if tname.startswith(system_name + " template "):
                d.update({k: v for k, v in t.items() if k not in ("name", "instantiation", "inherits", "from", "type")})
    d.update(extra or {})
    d.update({"name": system_name, "from": "system", "inherits": "", "type": kind, "instantiation": "true"})
    return d


GAP = 10.0   # mm between parts: room for the auto brim and tree supports


def layout(machine, out):
    """Place the parts on plates, shelf by shelf, and write each plate's parts to
    out/plate<n>/. Whatever does not fit on a plate goes on the next: on a 256 mm bed
    that makes two plates, each its own file, so every print is a plain one-plate job.
    (The CLI's own arrange also spills onto a second plate, inside one file.)"""
    import trimesh

    d = preset("machine", machine)
    area = d["printable_area"]
    if d.get("extruder_printable_area"):   # two nozzles: only where both reach
        areas = [[tuple(map(float, q.strip().split("x"))) for q in a.split(",")] for a in d["extruder_printable_area"]]
        lo_x = max(min(x for x, _ in a) for a in areas); hi_x = min(max(x for x, _ in a) for a in areas)
        lo_y = max(min(y for _, y in a) for a in areas); hi_y = min(max(y for _, y in a) for a in areas)
        area = [f"{lo_x}x{lo_y}", f"{hi_x}x{hi_y}"]
    xs, ys = zip(*(map(float, p.strip().split("x")) for p in area))
    excl = [tuple(map(float, p.strip().split("x"))) for p in d.get("bed_exclude_area") or []]
    x_min, y_min = min(xs) + GAP, min(ys) + GAP + (max(y for _, y in excl) if excl else 0)
    x_max, y_max = max(xs) - GAP, max(ys) - GAP
    todo = []
    for f in STL:
        m = trimesh.load(f, force="mesh")
        w, h = m.extents[:2]
        if w > h:   # long side along y, so shelves pack tighter
            m.apply_transform(trimesh.transformations.rotation_matrix(1.5707963, [0, 0, 1]))
        m.apply_translation(-m.bounds[0])
        todo.append((f.name, m))
    todo.sort(key=lambda t: -t[1].extents[1])
    plates = []
    while todo:
        x, y, shelf, placed, left = x_min, y_min, 0.0, [], []
        for name, m in todo:
            w, h = m.extents[:2]
            if x + w > x_max:
                x, y, shelf = x_min, y + shelf + GAP, 0.0
            if y + h > y_max:
                left.append((name, m))
                continue
            placed.append((name, m.copy().apply_translation([x, y, 0])))
            x, shelf = x + w + GAP, max(shelf, h)
        if not placed:
            raise SystemExit(f"{machine}: {todo[0][0]} does not fit on the bed")
        folder = out / f"plate{len(plates) + 1}"
        folder.mkdir()
        for name, m in placed:
            m.export(folder / name)
        plates.append(sorted(folder.glob("*.stl")))
        todo = left
    return plates


def slice_one(printer, fil, out_dir):
    machine, process, suffix = PRINTERS[printer]
    names = _index("filament")   # some are "... @BBL X2D 0.4 nozzle", some "... @BBL H2S"
    filament = next(n for n in (f"{FILAMENTS[fil]} {suffix}", f"{FILAMENTS[fil]} {suffix} 0.4 nozzle") if n in names)
    outs = []
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        paths = {}
        # a two-nozzle printer (H2D) refuses "auto" nozzle choice from the CLI: one filament, nozzle 1
        dual = len(preset("machine", machine).get("extruder_printable_area") or []) > 1
        mextra = {"filament_map_mode": "Manual", "filament_map": ["1"]} if dual else None
        for kind, name, extra in (("machine", machine, mextra), ("process", process, PRINT_OVERRIDES),
                                  ("filament", filament, None)):
            p = tmp / f"{kind}.json"
            p.write_text(json.dumps(preset(kind, name, extra)))
            paths[kind] = p
        parts = tmp / "parts"
        parts.mkdir()
        plates = layout(machine, parts)
        for i, stls in enumerate(plates, 1):
            tag = f"_plate{i}" if len(plates) > 1 else ""
            out = out_dir / f"sesame_atech_{fil}_{printer}{tag}.gcode.3mf"
            cmd = [str(CLI), "--arrange", "0", "--orient", "0", "--slice", "0",
                   "--load-settings", f"{paths['machine']};{paths['process']}",
                   "--load-filaments", str(paths["filament"]),
                   "--export-3mf", str(out), *map(str, stls)]
            r = subprocess.run(cmd, capture_output=True, text=True, cwd=tmp)
            if r.returncode != 0 or not out.exists():
                sys.exit(f"{out.name}: slicing failed ({r.returncode})\n{r.stdout[-3000:]}\n{r.stderr[-3000:]}")
            print(out, "  ", ", ".join(s.stem for s in stls))
            outs.append(out)
    return outs


if __name__ == "__main__":
    out_dir = pathlib.Path(sys.argv[1])
    out_dir.mkdir(parents=True, exist_ok=True)
    want = set(sys.argv[2:])
    for printer, fil in JOBS:
        if not want or printer in want:
            slice_one(printer, fil, out_dir)
