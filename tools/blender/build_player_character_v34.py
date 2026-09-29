import bpy
import math
import os
from mathutils import Vector

# Lembah Sari Character V3.4 — corrective appeal pass after inspecting V3.3.
# V3.3 proved that explicit tiny fingers read like claws at gameplay scale and
# flat hair plates read like cardboard. V3.4 uses a larger concept-like head,
# 3D tapered hair locks, and a unified organic hand with finger grooves.

BASE = os.path.join(os.path.dirname(__file__), "build_player_character_v33.py")
exec(compile(open(BASE, "r", encoding="utf-8").read(), BASE, "exec"), globals(), globals())


def remove_obj(name):
    obj = bpy.data.objects.get(name)
    if obj:
        bpy.data.objects.remove(obj, do_unlink=True)


def make_mat_local(name, rgb, roughness=0.96):
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = bpy.data.materials.new(name)
        mat.use_nodes = True
    mat.diffuse_color = (*rgb, 1.0)
    if mat.use_nodes:
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs["Base Color"].default_value = (*rgb, 1.0)
            bsdf.inputs["Roughness"].default_value = roughness
    return mat


HAND_LINE = make_mat_local("Hand Crease", (0.50, 0.245, 0.145), 0.98)

# -----------------------------------------------------------------------------
# HEAD / FACE PROPORTION — the concept is ~4–4.5 heads tall, while V3.3 still
# read too adult/small-headed. Enlarge the face group without touching body scale.
# -----------------------------------------------------------------------------
HEAD_PIVOT_V34 = (0.0, 0.0, 1.700)
face_group = [
    "Head", "Ear_-1", "Ear_1", "Blush_-1", "Blush_1",
    "EyeWhite_-1", "EyeWhite_1", "Iris_-1", "Iris_1",
    "Pupil_-1", "Pupil_1", "EyeGlint_-1", "EyeGlint_1",
    "UpperLidL", "UpperLidR", "BrowL", "BrowR", "Nose", "Smile",
]
for name in face_group:
    obj = bpy.data.objects.get(name)
    if obj:
        world_scale_about(obj, HEAD_PIVOT_V34, 1.14, 1.10, 1.13)

# Eye/iris readability gets a modest extra boost after the head enlargement.
for side in (-1, 1):
    for prefix, sx, sz in [
        ("EyeWhite", 1.035, 1.055),
        ("Iris", 1.06, 1.075),
        ("Pupil", 1.035, 1.045),
    ]:
        obj = bpy.data.objects.get(f"{prefix}_{side}")
        if obj:
            obj.scale.x *= sx
            obj.scale.z *= sz

# -----------------------------------------------------------------------------
# HANDS — remove tiny separated claw fingers. Build one smooth stylized hand
# volume and indicate finger separation with subtle front grooves.
# -----------------------------------------------------------------------------
for side in (-1, 1):
    # Read center from current palm before replacing it.
    old_palm = bpy.data.objects.get(f"Palm_{side}")
    p = old_palm.matrix_world.translation.copy() if old_palm else Vector((0.21 * side, -0.09, 0.77))

    remove_obj(f"Palm_{side}")
    remove_obj(f"Thumb_{side}")
    remove_obj(f"ThumbTip_{side}")
    for i in range(4):
        remove_obj(f"Finger_{side}_{i}")
        remove_obj(f"FingerTip_{side}_{i}")

    # Organic mitten-like hand, tapered from knuckles to fingertip area.
    profile(f"Palm_{side}", [
        (p.z + 0.052, 0.029, 0.021, p.x, p.y),
        (p.z + 0.025, 0.036, 0.025, p.x, p.y),
        (p.z - 0.008, 0.039, 0.028, p.x, p.y),
        (p.z - 0.040, 0.036, 0.026, p.x, p.y - 0.002),
        (p.z - 0.067, 0.028, 0.020, p.x, p.y - 0.004),
        (p.z - 0.078, 0.016, 0.013, p.x, p.y - 0.004),
    ], SKIN, 28)

    # Three subtle crease grooves make four fingers readable without spaghetti geometry.
    for i, off in enumerate((-0.017, 0.0, 0.017)):
        curve(
            f"FingerGroove_{side}_{i}",
            [
                (p.x + off, p.y - 0.0285, p.z - 0.006),
                (p.x + off * 0.92, p.y - 0.0290, p.z - 0.035),
                (p.x + off * 0.76, p.y - 0.0255, p.z - 0.059),
            ],
            HAND_LINE,
            0.0018,
        )

    # Rounded thumb integrated into the side silhouette.
    s = float(side)
    thumb_a = Vector((p.x + 0.030 * s, p.y - 0.002, p.z + 0.016))
    thumb_b = Vector((p.x + 0.047 * s, p.y - 0.011, p.z - 0.018))
    tapered(f"Thumb_{side}", thumb_a, thumb_b, 0.0125, 0.0095, SKIN, 18, 0.003)
    uv(f"ThumbTip_{side}", tuple(thumb_b), (0.0095, 0.0105, 0.010), SKIN, 16, 10)

