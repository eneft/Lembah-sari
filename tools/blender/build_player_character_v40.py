import bpy
import math
import os
from mathutils import Vector

# Lembah Sari Character V4.0 — major appeal rebuild.
# Rebuilds the visual core instead of continuing the V3.x patch chain:
# new tapered head/face, smooth 3D oval eyes, rounded subdivided hair locks,
# soft sleeve/forearm volumes, and relaxed semi-closed hands.

BASE = os.path.join(os.path.dirname(__file__), "build_player_character_v39.py")
exec(compile(open(BASE, "r", encoding="utf-8").read(), BASE, "exec"), globals(), globals())


def remove_many(names):
    for name in names:
        obj = bpy.data.objects.get(name)
        if obj:
            bpy.data.objects.remove(obj, do_unlink=True)


def ellipsoid_between(name, p1, p2, radius_x, radius_y, mat, segments=30, rings=18):
    a = Vector(p1)
    b = Vector(p2)
    d = b - a
    mid = (a + b) * 0.5
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings, radius=1.0, location=mid)
    obj = bpy.context.object
    obj.name = name
    obj.scale = (radius_x, radius_y, d.length * 0.5)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.rotation_mode = "QUATERNION"
    obj.rotation_quaternion = Vector((0.0, 0.0, 1.0)).rotation_difference(d.normalized())
    for poly in obj.data.polygons:
        poly.use_smooth = True
    obj.data.materials.append(mat)
    obj.parent = ROOT
    return obj


def smooth_loft(name, path, mat, sides=16):
    # path: [(x,y,z,width,depth), ...]
    verts = []
    faces = []
    n = len(path)
    for i, (x, y, z, w, d) in enumerate(path):
        if i == 0:
            x2, _, z2, _, _ = path[i + 1]
            tx, tz = x2 - x, z2 - z
        elif i == n - 1:
            x1, _, z1, _, _ = path[i - 1]
            tx, tz = x - x1, z - z1
        else:
            x1, _, z1, _, _ = path[i - 1]
            x2, _, z2, _, _ = path[i + 1]
            tx, tz = x2 - x1, z2 - z1
        ln = max(1e-6, math.sqrt(tx * tx + tz * tz))
        px, pz = -tz / ln, tx / ln
        for s in range(sides):
            a = math.tau * s / sides
            c = math.cos(a)
            sn = math.sin(a)
            verts.append((x + px * w * c, y + d * sn, z + pz * w * c))
    for i in range(n - 1):
        base = i * sides
        nxt = (i + 1) * sides
        for s in range(sides):
            ns = (s + 1) % sides
            faces.append((base + s, base + ns, nxt + ns, nxt + s))
    faces.append(tuple(reversed(range(sides))))
    top = (n - 1) * sides
    faces.append(tuple(top + s for s in range(sides)))
    mesh = bpy.data.meshes.new(name + "Mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.parent = ROOT
    obj.data.materials.append(mat)
    for poly in obj.data.polygons:
        poly.use_smooth = True
    sub = obj.modifiers.new("SoftHair", "SUBSURF")
    sub.subdivision_type = "CATMULL_CLARK"
    sub.levels = 1
    sub.render_levels = 1
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=sub.name)
    return obj


# Approved concept palette: warm skin, deep brown hair, cream + moss clothing.
recolor(SKIN, (0.86, 0.57, 0.39))
recolor(BLUSH, (0.82, 0.34, 0.24))
recolor(HAIR, (0.045, 0.018, 0.010))
recolor(HAIR_WARM, (0.085, 0.034, 0.016))
recolor(EYE_WHITE, (0.94, 0.88, 0.76))
recolor(IRIS, (0.115, 0.040, 0.012))

# -----------------------------------------------------------------------------
# HEAD / FACE — replace inherited V3.x face entirely.
# -----------------------------------------------------------------------------
remove_many([
    "Head", "Ear_-1", "Ear_1", "Blush_-1", "Blush_1",
    "EyeWhite_-1", "EyeWhite_1", "Iris_-1", "Iris_1", "Pupil_-1", "Pupil_1",
    "EyeGlint_-1", "EyeGlint_1", "BrowL", "BrowR", "Nose", "Smile",
])

