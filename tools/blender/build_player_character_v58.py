import bpy
import math
import os

# Lembah Sari Character V5.8 — rounded convergence pass.
# Candidate only. Keeps the V5.7 body/head direction while removing the
# remaining blade-like hair read, shrinking the doll-like eyes, and replacing
# round fists with a single relaxed stylized hand silhouette.

BASE = os.path.join(os.path.dirname(__file__), "build_player_character_v57.py")
exec(compile(open(BASE, "r", encoding="utf-8").read(), BASE, "exec"), globals(), globals())


def soften_clump(name, sections, material):
    obj = blade_clump(name, sections, material, ring_sides=14)
    if obj:
        sub = obj.modifiers.new('OrganicHair', 'SUBSURF')
        sub.subdivision_type = 'CATMULL_CLARK'
        sub.levels = 1
        sub.render_levels = 1
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        try:
            bpy.ops.object.modifier_apply(modifier=sub.name)
        except Exception:
            pass
        for p in obj.data.polygons:
            p.use_smooth = True
    return obj


# -----------------------------------------------------------------------------
# FACE — reduce icon/doll eye read while preserving the friendly expression.
# -----------------------------------------------------------------------------
for side in (-1, 1):
    eye = bpy.data.objects.get(f'EyeWhite_{side}')
    iris = bpy.data.objects.get(f'Iris_{side}')
    pupil = bpy.data.objects.get(f'Pupil_{side}')
    glint = bpy.data.objects.get(f'EyeGlint_{side}')
    if eye:
        eye.scale.x *= 0.93
        eye.scale.z *= 0.90
    if iris:
        iris.scale.x *= 0.90
        iris.scale.z *= 0.90
    if pupil:
        pupil.scale.x *= 0.88
        pupil.scale.z *= 0.88
    if glint:
        glint.scale *= 0.90

nose = bpy.data.objects.get('Nose')
if nose:
    nose.location.y -= 0.006
    nose.scale *= 1.04

# -----------------------------------------------------------------------------
# HAIR — fewer, wider, round-ended masses. No crown spikes.
# -----------------------------------------------------------------------------
remove_many([
    'V57HairCap','V57HairBack','V57SweepBack','V57SweepHero','V57CenterBang',
    'V57RightBang','V57LeftTemple','V57RightTemple',
    'V57CrownA','V57CrownB','V57CrownC'
])
recolor(HAIR, (0.042, 0.013, 0.006))
recolor(HAIR_WARM, (0.090, 0.028, 0.010))

# Shells hug the skull instead of creating a bun-like rear silhouette.
uv('V58HairCap', (0.0, 0.046, 1.865), (0.214, 0.158, 0.167), HAIR, 52, 30)
uv('V58HairBack', (0.0, 0.098, 1.805), (0.198, 0.118, 0.142), HAIR, 46, 26)

# Three broad overlapping front masses define the sweep.
soften_clump('V58SweepLeft', [
    (0.050,-0.020,2.030,0.086,0.038),
    (0.005,-0.055,2.015,0.090,0.038),
    (-0.055,-0.090,1.988,0.082,0.035),
    (-0.108,-0.122,1.950,0.064,0.030),
    (-0.145,-0.145,1.915,0.032,0.020),
    (-0.158,-0.154,1.895,0.018,0.013),
], HAIR)

soften_clump('V58SweepHero', [
    (0.095,-0.025,2.020,0.075,0.034),
    (0.060,-0.067,1.995,0.077,0.034),
    (0.020,-0.107,1.958,0.068,0.031),
    (-0.012,-0.137,1.918,0.052,0.026),
    (-0.030,-0.157,1.878,0.034,0.020),
    (-0.034,-0.166,1.850,0.018,0.013),
], HAIR_WARM)

soften_clump('V58SweepRight', [
    (0.150,-0.005,1.992,0.052,0.028),
    (0.170,-0.040,1.966,0.050,0.026),
    (0.183,-0.074,1.932,0.042,0.023),
    (0.188,-0.103,1.895,0.032,0.019),
    (0.184,-0.124,1.862,0.020,0.014),
], HAIR)

# Compact temples connect the sweep into the cap and keep the side view clean.
soften_clump('V58TempleL', [
    (-0.185,-0.012,1.928,0.040,0.024),
    (-0.202,-0.047,1.892,0.036,0.022),
    (-0.210,-0.078,1.850,0.030,0.019),
    (-0.207,-0.101,1.812,0.020,0.014),
], HAIR)
soften_clump('V58TempleR', [
    (0.182,0.000,1.930,0.038,0.023),
    (0.200,-0.030,1.898,0.034,0.021),
    (0.208,-0.060,1.860,0.027,0.018),
    (0.205,-0.082,1.825,0.018,0.013),
], HAIR_WARM)

# -----------------------------------------------------------------------------
# HANDS — one organic palm/finger mass with a subtle integrated thumb.
# -----------------------------------------------------------------------------
for side in (-1, 1):
    s = float(side)
    remove_many([f'HandV57_{side}'])
    cx, cy, cz = 0.220*s, -0.104, 0.806

    palm_name = f'V58Palm_{side}'
    finger_name = f'V58FingerMass_{side}'
    thumb_name = f'V58Thumb_{side}'

    uv(palm_name, (cx, cy, cz), (0.040, 0.029, 0.047), SKIN, 28, 18)
    uv(finger_name, (cx, cy-0.002, cz-0.055), (0.036, 0.027, 0.038), SKIN, 28, 18)
    uv(thumb_name, (cx+0.034*s, cy-0.012, cz-0.020),
       (0.017, 0.015, 0.028), SKIN, 22, 14,
       rot=(0, math.radians(8*s), math.radians(24*s)))

    hand = fuse_meshes([palm_name, finger_name, thumb_name],
                       f'HandV58_{side}', SKIN, 0.0035)
    if hand:
        hand.rotation_euler.z = math.radians(-3*s)
        hand.scale.x *= 1.02
        hand.scale.z *= 1.02

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
print(f'Exported Lembah Sari Character V5.8 rounded convergence candidate to {OUT_PATH}')
