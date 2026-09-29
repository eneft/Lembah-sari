import bpy
import math
import os
from mathutils import Vector

# Lembah Sari Character V3.3 — appeal rebuild.
# This is intentionally not a micro-polish pass. The approved concept sheet is
# the target: softer tapered face, almond eyes, readable friendly expression,
# layered side-swept hair, and actual stylized fingers instead of bead hands.

BASE = os.path.join(os.path.dirname(__file__), "build_player_character_v32.py")
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


def almond_outline(cx, cz, rx, rz):
    return [
        (cx - rx, cz),
        (cx - rx * 0.70, cz + rz * 0.72),
        (cx, cz + rz),
        (cx + rx * 0.70, cz + rz * 0.72),
        (cx + rx, cz),
        (cx + rx * 0.70, cz - rz * 0.72),
        (cx, cz - rz),
        (cx - rx * 0.70, cz - rz * 0.72),
    ]


# -----------------------------------------------------------------------------
# FACE — rebuild from scratch instead of scaling the previous toy-like face.
# -----------------------------------------------------------------------------
face_names = [
    "Head", "Ear_-1", "Ear_1", "Blush_-1", "Blush_1",
    "EyeWhite_-1", "EyeWhite_1", "Iris_-1", "Iris_1",
    "Pupil_-1", "Pupil_1", "EyeGlint_-1", "EyeGlint_1",
    "UpperLidL", "UpperLidR", "BrowL", "BrowR", "Nose", "Smile",
]
for name in face_names:
    remove_obj(name)

# Slightly warmer skin, closer to the approved concept under the current studio light.
recolor(SKIN, (0.80, 0.49, 0.31))
recolor(BLUSH, (0.72, 0.27, 0.20))

# Soft oval skull: full cheeks, narrower jaw/chin, no spherical doll head.
profile("Head", [
    (1.535, 0.070, 0.078, 0.0, -0.004),
    (1.555, 0.104, 0.103, 0.0, -0.004),
    (1.590, 0.137, 0.126, 0.0, -0.003),
    (1.635, 0.160, 0.143, 0.0, -0.001),
    (1.690, 0.174, 0.151, 0.0,  0.002),
    (1.748, 0.172, 0.150, 0.0,  0.004),
    (1.805, 0.156, 0.142, 0.0,  0.005),
    (1.845, 0.119, 0.117, 0.0,  0.004),
    (1.865, 0.066, 0.075, 0.0,  0.003),
], SKIN, 40)

# Ears are tucked into the hair line rather than reading as round side discs.
for side in (-1, 1):
    s = float(side)
    uv(f"Ear_{side}", (0.166 * s, -0.001, 1.690), (0.026, 0.017, 0.041), SKIN, 20, 12)

# Almond sclera + dominant brown iris. This removes the stacked-circle toy look.
for side in (-1, 1):
    s = float(side)
    cx = 0.058 * s
    patch(f"EyeWhite_{side}", almond_outline(cx, 1.708, 0.048, 0.033), -0.1515, EYE_WHITE, 0.0045, 0.0025)
    uv(f"Iris_{side}", (cx, -0.1555, 1.706), (0.025, 0.0030, 0.028), IRIS, 22, 14)
    uv(f"Pupil_{side}", (cx, -0.1585, 1.704), (0.0125, 0.0020, 0.018), PUPIL, 18, 12)
    uv(f"EyeGlint_{side}", (cx - 0.008 * s, -0.1605, 1.720), (0.0045, 0.0012, 0.0060), EYE_WHITE, 12, 8)
    uv(f"Blush_{side}", (0.105 * s, -0.1475, 1.646), (0.022, 0.0018, 0.008), BLUSH, 14, 8)

curve("UpperLidL", [(-0.107, -0.156, 1.714), (-0.060, -0.161, 1.742), (-0.012, -0.156, 1.715)], HAIR, 0.0045)
curve("UpperLidR", [(0.012, -0.156, 1.715), (0.060, -0.161, 1.742), (0.107, -0.156, 1.714)], HAIR, 0.0045)
curve("BrowL", [(-0.108, -0.147, 1.775), (-0.065, -0.153, 1.788), (-0.027, -0.148, 1.782)], HAIR, 0.0065)
curve("BrowR", [(0.027, -0.148, 1.782), (0.065, -0.153, 1.788), (0.108, -0.147, 1.775)], HAIR, 0.0065)

# Tiny nose, subtle smile; avoid a protruding bead in the middle of the face.
uv("Nose", (0.0, -0.1535, 1.655), (0.009, 0.0035, 0.008), SKIN, 16, 10)
curve("Smile", [(-0.038, -0.151, 1.605), (-0.018, -0.156, 1.596), (0.0, -0.158, 1.594), (0.020, -0.156, 1.597), (0.040, -0.151, 1.607)], MOUTH, 0.0035)

# -----------------------------------------------------------------------------
# HANDS — replace oval paddles with palm + four readable fingers + thumb.
# Keep the existing forearm endpoint so gameplay silhouette/scale remains stable.
# -----------------------------------------------------------------------------
hand_centers = {}
for side in (-1, 1):
    old = bpy.data.objects.get(f"Palm_{side}")
    if old:
        hand_centers[side] = old.matrix_world.translation.copy()
    else:
        hand_centers[side] = Vector((0.21 * side, -0.09, 0.77))
    remove_obj(f"Palm_{side}")
    remove_obj(f"Thumb_{side}")
    for i in range(4):
        remove_obj(f"Finger_{side}_{i}")
        remove_obj(f"FingerTip_{side}_{i}")

