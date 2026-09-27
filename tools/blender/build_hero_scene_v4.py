import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

# build_hero_scene_polish historically calls base.main() at module import time.
# Suppress that import side-effect so this file builds exactly once after all
# composition overrides are installed.
import build_hero_scene as base
_real_main = base.main
base.main = lambda: None
import build_hero_scene_polish as polish
base.main = _real_main

_old_ground = base.build_ground
_old_rice = base.build_rice_fields
_old_foliage = base.build_foliage

MAT_HILL_HAZE = base.mat("Distant Haze Hill", (0.48, 0.57, 0.42), 0.98)
MAT_HILL_MID = base.mat("Mid Haze Hill", (0.38, 0.49, 0.32), 0.98)


def _smooth(obj):
    if obj is not None and obj.type == 'MESH':
        for poly in obj.data.polygons:
            poly.use_smooth = True


def v5_ground():
    _old_ground()

    # The previous large stretched icospheres read as giant capsules. Hide them and
    # rebuild the horizon from overlapping smaller ridges in two atmospheric layers.
    for name in ("BackHillA", "BackHillB", "BackHillC", "FarHillA", "FarHillB", "FarHillC"):
        obj = base.bpy.data.objects.get(name)
        if obj is not None:
            obj.hide_render = True

    back_ridges = [
        (-11.5, 14.8, 1.0, 4.2, 2.9, 1.45),
        (-6.7, 15.4, 1.3, 4.7, 3.1, 1.65),
        (-1.5, 14.9, 1.15, 4.3, 3.0, 1.50),
        (3.4, 15.5, 1.35, 4.8, 3.2, 1.70),
        (8.7, 14.8, 1.10, 4.4, 2.9, 1.50),
        (13.2, 15.2, 0.95, 3.8, 2.7, 1.35),
    ]
    for i, (x, y, z, sx, sy, sz) in enumerate(back_ridges):
        hill = base.ico(f"HazeRidge_{i}", (x, y, z), (sx, sy, sz), MAT_HILL_HAZE, 3)
        _smooth(hill)

    mid_ridges = [
        (-9.5, 11.9, 0.65, 3.2, 2.4, 1.25),
        (-5.2, 12.2, 0.80, 3.8, 2.6, 1.45),
        (-0.8, 11.8, 0.70, 3.5, 2.4, 1.30),
        (3.6, 12.1, 0.82, 3.8, 2.6, 1.45),
        (8.0, 11.6, 0.65, 3.3, 2.3, 1.25),
        (11.8, 12.0, 0.58, 3.0, 2.2, 1.15),
    ]
    for i, (x, y, z, sx, sy, sz) in enumerate(mid_ridges):
        hill = base.ico(f"MidRidge_{i}", (x, y, z), (sx, sy, sz), MAT_HILL_MID, 3)
        _smooth(hill)


def v4_rice(wheat_t, grass_t):
    _old_rice(wheat_t, grass_t)
    # Additional staggered terraces push the rice landscape deeper into right background.
    terraces = [
        ((6.8, 5.7, 0.07), (4.6, 1.45, 0.10), -8),
        ((4.9, 7.0, 0.13), (4.0, 1.25, 0.10), 7),
        ((8.4, 7.2, 0.18), (3.0, 1.10, 0.10), -4),
    ]
    for i, (loc, dims, rot) in enumerate(terraces):
        base.box(
            f"V4Paddy_{i}", loc, dims, base.MAT_WATER_SHALLOW,
            rot=(0, 0, base.math.radians(rot)), bevel=0.28,
        )
        x, y, z = loc
        w, h, _ = dims
        for yy in (-h * 0.5, h * 0.5):
            base.box(
                "V4Bund", (x, y + yy, z + 0.09), (w + 0.3, 0.22, 0.22),
                base.MAT_SOIL_LIGHT, rot=(0, 0, base.math.radians(rot)), bevel=0.09,
            )
        for row in range(2):
            for col in range(max(3, int(w / 0.72))):
                base.place(
                    wheat_t,
                    f"V4Rice_{i}_{row}_{col}",
                    (x - w * 0.36 + col * 0.65, y - h * 0.22 + row * 0.52, z + 0.15),
                    0.29 + (col % 2) * 0.025,
                    (i * 19 + row * 11 + col * 13) % 43,
                )


def v4_foliage(tree_t, palm_t, bush_t, grass_t, flower_t, rock_t):
    _old_foliage(tree_t, palm_t, bush_t, grass_t, flower_t, rock_t)
    # Foreground side framing; center stays open to preserve path -> bridge -> paddy sightline.
    trees = [
        (-10.8, -2.0, 0.92, 15), (-10.2, 1.7, 0.78, -18),
        (10.4, -1.7, 0.82, 22), (10.6, 2.0, 0.72, -25),
    ]
    palms = [(-9.0, 4.0, 0.78, 18), (9.2, 4.3, 0.74, -22)]
    for i, (x, y, s, r) in enumerate(trees):
        base.place(tree_t, f"V4Tree_{i}", (x, y, 0), s, r)
    for i, (x, y, s, r) in enumerate(palms):
        base.place(palm_t, f"V4Palm_{i}", (x, y, 0), s, r)
    for i, (x, y) in enumerate([
        (-7, -2.8), (-6.2, -3.0), (-5.4, -3.2), (3.5, -3.0), (4.5, -3.2),
        (5.5, -3.0), (7, -2.8), (-2, 5.7), (0, 5.9), (2, 5.8),
    ]):
        base.place(bush_t, f"V4Bush_{i}", (x, y, 0.02), 0.48 + (i % 3) * 0.05, i * 27)
    for i, (x, y) in enumerate([
        (-7.8, -3.5), (-6.7, -3.8), (-5.7, -3.7), (2.5, -3.8),
        (3.6, -3.6), (4.8, -3.8), (6, -3.6), (7.3, -3.7),
    ]):
        base.place(grass_t, f"V4Grass_{i}", (x, y, 0.03), 0.48 + (i % 3) * 0.05, i * 21)


base.build_ground = v5_ground
base.build_rice_fields = v4_rice
base.build_foliage = v4_foliage
base.main()
