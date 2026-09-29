import bpy
import math
import os
from mathutils import Vector

# Lembah Sari Character V3.7 — silhouette/anatomy pass.
# Reset from V3.6, then rebuild the features that still read as prototype:
# almond eyes, broad layered ribbon hair, relaxed arms, readable stylized hands,
# and looser trouser proportions. Studio-review candidate only until approved.

BASE = os.path.join(os.path.dirname(__file__), "build_player_character_v36.py")
exec(compile(open(BASE, "r", encoding="utf-8").read(), BASE, "exec"), globals(), globals())


def remove_many(names):
    for name in names:
        obj = bpy.data.objects.get(name)
        if obj:
            bpy.data.objects.remove(obj, do_unlink=True)


def solid_patch(name, verts2d, y, mat, thickness=0.010, bevel_width=0.003):
    # verts2d is [(x,z), ...] in front-view order.
    mesh = bpy.data.meshes.new(name + "Mesh")
    mesh.from_pydata([(x, y, z) for x, z in verts2d], [], [tuple(range(len(verts2d)))])
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.parent = ROOT
    if hasattr(obj.data, "materials"):
        obj.data.materials.append(mat)
    solid = obj.modifiers.new("Depth", "SOLIDIFY")
    solid.thickness = thickness
    solid.offset = 0.0
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=solid.name)
    if bevel_width:
        bevel(obj, bevel_width, 2)
    return obj


def almond(name, cx, cz, rx, rz, y, mat, thickness=0.007):
    pts = [
        (cx-rx, cz),
        (cx-rx*0.62, cz+rz*0.78),
        (cx, cz+rz),
        (cx+rx*0.62, cz+rz*0.78),
        (cx+rx, cz),
        (cx+rx*0.62, cz-rz*0.78),
        (cx, cz-rz),
        (cx-rx*0.62, cz-rz*0.78),
    ]
    return solid_patch(name, pts, y, mat, thickness, 0.0025)


def ribbon_lock(name, path, mat, thickness=0.030):
    # path: [(x,y,z,width), ...]; builds a broad, tapered, solid hair blade.
    left = []
    right = []
    n = len(path)
    for i, (x, y, z, w) in enumerate(path):
        if i == 0:
            x2, _, z2, _ = path[i+1]
            tx, tz = x2-x, z2-z
        elif i == n-1:
            x1, _, z1, _ = path[i-1]
            tx, tz = x-x1, z-z1
        else:
            x1, _, z1, _ = path[i-1]
            x2, _, z2, _ = path[i+1]
            tx, tz = x2-x1, z2-z1
        ln = max(1e-6, math.sqrt(tx*tx + tz*tz))
        px, pz = -tz/ln, tx/ln
        left.append((x + px*w, y, z + pz*w))
        right.append((x - px*w, y, z - pz*w))

    verts = left + list(reversed(right))
    mesh = bpy.data.meshes.new(name + "Mesh")
    mesh.from_pydata(verts, [], [tuple(range(len(verts)))])
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.parent = ROOT
    obj.data.materials.append(mat)
    solid = obj.modifiers.new("HairDepth", "SOLIDIFY")
    solid.thickness = thickness
    solid.offset = 0.0
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=solid.name)
    bevel(obj, 0.006, 3)
    return obj


# -----------------------------------------------------------------------------
# FACE — rebuild eyes as almond surfaces. This removes the toy/dot-eye read.
# -----------------------------------------------------------------------------
for side in (-1, 1):
    remove_many([
        f"EyeWhite_{side}", f"Iris_{side}", f"Pupil_{side}", f"EyeGlint_{side}",
    ])
remove_many(["BrowL", "BrowR", "Nose", "Smile"])

for side in (-1, 1):
    s = float(side)
    cx = 0.074 * s
    almond(f"EyeWhite_{side}", cx, 1.746, 0.052, 0.031, -0.186, EYE_WHITE, 0.006)
    almond(f"Iris_{side}", cx + 0.004*s, 1.744, 0.024, 0.027, -0.191, IRIS, 0.006)
    almond(f"Pupil_{side}", cx + 0.005*s, 1.744, 0.010, 0.017, -0.195, PUPIL, 0.005)
    uv(f"EyeGlint_{side}", (cx - 0.004*s, -0.200, 1.758), (0.0048, 0.0022, 0.0058), EYE_WHITE, 12, 8)

