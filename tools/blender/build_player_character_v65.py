import bpy
import math
import os

# Lembah Sari Character V6.5 — silhouette continuity pass.
# Candidate only. Rebuilds the remaining mannequin-like weak points visible in
# the V6.4 turnaround: upper-sleeve capsules, wrist/hand segmentation, straight
# trouser columns, and flat front-hair plates.

BASE = os.path.join(os.path.dirname(__file__), "build_player_character_v64.py")
exec(compile(open(BASE, "r", encoding="utf-8").read(), BASE, "exec"), globals(), globals())


def remove_many(names):
    for name in names:
        obj = bpy.data.objects.get(name)
        if obj:
            bpy.data.objects.remove(obj, do_unlink=True)


def continuous_skin_arm(name, side):
    """One continuous forearm -> wrist -> relaxed hand silhouette."""
    s = float(side)
    # z, absolute x center, x radius, y radius.
    # The hand grows naturally from the wrist; outward center drift supplies a
    # thumb-side silhouette without attaching a separate thumb primitive.
    rings = [
        (1.088, 0.229, 0.039, 0.034),
        (1.045, 0.228, 0.038, 0.033),
        (0.995, 0.226, 0.036, 0.031),
        (0.945, 0.224, 0.033, 0.029),
        (0.900, 0.222, 0.030, 0.026),
        (0.866, 0.221, 0.027, 0.023),
        (0.842, 0.222, 0.031, 0.024),
        (0.816, 0.225, 0.037, 0.026),
        (0.790, 0.228, 0.041, 0.027),
        (0.764, 0.228, 0.040, 0.026),
        (0.741, 0.226, 0.036, 0.024),
        (0.722, 0.223, 0.030, 0.021),
        (0.708, 0.221, 0.022, 0.017),
        (0.700, 0.220, 0.013, 0.011),
    ]
    sides = 36
    verts, faces = [], []
    for z, cxa, rx, ry in rings:
        cx = cxa * s
        for i in range(sides):
            a = math.tau * i / sides
            ca = math.cos(a)
            # Slight outer-side fullness around the palm, kept inside the same
            # mesh so the result still reads as one stylized hand.
            outer = max(0.0, ca * s)
            palm = max(0.0, min(1.0, (0.87 - z) / 0.08)) if z < 0.87 else 0.0
            x = cx + ca * rx + s * outer * palm * 0.0035
            y = -0.045 - (1.088 - z) * 0.070 + math.sin(a) * ry
            verts.append((x, y, z))
    for r in range(len(rings) - 1):
        a0 = r * sides
        b0 = (r + 1) * sides
        for i in range(sides):
            j = (i + 1) % sides
            faces.append((a0 + i, a0 + j, b0 + j, b0 + i))
    faces.append(tuple(reversed(range(sides))))
    end = (len(rings) - 1) * sides
    faces.append(tuple(end + i for i in range(sides)))

    mesh = bpy.data.meshes.new(name + "Mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.parent = ROOT
    obj.data.materials.append(SKIN)
    for p in obj.data.polygons:
        p.use_smooth = True
    bev = obj.modifiers.new("ArmHandSoftness", "BEVEL")
    bev.width = 0.0032
    bev.segments = 3
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    try:
        bpy.ops.object.modifier_apply(modifier=bev.name)
    except Exception:
        pass
    return obj


def taper_trouser(obj):
    """Preserve relaxed thigh volume while tapering naturally to the ankle."""
    if not obj or obj.type != 'MESH' or not obj.data.vertices:
        return
    xs = [v.co.x for v in obj.data.vertices]
    ys = [v.co.y for v in obj.data.vertices]
    zs = [v.co.z for v in obj.data.vertices]
    cx = (min(xs) + max(xs)) * 0.5
    cy = (min(ys) + max(ys)) * 0.5
    z0, z1 = min(zs), max(zs)
    span = max(1e-6, z1 - z0)
    for v in obj.data.vertices:
        t = max(0.0, min(1.0, (v.co.z - z0) / span))
        # Bottom ~0.87, knee ~0.93, thigh ~1.00.
        fx = 0.87 + 0.13 * (t ** 0.82)
        fy = 0.92 + 0.08 * (t ** 0.90)
        # Tiny knee ease prevents a rigid cone silhouette.
        knee = math.exp(-((t - 0.53) / 0.20) ** 2) * 0.018
        fx += knee
        v.co.x = cx + (v.co.x - cx) * fx
        v.co.y = cy + (v.co.y - cy) * fy


# -----------------------------------------------------------------------------
# ARMS — remove the capsule chain and rebuild two clean material masses:
# one tapered cloth sleeve + one continuous skin forearm/hand.
# -----------------------------------------------------------------------------
for side in (-1, 1):
    s = float(side)
    remove_many([
        f'Sleeve_{side}', f'SleeveTrim_{side}', f'RolledSleeve_{side}',
        f'Forearm_{side}', f'HandV64_{side}', f'HandV62_{side}', f'HandV63_{side}'
    ])

    # Shoulder starts tucked under the torso silhouette and flows outward/down,
    # avoiding the detached vertical pill visible in V6.4.
    soft_tube(f'SleeveV65_{side}', [
        (0.163*s, -0.003, 1.385, 0.046, 0.050),
        (0.179*s, -0.006, 1.360, 0.050, 0.052),
        (0.197*s, -0.011, 1.325, 0.053, 0.053),
        (0.213*s, -0.016, 1.280, 0.054, 0.052),
        (0.225*s, -0.021, 1.225, 0.052, 0.049),
        (0.231*s, -0.026, 1.165, 0.048, 0.045),
        (0.231*s, -0.031, 1.112, 0.044, 0.041),
        (0.229*s, -0.035, 1.079, 0.041, 0.038),
    ], SHIRT, 28)

    continuous_skin_arm(f'ArmHandV65_{side}', side)

# -----------------------------------------------------------------------------
# LOWER BODY — remove the twin-column read while retaining workwear volume.
# -----------------------------------------------------------------------------
for side in (-1, 1):
    taper_trouser(bpy.data.objects.get(f'Trouser_{side}'))
    cuff = bpy.data.objects.get(f'TrouserCuff_{side}') or bpy.data.objects.get(f'Cuff_{side}')
    if cuff:
        cuff.scale.x *= 0.91
        cuff.scale.y *= 0.95

hips = bpy.data.objects.get('OverallHips')
if hips:
    hips.scale.x *= 0.96
    hips.scale.y *= 0.98

# -----------------------------------------------------------------------------
# HAIR — replace three flat patches with short, rounded volumetric sweep masses.
# -----------------------------------------------------------------------------
remove_many(['V60FringeMain', 'V60FringeLeft', 'V60FringeRight'])
recolor(HAIR, (0.040, 0.012, 0.005))
recolor(HAIR_WARM, (0.078, 0.023, 0.009))

blade_clump('V65FringeSweep', [
    (0.070, -0.082, 1.944, 0.074, 0.031),
    (0.020, -0.116, 1.927, 0.076, 0.030),
    (-0.040, -0.143, 1.900, 0.064, 0.027),
    (-0.092, -0.159, 1.866, 0.042, 0.021),
    (-0.118, -0.164, 1.837, 0.014, 0.010),
], HAIR_WARM, 12)
blade_clump('V65FringeLeft', [
    (-0.088, -0.075, 1.930, 0.056, 0.027),
    (-0.132, -0.108, 1.902, 0.052, 0.025),
    (-0.165, -0.137, 1.868, 0.036, 0.020),
    (-0.178, -0.151, 1.838, 0.012, 0.009),
], HAIR, 12)
blade_clump('V65FringeRight', [
    (0.112, -0.064, 1.927, 0.050, 0.026),
    (0.148, -0.094, 1.900, 0.046, 0.023),
    (0.171, -0.122, 1.868, 0.031, 0.018),
    (0.177, -0.136, 1.840, 0.010, 0.008),
], HAIR, 12)

# -----------------------------------------------------------------------------
# FACE — slightly less round/iconic eyes; preserve the friendly expression.
# -----------------------------------------------------------------------------
for side in (-1, 1):
    eye = bpy.data.objects.get(f'EyeWhite_{side}')
    iris = bpy.data.objects.get(f'Iris_{side}')
    pupil = bpy.data.objects.get(f'Pupil_{side}')
    if eye:
        eye.scale.x *= 0.97
        eye.scale.z *= 0.90
    if iris:
        iris.scale.x *= 0.95
        iris.scale.z *= 0.91
    if pupil:
        pupil.scale.x *= 0.95
        pupil.scale.z *= 0.91

# Final candidate export only. Gameplay asset remains untouched.
bpy.ops.object.select_all(action='DESELECT')
ROOT.select_set(True)
for obj in ROOT.children_recursive:
    obj.select_set(True)
bpy.context.view_layer.objects.active = ROOT
bpy.ops.export_scene.gltf(
    filepath=OUT_PATH,
    export_format='GLB',
    use_selection=True,
    export_apply=True,
    export_yup=True,
)
print(f'Exported Lembah Sari Character V6.5 silhouette-continuity candidate to {OUT_PATH}')
