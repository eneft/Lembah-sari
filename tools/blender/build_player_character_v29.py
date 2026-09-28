import bpy
import math
import os

# V2.9 polish layer over V2.8.
# Focus: asymmetric hero fringe, warmer face read, gear detail and less toy-like extremities.

BASE = os.path.join(os.path.dirname(__file__), "build_player_character_v28.py")
exec(compile(open(BASE, "r", encoding="utf-8").read(), BASE, "exec"), globals(), globals())


def remove_obj(name):
    obj = bpy.data.objects.get(name)
    if obj:
        bpy.data.objects.remove(obj, do_unlink=True)


# -----------------------------------------------------------------------------
# HERO HAIR — a dominant diagonal sweep like the approved concept sheet.
# -----------------------------------------------------------------------------
for name in [
    "ConceptBangLeft", "ConceptBangCenter", "ConceptBangRight",
    "ConceptTopLeft", "ConceptTopCenter", "ConceptTopRight"
]:
    remove_obj(name)

path_lock(
    "HeroFringeOuterL",
    [(-0.155, -0.040, 1.790), (-0.168, -0.095, 1.748), (-0.160, -0.142, 1.690)],
    [(0.058, 0.042), (0.050, 0.037), (0.038, 0.029)],
    (-0.150, -0.180, 1.595), HAIR,
)
path_lock(
    "HeroFringeSweep",
    [(-0.105, -0.052, 1.815), (-0.070, -0.102, 1.778), (-0.025, -0.140, 1.730)],
    [(0.082, 0.051), (0.070, 0.046), (0.053, 0.037)],
    (0.050, -0.183, 1.630), HAIR_WARM,
)
path_lock(
    "HeroFringeShortR",
    [(0.050, -0.045, 1.805), (0.088, -0.088, 1.770), (0.110, -0.125, 1.728)],
    [(0.052, 0.039), (0.044, 0.034), (0.032, 0.026)],
    (0.142, -0.165, 1.665), HAIR,
)

# Low sideways crown sweep plus a small playful tuft.
path_lock(
    "HeroTopSweep",
    [(-0.095, 0.020, 1.815), (-0.025, 0.016, 1.850), (0.045, 0.010, 1.852)],
    [(0.060, 0.043), (0.052, 0.039), (0.040, 0.031)],
    (0.125, -0.003, 1.820), HAIR_WARM,
)
path_lock(
    "HeroTopTuft",
    [(-0.010, 0.010, 1.842), (0.012, 0.003, 1.872), (0.032, -0.004, 1.885)],
    [(0.036, 0.029), (0.030, 0.025), (0.022, 0.019)],
    (0.055, -0.012, 1.878), HAIR,
)

# -----------------------------------------------------------------------------
# FACE / SCARF polish.
# -----------------------------------------------------------------------------
smile = bpy.data.objects.get("Smile")
if smile:
    smile.scale.x *= 1.08

knot = bpy.data.objects.get("ScarfKnot")
if knot:
    knot.scale.x *= 1.15
    knot.scale.z *= 1.08
for name in ["ScarfTailL", "ScarfTailR"]:
    obj = bpy.data.objects.get(name)
    if obj:
        obj.scale.z *= 1.08

# Hands read slightly more like stylized palms than beads.
for side in (-1, 1):
    palm = bpy.data.objects.get(f"Palm_{side}")
    thumb = bpy.data.objects.get(f"Thumb_{side}")
    if palm:
        palm.scale.x *= 1.08
        palm.scale.z *= 1.06
        palm.location.y -= 0.006
    if thumb:
        thumb.scale.z *= 1.05

# -----------------------------------------------------------------------------
# BOOTS — add a raised tongue and top rim to support the lace silhouette.
# -----------------------------------------------------------------------------
for side in (-1, 1):
    s = float(side)
    x = 0.112 * s
    rounded_box(f"BootTongue_{side}", (x, -0.165, 0.240), (0.090, 0.022, 0.185), BOOT_EDGE, 0.015)
    curve(f"BootTopRim_{side}", [(x-0.063, -0.085, 0.350), (x, -0.105, 0.360), (x+0.063, -0.085, 0.350)], BOOT_EDGE, 0.005)

# -----------------------------------------------------------------------------
# OVERALL seams — tiny details that make the clothing read as constructed fabric.
# -----------------------------------------------------------------------------
for side in (-1, 1):
    s = float(side)
    curve(f"TrouserSeam_{side}", [(0.115*s, -0.109, 0.810), (0.112*s, -0.112, 0.620), (0.108*s, -0.108, 0.430)], OVERALL_DARK, 0.0035)

curve("BibTopSeam", [(-0.085, -0.164, 1.280), (0.0, -0.169, 1.274), (0.085, -0.164, 1.280)], OVERALL_DARK, 0.0035)

# -----------------------------------------------------------------------------
# BACKPACK — flap buckles + side pouch for the explorer silhouette.
# -----------------------------------------------------------------------------
for side in (-1, 1):
    s = float(side)
    curve(f"BackpackFlapStrap_{side}", [(0.075*s, 0.285, 1.270), (0.075*s, 0.290, 1.190), (0.075*s, 0.292, 1.125)], BAG, 0.007)
    ico(f"BackpackFlapBuckle_{side}", (0.075*s, 0.298, 1.180), (0.016, 0.006, 0.019), BRASS, 2)
rounded_box("BackpackSidePouch", (0.162, 0.185, 1.015), (0.060, 0.118, 0.165), BAG_EDGE, 0.025)

# Re-export final V2.9 review asset.
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
print(f"Exported Lembah Sari Character Rework V2.9 to {OUT_PATH}")