curve("BrowL", [(-0.128, -0.181, 1.804), (-0.083, -0.186, 1.818), (-0.040, -0.181, 1.811)], HAIR, 0.0052)
curve("BrowR", [(0.040, -0.181, 1.811), (0.083, -0.186, 1.818), (0.128, -0.181, 1.804)], HAIR, 0.0052)
uv("Nose", (0.0, -0.183, 1.671), (0.0055, 0.0028, 0.0055), SKIN, 14, 8)
curve("Smile", [(-0.047, -0.180, 1.615), (-0.024, -0.185, 1.606), (0.0, -0.187, 1.604), (0.025, -0.185, 1.608), (0.048, -0.179, 1.617)], MOUTH, 0.0032)

# -----------------------------------------------------------------------------
# TROUSERS — looser thigh/seat and a gentle taper into rolled cuffs.
# -----------------------------------------------------------------------------
for side in (-1, 1):
    tr = bpy.data.objects.get(f"Trouser_{side}")
    cf = bpy.data.objects.get(f"TrouserCuff_{side}")
    if tr:
        tr.scale.x *= 1.12
        tr.scale.y *= 1.10
        tr.location.x *= 1.035
    if cf:
        cf.scale.x *= 1.045
        cf.scale.y *= 1.05
        cf.location.x *= 1.025
hips = bpy.data.objects.get("OverallHips")
if hips:
    hips.scale.x *= 1.06
    hips.scale.y *= 1.045

# -----------------------------------------------------------------------------
# ARMS + HANDS — rebuild as one relaxed chain with a larger, readable hand.
# Fingers are short lobes merged visually into the palm, not claws/cylinders.
# -----------------------------------------------------------------------------
HAND_LINE = bpy.data.materials.get("Hand Crease") or MOUTH
for side in (-1, 1):
    s = float(side)
    remove_many([
        f"Sleeve_{side}", f"RolledSleeve_{side}", f"Forearm_{side}",
        f"Palm_{side}", f"Thumb_{side}", f"ThumbTip_{side}",
    ] + [f"Finger_{side}_{i}" for i in range(4)] +
        [f"FingerTip_{side}_{i}" for i in range(4)] +
        [f"FingerGroove_{side}_{i}" for i in range(4)])

    shoulder = Vector((0.190*s, -0.004, 1.360))
    elbow = Vector((0.250*s, -0.020, 1.155))
    cuff_a = Vector((0.246*s, -0.026, 1.090))
    wrist = Vector((0.224*s, -0.055, 0.845))
    palm_c = Vector((0.220*s, -0.070, 0.775))

    tapered(f"Sleeve_{side}", shoulder, elbow, 0.074, 0.064, SHIRT, 28, 0.008)
    tapered(f"RolledSleeve_{side}", elbow, cuff_a, 0.068, 0.063, SHIRT_SHADOW, 26, 0.007)
    tapered(f"Forearm_{side}", cuff_a, wrist, 0.049, 0.041, SKIN, 24, 0.006)

    # Palm has soft knuckle width and tapered heel.
    profile(f"Palm_{side}", [
        (palm_c.z + 0.048, 0.034, 0.028, palm_c.x, palm_c.y),
        (palm_c.z + 0.022, 0.043, 0.033, palm_c.x, palm_c.y),
        (palm_c.z - 0.012, 0.044, 0.034, palm_c.x, palm_c.y - 0.002),
        (palm_c.z - 0.041, 0.040, 0.031, palm_c.x, palm_c.y - 0.003),
    ], SKIN, 28)

    # Finger pads: short, rounded, overlapped into the palm so they read as a hand.
    offs = (-0.024, -0.008, 0.008, 0.024)
    lens = (0.030, 0.038, 0.037, 0.029)
    for i, (off, ln) in enumerate(zip(offs, lens)):
        x = palm_c.x + off
        z = palm_c.z - 0.049 - ln*0.28
        uv(f"Finger_{side}_{i}", (x, palm_c.y - 0.004, z), (0.0125, 0.0130, ln), SKIN, 18, 10)
    thumb_a = Vector((palm_c.x + 0.032*s, palm_c.y - 0.002, palm_c.z + 0.006))
    thumb_b = Vector((palm_c.x + 0.055*s, palm_c.y - 0.012, palm_c.z - 0.025))
    tapered(f"Thumb_{side}", thumb_a, thumb_b, 0.0145, 0.0110, SKIN, 20, 0.0035)
    uv(f"ThumbTip_{side}", tuple(thumb_b), (0.0115, 0.0120, 0.0130), SKIN, 16, 10)

    # Two very subtle crease lines; enough separation without visual noise.
    for i, off in enumerate((-0.010, 0.010)):
        curve(f"FingerGroove_{side}_{i}", [
            (palm_c.x + off, palm_c.y - 0.034, palm_c.z - 0.025),
            (palm_c.x + off*0.85, palm_c.y - 0.034, palm_c.z - 0.050),
        ], HAND_LINE, 0.0014)

