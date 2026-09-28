import bpy
import math
import os
from mathutils import Vector

# Lembah Sari Character V3.1 — final concept polish.
# Keep V3.0 proportions, refine palette, sleeves, hair layering and gear read.

BASE = os.path.join(os.path.dirname(__file__), "build_player_character_v30.py")
exec(compile(open(BASE, "r", encoding="utf-8").read(), BASE, "exec"), globals(), globals())


def remove_obj(name):
    obj = bpy.data.objects.get(name)
    if obj:
        bpy.data.objects.remove(obj, do_unlink=True)


def recolor(mat, rgb):
    mat.diffuse_color = (*rgb, 1.0)
    if mat.use_nodes:
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs["Base Color"].default_value = (*rgb, 1.0)


# -----------------------------------------------------------------------------
# PALETTE — closer to the approved concept sheet under the current Godot light.
# -----------------------------------------------------------------------------
recolor(SHIRT, (0.44, 0.37, 0.265))
recolor(SHIRT_SHADOW, (0.35, 0.285, 0.195))
recolor(OVERALL, (0.078, 0.096, 0.038))
recolor(OVERALL_DARK, (0.046, 0.058, 0.020))
recolor(OVERALL_CUFF, (0.34, 0.285, 0.205))
recolor(SCARF, (0.305, 0.072, 0.024))
recolor(BOOT, (0.032, 0.010, 0.004))
recolor(BOOT_EDGE, (0.066, 0.020, 0.007))
recolor(BAG, (0.070, 0.025, 0.009))
recolor(BAG_EDGE, (0.125, 0.045, 0.015))
recolor(HAIR, (0.021, 0.006, 0.0025))
recolor(HAIR_WARM, (0.045, 0.012, 0.004))

# -----------------------------------------------------------------------------
# SLEEVES — replace stiff straight tapered upper sleeves with soft puffy forms.
# Keep forearms/hands from V3.0.
# -----------------------------------------------------------------------------
for side in (-1, 1):
    remove_obj(f"Sleeve_{side}")
    remove_obj(f"RolledSleeve_{side}")

for side in (-1, 1):
    s = float(side)
    # Upper sleeve follows a gentle A-pose and has the soft volume of rolled linen.
    uv(
        f"Sleeve_{side}",
        (0.218 * s, -0.012, 1.185),
        (0.080, 0.066, 0.145),
        SHIRT,
        24,
        14,
        rot=(0.0, math.radians(13.0 * s), 0.0),
    )
    uv(
        f"RolledSleeve_{side}",
        (0.246 * s, -0.027, 1.052),
        (0.073, 0.060, 0.045),
        SHIRT_SHADOW,
        22,
        12,
        rot=(0.0, math.radians(11.0 * s), 0.0),
    )
    # Thin seam where the roll meets the forearm.
    curve(
        f"SleeveFold_{side}",
        [
            (0.205 * s, -0.082, 1.055),
            (0.246 * s, -0.091, 1.046),
            (0.285 * s, -0.080, 1.055),
        ],
        SHIRT_SHADOW,
        0.0035,
    )

# -----------------------------------------------------------------------------
# HAIR — keep the V2.9/V3.0 hero fringe but add subtle layered breakup.
# -----------------------------------------------------------------------------
path_lock(
    "V31TempleLayerL",
    [(-0.145, -0.015, 1.760), (-0.177, -0.038, 1.725), (-0.184, -0.065, 1.690)],
    [(0.032, 0.027), (0.027, 0.023), (0.021, 0.018)],
    (-0.185, -0.082, 1.650),
    HAIR_WARM,
)
path_lock(
    "V31TempleLayerR",
    [(0.146, -0.005, 1.748), (0.175, -0.027, 1.718), (0.180, -0.052, 1.688)],
    [(0.030, 0.025), (0.025, 0.021), (0.019, 0.017)],
    (0.178, -0.075, 1.655),
    HAIR,
)
path_lock(
    "V31TopAccent",
    [(-0.035, 0.005, 1.865), (-0.005, -0.002, 1.893)],
    [(0.026, 0.021), (0.019, 0.016)],
    (0.026, -0.010, 1.888),
    HAIR_WARM,
)

# -----------------------------------------------------------------------------
# CLOTHING DETAILS — modest seams/folds, no noisy PBR.
# -----------------------------------------------------------------------------
curve(
    "BibCenterStitch",
    [(0.0, -0.172, 1.255), (0.0, -0.174, 1.165), (0.0, -0.171, 1.085)],
    OVERALL_DARK,
    0.0028,
)
for side in (-1, 1):
    s = float(side)
    curve(
        f"KneeFold_{side}",
        [(0.072 * s, -0.115, 0.610), (0.112 * s, -0.123, 0.595), (0.150 * s, -0.112, 0.603)],
        OVERALL_DARK,
        0.0028,
    )

# -----------------------------------------------------------------------------
# BOOTS — slightly more concept-like sole and lace visibility.
# -----------------------------------------------------------------------------
for side in (-1, 1):
    s = float(side)
    sole = bpy.data.objects.get(f"BootSole_{side}")
    if sole:
        sole.scale.y *= 1.035
        sole.scale.z *= 0.86
    for i in range(3):
        lace = bpy.data.objects.get(f"BootLace_{side}_{i}")
        if lace:
            lace.scale *= 1.05
    curve(
        f"BootToeSeam_{side}",
        [
            (0.112 * s - 0.058, -0.194, 0.145),
            (0.112 * s, -0.207, 0.154),
            (0.112 * s + 0.058, -0.194, 0.145),
        ],
        BOOT,
        0.0038,
    )

# -----------------------------------------------------------------------------
# BACKPACK — retain V2.9 details and add soft side strap read.
# -----------------------------------------------------------------------------
for side in (-1, 1):
    s = float(side)
    curve(
        f"PackSideBinding_{side}",
        [(0.145 * s, 0.250, 1.250), (0.154 * s, 0.270, 1.105), (0.145 * s, 0.252, 0.960)],
        BAG_EDGE,
        0.005,
    )

# Final V3.1 export.
bpy.ops.object.select_all(action="DESELECT")
ROOT.select_set(True)
for obj in ROOT.children_recursive:
    obj.select_set(True)
bpy.context.view_layer.objects.active = ROOT
bpy.ops.export_scene.gltf(
    filepath=OUT_PATH,
    export_format="GLB",
    use_selection=True,
    export_apply=True,
    export_yup=True,
)
print(f"Exported Lembah Sari Character V3.1 final concept polish to {OUT_PATH}")
