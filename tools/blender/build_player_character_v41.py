import bpy
import math
import os
from mathutils import Vector

# Lembah Sari Character V4.1 — simplification/appeal pass.
# Keeps the V4.0 head/outfit foundation but removes over-constructed forms:
# coherent hair mass + broad fringe, continuous sleeves/forearms, and one-piece hands.

BASE = os.path.join(os.path.dirname(__file__), "build_player_character_v40.py")
exec(compile(open(BASE, "r", encoding="utf-8").read(), BASE, "exec"), globals(), globals())


def remove_many(names):
    for name in names:
        obj = bpy.data.objects.get(name)
        if obj:
            bpy.data.objects.remove(obj, do_unlink=True)


def soft_tube(name, path, mat, sides=20):
    # path: [(x,y,z,rx,ry), ...], smooth continuous tube along centerline.
    verts = []
    faces = []
    n = len(path)
    for i, (x, y, z, rx, ry) in enumerate(path):
        for s in range(sides):
            a = math.tau * s / sides
            verts.append((x + math.cos(a) * rx, y + math.sin(a) * ry, z))
    for i in range(n - 1):
        a0 = i * sides
        b0 = (i + 1) * sides
        for s in range(sides):
            ns = (s + 1) % sides
            faces.append((a0+s, a0+ns, b0+ns, b0+s))
    faces.append(tuple(reversed(range(sides))))
    top = (n - 1) * sides
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
    sub = obj.modifiers.new("SoftTube", "SUBSURF")
    sub.subdivision_type = "CATMULL_CLARK"
    sub.levels = 1
    sub.render_levels = 1
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=sub.name)
    return obj


def hand_shape(name, side, center, mat):
    s = float(side)
    cx, y, cz = center
    # One readable relaxed hand silhouette. Tiny contour variations imply fingers,
    # but nothing hangs below as separate beads.
    local = [
        (-0.034, 0.052), (0.028, 0.050), (0.043, 0.033),
        (0.047, 0.010), (0.044, -0.018), (0.038, -0.044),
        (0.025, -0.061), (0.009, -0.068), (-0.010, -0.066),
        (-0.026, -0.057), (-0.038, -0.038), (-0.043, -0.012),
        (-0.041, 0.019),
    ]
    outline = [(cx + dx*s, cz + dz) for dx, dz in local]
    obj = solid_patch(name, outline, y, mat, 0.060, 0.010)
    return obj


# Warm concept skin; keep whites warm instead of stark.
recolor(SKIN, (0.75, 0.43, 0.29))
recolor(BLUSH, (0.74, 0.27, 0.18))
recolor(EYE_WHITE, (0.90, 0.83, 0.70))
recolor(HAIR, (0.070, 0.023, 0.008))
recolor(HAIR_WARM, (0.130, 0.045, 0.014))

# -----------------------------------------------------------------------------
# FACE — flatten eyes into the face and add lids so they stop reading googly.
# -----------------------------------------------------------------------------
remove_many([
    "EyeWhite_-1", "EyeWhite_1", "Iris_-1", "Iris_1", "Pupil_-1", "Pupil_1",
    "EyeGlint_-1", "EyeGlint_1", "BrowL", "BrowR",
])
for side in (-1, 1):
    s = float(side)
    x = 0.079*s
    uv(f"EyeWhite_{side}", (x, -0.180, 1.758), (0.057, 0.0065, 0.043), EYE_WHITE, 28, 16)
    uv(f"Iris_{side}", (x + 0.004*s, -0.186, 1.756), (0.031, 0.0045, 0.033), IRIS, 24, 14)
    uv(f"Pupil_{side}", (x + 0.005*s, -0.190, 1.756), (0.013, 0.0032, 0.020), PUPIL, 20, 12)
    uv(f"EyeGlint_{side}", (x - 0.006*s, -0.193, 1.770), (0.0055, 0.002, 0.006), EYE_WHITE, 12, 8)
curve("UpperLidL", [(-0.137,-0.182,1.778),(-0.092,-0.188,1.791),(-0.043,-0.183,1.780)], HAIR, 0.0042)
curve("UpperLidR", [(0.043,-0.183,1.780),(0.092,-0.188,1.791),(0.137,-0.182,1.778)], HAIR, 0.0042)
curve("BrowL", [(-0.143,-0.178,1.828),(-0.094,-0.184,1.842),(-0.049,-0.179,1.834)], HAIR, 0.0054)
curve("BrowR", [(0.049,-0.179,1.834),(0.094,-0.184,1.842),(0.143,-0.178,1.828)], HAIR, 0.0054)

# -----------------------------------------------------------------------------
# HAIR — remove all V40 locks. Keep a cohesive cap and only five broad pieces.
# -----------------------------------------------------------------------------
remove_many([
    "HairCap", "HairRear",
    "V40HeroSweep", "V40FrontLeft", "V40FrontMid", "V40FrontRight",
    "V40CrownL", "V40CrownC", "V40CrownR",
    "V40TempleL", "V40TempleR", "V40BackL", "V40BackR",
])

uv("HairMass", (0.0, 0.045, 1.840), (0.211, 0.164, 0.177), HAIR, 48, 26)
uv("HairBack", (0.0, 0.112, 1.790), (0.190, 0.154, 0.142), HAIR, 42, 24)

