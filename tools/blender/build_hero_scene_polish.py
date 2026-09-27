import bpy
import math
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

import build_hero_scene as base


def recolor(material, rgb):
    material.diffuse_color = (*rgb, 1.0)
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    if bsdf is not None:
        bsdf.inputs["Base Color"].default_value = (*rgb, 1.0)


# V4 palette: lush tropical greens, earthy soil, softer distant hills.
recolor(base.MAT_GRASS, (0.18, 0.36, 0.12))
recolor(base.MAT_GRASS_2, (0.26, 0.46, 0.17))
recolor(base.MAT_SOIL, (0.28, 0.16, 0.075))
recolor(base.MAT_SOIL_LIGHT, (0.43, 0.27, 0.13))
recolor(base.MAT_WATER, (0.10, 0.39, 0.48))
recolor(base.MAT_WATER_SHALLOW, (0.25, 0.48, 0.34))
recolor(base.MAT_HILL, (0.29, 0.42, 0.27))
recolor(base.MAT_HILL_LIGHT, (0.37, 0.51, 0.33))

_original_ground = base.build_ground
_original_import = base.import_obj_template
_original_house = base.import_house
_original_foliage = base.build_foliage


def _smooth(obj):
    if obj is not None and obj.type == 'MESH':
        for poly in obj.data.polygons:
            poly.use_smooth = True


def polished_ground():
    # Wide under-bed ensures the frame never reads like a floating diorama.
    base.box(
        "ExtendedVillageGround",
        (0.0, 2.0, -0.52),
        (36.0, 30.0, 0.34),
        base.MAT_GRASS_2,
        bevel=0.28,
    )
    _original_ground()

    ground = bpy.data.objects.get("SculptedVillageGround")
    if ground is not None:
        ground.scale.x *= 1.08
        ground.scale.y *= 1.10

    # Soften and stagger the hill wall so the background has atmospheric layers,
    # not one dark polygon strip.
    hill_specs = {
        "BackHillA": ((-8.6, 8.6, 1.25), (1.15, 1.10, 0.90)),
        "BackHillB": ((0.8, 10.0, 1.55), (1.20, 1.18, 0.94)),
        "BackHillC": ((9.4, 8.9, 1.20), (1.18, 1.12, 0.90)),
    }
    for name, (location, scale) in hill_specs.items():
        hill = bpy.data.objects.get(name)
        if hill is not None:
            hill.location = location
            hill.scale = scale
            _smooth(hill)

    far_a = base.ico("FarHillA", (-10.5, 12.2, 1.1), (7.0, 3.2, 2.15), base.MAT_HILL_LIGHT, 3)
    far_b = base.ico("FarHillB", (2.0, 13.0, 1.45), (8.5, 3.8, 2.5), base.MAT_HILL_LIGHT, 3)
    far_c = base.ico("FarHillC", (12.0, 11.5, 1.0), (6.8, 3.2, 2.1), base.MAT_HILL_LIGHT, 3)
    for hill in (far_a, far_b, far_c):
        _smooth(hill)


def polished_house():
    root = _original_house()
    # House remains the hero, but now sits left/back instead of occupying half the frame.
    root.location = (-4.25, 2.85, 0.02)
    root.scale = (0.90, 0.90, 0.90)
    return root


def polished_import(asset_name):
    obj = _original_import(asset_name)
    if asset_name in ("Grass_Short", "Plant_3", "Wheat"):
        for material in obj.data.materials:
            if material is None:
                continue
            if asset_name == "Wheat":
                recolor(material, (0.34, 0.55, 0.18))
            elif asset_name == "Plant_3":
                recolor(material, (0.20, 0.43, 0.14))
            else:
                recolor(material, (0.22, 0.44, 0.15))
    return obj