# -----------------------------------------------------------------------------
# HAIR — replace helmet/profile clumps with broad layered ribbon locks.
# A smaller continuous cap prevents scalp gaps; large ribbons create the shape.
# -----------------------------------------------------------------------------
remove_many([
    "HairBack",
    "V36FringeL", "V36FringeHero", "V36FringeR",
    "V36SideL", "V36SideR", "V36CrownL", "V36CrownC", "V36CrownR",
])

# Subtle under-cap, mostly hidden by locks.
uv("HairBack", (0.0, 0.040, 1.825), (0.204, 0.158, 0.170), HAIR, 40, 22)

# Front side-swept layers — chunky, asymmetrical, tips stop around brows/temples.
ribbon_lock("V37FringeHero", [
    (-0.150, -0.145, 1.930, 0.060),
    (-0.105, -0.166, 1.895, 0.070),
    (-0.050, -0.178, 1.842, 0.065),
    (0.004, -0.180, 1.790, 0.047),
    (0.035, -0.178, 1.752, 0.008),
], HAIR_WARM, 0.034)
ribbon_lock("V37FringeLeft", [
    (-0.188, -0.120, 1.905, 0.052),
    (-0.180, -0.150, 1.855, 0.058),
    (-0.168, -0.165, 1.805, 0.046),
    (-0.150, -0.166, 1.760, 0.008),
], HAIR, 0.032)
ribbon_lock("V37FringeMid", [
    (-0.025, -0.150, 1.944, 0.052),
    (0.025, -0.170, 1.905, 0.058),
    (0.075, -0.176, 1.856, 0.047),
    (0.102, -0.170, 1.812, 0.008),
], HAIR, 0.032)
ribbon_lock("V37FringeRight", [
    (0.085, -0.120, 1.925, 0.047),
    (0.132, -0.145, 1.895, 0.052),
    (0.168, -0.156, 1.850, 0.041),
    (0.178, -0.150, 1.806, 0.008),
], HAIR_WARM, 0.031)

# Crown layers create the messy concept silhouette without separated spikes.
ribbon_lock("V37CrownL", [
    (-0.175, 0.000, 1.930, 0.055),
    (-0.130, -0.010, 1.982, 0.062),
    (-0.080, -0.016, 2.020, 0.046),
    (-0.035, -0.020, 2.040, 0.008),
], HAIR_WARM, 0.038)
ribbon_lock("V37CrownC", [
    (-0.055, -0.010, 1.968, 0.050),
    (-0.015, -0.018, 2.022, 0.056),
    (0.022, -0.020, 2.060, 0.041),
    (0.055, -0.018, 2.078, 0.008),
], HAIR, 0.036)
ribbon_lock("V37CrownR", [
    (0.035, 0.000, 1.958, 0.050),
    (0.085, -0.008, 2.004, 0.056),
    (0.132, -0.010, 2.034, 0.041),
    (0.172, -0.006, 2.046, 0.008),
], HAIR_WARM, 0.036)

# Side/back locks break the helmet silhouette in side and 3/4 views.
ribbon_lock("V37TempleL", [
    (-0.193, -0.030, 1.862, 0.042),
    (-0.210, -0.048, 1.805, 0.046),
    (-0.211, -0.054, 1.742, 0.035),
    (-0.202, -0.050, 1.685, 0.008),
], HAIR, 0.031)
ribbon_lock("V37TempleR", [
    (0.192, -0.025, 1.858, 0.040),
    (0.207, -0.044, 1.805, 0.044),
    (0.208, -0.050, 1.748, 0.033),
    (0.198, -0.047, 1.698, 0.008),
], HAIR, 0.031)
ribbon_lock("V37BackL", [
    (-0.160, 0.110, 1.890, 0.040),
    (-0.190, 0.105, 1.835, 0.044),
    (-0.205, 0.090, 1.775, 0.035),
    (-0.202, 0.075, 1.718, 0.008),
], HAIR, 0.032)
ribbon_lock("V37BackR", [
    (0.158, 0.112, 1.885, 0.039),
    (0.188, 0.106, 1.835, 0.043),
    (0.202, 0.092, 1.780, 0.034),
    (0.200, 0.077, 1.725, 0.008),
], HAIR_WARM, 0.032)

# Export V3.7 candidate.
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
print(f"Exported Lembah Sari Character V3.7 silhouette/anatomy candidate to {OUT_PATH}")