# Round skull, soft cheek volume and a slightly tapered lower face.
profile("Head", [
    (1.515, 0.060, 0.078, 0.0, 0.000),
    (1.540, 0.108, 0.120, 0.0, -0.004),
    (1.590, 0.158, 0.158, 0.0, -0.004),
    (1.655, 0.192, 0.178, 0.0, -0.002),
    (1.735, 0.205, 0.184, 0.0, 0.000),
    (1.815, 0.198, 0.181, 0.0, 0.003),
    (1.885, 0.178, 0.168, 0.0, 0.005),
    (1.940, 0.135, 0.142, 0.0, 0.005),
    (1.975, 0.078, 0.095, 0.0, 0.003),
], SKIN, 40)

for side in (-1, 1):
    s = float(side)
    uv(f"Ear_{side}", (0.201 * s, -0.002, 1.730), (0.041, 0.026, 0.058), SKIN, 22, 12)
    uv(f"Blush_{side}", (0.118 * s, -0.184, 1.648), (0.026, 0.0022, 0.012), BLUSH, 16, 8)
    x = 0.079 * s
    uv(f"EyeWhite_{side}", (x, -0.190, 1.758), (0.059, 0.014, 0.048), EYE_WHITE, 28, 16)
    uv(f"Iris_{side}", (x + 0.004 * s, -0.202, 1.756), (0.033, 0.008, 0.037), IRIS, 24, 14)
    uv(f"Pupil_{side}", (x + 0.005 * s, -0.209, 1.756), (0.014, 0.005, 0.022), PUPIL, 20, 12)
    uv(f"EyeGlint_{side}", (x - 0.007 * s, -0.214, 1.773), (0.006, 0.003, 0.007), EYE_WHITE, 12, 8)

curve("BrowL", [(-0.145, -0.185, 1.829), (-0.095, -0.192, 1.845), (-0.047, -0.186, 1.836)], HAIR, 0.0062)
curve("BrowR", [(0.047, -0.186, 1.836), (0.095, -0.192, 1.845), (0.145, -0.185, 1.829)], HAIR, 0.0062)
uv("Nose", (0.0, -0.188, 1.670), (0.007, 0.005, 0.009), SKIN, 16, 10)
curve("Smile", [(-0.052, -0.190, 1.613), (-0.026, -0.197, 1.604), (0.0, -0.199, 1.603), (0.028, -0.197, 1.608), (0.055, -0.189, 1.618)], MOUTH, 0.0034)

# -----------------------------------------------------------------------------
# UPPER BODY / ARMS — replace segmented cylinder read with soft volumes.
# -----------------------------------------------------------------------------
for name, sx, sy in [
    ("ShirtTorso", 1.050, 1.025),
    ("OverallBib", 1.025, 1.000),
    ("BibPocket", 1.020, 1.000),
]:
    obj = bpy.data.objects.get(name)
    if obj:
        obj.scale.x *= sx
        obj.scale.y *= sy

