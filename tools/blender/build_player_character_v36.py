import bpy
import math
import os
from mathutils import Vector

# Lembah Sari Character V3.6 — corrective reset from stable V3.4.
# V3.5 over-separated the hair and exposed scalp. V3.6 keeps a continuous cap,
# then overlays a small number of broad pointed clumps. Face and hands are tuned
# for readability at gameplay scale rather than micro-detail.

BASE = os.path.join(os.path.dirname(__file__), "build_player_character_v34.py")
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


def pointed_lock(name, rings, mat, segments=26):
    return profile(name, rings, mat, segments)


# Warmer, calmer palette closer to approved concept art.
recolor(SKIN, (0.84, 0.53, 0.35))
recolor(BLUSH, (0.78, 0.29, 0.20))
recolor(SHIRT, (0.70, 0.63, 0.50))

# -----------------------------------------------------------------------------
# FACE — keep V3.4 head volume, simplify facial linework and restore sclera.
# -----------------------------------------------------------------------------
for name in ["UpperLidL", "UpperLidR", "BrowL", "BrowR", "Nose", "Smile"]:
    remove_obj(name)

# Make whites visibly larger than iris — key difference from toy/dot eyes.
for side in (-1, 1):
    white = bpy.data.objects.get(f"EyeWhite_{side}")
    iris = bpy.data.objects.get(f"Iris_{side}")
    pupil = bpy.data.objects.get(f"Pupil_{side}")
    glint = bpy.data.objects.get(f"EyeGlint_{side}")
    if white:
        white.scale.x *= 1.22
        white.scale.z *= 1.14
        white.location.y -= 0.004
    if iris:
        iris.scale.x *= 0.82
        iris.scale.z *= 0.88
        iris.location.y -= 0.007
    if pupil:
        pupil.scale.x *= 0.88
        pupil.scale.z *= 0.90
        pupil.location.y -= 0.009
    if glint:
        glint.scale *= 1.10
        glint.location.y -= 0.010

# Brows are strong but simple and sit clearly above the eye, matching concept.
curve("BrowL", [(-0.122, -0.172, 1.809), (-0.078, -0.179, 1.824), (-0.034, -0.173, 1.818)], HAIR, 0.0070)
curve("BrowR", [(0.034, -0.173, 1.818), (0.078, -0.179, 1.824), (0.122, -0.172, 1.809)], HAIR, 0.0070)

# Nose stays almost flush; mouth slightly wider and lower for a friendly expression.
uv("Nose", (0.0, -0.176, 1.655), (0.0075, 0.0035, 0.0075), SKIN, 16, 8)
curve("Smile", [(-0.052, -0.175, 1.603), (-0.026, -0.181, 1.592), (0.0, -0.183, 1.590), (0.027, -0.181, 1.594), (0.052, -0.174, 1.606)], MOUTH, 0.0035)

# Slightly larger ears are part of the concept's friendly silhouette.
for side in (-1, 1):
    ear = bpy.data.objects.get(f"Ear_{side}")
    if ear:
        ear.scale.x *= 1.10
        ear.scale.z *= 1.08

# -----------------------------------------------------------------------------
# HANDS + ARM RELATION — larger hand silhouette, short readable fingers.
# -----------------------------------------------------------------------------
for side in (-1, 1):
    s = float(side)
    old = bpy.data.objects.get(f"Palm_{side}")
    p = old.matrix_world.translation.copy() if old else Vector((0.205*s, -0.068, 0.720))

    # Slightly shorten visual forearm and narrow sleeve so hand is not swallowed.
    for prefix, xy in (("Sleeve", 0.90), ("RolledSleeve", 0.92), ("Forearm", 0.92)):
        obj = bpy.data.objects.get(f"{prefix}_{side}")
        if obj:
            obj.scale.x *= xy
            obj.scale.y *= xy
            obj.location.x *= 0.96

    for name in [f"Palm_{side}", f"Thumb_{side}", f"ThumbTip_{side}"]:
        remove_obj(name)
    for i in range(4):
        remove_obj(f"FingerGroove_{side}_{i}")
        remove_obj(f"Finger_{side}_{i}")
        remove_obj(f"FingerTip_{side}_{i}")

    # Fuller rounded palm.
    profile(f"Palm_{side}", [
        (p.z + 0.048, 0.033, 0.026, p.x, p.y),
        (p.z + 0.020, 0.040, 0.030, p.x, p.y),
        (p.z - 0.014, 0.041, 0.031, p.x, p.y),
        (p.z - 0.035, 0.036, 0.027, p.x, p.y - 0.002),
    ], SKIN, 26)

    # Four short, thick, tightly grouped fingers — readable but not claw-like.
    offsets = (-0.024, -0.008, 0.008, 0.024)
    lengths = (0.031, 0.038, 0.037, 0.029)
    for i, (off, length) in enumerate(zip(offsets, lengths)):
        x = p.x + off
        z0 = p.z - 0.028
        z1 = z0 - length
        tapered(f"Finger_{side}_{i}", (x, p.y - 0.001, z0), (x, p.y - 0.004, z1), 0.0115, 0.0100, SKIN, 18, 0.0035)
        uv(f"FingerTip_{side}_{i}", (x, p.y - 0.004, z1), (0.0100, 0.0105, 0.0105), SKIN, 16, 10)

    thumb_a = Vector((p.x + 0.031*s, p.y - 0.002, p.z + 0.010))
    thumb_b = Vector((p.x + 0.052*s, p.y - 0.010, p.z - 0.018))
    tapered(f"Thumb_{side}", thumb_a, thumb_b, 0.0135, 0.0105, SKIN, 18, 0.0035)
    uv(f"ThumbTip_{side}", tuple(thumb_b), (0.0105, 0.0110, 0.0110), SKIN, 16, 10)