for side in (-1, 1):
    s = float(side)
    p = hand_centers[side]

    # Palm is narrower at wrist/finger roots and fuller through the knuckles.
    profile(f"Palm_{side}", [
        (p.z - 0.022, 0.027, 0.021, p.x, p.y),
        (p.z - 0.004, 0.034, 0.024, p.x, p.y),
        (p.z + 0.024, 0.036, 0.026, p.x, p.y),
        (p.z + 0.048, 0.030, 0.023, p.x, p.y),
    ], SKIN, 24)

    # Four separate stylized fingers. They touch at the base but retain readable seams.
    offsets = (-0.021, -0.007, 0.007, 0.021)
    lengths = (0.045, 0.054, 0.052, 0.041)
    radii = (0.0072, 0.0080, 0.0078, 0.0068)
    for i, (off, length, rad) in enumerate(zip(offsets, lengths, radii)):
        base = Vector((p.x + off, p.y - 0.002, p.z - 0.012))
        tip = Vector((p.x + off + (i - 1.5) * 0.0015, p.y - 0.008, p.z - 0.012 - length))
        tapered(f"Finger_{side}_{i}", base, tip, rad * 1.12, rad, SKIN, 16, 0.0025)
        uv(f"FingerTip_{side}_{i}", tuple(tip), (rad, rad * 1.15, rad * 1.05), SKIN, 14, 8)

    # Thumb angles outward and down like the relaxed turnaround pose.
    thumb_a = Vector((p.x + 0.027 * s, p.y - 0.002, p.z + 0.012))
    thumb_b = Vector((p.x + 0.045 * s, p.y - 0.010, p.z - 0.018))
    tapered(f"Thumb_{side}", thumb_a, thumb_b, 0.0115, 0.0085, SKIN, 16, 0.0025)
    uv(f"ThumbTip_{side}", tuple(thumb_b), (0.0085, 0.0095, 0.009), SKIN, 14, 8)

# -----------------------------------------------------------------------------
# HAIR — full rebuild of the face framing. Fewer, broader graphic locks like the
# concept sheet instead of thin tubes / helmet-like blobs.
# -----------------------------------------------------------------------------
hair_remove = [
    "HairBack", "ConceptSideLeft", "ConceptSideRight",
    "HeroFringeOuterL", "HeroFringeSweep", "HeroFringeShortR",
    "HeroTopSweep", "HeroTopTuft", "V31TempleLayerL", "V31TempleLayerR",
    "V31TopAccent",
]
for name in hair_remove:
    remove_obj(name)

# Rounded back volume.
uv("HairBack", (0.0, 0.030, 1.790), (0.188, 0.145, 0.158), HAIR, 32, 18)

# Graphic face-framing plates: dominant long left-to-center sweep, open right forehead.
patch("HeroBangLeft", [
    (-0.182, 1.810), (-0.145, 1.875), (-0.085, 1.916), (-0.025, 1.918),
    (0.012, 1.886), (0.010, 1.826), (-0.010, 1.758), (-0.026, 1.682),
    (-0.054, 1.633), (-0.066, 1.715), (-0.118, 1.772),
], -0.159, HAIR_WARM, 0.026, 0.007)

patch("HeroBangRight", [
    (-0.015, 1.892), (0.045, 1.920), (0.110, 1.895), (0.158, 1.842),
    (0.158, 1.785), (0.132, 1.730), (0.095, 1.681), (0.091, 1.754),
    (0.050, 1.817),
], -0.156, HAIR, 0.025, 0.007)

patch("HeroTempleLeft", [
    (-0.175, 1.840), (-0.214, 1.790), (-0.215, 1.710), (-0.190, 1.625),
    (-0.165, 1.590), (-0.164, 1.688), (-0.145, 1.776),
], -0.132, HAIR, 0.026, 0.006)

patch("HeroTempleRight", [
    (0.142, 1.827), (0.190, 1.790), (0.204, 1.722), (0.190, 1.655),
    (0.166, 1.615), (0.160, 1.710), (0.128, 1.775),
], -0.126, HAIR_WARM, 0.025, 0.006)

# Top/crown clumps add the playful asymmetry and volume visible in the concept.
path_lock(
    "HeroTopLockL",
    [(-0.120, 0.000, 1.875), (-0.095, -0.008, 1.925), (-0.055, -0.012, 1.944)],
    [(0.050, 0.040), (0.040, 0.033), (0.028, 0.024)],
    (-0.018, -0.015, 1.935), HAIR_WARM,
)
path_lock(
    "HeroTopLockC",
    [(-0.020, 0.005, 1.900), (0.010, -0.004, 1.955), (0.030, -0.010, 1.970)],
    [(0.042, 0.034), (0.032, 0.027), (0.021, 0.018)],
    (0.052, -0.015, 1.944), HAIR,
)
path_lock(
    "HeroTopLockR",
    [(0.060, 0.010, 1.887), (0.105, 0.000, 1.925), (0.140, -0.006, 1.930)],
    [(0.040, 0.033), (0.032, 0.027), (0.022, 0.019)],
    (0.168, -0.012, 1.910), HAIR_WARM,
)

# Add small back-side locks so the side view does not collapse into a sphere.
path_lock(
    "HeroBackLockL",
    [(-0.150, 0.080, 1.800), (-0.180, 0.070, 1.745), (-0.184, 0.052, 1.695)],
    [(0.036, 0.030), (0.030, 0.026), (0.022, 0.019)],
    (-0.178, 0.032, 1.645), HAIR,
)
path_lock(
    "HeroBackLockR",
    [(0.145, 0.085, 1.795), (0.175, 0.073, 1.748), (0.182, 0.052, 1.705)],
    [(0.034, 0.029), (0.029, 0.025), (0.021, 0.018)],
    (0.174, 0.035, 1.658), HAIR_WARM,
)

# Export V3.3 candidate.
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
print(f"Exported Lembah Sari Character V3.3 face/hand appeal rebuild to {OUT_PATH}")
