import bpy
import math
import os
from mathutils import Vector

# Lembah Sari Character V3.8 — volumetric appeal pass.
# Builds on V3.7 but replaces flat ribbon hair with smooth lofted 3D locks,
# enlarges/softens the face and hands, and relaxes the upper-body silhouette.

BASE = os.path.join(os.path.dirname(__file__), "build_player_character_v37.py")
exec(compile(open(BASE, "r", encoding="utf-8").read(), BASE, "exec"), globals(), globals())


def remove_many(names):
    for name in names:
        obj = bpy.data.objects.get(name)
        if obj:
            bpy.data.objects.remove(obj, do_unlink=True)


def loft_lock(name, path, mat, sides=10):
    # path: [(x,y,z,width,depth), ...]
    verts = []
    faces = []
    n = len(path)
    for i, (x, y, z, w, d) in enumerate(path):
        if i == 0:
            x2, _, z2, _, _ = path[i+1]
            tx, tz = x2-x, z2-z
        elif i == n-1:
            x1, _, z1, _, _ = path[i-1]
            tx, tz = x-x1, z-z1
        else:
            x1, _, z1, _, _ = path[i-1]
            x2, _, z2, _, _ = path[i+1]
            tx, tz = x2-x1, z2-z1
        ln = max(1e-6, math.sqrt(tx*tx + tz*tz))
        px, pz = -tz/ln, tx/ln
        for s in range(sides):
            a = math.tau * s / sides
            c = math.cos(a)
            sn = math.sin(a)
            verts.append((x + px*w*c, y + d*sn, z + pz*w*c))
    for i in range(n-1):
        base = i*sides
        nxt = (i+1)*sides
        for s in range(sides):
            ns = (s+1) % sides
            faces.append((base+s, base+ns, nxt+ns, nxt+s))
    faces.append(tuple(reversed(range(sides))))
    top = (n-1)*sides
    faces.append(tuple(top+s for s in range(sides)))
    mesh = bpy.data.meshes.new(name + "Mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.parent = ROOT
    obj.data.materials.append(mat)
    for p in obj.data.polygons:
        p.use_smooth = True
    bevel(obj, 0.004, 2)
    return obj


# -----------------------------------------------------------------------------
# HEAD / FACE — slightly fuller cheek/skull volume; eyes larger and softer.
# -----------------------------------------------------------------------------
head = bpy.data.objects.get("Head")
if head:
    world_scale_about(head, (0.0, 0.0, 1.720), 1.035, 1.070, 1.025)
for side in (-1, 1):
    ear = bpy.data.objects.get(f"Ear_{side}")
    blush = bpy.data.objects.get(f"Blush_{side}")
    if ear:
        world_scale_about(ear, (0.0, 0.0, 1.720), 1.035, 1.050, 1.025)
    if blush:
        world_scale_about(blush, (0.0, 0.0, 1.720), 1.035, 1.050, 1.025)

remove_many([
    "EyeWhite_-1", "EyeWhite_1", "Iris_-1", "Iris_1", "Pupil_-1", "Pupil_1",
    "EyeGlint_-1", "EyeGlint_1", "BrowL", "BrowR", "Nose", "Smile",
])

# Re-use V3.7 almond helper, now with a concept-like larger eye/iris balance.
for side in (-1, 1):
    s = float(side)
    cx = 0.078*s
    almond(f"EyeWhite_{side}", cx, 1.752, 0.059, 0.038, -0.194, EYE_WHITE, 0.006)
    almond(f"Iris_{side}", cx + 0.004*s, 1.750, 0.031, 0.034, -0.199, IRIS, 0.006)
    almond(f"Pupil_{side}", cx + 0.005*s, 1.750, 0.014, 0.021, -0.203, PUPIL, 0.005)
    uv(f"EyeGlint_{side}", (cx - 0.006*s, -0.207, 1.766), (0.0058, 0.0022, 0.0068), EYE_WHITE, 12, 8)

curve("BrowL", [(-0.138, -0.189, 1.814), (-0.088, -0.195, 1.830), (-0.043, -0.189, 1.822)], HAIR, 0.0055)
curve("BrowR", [(0.043, -0.189, 1.822), (0.088, -0.195, 1.830), (0.138, -0.189, 1.814)], HAIR, 0.0055)
uv("Nose", (0.0, -0.193, 1.674), (0.0055, 0.0026, 0.0058), SKIN, 14, 8)
curve("Smile", [(-0.050, -0.190, 1.616), (-0.025, -0.195, 1.608), (0.0, -0.197, 1.607), (0.026, -0.195, 1.611), (0.052, -0.189, 1.620)], MOUTH, 0.0033)

# -----------------------------------------------------------------------------
# UPPER BODY — broaden chest slightly and soften sleeve relation.
# -----------------------------------------------------------------------------
for name, sx, sy in [
    ("ShirtTorso", 1.070, 1.035),
    ("OverallBib", 1.045, 1.000),
    ("BibPocket", 1.035, 1.000),
]:
    obj = bpy.data.objects.get(name)
    if obj:
        obj.scale.x *= sx
        obj.scale.y *= sy

for side in (-1, 1):
    s = float(side)
    remove_many([
        f"Sleeve_{side}", f"RolledSleeve_{side}", f"Forearm_{side}",
        f"Palm_{side}", f"Thumb_{side}", f"ThumbTip_{side}",
    ] + [f"Finger_{side}_{i}" for i in range(4)] +
        [f"FingerTip_{side}_{i}" for i in range(4)] +
        [f"FingerGroove_{side}_{i}" for i in range(4)])

    shoulder = Vector((0.202*s, -0.003, 1.365))
    upper = Vector((0.266*s, -0.018, 1.205))
    elbow = Vector((0.258*s, -0.024, 1.120))
    wrist = Vector((0.232*s, -0.056, 0.850))
    palm_c = Vector((0.228*s, -0.071, 0.770))

    # Slight fabric puff at upper arm, then rolled cuff.
    tapered(f"Sleeve_{side}", shoulder, upper, 0.087, 0.075, SHIRT, 30, 0.009)
    tapered(f"SleeveLower_{side}", upper, elbow, 0.076, 0.068, SHIRT, 28, 0.008)
    tapered(f"RolledSleeve_{side}", elbow, Vector((0.255*s, -0.028, 1.070)), 0.071, 0.066, SHIRT_SHADOW, 28, 0.007)
    tapered(f"Forearm_{side}", Vector((0.255*s, -0.028, 1.070)), wrist, 0.051, 0.043, SKIN, 26, 0.006)

    # Larger palm and finger lobes; proportions intentionally closer to the concept.
    profile(f"Palm_{side}", [
        (palm_c.z + 0.052, 0.038, 0.031, palm_c.x, palm_c.y),
        (palm_c.z + 0.024, 0.048, 0.037, palm_c.x, palm_c.y),
        (palm_c.z - 0.012, 0.050, 0.038, palm_c.x, palm_c.y - 0.002),
        (palm_c.z - 0.044, 0.045, 0.034, palm_c.x, palm_c.y - 0.004),
    ], SKIN, 30)

    offs = (-0.029, -0.010, 0.010, 0.029)
    lens = (0.033, 0.043, 0.041, 0.032)
    for i, (off, ln) in enumerate(zip(offs, lens)):
        x = palm_c.x + off
        z = palm_c.z - 0.052 - ln*0.24
        uv(f"Finger_{side}_{i}", (x, palm_c.y - 0.005, z), (0.0145, 0.0150, ln), SKIN, 20, 12)
    thumb_a = Vector((palm_c.x + 0.038*s, palm_c.y - 0.002, palm_c.z + 0.006))
    thumb_b = Vector((palm_c.x + 0.064*s, palm_c.y - 0.013, palm_c.z - 0.028))
    tapered(f"Thumb_{side}", thumb_a, thumb_b, 0.0160, 0.0125, SKIN, 22, 0.0035)
    uv(f"ThumbTip_{side}", tuple(thumb_b), (0.0128, 0.0132, 0.0140), SKIN, 18, 10)

# -----------------------------------------------------------------------------
# HAIR — true 3D broad lofted locks over a smaller under-cap.
# -----------------------------------------------------------------------------
remove_many([
    "HairBack",
    "V37FringeHero", "V37FringeLeft", "V37FringeMid", "V37FringeRight",
    "V37CrownL", "V37CrownC", "V37CrownR",
    "V37TempleL", "V37TempleR", "V37BackL", "V37BackR",
])

# Smaller cap + rear volume: enough continuity, not a helmet.
uv("HairCap", (0.0, 0.030, 1.830), (0.198, 0.150, 0.166), HAIR, 42, 24)
uv("HairRear", (0.0, 0.095, 1.800), (0.184, 0.150, 0.150), HAIR, 36, 20)

# Front asymmetric locks. Broad, flattened in depth, with smooth pointed tips.
loft_lock("V38HeroSweep", [
    (-0.165, -0.118, 1.940, 0.074, 0.032),
    (-0.120, -0.150, 1.905, 0.080, 0.034),
    (-0.065, -0.173, 1.855, 0.074, 0.033),
    (-0.005, -0.183, 1.800, 0.055, 0.028),
    (0.038, -0.181, 1.758, 0.009, 0.008),
], HAIR_WARM, 12)
loft_lock("V38FrontLeft", [
    (-0.200, -0.090, 1.910, 0.058, 0.030),
    (-0.192, -0.132, 1.858, 0.064, 0.032),
    (-0.177, -0.158, 1.805, 0.052, 0.028),
    (-0.155, -0.164, 1.760, 0.008, 0.007),
], HAIR, 12)
loft_lock("V38FrontMid", [
    (-0.035, -0.122, 1.955, 0.060, 0.030),
    (0.018, -0.155, 1.920, 0.066, 0.032),
    (0.070, -0.176, 1.875, 0.054, 0.029),
    (0.105, -0.177, 1.825, 0.008, 0.007),
], HAIR, 12)
loft_lock("V38FrontRight", [
    (0.090, -0.090, 1.930, 0.054, 0.028),
    (0.140, -0.124, 1.900, 0.058, 0.030),
    (0.176, -0.150, 1.855, 0.048, 0.026),
    (0.185, -0.154, 1.810, 0.008, 0.007),
], HAIR_WARM, 12)

# Crown: fewer, larger locks like the concept art.
loft_lock("V38CrownLeft", [
    (-0.175, 0.010, 1.935, 0.064, 0.036),
    (-0.130, -0.005, 1.990, 0.070, 0.037),
    (-0.075, -0.014, 2.030, 0.052, 0.032),
    (-0.025, -0.018, 2.052, 0.008, 0.007),
], HAIR_WARM, 12)
loft_lock("V38CrownCenter", [
    (-0.045, 0.002, 1.972, 0.058, 0.034),
    (-0.005, -0.010, 2.030, 0.064, 0.035),
    (0.030, -0.015, 2.072, 0.047, 0.029),
    (0.060, -0.014, 2.092, 0.008, 0.007),
], HAIR, 12)
loft_lock("V38CrownRight", [
    (0.045, 0.010, 1.960, 0.056, 0.033),
    (0.098, -0.002, 2.008, 0.062, 0.034),
    (0.148, -0.008, 2.040, 0.046, 0.028),
    (0.187, -0.006, 2.052, 0.008, 0.007),
], HAIR_WARM, 12)

# Temple and rear breakup for 3/4 / side views.
loft_lock("V38TempleL", [
    (-0.198, -0.010, 1.865, 0.046, 0.028),
    (-0.216, -0.030, 1.810, 0.050, 0.030),
    (-0.216, -0.042, 1.750, 0.038, 0.025),
    (-0.205, -0.040, 1.692, 0.008, 0.007),
], HAIR, 10)
loft_lock("V38TempleR", [
    (0.196, -0.006, 1.860, 0.044, 0.028),
    (0.214, -0.026, 1.810, 0.048, 0.029),
    (0.214, -0.038, 1.756, 0.036, 0.024),
    (0.202, -0.038, 1.704, 0.008, 0.007),
], HAIR, 10)
loft_lock("V38BackLeft", [
    (-0.150, 0.130, 1.900, 0.048, 0.034),
    (-0.188, 0.135, 1.850, 0.052, 0.036),
    (-0.205, 0.122, 1.792, 0.040, 0.030),
    (-0.200, 0.102, 1.730, 0.008, 0.007),
], HAIR, 10)
loft_lock("V38BackRight", [
    (0.150, 0.132, 1.895, 0.047, 0.034),
    (0.186, 0.136, 1.850, 0.051, 0.035),
    (0.203, 0.124, 1.798, 0.039, 0.029),
    (0.198, 0.104, 1.738, 0.008, 0.007),
], HAIR_WARM, 10)

# Export V3.8 candidate.
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
print(f"Exported Lembah Sari Character V3.8 volumetric appeal candidate to {OUT_PATH}")