# -----------------------------------------------------------------------------
# HAIR — continuous cap first, then a few broad pointed clumps. No scalp gaps.
# -----------------------------------------------------------------------------
for name in [
    "HairBack", "V34FringeLeftOuter", "V34FringeHeroSweep", "V34FringeCenter", "V34FringeRight",
    "V34TempleL", "V34TempleR", "V34CrownLeft", "V34CrownMid", "V34CrownRight",
    "V34TuftHero", "V34BackL", "V34BackR",
]:
    remove_obj(name)

# The cap fully covers the top/front scalp. Flattened slightly in depth to avoid helmet bulk.
uv("HairBack", (0.0, 0.018, 1.812), (0.222, 0.190, 0.183), HAIR, 40, 22)

# Front fringe. Broad roots overlap the cap; tips land around forehead/brow, not eyes.
pointed_lock("V36FringeL", [
    (1.748, 0.009, 0.008, -0.125, -0.166),
    (1.790, 0.040, 0.025, -0.132, -0.158),
    (1.842, 0.066, 0.034, -0.126, -0.142),
    (1.895, 0.076, 0.040, -0.100, -0.116),
    (1.938, 0.058, 0.035, -0.062, -0.090),
    (1.960, 0.012, 0.009, -0.028, -0.072),
], HAIR, 26)
pointed_lock("V36FringeHero", [
    (1.760, 0.009, 0.008, -0.025, -0.174),
    (1.804, 0.045, 0.027, -0.030, -0.163),
    (1.858, 0.073, 0.036, -0.032, -0.145),
    (1.910, 0.082, 0.041, -0.020, -0.116),
    (1.950, 0.060, 0.035, 0.012, -0.090),
    (1.970, 0.012, 0.009, 0.045, -0.072),
], HAIR_WARM, 26)
pointed_lock("V36FringeR", [
    (1.775, 0.009, 0.008, 0.085, -0.166),
    (1.815, 0.038, 0.024, 0.090, -0.156),
    (1.865, 0.060, 0.032, 0.092, -0.138),
    (1.912, 0.064, 0.034, 0.104, -0.111),
    (1.946, 0.045, 0.028, 0.132, -0.088),
    (1.962, 0.010, 0.008, 0.156, -0.073),
], HAIR, 24)

# Side locks frame ears and taper to real points.
pointed_lock("V36SideL", [
    (1.655, 0.009, 0.008, -0.199, -0.067),
    (1.705, 0.031, 0.023, -0.207, -0.058),
    (1.770, 0.045, 0.031, -0.205, -0.036),
    (1.830, 0.048, 0.033, -0.192, -0.008),
    (1.858, 0.010, 0.008, -0.170, 0.008),
], HAIR, 22)
pointed_lock("V36SideR", [
    (1.665, 0.009, 0.008, 0.198, -0.063),
    (1.715, 0.030, 0.022, 0.206, -0.054),
    (1.775, 0.044, 0.030, 0.204, -0.033),
    (1.833, 0.047, 0.032, 0.190, -0.006),
    (1.860, 0.010, 0.008, 0.168, 0.010),
], HAIR_WARM, 22)

# Three crown clumps give concept-like messy silhouette while retaining the solid cap.
pointed_lock("V36CrownL", [
    (1.900, 0.012, 0.009, -0.145, 0.016),
    (1.940, 0.050, 0.032, -0.120, 0.022),
    (1.980, 0.062, 0.037, -0.082, 0.024),
    (2.010, 0.040, 0.028, -0.042, 0.018),
    (2.026, 0.009, 0.007, -0.010, 0.008),
], HAIR_WARM, 22)
pointed_lock("V36CrownC", [
    (1.922, 0.010, 0.008, -0.020, 0.020),
    (1.962, 0.039, 0.028, -0.010, 0.024),
    (2.008, 0.047, 0.031, 0.008, 0.022),
    (2.045, 0.030, 0.022, 0.025, 0.012),
    (2.062, 0.008, 0.006, 0.040, 0.002),
], HAIR, 22)
pointed_lock("V36CrownR", [
    (1.902, 0.010, 0.008, 0.145, 0.015),
    (1.940, 0.043, 0.029, 0.128, 0.022),
    (1.980, 0.054, 0.034, 0.100, 0.024),
    (2.010, 0.036, 0.025, 0.070, 0.017),
    (2.024, 0.008, 0.006, 0.045, 0.008),
], HAIR_WARM, 22)

# Export V3.6 candidate.
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
print(f"Exported Lembah Sari Character V3.6 face/hair/hand correction to {OUT_PATH}")