def polished_path_stream_bridge(rock_t, grass_t, lilypad_t):
    # Curving path leaves the veranda and drifts right toward the bridge.
    path_pts = [
        (-4.0, 0.0), (-3.45, -1.1), (-2.55, -2.2), (-1.25, -3.3),
        (0.15, -4.15), (1.25, -4.75), (2.05, -5.35),
    ]
    base.ribbon("VillageDirtPath", path_pts, [1.0, 1.15, 1.3, 1.45, 1.45, 1.30, 1.15], base.MAT_SOIL_LIGHT, 0.03, 0.11)

    # Meandering stream instead of a ruler-straight foreground stripe.
    stream_pts = [
        (-10.8, -5.8), (-8.2, -5.15), (-5.3, -5.75), (-2.2, -5.15),
        (0.6, -5.75), (3.0, -5.25), (5.7, -5.80), (8.4, -5.1), (11.0, -5.55),
    ]
    base.ribbon("StreamBank", stream_pts, [2.9, 3.0, 2.8, 3.05, 2.95, 3.1, 2.9, 2.85, 2.7], base.MAT_SOIL, -0.07, 0.15)
    base.ribbon("StreamWater", stream_pts, [1.75, 1.95, 1.72, 2.02, 1.85, 2.06, 1.82, 1.74, 1.62], base.MAT_WATER, 0.00, 0.10)

    # Bridge is deliberately right of center: secondary focal point.
    center_x = 2.05
    for i in range(10):
        y = -6.25 + i * 0.24
        arch = math.sin(i / 9.0 * math.pi) * 0.16
        base.box(f"BridgePlank_{i}", (center_x, y, 0.31 + arch), (2.15, 0.28, 0.14), base.MAT_WOOD, bevel=0.045)
    for x in (center_x - 0.98, center_x + 0.98):
        for y in (-6.20, -5.30, -4.40):
            base.cylinder("BridgePost", (x, y, 0.86), 0.075, 1.34, base.MAT_WOOD_DARK, vertices=10, bevel=0.02)
        base.box("BridgeRailA", (x, -5.78, 1.24), (0.10, 1.02, 0.10), base.MAT_WOOD_DARK, rot=(math.radians(-10), 0, 0), bevel=0.025)
        base.box("BridgeRailB", (x, -4.86, 1.24), (0.10, 1.02, 0.10), base.MAT_WOOD_DARK, rot=(math.radians(10), 0, 0), bevel=0.025)

    rock_spots = [
        (-9.4,-5.2,0.05,0.62,10),(-7.6,-6.0,0.04,0.48,-16),(-5.3,-4.9,0.05,0.56,24),
        (-2.8,-5.9,0.04,0.46,-28),(0.1,-4.95,0.05,0.54,14),(4.3,-5.9,0.04,0.58,-22),
        (6.8,-4.9,0.05,0.50,30),(9.0,-5.9,0.04,0.46,-8),
    ]
    for idx,(x,y,z,s,r) in enumerate(rock_spots):
        base.place(rock_t, f"RiverRock_{idx}", (x,y,z), s, r)

    bank_grass = [
        (-10.0,-4.7),(-8.7,-6.25),(-7.0,-4.55),(-5.8,-6.4),(-4.0,-4.5),(-2.3,-6.25),
        (-0.8,-4.6),(0.5,-6.45),(3.9,-4.55),(5.0,-6.35),(6.6,-4.45),(8.0,-6.2),(9.6,-4.7),
    ]
    for idx,(x,y) in enumerate(bank_grass):
        base.place(grass_t, f"BankGrass_{idx}", (x,y,0.05), 0.52 + (idx%4)*0.07, idx*23)

    lilies = [(-8.1,-5.45,0.38),(-6.1,-5.55,0.31),(-3.8,-5.35,0.34),(-0.8,-5.55,0.32),(5.1,-5.45,0.34),(7.5,-5.40,0.30)]
    for idx,(x,y,s) in enumerate(lilies):
        base.place(lilypad_t, f"Lily_{idx}", (x,y,0.08), s, idx*39)


def polished_rice_fields(wheat_t, grass_t):
    # Three staggered paddies form a larger right/background farming mass.
    fields = [
        ((4.0, 1.0, 0.04), (4.5, 2.7, 0.16), -5),
        ((6.7, 3.35, 0.08), (4.6, 2.65, 0.16), 5),
        ((8.2, 5.35, 0.12), (4.2, 2.35, 0.16), -4),
    ]
    for idx,(loc,dims,rot) in enumerate(fields):
        x,y,z = loc
        w,h,_ = dims
        base.box(f"PaddyBund_{idx}", (x,y,z-0.02), (w+0.46,h+0.46,0.16), base.MAT_SOIL, rot=(0,0,math.radians(rot)), bevel=0.20)
        base.box(f"PaddyWater_{idx}", (x,y,z+0.07), (w,h,0.09), base.MAT_WATER_SHALLOW, rot=(0,0,math.radians(rot)), bevel=0.20)

        cols = 6 if idx < 2 else 5
        rows = 4
        for row in range(rows):
            for col in range(cols):
                px = x - w*0.38 + col * (w*0.76/max(1,cols-1)) + ((row % 2) * 0.08)
                py = y - h*0.34 + row * (h*0.68/max(1,rows-1))
                scale = 0.30 + ((row + col + idx) % 3) * 0.025
                base.place(wheat_t, f"Rice_{idx}_{row}_{col}", (px,py,z+0.12), scale, (row*11 + col*17 + idx*13) % 45 - 22)

    for idx,(x,y) in enumerate([(2.1,-0.2),(4.7,4.7),(6.2,5.7),(9.8,2.5),(10.0,5.7)]):
        base.place(grass_t, f"PaddyGrass_{idx}", (x,y,0.04), 0.48 + (idx%2)*0.06, idx*37)


