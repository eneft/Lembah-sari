import bpy
import math
import os

# Lembah Sari Character V6.3 — hand-contour convergence pass.
# Candidate only. Keeps the accepted V6.2 body/head proportions and replaces
# paddle-like capsule hands with a single front-readable hand outline.

BASE = os.path.join(os.path.dirname(__file__), "build_player_character_v62.py")
exec(compile(open(BASE, "r", encoding="utf-8").read(), BASE, "exec"), globals(), globals())


def build_hand_patch(name, side, material):
    s = float(side)
    cx = 0.223 * s
    cz = 0.798
    # Canonical right-hand outline in X/Z, mirrored by side.
    # Includes a thumb bulge and a softly stepped fingertip edge while staying
    # stylized enough to read at gameplay distance.
    local = [
        (-0.024,  0.077),
        ( 0.022,  0.077),
        ( 0.030,  0.057),
        ( 0.032,  0.035),
        ( 0.048,  0.018),
        ( 0.050, -0.002),
        ( 0.041, -0.018),
        ( 0.032, -0.024),
        ( 0.031, -0.049),
        ( 0.025, -0.067),
        ( 0.015, -0.076),
        ( 0.007, -0.071),
        (-0.001, -0.079),
        (-0.010, -0.073),
        (-0.019, -0.077),
        (-0.029, -0.066),
        (-0.036, -0.050),
        (-0.039, -0.028),
        (-0.038,  0.005),
        (-0.034,  0.038),
    ]
    outline = [(cx + dx*s, cz + dz) for dx, dz in local]
    obj = patch(name, outline, -0.073, material, thickness=0.046, radius=0.008)
    if obj and obj.type == 'MESH':
        for p in obj.data.polygons:
            p.use_smooth = True
        bevel = obj.modifiers.new('HandContourSoftness', 'BEVEL')
        bevel.width = 0.004
        bevel.segments = 3
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        try:
            bpy.ops.object.modifier_apply(modifier=bevel.name)
        except Exception:
            pass
    return obj


# Replace V6.2 capsule hands only.
for side in (-1, 1):
    old = bpy.data.objects.get(f'HandV62_{side}')
    if old:
        bpy.data.objects.remove(old, do_unlink=True)
    hand = build_hand_patch(f'HandV63_{side}', side, SKIN)
    if hand:
        hand.rotation_euler.y = math.radians(2.0 * side)
        hand.rotation_euler.z = math.radians(-1.5 * side)

# Slightly tame the three front fringe masses so the silhouette reads as one
# sweep rather than three equal blobs. No new hair pieces are introduced.
for name, sx, sz in [
    ('V60FringeMain', 1.00, 0.95),
    ('V60FringeLeft', 0.96, 0.94),
    ('V60FringeRight', 0.94, 0.94),
]:
    obj = bpy.data.objects.get(name)
    if obj:
        obj.scale.x *= sx
        obj.scale.z *= sz

# Small eye restraint for a less doll-like close-up without losing readability.
for side in (-1, 1):
    for prefix, factor in [('EyeWhite', 0.97), ('Iris', 0.96), ('Pupil', 0.96)]:
        obj = bpy.data.objects.get(f'{prefix}_{side}')
        if obj:
            obj.scale.x *= factor
            obj.scale.z *= factor

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
print(f'Exported Lembah Sari Character V6.3 hand-contour candidate to {OUT_PATH}')
