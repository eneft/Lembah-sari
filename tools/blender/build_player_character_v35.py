import bpy
import math
import os
from mathutils import Vector

# Lembah Sari Character V3.5 — concept shape-language rewrite.
# Goal after V3.4 review: remove sausage hair, mitten hands and toy-like facial lines.
# Keep the proven body scale/outfit while rebuilding the high-attention silhouette.

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


def lock_profile(name, rings, mat, segments=24):
    """Broad, flattened, pointed 3D hair lock using varying centers/radii."""
    return profile(name, rings, mat, segments)


# Palette alignment to the approved sheet: warmer skin, softer cream, less yellow.
recolor(SKIN, (0.86, 0.56, 0.38))
recolor(BLUSH, (0.78, 0.30, 0.22))
recolor(SHIRT, (0.72, 0.65, 0.52))

# -----------------------------------------------------------------------------
# FACE — remove double-line toy treatment and rebuild simpler expression.
# -----------------------------------------------------------------------------
for name in ["UpperLidL", "UpperLidR", "BrowL", "BrowR", "Nose", "Smile"]:
    remove_obj(name)

# Eyebrows: straighter and broader, as in the concept, not circular eye-rings.
curve("BrowL", [(-0.120, -0.170, 1.807), (-0.076, -0.177, 1.821), (-0.032, -0.170, 1.817)], HAIR, 0.0075)
curve("BrowR", [(0.032, -0.170, 1.817), (0.076, -0.177, 1.821), (0.120, -0.170, 1.807)], HAIR, 0.0075)

# Tiny softly protruding nose and a longer relaxed smile.
uv("Nose", (0.0, -0.179, 1.653), (0.010, 0.0055, 0.010), SKIN, 18, 10)
curve("Smile", [(-0.047, -0.176, 1.600), (-0.023, -0.181, 1.590), (0.0, -0.183, 1.588), (0.025, -0.181, 1.592), (0.049, -0.175, 1.604)], MOUTH, 0.0034)

# Move eyes a touch farther forward and slightly enlarge/tilt their readable area.
for side in (-1, 1):
    for prefix in ("EyeWhite", "Iris", "Pupil", "EyeGlint"):
        obj = bpy.data.objects.get(f"{prefix}_{side}")
        if obj:
            obj.location.y -= 0.005
    eye = bpy.data.objects.get(f"EyeWhite_{side}")
    iris = bpy.data.objects.get(f"Iris_{side}")
    if eye:
        eye.scale.x *= 1.08
        eye.scale.z *= 1.06
    if iris:
        iris.scale.x *= 1.04
        iris.scale.z *= 1.04

# Slight cheek fullness at lower face, subtle enough not to read as separate balls.
for side in (-1, 1):
    s = float(side)
    uv(f"CheekSoft_{side}", (0.107*s, -0.070, 1.645), (0.064, 0.080, 0.056), SKIN, 22, 14)

# -----------------------------------------------------------------------------
# UPPER BODY / ARMS — narrower sleeves and a mild inward relaxed stance.
# -----------------------------------------------------------------------------
for side in (-1, 1):
    s = float(side)
    for prefix in ("Sleeve", "RolledSleeve"):
        obj = bpy.data.objects.get(f"{prefix}_{side}")
        if obj:
            obj.scale.x *= 0.86
            obj.scale.y *= 0.86
            obj.location.x *= 0.95
    arm = bpy.data.objects.get(f"Forearm_{side}")
    if arm:
        arm.scale.x *= 0.92
        arm.scale.y *= 0.92
        arm.location.x *= 0.94

