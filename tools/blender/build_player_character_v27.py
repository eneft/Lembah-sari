import bpy
import math
import os

# V2.7 refinement layer over the stable V2.6 builder.
# V2.6 constructs a complete character; this pass reshapes the most visible
# concept mismatches before the final GLB export.

BASE = os.path.join(os.path.dirname(__file__), "build_player_character_v26.py")
exec(compile(open(BASE, "r", encoding="utf-8").read(), BASE, "exec"), globals(), globals())


def remove_obj(name):
    obj = bpy.data.objects.get(name)
    if obj is None:
        return
    data = obj.data if hasattr(obj, "data") else None
    bpy.data.objects.remove(obj, do_unlink=True)
    if data is not None and getattr(data, "users", 1) == 0:
        try:
            if data.__class__.__name__.endswith("Mesh"):
                bpy.data.meshes.remove(data)
        except Exception:
            pass


def set_mat_color(mat, rgb):
    mat.diffuse_color = (*rgb, 1.0)
    if mat.use_nodes:
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs["Base Color"].default_value = (*rgb, 1.0)


# 1) Softer tapered chin and lower cheeks: closer to the approved concept.
head = bpy.data.objects.get("Head")
if head and head.type == "MESH":
    for v in head.data.vertices:
        z = v.co.z
        if z < 1.50:
            t = max(0.0, min(1.0, (z - 1.40) / 0.10))
            factor = 0.78 + 0.18 * t
            v.co.x *= factor
        elif z < 1.55:
            v.co.x *= 0.97

# Bring ears slightly inward so they do not read as round side discs.
for side in (-1, 1):
    ear = bpy.data.objects.get(f"Ear_{side}")
    if ear:
        ear.location.x *= 0.94
        ear.scale *= 0.92

# 2) Eyes: reduce visible ivory ring and let the dark iris dominate.
for side in (-1, 1):
    white = bpy.data.objects.get(f"EyeWhite_{side}")
    iris = bpy.data.objects.get(f"Iris_{side}")
    pupil = bpy.data.objects.get(f"Pupil_{side}")
    if white:
        white.scale.x *= 0.93
        white.scale.z *= 0.94
    if iris:
        iris.scale.x *= 1.06
        iris.scale.z *= 1.04
    if pupil:
        pupil.scale.x *= 0.96
        pupil.scale.z *= 0.98

# 3) Replace sausage-like fringe with fewer, broader swept locks.
for name in [
    "FringeOuterL", "FringeHeavyL", "FringeCenter", "FringeRight",
    "HairTopL", "HairTopC", "HairTopR", "SideLockL", "SideLockR",
    "BackLayerL", "BackLayerR"
]:
    remove_obj(name)

# Broad layered crown, swept from character-left to right.
hair_blob("CrownMassL", (-0.080, 0.000, 1.768), (0.138, 0.092, 0.072),
          (math.radians(-9), math.radians(-13), math.radians(-24)), True)
hair_blob("CrownMassR", (0.065, 0.008, 1.755), (0.125, 0.088, 0.068),
          (math.radians(-7), math.radians(13), math.radians(25)), False)
hair_blob("CrownSweep", (-0.010, -0.020, 1.805), (0.128, 0.078, 0.060),
          (math.radians(-8), math.radians(8), math.radians(8)), True)

# The concept has one dominant left sweep, a center lock, then an open right forehead.
hair_blob("BangSweepL", (-0.112, -0.118, 1.695), (0.078, 0.045, 0.142),
          (math.radians(16), math.radians(-7), math.radians(-19)), True)
hair_blob("BangSweepCenter", (-0.045, -0.137, 1.705), (0.070, 0.041, 0.132),
          (math.radians(13), math.radians(2), math.radians(-5)), False)
hair_blob("BangShortR", (0.050, -0.125, 1.712), (0.052, 0.038, 0.090),
          (math.radians(10), math.radians(8), math.radians(24)), True)

# Sideburns are narrow and tucked around the ears.
hair_blob("TempleSoftL", (-0.176, -0.025, 1.642), (0.036, 0.034, 0.082),
          (math.radians(3), 0.0, math.radians(-8)), False)
hair_blob("TempleSoftR", (0.174, -0.018, 1.653), (0.033, 0.032, 0.072),
          (math.radians(3), 0.0, math.radians(10)), False)

# 4) Rolled trouser cuffs are lighter like the concept art fabric turn-up.
set_mat_color(OVERALL_CUFF, (0.46, 0.40, 0.29))

# Add a readable cargo pocket on the outer left thigh.
patch("CargoPocketV27", [
    (-0.229, 0.745), (-0.154, 0.740), (-0.151, 0.625),
    (-0.162, 0.602), (-0.222, 0.606), (-0.232, 0.630),
], -0.040, OVERALL_DARK, 0.010, 0.006)
ico("CargoButtonV27", (-0.188, -0.054, 0.724), (0.012, 0.005, 0.012), BRASS, 2)

# 5) Boots: reduce the brick-like sole profile, keep chunky rounded toes.
for side in (-1, 1):
    sole = bpy.data.objects.get(f"BootSole_{side}")
    toe = bpy.data.objects.get(f"BootToe_{side}")
    shaft = bpy.data.objects.get(f"BootShaft_{side}")
    if sole:
        sole.scale.x *= 0.92
        sole.scale.y *= 0.91
        sole.scale.z *= 0.58
        sole.location.z += 0.010
    if toe:
        toe.scale.x *= 1.02
        toe.scale.y *= 1.03
        toe.location.z += 0.006
    if shaft:
        shaft.scale.x *= 0.96

# 6) Hands: slightly flatter palm depth and a touch larger vertically.
for side in (-1, 1):
    palm = bpy.data.objects.get(f"Palm_{side}")
    thumb = bpy.data.objects.get(f"Thumb_{side}")
    if palm:
        palm.scale.y *= 0.86
        palm.scale.z *= 1.05
    if thumb:
        thumb.scale *= 0.92

# 7) Backpack: rounder and a fraction wider, as in the hero concept.
pack = bpy.data.objects.get("Backpack")
flap = bpy.data.objects.get("BackpackFlap")
if pack:
    pack.scale.x *= 1.05
    pack.scale.z *= 1.03
if flap:
    flap.scale.x *= 1.04

# Re-export after refinements.
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
print(f"Exported Lembah Sari Character Rework V2.7 to {OUT_PATH}")
