import bpy
import math
import os

# Lembah Sari Character V7.0 — decisive concept-face rebuild.
# Candidate only. Keeps V6.8/V6.9 body, outfit, hands and unified hair direction,
# but replaces the head and every facial element with deterministic concept-led
# geometry instead of cumulatively scaled legacy parts.

BASE = os.path.join(os.path.dirname(__file__), "build_player_character_v69.py")
exec(compile(open(BASE, "r", encoding="utf-8").read(), BASE, "exec"), globals(), globals())


def remove_many(names):
    for name in names:
        obj = bpy.data.objects.get(name)
        if obj:
            bpy.data.objects.remove(obj, do_unlink=True)


def concept_head(name, material):
    # Front is -Y. Full cheeks + compact chin + softer crown follow the concept
    # sheet without inflating the total gameplay silhouette.
    rings = [
        # z, radius_x, radius_y, center_y
        (1.545, 0.056, 0.060, -0.004),
        (1.574, 0.104, 0.094, -0.010),
        (1.616, 0.154, 0.126, -0.016),
        (1.665, 0.193, 0.150, -0.020),
        (1.718, 0.216, 0.166, -0.019),
        (1.772, 0.220, 0.172, -0.014),
        (1.826, 0.213, 0.169, -0.006),
        (1.875, 0.196, 0.160,  0.003),
        (1.918, 0.166, 0.145,  0.011),
        (1.950, 0.120, 0.116,  0.017),
        (1.972, 0.065, 0.068,  0.020),
    ]
    sides = 56
    verts, faces = [], []
    for z, rx, ry, cy in rings:
        for i in range(sides):
            a = math.tau * i / sides
            sy = math.sin(a)
            y = cy + ry * sy
            # Flatten only the foremost face plane slightly so the eyes/nose
            # sit naturally on the surface instead of looking pasted onto a ball.
            if sy < -0.34:
                y += 0.012 * ((-sy - 0.34) / 0.66)
            verts.append((rx * math.cos(a), y, z))
    for r in range(len(rings) - 1):
        a0, b0 = r * sides, (r + 1) * sides
        for i in range(sides):
            j = (i + 1) % sides
            faces.append((a0 + i, a0 + j, b0 + j, b0 + i))
    faces.append(tuple(reversed(range(sides))))
    top = (len(rings) - 1) * sides
    faces.append(tuple(top + i for i in range(sides)))

    mesh = bpy.data.meshes.new(name + 'Mesh')
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.parent = ROOT
    obj.data.materials.append(material)
    for poly in obj.data.polygons:
        poly.use_smooth = True
    bevel_mod = obj.modifiers.new('ConceptFaceSoftness', 'BEVEL')
    bevel_mod.width = 0.0045
    bevel_mod.segments = 2
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    try:
        bpy.ops.object.modifier_apply(modifier=bevel_mod.name)
    except Exception:
        pass
    return obj


# Remove all legacy/current facial geometry so V7.0 has exactly one clean face.
remove_many([
    'HeadV57',
    'EyeWhite_-1', 'EyeWhite_1',
    'Iris_-1', 'Iris_1',
    'Pupil_-1', 'Pupil_1',
    'EyeGlint_-1', 'EyeGlint_1',
    'LidL', 'LidR', 'UpperLidL', 'UpperLidR',
    'BrowL', 'BrowR',
    'Nose', 'Smile',
    'Blush_-1', 'Blush_1',
    'Ear_-1', 'Ear_1',
    'EarInner_-1', 'EarInner_1',
])

concept_head('HeadV70', SKIN)

# Eyes: larger and warmer than V6.8 but still game-model simple. Slightly oval,
# with visible warm white around the iris and a compact dark pupil.
for side in (-1, 1):
    s = float(side)
    x = 0.071 * s
    uv(f'EyeWhite_{side}', (x, -0.1665, 1.758),
       (0.052, 0.0058, 0.041), EYE_WHITE, 30, 18)
    uv(f'Iris_{side}', (x + 0.0025 * s, -0.1720, 1.756),
       (0.030, 0.0044, 0.032), IRIS, 26, 16)
    uv(f'Pupil_{side}', (x + 0.0030 * s, -0.1755, 1.755),
       (0.012, 0.0030, 0.018), PUPIL, 20, 12)
    uv(f'EyeGlint_{side}', (x - 0.008 * s, -0.1780, 1.769),
       (0.0048, 0.0016, 0.0055), EYE_WHITE, 12, 8)

    # Concept cheeks: soft peach patches, shallow enough to read as blush only.
    uv(f'Blush_{side}', (0.128 * s, -0.1585, 1.672),
       (0.029, 0.0015, 0.013), BLUSH, 18, 10)

    # Properly placed compact ears around eye/cheek height.
    uv(f'Ear_{side}', (0.201 * s, -0.002, 1.744),
       (0.034, 0.024, 0.047), SKIN, 22, 14)
    uv(f'EarInner_{side}', (0.205 * s, -0.018, 1.744),
       (0.016, 0.0030, 0.025), BLUSH, 16, 10)

# Upper lids track the new larger eye shapes.
curve('UpperLidL', [
    (-0.124, -0.170, 1.778),
    (-0.073, -0.176, 1.793),
    (-0.020, -0.170, 1.780),
], HAIR, 0.0031)
curve('UpperLidR', [
    (0.020, -0.170, 1.780),
    (0.073, -0.176, 1.793),
    (0.124, -0.170, 1.778),
], HAIR, 0.0031)

# Friendly curious brows — slightly lifted toward the center, never stern.
curve('BrowL', [
    (-0.126, -0.158, 1.827),
    (-0.080, -0.164, 1.842),
    (-0.038, -0.159, 1.835),
], HAIR, 0.0043)
curve('BrowR', [
    (0.038, -0.159, 1.835),
    (0.080, -0.164, 1.842),
    (0.126, -0.158, 1.827),
], HAIR, 0.0043)

# Nose is visible only as a tiny soft form. Smile is wider and subtly upturned.
uv('Nose', (0.0, -0.1650, 1.688),
   (0.0062, 0.0032, 0.0072), SKIN, 18, 10)
curve('Smile', [
    (-0.048, -0.160, 1.635),
    (-0.025, -0.166, 1.626),
    (0.000, -0.168, 1.624),
    (0.026, -0.166, 1.628),
    (0.050, -0.159, 1.638),
], MOUTH, 0.0022)

# Slightly fuller hair framing around the face without changing the unified V6.8
# mass topology or introducing new loose spikes.
hair = bpy.data.objects.get('HairV68Unified')
if hair:
    hair.scale.x *= 1.020
    hair.scale.y *= 1.018
    hair.scale.z *= 1.025
    hair.location.z += 0.004

# Candidate export only. Approved gameplay asset remains V6.8 until visual review.
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
print(f'Exported Lembah Sari Character V7.0 concept-face rebuild candidate to {OUT_PATH}')