# -----------------------------------------------------------------------------
# HANDS — proper stylized palm plus four short rounded finger pads.
# No claws, no single mitten silhouette.
# -----------------------------------------------------------------------------
for side in (-1, 1):
    # Find current hand center from V3.4 then remove all hand pieces/creases.
    palm_old = bpy.data.objects.get(f"Palm_{side}")
    p = palm_old.matrix_world.translation.copy() if palm_old else Vector((0.205*side, -0.068, 0.720))
    for name in [f"Palm_{side}", f"Thumb_{side}", f"ThumbTip_{side}"]:
        remove_obj(name)
    for i in range(4):
        remove_obj(f"FingerGroove_{side}_{i}")
        remove_obj(f"Finger_{side}_{i}")
        remove_obj(f"FingerTip_{side}_{i}")

    # Compact palm, narrower than V3.4 mitten.
    profile(f"Palm_{side}", [
        (p.z + 0.045, 0.030, 0.023, p.x, p.y),
        (p.z + 0.020, 0.034, 0.026, p.x, p.y),
        (p.z - 0.012, 0.036, 0.027, p.x, p.y),
        (p.z - 0.035, 0.032, 0.024, p.x, p.y - 0.002),
    ], SKIN, 24)

    # Four short fingers grouped naturally; large enough to read as a hand, not claws.
    offsets = (-0.0225, -0.0075, 0.0075, 0.0225)
    lengths = (0.038, 0.045, 0.044, 0.034)
    for i, (off, length) in enumerate(zip(offsets, lengths)):
        x = p.x + off
        z0 = p.z - 0.025
        z1 = z0 - length
        # Rounded finger body and tip, tightly packed.
        tapered(f"Finger_{side}_{i}", (x, p.y - 0.001, z0), (x, p.y - 0.006, z1), 0.0105, 0.0088, SKIN, 18, 0.003)
        uv(f"FingerTip_{side}_{i}", (x, p.y - 0.006, z1), (0.0088, 0.0095, 0.0100), SKIN, 16, 10)

    s = float(side)
    thumb_a = Vector((p.x + 0.028*s, p.y - 0.002, p.z + 0.008))
    thumb_b = Vector((p.x + 0.048*s, p.y - 0.010, p.z - 0.020))
    tapered(f"Thumb_{side}", thumb_a, thumb_b, 0.0125, 0.0095, SKIN, 18, 0.003)
    uv(f"ThumbTip_{side}", tuple(thumb_b), (0.0095, 0.0100, 0.0100), SKIN, 16, 10)

# -----------------------------------------------------------------------------
# HAIR — replace all rounded path-lock sausages with broad flattened pointed lobes.
# Each lock is a real volume with an asymmetrical centerline and a sharp tip.
# -----------------------------------------------------------------------------
for name in [
    "HairBack", "V34FringeLeftOuter", "V34FringeHeroSweep", "V34FringeCenter", "V34FringeRight",
    "V34TempleL", "V34TempleR", "V34CrownLeft", "V34CrownMid", "V34CrownRight",
    "V34TuftHero", "V34BackL", "V34BackR",
]:
    remove_obj(name)

# Cohesive back cap, slightly flattened front/back so locks define the silhouette.
uv("HairBack", (0.0, 0.050, 1.815), (0.214, 0.150, 0.178), HAIR, 36, 20)

# Front locks: wide roots, flattened depth, pointed lower tips; both eyes remain open.
lock_profile("V35BangOuterL", [
    (1.735, 0.012, 0.010, -0.150, -0.145),
    (1.770, 0.040, 0.024, -0.156, -0.134),
    (1.825, 0.068, 0.032, -0.145, -0.110),
    (1.885, 0.076, 0.036, -0.105, -0.075),
    (1.925, 0.050, 0.029, -0.065, -0.045),
    (1.942, 0.012, 0.009, -0.035, -0.030),
], HAIR, 24)
lock_profile("V35BangHero", [
    (1.755, 0.011, 0.009, -0.030, -0.158),
    (1.790, 0.045, 0.024, -0.042, -0.145),
    (1.845, 0.075, 0.034, -0.050, -0.115),
    (1.905, 0.082, 0.038, -0.035, -0.075),
    (1.950, 0.055, 0.030, -0.005, -0.044),
    (1.967, 0.012, 0.009, 0.025, -0.028),
], HAIR_WARM, 24)
lock_profile("V35BangCenterR", [
    (1.785, 0.010, 0.009, 0.066, -0.151),
    (1.820, 0.038, 0.022, 0.067, -0.138),
    (1.870, 0.060, 0.030, 0.060, -0.112),
    (1.918, 0.066, 0.032, 0.075, -0.078),
    (1.950, 0.040, 0.025, 0.108, -0.050),
    (1.962, 0.010, 0.008, 0.130, -0.035),
], HAIR, 24)
lock_profile("V35BangRight", [
    (1.745, 0.010, 0.008, 0.158, -0.126),
    (1.785, 0.035, 0.020, 0.164, -0.112),
    (1.835, 0.052, 0.027, 0.158, -0.086),
    (1.882, 0.054, 0.028, 0.145, -0.058),
    (1.915, 0.032, 0.021, 0.128, -0.040),
    (1.930, 0.009, 0.007, 0.108, -0.030),
], HAIR_WARM, 22)