for side in (-1, 1):
    s = float(side)
    remove_many([
        f"Sleeve_{side}", f"SleeveLower_{side}", f"RolledSleeve_{side}", f"Forearm_{side}",
        f"Palm_{side}", f"Thumb_{side}", f"ThumbTip_{side}",
    ] + [f"Finger_{side}_{i}" for i in range(4)] + [f"FingerTip_{side}_{i}" for i in range(4)] + [f"FingerGroove_{side}_{i}" for i in range(4)])

    shoulder = Vector((0.212 * s, -0.002, 1.365))
    upper_mid = Vector((0.265 * s, -0.015, 1.235))
    elbow = Vector((0.258 * s, -0.025, 1.115))
    cuff_end = Vector((0.252 * s, -0.032, 1.065))
    wrist = Vector((0.228 * s, -0.057, 0.855))
    palm_c = Vector((0.224 * s, -0.071, 0.770))

    ellipsoid_between(f"Sleeve_{side}", shoulder, upper_mid, 0.094, 0.082, SHIRT)
    ellipsoid_between(f"SleeveLower_{side}", upper_mid, elbow, 0.080, 0.070, SHIRT)
    tapered(f"RolledSleeve_{side}", elbow, cuff_end, 0.073, 0.068, SHIRT_SHADOW, 30, 0.006)
    ellipsoid_between(f"Forearm_{side}", cuff_end, wrist, 0.050, 0.043, SKIN, 28, 16)

    # One coherent relaxed hand; finger pads overlap the palm instead of dangling.
    profile(f"Palm_{side}", [
        (palm_c.z + 0.055, 0.040, 0.033, palm_c.x, palm_c.y),
        (palm_c.z + 0.025, 0.050, 0.039, palm_c.x, palm_c.y),
        (palm_c.z - 0.010, 0.052, 0.040, palm_c.x, palm_c.y - 0.002),
        (palm_c.z - 0.040, 0.047, 0.036, palm_c.x, palm_c.y - 0.004),
        (palm_c.z - 0.058, 0.040, 0.031, palm_c.x, palm_c.y - 0.005),
    ], SKIN, 32)

    offs = (-0.028, -0.009, 0.010, 0.029)
    zoffs = (-0.047, -0.053, -0.052, -0.045)
    for i, (off, zo) in enumerate(zip(offs, zoffs)):
        uv(f"Finger_{side}_{i}", (palm_c.x + off, palm_c.y - 0.006, palm_c.z + zo), (0.015, 0.014, 0.020), SKIN, 20, 12)

    thumb_a = Vector((palm_c.x + 0.039 * s, palm_c.y - 0.001, palm_c.z + 0.010))
    thumb_b = Vector((palm_c.x + 0.063 * s, palm_c.y - 0.013, palm_c.z - 0.022))
    ellipsoid_between(f"Thumb_{side}", thumb_a, thumb_b, 0.016, 0.014, SKIN, 22, 14)
    uv(f"ThumbTip_{side}", tuple(thumb_b), (0.013, 0.013, 0.014), SKIN, 18, 10)

# -----------------------------------------------------------------------------
# HAIR — fully remove V3.9 pieces and rebuild rounded subdivided locks.
# -----------------------------------------------------------------------------
remove_many([
    "HairCap", "HairRear",
    "V39HeroSweep", "V39FrontLeft", "V39FrontMid", "V39FrontRight",
    "V39CrownL", "V39CrownC", "V39CrownR",
    "V39TempleL", "V39TempleR", "V39BackLeft", "V39BackRight",
])

uv("HairCap", (0.0, 0.040, 1.848), (0.205, 0.158, 0.172), HAIR, 48, 26)
uv("HairRear", (0.0, 0.112, 1.815), (0.190, 0.156, 0.154), HAIR, 44, 24)

smooth_loft("V40HeroSweep", [
    (-0.182, -0.090, 1.953, 0.072, 0.034), (-0.155, -0.116, 1.936, 0.080, 0.036),
    (-0.122, -0.142, 1.912, 0.084, 0.037), (-0.082, -0.165, 1.884, 0.082, 0.037),
    (-0.040, -0.183, 1.850, 0.075, 0.035), (0.000, -0.194, 1.814, 0.062, 0.031),
    (0.030, -0.196, 1.780, 0.040, 0.024), (0.048, -0.194, 1.758, 0.010, 0.008),
], HAIR_WARM, 16)
smooth_loft("V40FrontLeft", [
    (-0.205, -0.060, 1.922, 0.055, 0.031), (-0.210, -0.092, 1.894, 0.062, 0.033),
    (-0.207, -0.125, 1.860, 0.061, 0.032), (-0.197, -0.151, 1.824, 0.054, 0.030),
    (-0.180, -0.166, 1.790, 0.040, 0.025), (-0.160, -0.168, 1.762, 0.009, 0.008),
], HAIR, 16)
smooth_loft("V40FrontMid", [
    (-0.035, -0.090, 1.962, 0.056, 0.032), (0.000, -0.120, 1.947, 0.063, 0.034),
    (0.038, -0.148, 1.923, 0.062, 0.033), (0.072, -0.171, 1.892, 0.055, 0.030),
    (0.098, -0.184, 1.856, 0.040, 0.025), (0.110, -0.184, 1.830, 0.009, 0.008),
], HAIR, 16)
smooth_loft("V40FrontRight", [
    (0.090, -0.060, 1.940, 0.050, 0.029), (0.125, -0.086, 1.928, 0.057, 0.031),
    (0.158, -0.115, 1.905, 0.057, 0.031), (0.181, -0.141, 1.875, 0.050, 0.029),
    (0.193, -0.157, 1.842, 0.035, 0.023), (0.195, -0.158, 1.818, 0.009, 0.008),
], HAIR_WARM, 16)