# -----------------------------------------------------------------------------
# HAIR — discard all V3.3 flat plates. Rebuild with broad 3D tapered locks that
# overlap like the reference while keeping both eyes visible.
# -----------------------------------------------------------------------------
for name in [
    "HairBack", "HeroBangLeft", "HeroBangRight", "HeroTempleLeft", "HeroTempleRight",
    "HeroTopLockL", "HeroTopLockC", "HeroTopLockR", "HeroBackLockL", "HeroBackLockR",
]:
    remove_obj(name)

# Back/crown mass follows enlarged head.
uv("HairBack", (0.0, 0.038, 1.805), (0.210, 0.158, 0.176), HAIR, 36, 20)

# Dominant side-swept front locks. Their tips stop around brow/temple, not over the eyes.
path_lock(
    "V34FringeLeftOuter",
    [(-0.150, -0.015, 1.900), (-0.164, -0.072, 1.850), (-0.150, -0.120, 1.800)],
    [(0.068, 0.048), (0.060, 0.044), (0.047, 0.036)],
    (-0.125, -0.154, 1.730), HAIR,
)
path_lock(
    "V34FringeHeroSweep",
    [(-0.095, -0.020, 1.925), (-0.060, -0.083, 1.885), (-0.018, -0.128, 1.835)],
    [(0.078, 0.052), (0.068, 0.047), (0.052, 0.038)],
    (0.020, -0.157, 1.755), HAIR_WARM,
)
path_lock(
    "V34FringeCenter",
    [(-0.012, -0.010, 1.930), (0.025, -0.070, 1.895), (0.050, -0.117, 1.850)],
    [(0.063, 0.046), (0.054, 0.041), (0.042, 0.033)],
    (0.060, -0.150, 1.785), HAIR,
)
path_lock(
    "V34FringeRight",
    [(0.065, -0.003, 1.905), (0.115, -0.052, 1.870), (0.145, -0.098, 1.825)],
    [(0.052, 0.041), (0.045, 0.036), (0.034, 0.029)],
    (0.151, -0.135, 1.770), HAIR_WARM,
)

# Temple locks frame cheeks/ears while leaving the face open.
path_lock(
    "V34TempleL",
    [(-0.185, 0.010, 1.830), (-0.205, -0.020, 1.770), (-0.208, -0.052, 1.715)],
    [(0.043, 0.035), (0.036, 0.030), (0.027, 0.023)],
    (-0.200, -0.075, 1.655), HAIR,
)
path_lock(
    "V34TempleR",
    [(0.182, 0.015, 1.825), (0.203, -0.014, 1.775), (0.205, -0.045, 1.725)],
    [(0.041, 0.034), (0.034, 0.029), (0.026, 0.022)],
    (0.197, -0.067, 1.670), HAIR,
)

# Layered crown: low sideways clumps + three playful tufts like the concept.
path_lock(
    "V34CrownLeft",
    [(-0.135, 0.035, 1.915), (-0.105, 0.020, 1.962), (-0.060, 0.010, 1.980)],
    [(0.060, 0.045), (0.050, 0.039), (0.036, 0.030)],
    (-0.020, 0.000, 1.968), HAIR_WARM,
)
path_lock(
    "V34CrownMid",
    [(-0.035, 0.030, 1.935), (0.005, 0.015, 1.990), (0.030, 0.000, 2.010)],
    [(0.052, 0.041), (0.041, 0.034), (0.028, 0.024)],
    (0.060, -0.006, 1.985), HAIR,
)
path_lock(
    "V34CrownRight",
    [(0.055, 0.032, 1.925), (0.105, 0.016, 1.965), (0.145, 0.003, 1.970)],
    [(0.050, 0.040), (0.040, 0.033), (0.028, 0.024)],
    (0.180, -0.008, 1.945), HAIR_WARM,
)
path_lock(
    "V34TuftHero",
    [(-0.010, 0.015, 1.980), (0.005, 0.005, 2.030), (0.020, -0.004, 2.050)],
    [(0.033, 0.028), (0.025, 0.022), (0.017, 0.015)],
    (0.045, -0.010, 2.030), HAIR,
)

# Rear side breakup for the turnaround silhouette.
path_lock(
    "V34BackL",
    [(-0.168, 0.095, 1.850), (-0.195, 0.085, 1.790), (-0.198, 0.065, 1.735)],
    [(0.040, 0.033), (0.033, 0.028), (0.024, 0.021)],
    (-0.190, 0.045, 1.680), HAIR,
)
path_lock(
    "V34BackR",
    [(0.165, 0.098, 1.845), (0.192, 0.086, 1.795), (0.197, 0.065, 1.745)],
    [(0.039, 0.032), (0.032, 0.027), (0.023, 0.020)],
    (0.188, 0.045, 1.695), HAIR_WARM,
)

# Export V3.4 candidate.
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
print(f"Exported Lembah Sari Character V3.4 organic face/hair/hands to {OUT_PATH}")