# Gentle top masses blend into cap instead of sticking up like fingers.
uv("HairTopL", (-0.085, 0.005, 1.965), (0.108, 0.080, 0.064), HAIR_WARM, 30, 18, rot=(math.radians(-8), math.radians(-10), math.radians(-14)))
uv("HairTopC", (0.010, -0.006, 1.986), (0.112, 0.080, 0.062), HAIR, 30, 18, rot=(math.radians(-6), math.radians(8), math.radians(8)))
uv("HairTopR", (0.095, 0.002, 1.955), (0.096, 0.074, 0.058), HAIR_WARM, 30, 18, rot=(math.radians(-4), math.radians(12), math.radians(18)))

# Broad beveled fringe pieces: side-swept and coherent, not sausage locks.
solid_patch("FringeHero", [
    (-0.185,1.930),(-0.120,1.955),(-0.040,1.934),(0.040,1.870),
    (0.070,1.815),(0.045,1.775),(-0.020,1.812),(-0.095,1.860),(-0.155,1.890)
], -0.170, HAIR_WARM, 0.050, 0.014)
solid_patch("FringeLeft", [
    (-0.205,1.895),(-0.168,1.920),(-0.118,1.885),(-0.132,1.820),
    (-0.155,1.765),(-0.190,1.735),(-0.207,1.780)
], -0.158, HAIR, 0.045, 0.012)
solid_patch("FringeRight", [
    (0.035,1.925),(0.105,1.930),(0.168,1.890),(0.190,1.842),
    (0.176,1.805),(0.138,1.830),(0.085,1.870)
], -0.160, HAIR, 0.045, 0.012)

uv("SideLockL", (-0.194, -0.018, 1.775), (0.045, 0.042, 0.096), HAIR, 24, 14, rot=(math.radians(4),0,math.radians(-7)))
uv("SideLockR", (0.194, -0.014, 1.785), (0.043, 0.040, 0.090), HAIR, 24, 14, rot=(math.radians(4),0,math.radians(8)))

# -----------------------------------------------------------------------------
# ARMS — one continuous cloth sleeve + one continuous forearm per side.
# -----------------------------------------------------------------------------
for side in (-1, 1):
    s = float(side)
    remove_many([
        f"Sleeve_{side}", f"SleeveLower_{side}", f"RolledSleeve_{side}",
        f"Forearm_{side}", f"Palm_{side}", f"Thumb_{side}", f"ThumbTip_{side}",
    ] + [f"Finger_{side}_{i}" for i in range(4)])

    soft_tube(f"Sleeve_{side}", [
        (0.205*s,-0.003,1.365,0.083,0.075),
        (0.236*s,-0.010,1.300,0.085,0.076),
        (0.258*s,-0.018,1.225,0.079,0.071),
        (0.262*s,-0.024,1.150,0.070,0.064),
        (0.256*s,-0.028,1.105,0.066,0.060),
    ], SHIRT, 22)
    soft_tube(f"RolledSleeve_{side}", [
        (0.256*s,-0.028,1.112,0.071,0.064),
        (0.254*s,-0.030,1.082,0.073,0.065),
        (0.251*s,-0.032,1.052,0.067,0.060),
    ], SHIRT_SHADOW, 22)
    soft_tube(f"Forearm_{side}", [
        (0.248*s,-0.036,1.045,0.049,0.043),
        (0.241*s,-0.044,0.970,0.047,0.041),
        (0.232*s,-0.052,0.895,0.043,0.038),
        (0.225*s,-0.060,0.835,0.038,0.034),
    ], SKIN, 20)

    p = (0.222*s, -0.074, 0.775)
    hand_shape(f"Palm_{side}", side, p, SKIN)
    # Thumb is a single soft oval emerging from the palm outer edge.
    uv(f"Thumb_{side}", (p[0] + 0.043*s, p[1]-0.010, p[2]+0.002), (0.018,0.016,0.035), SKIN, 20, 12, rot=(0,math.radians(8*s),math.radians(20*s)))
    # Subtle two crease strokes hint at fingers without separate geometry.
    curve(f"HandCreaseA_{side}", [(p[0]-0.010*s,p[1]-0.032,p[2]-0.012),(p[0]-0.006*s,p[1]-0.033,p[2]-0.038)], MOUTH, 0.0013)
    curve(f"HandCreaseB_{side}", [(p[0]+0.010*s,p[1]-0.032,p[2]-0.010),(p[0]+0.012*s,p[1]-0.033,p[2]-0.036)], MOUTH, 0.0013)

# Looser lower-body read, closer to concept turnout.
for side in (-1,1):
    tr = bpy.data.objects.get(f"Trouser_{side}")
    if tr:
        tr.scale.x *= 1.055
        tr.scale.y *= 1.035
hips = bpy.data.objects.get("OverallHips")
if hips:
    hips.scale.x *= 1.025

# Export V4.1 candidate.
bpy.ops.object.select_all(action="DESELECT")
ROOT.select_set(True)
for obj in ROOT.children_recursive:
    obj.select_set(True)
bpy.context.view_layer.objects.active = ROOT
bpy.ops.export_scene.gltf(filepath=OUT_PATH, export_format="GLB", use_selection=True, export_apply=True, export_yup=True)
print(f"Exported Lembah Sari Character V4.1 simplified appeal candidate to {OUT_PATH}")
