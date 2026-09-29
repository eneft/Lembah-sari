import bpy
import math
import os

# Lembah Sari Character V5.6 — appeal/proportion pass.
# Candidate only. Converts the flat V5.5 fringe into rounded blade volumes,
# softens the lower face, enlarges the readable hand, and removes boxy trousers.

BASE = os.path.join(os.path.dirname(__file__), "build_player_character_v55.py")
exec(compile(open(BASE, "r", encoding="utf-8").read(), BASE, "exec"), globals(), globals())


def remove_many(names):
    for name in names:
        obj = bpy.data.objects.get(name)
        if obj:
            bpy.data.objects.remove(obj, do_unlink=True)


def blade_clump(name, sections, material, ring_sides=8):
    """Rounded flat 3D hair blade.
    sections: [(x,y,z,width,depth), ...]. Width is X, depth is Y.
    The result is broad enough to read like sculpted concept hair, but shallow
    enough to avoid the sausage/tube look of the earlier path-lock attempts.
    """
    verts = []
    faces = []
    for x, y, z, width, depth in sections:
        for i in range(ring_sides):
            a = math.tau * i / ring_sides
            verts.append((x + math.cos(a) * width,
                          y + math.sin(a) * depth,
                          z))
    rings = len(sections)
    for r in range(rings - 1):
        a0 = r * ring_sides
        b0 = (r + 1) * ring_sides
        for i in range(ring_sides):
            j = (i + 1) % ring_sides
            faces.append((a0+i, a0+j, b0+j, b0+i))
    faces.append(tuple(reversed(range(ring_sides))))
    end = (rings - 1) * ring_sides
    faces.append(tuple(end+i for i in range(ring_sides)))
    mesh = bpy.data.meshes.new(name + "Mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.parent = ROOT
    obj.data.materials.append(material)
    for p in obj.data.polygons:
        p.use_smooth = True
    bevel = obj.modifiers.new("BladeSoftness", "BEVEL")
    bevel.width = 0.0045
    bevel.segments = 2
    bpy.context.view_layer.objects.active = obj
    try:
        bpy.ops.object.modifier_apply(modifier=bevel.name)
    except Exception:
        pass
    return obj


# -----------------------------------------------------------------------------
# HAIR — replace all V5.5 flat plates with volumetric layered clumps.
# -----------------------------------------------------------------------------
remove_many([
    'V55HairCap','V55HairBack','V55BangOuterL','V55BangHero','V55BangMid',
    'V55BangMidR','V55BangRight','V55SideL','V55SideR',
    'V55Crown1','V55Crown2','V55Crown3','V55Crown4'
])
recolor(HAIR, (0.045, 0.014, 0.006))
recolor(HAIR_WARM, (0.105, 0.032, 0.012))

# Continuous crown/back volume.
uv('V56HairCap', (0.0, 0.052, 1.858), (0.202,0.158,0.161), HAIR, 48, 28)
uv('V56HairBack', (0.0, 0.120, 1.800), (0.194,0.149,0.141), HAIR, 42, 24)

# Front sweep — asymmetrical, broad roots, tapered tips, shallow Y depth.
blade_clump('V56BangOuterL', [
    (-0.165,-0.082,1.985,0.060,0.030),
    (-0.176,-0.112,1.930,0.055,0.027),
    (-0.184,-0.142,1.865,0.041,0.023),
    (-0.188,-0.160,1.805,0.022,0.016),
    (-0.186,-0.169,1.765,0.008,0.008),
], HAIR)
blade_clump('V56BangHero', [
    (-0.105,-0.085,2.005,0.074,0.032),
    (-0.085,-0.118,1.962,0.070,0.029),
    (-0.058,-0.149,1.910,0.058,0.026),
    (-0.028,-0.166,1.855,0.038,0.020),
    (-0.006,-0.174,1.810,0.010,0.009),
], HAIR_WARM)
blade_clump('V56BangCenter', [
    (-0.020,-0.082,2.018,0.058,0.029),
    (0.002,-0.116,1.978,0.054,0.026),
    (0.018,-0.146,1.930,0.044,0.022),
    (0.025,-0.163,1.880,0.030,0.017),
    (0.020,-0.171,1.842,0.008,0.008),
], HAIR)
blade_clump('V56BangMidR', [
    (0.050,-0.075,2.015,0.050,0.027),
    (0.075,-0.108,1.980,0.047,0.024),
    (0.094,-0.137,1.938,0.038,0.020),
    (0.103,-0.154,1.895,0.025,0.015),
    (0.100,-0.161,1.862,0.007,0.007),
], HAIR_WARM)
blade_clump('V56BangRight', [
    (0.125,-0.060,1.995,0.048,0.026),
    (0.158,-0.090,1.965,0.043,0.023),
    (0.178,-0.119,1.925,0.034,0.019),
    (0.188,-0.140,1.882,0.022,0.014),
    (0.185,-0.151,1.850,0.006,0.006),
], HAIR)

# Temples / sideburns anchor the face silhouette.
blade_clump('V56SideL', [
    (-0.188,-0.025,1.925,0.042,0.025),
    (-0.205,-0.065,1.880,0.036,0.022),
    (-0.210,-0.100,1.830,0.028,0.018),
    (-0.205,-0.123,1.782,0.016,0.012),
    (-0.198,-0.134,1.752,0.006,0.006),
], HAIR)
blade_clump('V56SideR', [
    (0.172,-0.015,1.932,0.039,0.023),
    (0.197,-0.052,1.895,0.034,0.020),
    (0.207,-0.086,1.850,0.025,0.016),
    (0.204,-0.108,1.812,0.012,0.010),
], HAIR_WARM)

# Small crown tufts from the concept — compact, swept, not vertical spikes.
blade_clump('V56CrownL', [
    (-0.110,0.012,1.992,0.047,0.023),
    (-0.130,-0.002,2.025,0.037,0.019),
    (-0.150,-0.010,2.045,0.018,0.011),
    (-0.166,-0.014,2.048,0.005,0.005),
], HAIR_WARM)
blade_clump('V56CrownM', [
    (-0.025,0.014,2.002,0.043,0.021),
    (-0.010,0.000,2.038,0.032,0.017),
    (0.010,-0.009,2.060,0.015,0.010),
    (0.026,-0.012,2.062,0.005,0.005),
], HAIR)
blade_clump('V56CrownR', [
    (0.060,0.018,1.998,0.040,0.021),
    (0.090,0.004,2.030,0.031,0.017),
    (0.122,-0.006,2.045,0.015,0.010),
    (0.145,-0.010,2.040,0.005,0.005),
], HAIR_WARM)

# -----------------------------------------------------------------------------
# FACE — soften sharp V5 jaw and restore concept-like cheek fullness.
# -----------------------------------------------------------------------------
head = bpy.data.objects.get('HeadV5')
if head:
    for v in head.data.vertices:
        z = v.co.z
        if z < 1.620:
            v.co.x *= 1.075
            v.co.z += 0.006
        elif z < 1.690:
            v.co.x *= 1.050
        elif z < 1.750:
            v.co.x *= 1.026
        # Slightly fuller mid-face depth, while keeping a gentle chin.
        if 1.620 < z < 1.760 and v.co.y < 0:
            v.co.y *= 1.018

# Rich concept eyes: large dark iris, controlled sclera.
recolor(IRIS, (0.105,0.025,0.008))
recolor(PUPIL, (0.006,0.002,0.001))
for side in (-1,1):
    iris = bpy.data.objects.get(f'Iris_{side}')
    pupil = bpy.data.objects.get(f'Pupil_{side}')
    eye = bpy.data.objects.get(f'EyeWhite_{side}')
    if iris:
        iris.scale.x *= 1.14
        iris.scale.z *= 1.15
    if pupil:
        pupil.scale.x *= 1.08
        pupil.scale.z *= 1.10
    if eye:
        eye.scale.x *= 1.015
        eye.scale.z *= 1.020

# Slightly smaller nose, softer friendly smile.
nose = bpy.data.objects.get('Nose')
if nose:
    nose.scale *= 0.82
remove_many(['Smile'])
curve('Smile', [(-0.042,-0.164,1.636),(-0.020,-0.168,1.628),(0.0,-0.169,1.627),
                (0.021,-0.168,1.630),(0.044,-0.163,1.640)], MOUTH, 0.0026)

# -----------------------------------------------------------------------------
# HAND — keep the fused fingers but restore readable concept scale.
# -----------------------------------------------------------------------------
for side in (-1,1):
    hand = bpy.data.objects.get(f'HandV55_{side}')
    if hand:
        hand.scale.x *= 1.10
        hand.scale.y *= 1.06
        hand.scale.z *= 1.12
        hand.location.z += 0.004

# -----------------------------------------------------------------------------
# LOWER BODY — remove rectangular trouser columns, keep relaxed workwear volume.
# -----------------------------------------------------------------------------
hips = bpy.data.objects.get('OverallHips')
if hips:
    hips.scale.x *= 0.96
for side in (-1,1):
    tr = bpy.data.objects.get(f'Trouser_{side}')
    if tr:
        tr.scale.x *= 0.88
        tr.scale.y *= 0.94
    cuff = bpy.data.objects.get(f'TrouserCuff_{side}') or bpy.data.objects.get(f'Cuff_{side}')
    if cuff:
        cuff.scale.x *= 0.92

# Final sleeve restraint.
for side in (-1,1):
    sleeve = bpy.data.objects.get(f'Sleeve_{side}')
    rolled = bpy.data.objects.get(f'RolledSleeve_{side}')
    if sleeve:
        sleeve.scale.x *= 0.95
        sleeve.scale.y *= 0.96
    if rolled:
        rolled.scale.x *= 0.95
        rolled.scale.y *= 0.95

# Export candidate only.
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
print(f'Exported Lembah Sari Character V5.6 appeal/proportion candidate to {OUT_PATH}')