def polished_foliage(tree_t, palm_t, bush_t, grass_t, flower_t, rock_t):
    _original_foliage(tree_t, palm_t, bush_t, grass_t, flower_t, rock_t)

    # Layered mid/background vegetation around the house and paddies.
    extra_trees = [
        (-10.2, 1.0, 0.86, 12), (-9.0, 6.1, 0.76, -22), (-6.0, 7.4, 0.68, 14),
        (5.4, 7.5, 0.68, -8), (8.1, 7.2, 0.76, 18), (10.3, 3.0, 0.74, -18),
    ]
    for idx,(x,y,s,r) in enumerate(extra_trees):
        base.place(tree_t, f"PolishTree_{idx}", (x,y,0.0), s, r)

    extra_palms = [(-8.0,3.6,0.76,22),(-5.8,6.4,0.68,-14),(7.4,6.8,0.72,-28),(9.2,4.7,0.66,18)]
    for idx,(x,y,s,r) in enumerate(extra_palms):
        base.place(palm_t, f"PolishPalm_{idx}", (x,y,0.0), s, r)

    extra_bushes = [
        (-7.2,-1.4),(-6.2,-2.0),(-5.2,-2.7),(-3.8,4.6),(-2.0,4.9),(-0.4,4.7),
        (1.1,5.0),(2.8,5.3),(4.5,5.1),(6.0,5.0),(7.5,-2.1),(8.4,-1.2),(9.2,0.2),
        (-8.8,-4.0),(-7.2,-4.4),(8.0,-4.3),(9.4,-4.0),
    ]
    for idx,(x,y) in enumerate(extra_bushes):
        base.place(bush_t, f"PolishBush_{idx}", (x,y,0.02), 0.46 + (idx%3)*0.06, idx*31)

    extra_grass = [
        (-9.4,-6.8),(-8.0,-7.0),(-6.6,-6.9),(-5.3,-7.1),(-3.8,-6.8),(-2.2,-7.0),
        (0.0,-7.1),(3.4,-7.0),(4.8,-6.8),(6.2,-7.0),(7.6,-6.7),(9.0,-7.0),
        (-6.0,3.6),(-4.8,4.0),(-2.6,3.8),(-0.8,4.1),(1.5,4.0),(3.4,4.2),(5.5,4.0),
    ]
    for idx,(x,y) in enumerate(extra_grass):
        base.place(grass_t, f"PolishGrass_{idx}", (x,y,0.03), 0.48 + (idx%4)*0.055, idx*19)

    extra_flowers = [(-6.1,-2.3),(-5.3,-2.7),(-3.0,-1.8),(2.0,-2.0),(3.0,-2.4),(4.5,-2.2),(6.0,-2.5)]
    for idx,(x,y) in enumerate(extra_flowers):
        base.place(flower_t, f"PolishFlower_{idx}", (x,y,0.03), 0.42 + (idx%2)*0.06, idx*43)

    # Foreground framing. These are intentionally near the camera edges and partly cropped.
    base.place(bush_t, "ForegroundBushL", (-10.4,-7.4,0.04), 0.92, -18)
    base.place(grass_t, "ForegroundGrassL", (-9.3,-7.6,0.04), 0.88, 22)
    base.place(bush_t, "ForegroundBushR", (9.9,-7.3,0.04), 0.86, 16)
    base.place(grass_t, "ForegroundGrassR", (8.9,-7.6,0.04), 0.92, -28)
    base.place(rock_t, "ForegroundRockL", (-8.0,-7.2,0.04), 0.62, 18)
    base.place(rock_t, "ForegroundRockR", (7.8,-7.15,0.04), 0.58, -21)


base.build_ground = polished_ground
base.import_house = polished_house
base.import_obj_template = polished_import
base.build_path_stream_bridge = polished_path_stream_bridge
base.build_rice_fields = polished_rice_fields
base.build_foliage = polished_foliage
base.main()