# Temple/side locks frame the ears with sharper lower points.
lock_profile("V35TempleL", [
    (1.640, 0.010, 0.009, -0.198, -0.060),
    (1.690, 0.030, 0.022, -0.205, -0.052),
    (1.755, 0.044, 0.030, -0.203, -0.032),
    (1.820, 0.050, 0.033, -0.190, -0.005),
    (1.850, 0.026, 0.020, -0.172, 0.015),
], HAIR, 22)
lock_profile("V35TempleR", [
    (1.655, 0.010, 0.009, 0.195, -0.055),
    (1.705, 0.030, 0.022, 0.203, -0.048),
    (1.765, 0.044, 0.029, 0.202, -0.026),
    (1.825, 0.048, 0.032, 0.188, 0.000),
    (1.855, 0.024, 0.019, 0.168, 0.018),
], HAIR, 22)

# Crown lobes, intentionally asymmetric with pointed ends like the concept sheet.
lock_profile("V35CrownLeft", [
    (1.900, 0.012, 0.010, -0.165, 0.010),
    (1.935, 0.050, 0.032, -0.135, 0.018),
    (1.970, 0.066, 0.038, -0.090, 0.022),
    (1.995, 0.044, 0.030, -0.045, 0.018),
    (2.010, 0.010, 0.008, -0.010, 0.010),
], HAIR_WARM, 22)
lock_profile("V35CrownMid", [
    (1.920, 0.012, 0.009, -0.035, 0.015),
    (1.965, 0.043, 0.029, -0.020, 0.020),
    (2.010, 0.052, 0.032, 0.000, 0.018),
    (2.045, 0.034, 0.024, 0.020, 0.010),
    (2.062, 0.008, 0.007, 0.040, 0.000),
], HAIR, 22)
lock_profile("V35CrownRight", [
    (1.900, 0.010, 0.008, 0.165, 0.010),
    (1.935, 0.042, 0.028, 0.145, 0.018),
    (1.975, 0.058, 0.034, 0.105, 0.022),
    (2.005, 0.040, 0.027, 0.070, 0.016),
    (2.020, 0.009, 0.007, 0.040, 0.008),
], HAIR_WARM, 22)

# Rear breakup for side/back readability.
lock_profile("V35BackL", [
    (1.690, 0.009, 0.008, -0.185, 0.075),
    (1.735, 0.032, 0.024, -0.198, 0.080),
    (1.790, 0.045, 0.030, -0.195, 0.085),
    (1.845, 0.038, 0.028, -0.180, 0.080),
    (1.875, 0.009, 0.008, -0.155, 0.065),
], HAIR, 20)
lock_profile("V35BackR", [
    (1.700, 0.009, 0.008, 0.184, 0.078),
    (1.745, 0.032, 0.024, 0.197, 0.083),
    (1.800, 0.044, 0.030, 0.193, 0.088),
    (1.850, 0.036, 0.027, 0.176, 0.080),
    (1.880, 0.009, 0.008, 0.150, 0.066),
], HAIR_WARM, 20)

# Export candidate.
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
print(f"Exported Lembah Sari Character V3.5 concept shape-language rewrite to {OUT_PATH}")
