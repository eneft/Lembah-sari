import bpy
import math
import os
from mathutils import Vector

# Lembah Sari Character V3.9 — concept appeal refinement.
# V3.8 proved the volumetric hair approach. V3.9 fixes presentation-critical
# mismatches: visible large eyes, softer/lighter hair, broader upper body,
# larger hands and smoother asymmetric main hair locks.

BASE = os.path.join(os.path.dirname(__file__), "build_player_character_v38.py")
exec(compile(open(BASE, "r", encoding="utf-8").read(), BASE, "exec"), globals(), globals())


def remove_many(names):
    for name in names:
        obj = bpy.data.objects.get(name)
        if obj:
            bpy.data.objects.remove(obj, do_unlink=True)


# -----------------------------------------------------------------------------
# PALETTE — concept hair reads deep warm brown, not near-black red.
# -----------------------------------------------------------------------------
recolor(HAIR, (0.090, 0.032, 0.014))
recolor(HAIR_WARM, (0.155, 0.060, 0.024))
recolor(IRIS, (0.105, 0.034, 0.010))
recolor(PUPIL, (0.010, 0.004, 0.002))

# -----------------------------------------------------------------------------
# FACE — move eyes clearly in front of the face and enlarge them.
# -----------------------------------------------------------------------------
remove_many([
    "EyeWhite_-1", "EyeWhite_1", "Iris_-1", "Iris_1", "Pupil_-1", "Pupil_1",
    "EyeGlint_-1", "EyeGlint_1", "BrowL", "BrowR", "Nose", "Smile",
])

for side in (-1, 1):
    s = float(side)
    cx = 0.080*s
    almond(f"EyeWhite_{side}", cx, 1.758, 0.066, 0.043, -0.218, EYE_WHITE, 0.007)
    almond(f"Iris_{side}", cx + 0.004*s, 1.756, 0.035, 0.038, -0.225, IRIS, 0.006)
    almond(f"Pupil_{side}", cx + 0.005*s, 1.756, 0.015, 0.023, -0.231, PUPIL, 0.005)
    uv(f"EyeGlint_{side}", (cx - 0.008*s, -0.236, 1.774), (0.0065, 0.0025, 0.0075), EYE_WHITE, 12, 8)

curve("BrowL", [(-0.145, -0.211, 1.826), (-0.092, -0.218, 1.842), (-0.045, -0.211, 1.833)], HAIR, 0.0058)
curve("BrowR", [(0.045, -0.211, 1.833), (0.092, -0.218, 1.842), (0.145, -0.211, 1.826)], HAIR, 0.0058)
uv("Nose", (0.0, -0.216, 1.677), (0.0052, 0.0025, 0.0056), SKIN, 14, 8)
curve("Smile", [(-0.052, -0.213, 1.618), (-0.026, -0.219, 1.609), (0.0, -0.221, 1.608), (0.027, -0.219, 1.612), (0.054, -0.212, 1.622)], MOUTH, 0.0034)

# Slight cheek width/softness; keep head height unchanged.
head = bpy.data.objects.get("Head")
if head:
    world_scale_about(head, (0.0, 0.0, 1.720), 1.025, 1.025, 1.000)
for side in (-1, 1):
    ear = bpy.data.objects.get(f"Ear_{side}")
    if ear:
        world_scale_about(ear, (0.0, 0.0, 1.720), 1.025, 1.025, 1.000)

# -----------------------------------------------------------------------------
# TORSO / SHOULDERS — concept has relaxed but broader shirt silhouette.
# -----------------------------------------------------------------------------
for name, sx, sy in [
    ("ShirtTorso", 1.055, 1.020),
    ("OverallBib", 1.035, 1.000),
    ("BibPocket", 1.025, 1.000),
]:
    obj = bpy.data.objects.get(name)
    if obj:
        obj.scale.x *= sx
        obj.scale.y *= sy

for side in (-1, 1):
    for prefix in ("Sleeve", "SleeveLower", "RolledSleeve"):
        obj = bpy.data.objects.get(f"{prefix}_{side}")
        if obj:
            obj.scale.x *= 1.045
            obj.scale.y *= 1.045
            obj.location.x *= 1.025

    # Scale the entire hand group about its palm center so it reads at gameplay distance.
    s = float(side)
    pivot = (0.228*s, -0.071, 0.770)
    names = [f"Palm_{side}", f"Thumb_{side}", f"ThumbTip_{side}"] + [f"Finger_{side}_{i}" for i in range(4)]
    for name in names:
        obj = bpy.data.objects.get(name)
        if obj:
            world_scale_about(obj, pivot, 1.18, 1.18, 1.18)

# -----------------------------------------------------------------------------
# HAIR — preserve V3.8 method but rebuild the locks smoother and more asymmetrical.
# -----------------------------------------------------------------------------
remove_many([
    "HairCap", "HairRear",
    "V38HeroSweep", "V38FrontLeft", "V38FrontMid", "V38FrontRight",
    "V38CrownLeft", "V38CrownCenter", "V38CrownRight",
    "V38TempleL", "V38TempleR", "V38BackLeft", "V38BackRight",
])