smooth_loft("V40CrownL", [
    (-0.180, 0.015, 1.945, 0.060, 0.036), (-0.150, 0.003, 1.978, 0.068, 0.038),
    (-0.112, -0.007, 2.010, 0.067, 0.038), (-0.073, -0.012, 2.036, 0.055, 0.034),
    (-0.036, -0.014, 2.052, 0.038, 0.026), (-0.010, -0.013, 2.058, 0.009, 0.008),
], HAIR_WARM, 16)
smooth_loft("V40CrownC", [
    (-0.050, 0.012, 1.985, 0.055, 0.034), (-0.024, 0.002, 2.018, 0.062, 0.036),
    (0.005, -0.005, 2.050, 0.060, 0.035), (0.032, -0.009, 2.078, 0.049, 0.031),
    (0.054, -0.009, 2.096, 0.032, 0.023), (0.070, -0.008, 2.103, 0.008, 0.007),
], HAIR, 16)
smooth_loft("V40CrownR", [
    (0.045, 0.017, 1.970, 0.053, 0.033), (0.080, 0.008, 2.000, 0.060, 0.035),
    (0.116, 0.001, 2.026, 0.059, 0.034), (0.150, -0.002, 2.047, 0.047, 0.030),
    (0.178, -0.001, 2.060, 0.031, 0.022), (0.198, 0.001, 2.064, 0.008, 0.007),
], HAIR_WARM, 16)

smooth_loft("V40TempleL", [
    (-0.204, 0.000, 1.880, 0.044, 0.029), (-0.220, -0.014, 1.840, 0.050, 0.031),
    (-0.225, -0.028, 1.796, 0.049, 0.030), (-0.222, -0.039, 1.750, 0.040, 0.027),
    (-0.212, -0.043, 1.708, 0.028, 0.021), (-0.202, -0.040, 1.684, 0.008, 0.007),
], HAIR, 14)
smooth_loft("V40TempleR", [
    (0.202, 0.002, 1.878, 0.043, 0.028), (0.218, -0.012, 1.840, 0.049, 0.030),
    (0.223, -0.026, 1.800, 0.048, 0.030), (0.220, -0.037, 1.756, 0.039, 0.026),
    (0.210, -0.041, 1.716, 0.027, 0.020), (0.200, -0.038, 1.694, 0.008, 0.007),
], HAIR, 14)
smooth_loft("V40BackL", [
    (-0.150, 0.140, 1.910, 0.047, 0.034), (-0.180, 0.148, 1.875, 0.053, 0.036),
    (-0.202, 0.147, 1.835, 0.051, 0.035), (-0.215, 0.137, 1.792, 0.043, 0.031),
    (-0.214, 0.121, 1.750, 0.031, 0.024), (-0.204, 0.104, 1.720, 0.008, 0.007),
], HAIR, 14)
smooth_loft("V40BackR", [
    (0.150, 0.142, 1.908, 0.046, 0.034), (0.178, 0.150, 1.875, 0.052, 0.036),
    (0.200, 0.149, 1.838, 0.050, 0.035), (0.213, 0.139, 1.798, 0.042, 0.030),
    (0.212, 0.123, 1.758, 0.030, 0.023), (0.202, 0.106, 1.730, 0.008, 0.007),
], HAIR_WARM, 14)

# Export V4.0 candidate.
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
print(f"Exported Lembah Sari Character V4.0 major appeal rebuild to {OUT_PATH}")
