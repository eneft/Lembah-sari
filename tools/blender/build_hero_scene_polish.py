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


# Deeper cozy palette; the first full-scene render was too washed-out.
recolor(base.MAT_GRASS, (0.22, 0.40, 0.15))
recolor(base.MAT_GRASS_2, (0.34, 0.53, 0.21))
recolor(base.MAT_SOIL, (0.31, 0.18, 0.085))
recolor(base.MAT_SOIL_LIGHT, (0.46, 0.29, 0.14))
recolor(base.MAT_WATER, (0.12, 0.42, 0.50))
recolor(base.MAT_WATER_SHALLOW, (0.30, 0.52, 0.38))
recolor(base.MAT_HILL, (0.15, 0.30, 0.15))
recolor(base.MAT_HILL_LIGHT, (0.22, 0.39, 0.19))

_original_ground = base.build_ground
_original_import = base.import_obj_template
_original_foliage = base.build_foliage


def polished_ground():
    # Large under-bed removes the floating-diorama edge from the hero camera.
    base.box(
        "ExtendedVillageGround",
        (0.0, 2.2, -0.48),
        (31.0, 25.0, 0.28),
        base.MAT_GRASS_2,
        bevel=0.22,
    )
    _original_ground()


def polished_import(asset_name):
    obj = _original_import(asset_name)
    # Tight palette correction for small vegetation assets. Keep trees/palms/rocks
    # on their original multi-material CC0 palette so trunks and leaves remain distinct.
    if asset_name in ("Grass_Short", "Plant_3", "Wheat"):
        for material in obj.data.materials:
            if material is None:
                continue
            if asset_name == "Wheat":
                recolor(material, (0.38, 0.58, 0.20))
            elif asset_name == "Plant_3":
                recolor(material, (0.25, 0.48, 0.18))
            else:
                recolor(material, (0.28, 0.50, 0.20))
    return obj


def polished_foliage(tree_t, palm_t, bush_t, grass_t, flower_t, rock_t):
    _original_foliage(tree_t, palm_t, bush_t, grass_t, flower_t, rock_t)

    extra_trees = [
        (-9.8, 1.2, 0.82, 12), (-8.8, 5.8, 0.74, -22),
        (7.2, 7.0, 0.78, 18), (10.0, 3.0, 0.72, -18),
    ]
    for idx, (x, y, s, r) in enumerate(extra_trees):
        base.place(tree_t, f"PolishTree_{idx}", (x, y, 0.0), s, r)

    extra_palms = [(-7.6, 3.7, 0.74, 22), (8.8, 4.7, 0.70, -28)]
    for idx, (x, y, s, r) in enumerate(extra_palms):
        base.place(palm_t, f"PolishPalm_{idx}", (x, y, 0.0), s, r)

    extra_bushes = [
        (-6.6,-1.1),(-5.8,-1.7),(-4.8,-2.6),(-3.5,4.7),(-1.8,4.9),
        (1.0,5.0),(3.0,5.2),(4.8,5.0),(6.4,4.9),(7.5,-2.2),(8.2,-1.4),
    ]
    for idx, (x, y) in enumerate(extra_bushes):
        base.place(bush_t, f"PolishBush_{idx}", (x, y, 0.02), 0.46 + (idx % 3) * 0.06, idx * 31)

    extra_grass = [
        (-8.7,-3.7),(-7.5,-4.0),(-6.2,-3.5),(-5.0,-3.8),(-3.8,-4.0),
        (1.2,-4.1),(2.6,-3.8),(4.0,-4.0),(5.4,-3.6),(6.8,-3.9),
        (-5.4,3.5),(-4.3,4.0),(-1.5,3.7),(0.0,4.1),(2.0,4.0),(4.0,4.2),(6.0,4.0),
    ]
    for idx, (x, y) in enumerate(extra_grass):
        base.place(grass_t, f"PolishGrass_{idx}", (x, y, 0.03), 0.46 + (idx % 4) * 0.055, idx * 19)

    extra_flowers = [(-5.0,-2.3),(-4.4,-2.6),(-2.3,-1.7),(2.7,-2.2),(3.4,-2.0),(5.1,-2.4)]
    for idx, (x, y) in enumerate(extra_flowers):
        base.place(flower_t, f"PolishFlower_{idx}", (x, y, 0.03), 0.42 + (idx % 2) * 0.06, idx * 43)


base.build_ground = polished_ground
base.import_obj_template = polished_import
base.build_foliage = polished_foliage
base.main()