uv("HairCap", (0.0, 0.035, 1.835), (0.200, 0.153, 0.168), HAIR, 44, 24)
uv("HairRear", (0.0, 0.100, 1.800), (0.188, 0.153, 0.152), HAIR, 40, 22)

# Dominant sweep — long, soft and clearly crossing the forehead like the concept.
loft_lock("V39HeroSweep", [
    (-0.178, -0.105, 1.948, 0.076, 0.036),
    (-0.150, -0.132, 1.928, 0.082, 0.037),
    (-0.112, -0.155, 1.900, 0.084, 0.037),
    (-0.070, -0.177, 1.866, 0.078, 0.035),
    (-0.025, -0.192, 1.828, 0.066, 0.032),
    (0.012, -0.199, 1.792, 0.047, 0.025),
    (0.040, -0.198, 1.765, 0.008, 0.007),
], HAIR_WARM, 16)
loft_lock("V39FrontLeft", [
    (-0.205, -0.078, 1.916, 0.060, 0.032),
    (-0.206, -0.112, 1.883, 0.064, 0.033),
    (-0.198, -0.142, 1.846, 0.061, 0.032),
    (-0.184, -0.164, 1.805, 0.050, 0.028),
    (-0.163, -0.170, 1.765, 0.008, 0.007),
], HAIR, 14)
loft_lock("V39FrontMid", [
    (-0.040, -0.105, 1.962, 0.061, 0.033),
    (0.000, -0.137, 1.943, 0.066, 0.034),
    (0.040, -0.164, 1.912, 0.063, 0.033),
    (0.077, -0.184, 1.875, 0.052, 0.029),
    (0.104, -0.187, 1.838, 0.008, 0.007),
], HAIR, 14)
loft_lock("V39FrontRight", [
    (0.082, -0.076, 1.940, 0.055, 0.030),
    (0.124, -0.106, 1.922, 0.060, 0.031),
    (0.158, -0.136, 1.892, 0.056, 0.030),
    (0.181, -0.158, 1.855, 0.045, 0.026),
    (0.188, -0.160, 1.820, 0.008, 0.007),
], HAIR_WARM, 14)

# Crown clumps: low, sweeping shapes rather than spikes.
loft_lock("V39CrownL", [
    (-0.178, 0.008, 1.938, 0.067, 0.038),
    (-0.145, -0.004, 1.976, 0.071, 0.039),
    (-0.103, -0.012, 2.011, 0.065, 0.037),
    (-0.060, -0.016, 2.036, 0.048, 0.031),
    (-0.024, -0.017, 2.048, 0.008, 0.007),
], HAIR_WARM, 14)
loft_lock("V39CrownC", [
    (-0.055, 0.005, 1.978, 0.060, 0.035),
    (-0.022, -0.005, 2.016, 0.065, 0.036),
    (0.010, -0.012, 2.052, 0.057, 0.033),
    (0.038, -0.014, 2.078, 0.042, 0.028),
    (0.064, -0.013, 2.090, 0.008, 0.007),
], HAIR, 14)
loft_lock("V39CrownR", [
    (0.045, 0.010, 1.964, 0.058, 0.034),
    (0.086, 0.000, 1.999, 0.062, 0.035),
    (0.126, -0.006, 2.027, 0.055, 0.032),
    (0.158, -0.008, 2.046, 0.040, 0.027),
    (0.185, -0.006, 2.052, 0.008, 0.007),
], HAIR_WARM, 14)

# Side/back layers preserve the shaggy turnaround silhouette.
loft_lock("V39TempleL", [
    (-0.200, -0.005, 1.872, 0.048, 0.030),
    (-0.217, -0.022, 1.825, 0.051, 0.031),
    (-0.220, -0.037, 1.773, 0.046, 0.029),
    (-0.214, -0.043, 1.725, 0.034, 0.024),
    (-0.202, -0.040, 1.690, 0.008, 0.007),
], HAIR, 12)
loft_lock("V39TempleR", [
    (0.198, -0.002, 1.868, 0.046, 0.029),
    (0.215, -0.020, 1.824, 0.049, 0.030),
    (0.218, -0.034, 1.777, 0.044, 0.028),
    (0.211, -0.040, 1.733, 0.033, 0.023),
    (0.200, -0.038, 1.702, 0.008, 0.007),
], HAIR, 12)
loft_lock("V39BackLeft", [
    (-0.150, 0.132, 1.902, 0.050, 0.036),
    (-0.180, 0.140, 1.862, 0.053, 0.037),
    (-0.202, 0.137, 1.815, 0.049, 0.034),
    (-0.210, 0.124, 1.766, 0.037, 0.028),
    (-0.202, 0.105, 1.728, 0.008, 0.007),
], HAIR, 12)
loft_lock("V39BackRight", [
    (0.148, 0.134, 1.900, 0.049, 0.036),
    (0.178, 0.142, 1.862, 0.052, 0.037),
    (0.200, 0.139, 1.818, 0.048, 0.034),
    (0.208, 0.126, 1.772, 0.036, 0.027),
    (0.200, 0.107, 1.736, 0.008, 0.007),
], HAIR_WARM, 12)

# Export V3.9 candidate.
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
print(f"Exported Lembah Sari Character V3.9 concept appeal candidate to {OUT_PATH}")
