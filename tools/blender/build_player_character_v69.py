import bpy
import math
import os

# Lembah Sari Character V6.9 — concept-face refinement candidate.
# Candidate only. Keeps the approved V6.8 gameplay body/outfit/hair direction,
# then rebuilds the visible face stack to match the concept sheet more closely:
# softer cheek/jaw silhouette, warmer larger eyes, clean lids/brows, subtle blush,
# smaller nose, gentler smile, and correctly raised ears.

BASE = os.path.join(os.path.dirname(__file__), "build_player_character_v68.py")
exec(compile(open(BASE, "r", encoding="utf-8").read(), BASE, "exec"), globals(), globals())


def remove_many(names):
    for name in names:
        obj = bpy.data.objects.get(name)
        if obj:
            bpy.data.objects.remove(obj, do_unlink=True)


# -----------------------------------------------------------------------------
# HEAD — preserve topology but bias the silhouette toward the concept:
# narrower rounded chin, fuller cheeks, slightly softer forehead.
# Front of the face is -Y.
# -----------------------------------------------------------------------------
head = bpy.data.objects.get('HeadV57')
if head and head.type == 'MESH':
    for v in head.data.vertices:
        z = v.co.z
        # Jaw/chin taper.
        if z < 1.640:
            v.co.x *= 0.935
            if v.co.y < 0.0:
                v.co.y -= 0.004
        # Youthful cheek fullness and a slightly more projected face plane.
        elif z < 1.805:
            v.co.x *= 1.045
            if v.co.y < 0.0:
                v.co.y -= 0.008
        # Gentle temple/forehead transition.
        elif z < 1.900:
            v.co.x *= 1.012
            if v.co.y < 0.0:
                v.co.y -= 0.003
        else:
            v.co.x *= 0.992
    for p in head.data.polygons:
        p.use_smooth = True


# -----------------------------------------------------------------------------
# FACE — remove legacy/duplicate face curves and rebuild one clean stack.
# -----------------------------------------------------------------------------
remove_many([
    'LidL', 'LidR', 'UpperLidL', 'UpperLidR',
    'BrowL', 'BrowR', 'Smile', 'Nose',
    'Blush_-1', 'Blush_1',
])

# Enlarge the V6.8 eyes moderately — expressive, not doll-like.
for side in (-1, 1):
    s = float(side)
    eye = bpy.data.objects.get(f'EyeWhite_{side}')
    iris = bpy.data.objects.get(f'Iris_{side}')
    pupil = bpy.data.objects.get(f'Pupil_{side}')
    glint = bpy.data.objects.get(f'EyeGlint_{side}')

    for obj in (eye, iris, pupil, glint):
        if obj:
            obj.location.x *= 0.965
            obj.location.z += 0.004

    if eye:
        eye.scale.x *= 1.16
        eye.scale.z *= 1.20
    if iris:
        iris.scale.x *= 1.16
        iris.scale.z *= 1.18
        iris.location.y -= 0.0012
    if pupil:
        pupil.scale.x *= 1.13
        pupil.scale.z *= 1.15
        pupil.location.y -= 0.0018
    if glint:
        glint.scale *= 1.08
        glint.location.y -= 0.0020

    # Warm soft cheek tint, kept shallow so it reads as color rather than a bump.
    uv(f'Blush_{side}', (0.124 * s, -0.169, 1.666),
       (0.030, 0.0017, 0.014), BLUSH, 20, 10)

# Clean concept-style upper lids: broad shallow arcs, no duplicate lower/old layer.
curve('UpperLidL', [
    (-0.124, -0.169, 1.776),
    (-0.079, -0.174, 1.788),
    (-0.032, -0.169, 1.778),
], HAIR, 0.0032)
curve('UpperLidR', [
    (0.032, -0.169, 1.778),
    (0.079, -0.174, 1.788),
    (0.124, -0.169, 1.776),
], HAIR, 0.0032)

# Softer, slightly lifted brows to keep the default expression friendly/curious.
curve('BrowL', [
    (-0.126, -0.160, 1.824),
    (-0.082, -0.166, 1.838),
    (-0.040, -0.161, 1.831),
], HAIR, 0.0044)
curve('BrowR', [
    (0.040, -0.161, 1.831),
    (0.082, -0.166, 1.838),
    (0.126, -0.160, 1.824),
], HAIR, 0.0044)

# Tiny soft nose and a gentle closed smile matching the concept's neutral hero face.
uv('Nose', (0.0, -0.174, 1.687), (0.0058, 0.0032, 0.0066), SKIN, 18, 10)
curve('Smile', [
    (-0.043, -0.169, 1.631),
    (-0.021, -0.173, 1.624),
    (0.000, -0.174, 1.623),
    (0.022, -0.173, 1.626),
    (0.045, -0.168, 1.634),
], MOUTH, 0.0023)

# Raise ears from the legacy low position to eye/cheek level; keep them compact.
for side in (-1, 1):
    ear = bpy.data.objects.get(f'Ear_{side}')
    if ear:
        ear.location.x = 0.194 * float(side)
        ear.location.y = 0.000
        ear.location.z = 1.735
        ear.scale *= 1.08

# A very small hair-frame lift/widening keeps the larger eyes from feeling exposed
# while preserving the unified V6.8 hair mass and gameplay silhouette.
hair = bpy.data.objects.get('HairV68Unified')
if hair:
    hair.scale.x *= 1.025
    hair.scale.z *= 1.018
    hair.location.z += 0.004

# Final candidate export only. Approved gameplay V6.8 remains untouched until
# full-body, close-up, and gameplay-scale visual review all pass.
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
print(f'Exported Lembah Sari Character V6.9 concept-face candidate to {OUT_PATH}')
