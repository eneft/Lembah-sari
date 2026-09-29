import bpy
import math
import os

# Lembah Sari Character V5.4 — concept silhouette polish.
# Candidate only. Replaces V5.3 tube-like hair with broad sculpted sheets,
# shortens the lower face, slims sleeves, and rebuilds smaller relaxed hands.

BASE = os.path.join(os.path.dirname(__file__), "build_player_character_v53.py")
exec(compile(open(BASE, "r", encoding="utf-8").read(), BASE, "exec"), globals(), globals())


def remove_many(names):
    for name in names:
        obj = bpy.data.objects.get(name)
        if obj:
            bpy.data.objects.remove(obj, do_unlink=True)


def relaxed_hand(name, side, center):
    s = float(side)
    cx, y, cz = center
    # Narrow neutral hand: small thumb bump + four softly stepped fingertips.
    local = [
        (-0.030, 0.052), (0.026, 0.052),
        (0.034, 0.040), (0.039, 0.020), (0.046, 0.005),
        (0.042,-0.010), (0.033,-0.019),
        (0.031,-0.036), (0.025,-0.050), (0.016,-0.056),
        (0.008,-0.052), (0.001,-0.061), (-0.008,-0.054),
        (-0.016,-0.061), (-0.024,-0.052), (-0.032,-0.057),
        (-0.039,-0.046), (-0.041,-0.027), (-0.038,-0.005),
        (-0.036, 0.020),
    ]
    outline = [(cx + dx*s, cz + dz) for dx, dz in local]
    return solid_patch(name, outline, y, SKIN, 0.050, 0.011)


# -----------------------------------------------------------------------------
# HAIR — broad layered sheets closer to the concept artwork.
# -----------------------------------------------------------------------------
remove_many([
    'HairV53Base','V53FringeHero','V53FringeCenter','V53FringeRight','V53SideLeft',
    'V53TopLeft','V53TopCenter','V53TopRight'
])
recolor(HAIR, (0.055, 0.020, 0.010))
recolor(HAIR_WARM, (0.120, 0.042, 0.018))

uv('V54HairCap', (0.0,0.050,1.860), (0.205,0.160,0.166), HAIR, 48, 28)
uv('V54HairBack', (0.0,0.118,1.800), (0.194,0.150,0.143), HAIR, 42, 24)

# Front clumps overlap each other and sink into the cap. Shapes are flat/broad,
# like carved stylized hair instead of cylindrical strands.
solid_patch('V54BangHero', [
    (-0.205,1.965),(-0.150,2.005),(-0.085,2.002),(-0.022,1.972),
    (0.030,1.925),(0.052,1.875),(0.036,1.830),(0.006,1.790),
    (-0.020,1.818),(-0.060,1.860),(-0.112,1.900),(-0.170,1.930)
], -0.171, HAIR_WARM, 0.056, 0.013)
solid_patch('V54BangCenter', [
    (-0.055,2.010),(0.005,2.022),(0.064,2.000),(0.095,1.960),
    (0.085,1.915),(0.055,1.875),(0.028,1.845),(0.004,1.872),
    (-0.020,1.922)
], -0.168, HAIR, 0.054, 0.012)
solid_patch('V54BangRight', [
    (0.055,1.995),(0.118,1.997),(0.170,1.970),(0.202,1.930),
    (0.198,1.890),(0.178,1.854),(0.150,1.830),(0.126,1.858),
    (0.105,1.905)
], -0.162, HAIR_WARM, 0.050, 0.012)
solid_patch('V54SideLeft', [
    (-0.210,1.925),(-0.182,1.955),(-0.142,1.928),(-0.145,1.870),
    (-0.160,1.812),(-0.182,1.762),(-0.205,1.735),(-0.220,1.780),
    (-0.222,1.855)
], -0.154, HAIR, 0.048, 0.011)
solid_patch('V54SideRight', [
    (0.160,1.946),(0.195,1.930),(0.218,1.895),(0.220,1.850),
    (0.208,1.808),(0.188,1.770),(0.170,1.792),(0.158,1.842)
], -0.150, HAIR, 0.046, 0.011)

# Crown spikes are modest and mostly sideways, matching the reference silhouette.
solid_patch('V54CrownL', [
    (-0.145,2.000),(-0.120,2.040),(-0.082,2.065),(-0.042,2.052),
    (-0.065,2.020),(-0.105,1.995)
], -0.020, HAIR_WARM, 0.046, 0.010)
solid_patch('V54CrownM', [
    (-0.040,2.020),(-0.012,2.070),(0.020,2.095),(0.045,2.075),
    (0.035,2.038),(0.005,2.012)
], -0.008, HAIR, 0.043, 0.010)
solid_patch('V54CrownR', [
    (0.040,2.022),(0.082,2.058),(0.128,2.065),(0.154,2.040),
    (0.128,2.014),(0.082,2.000)
], -0.004, HAIR_WARM, 0.043, 0.010)

# -----------------------------------------------------------------------------
# FACE — shorten lower face and make the youthful cheek/jaw ratio closer.
# -----------------------------------------------------------------------------
head = bpy.data.objects.get('HeadV5')
if head:
    pivot = 1.710
    for vert in head.data.vertices:
        if vert.co.z < pivot:
            vert.co.z = pivot + (vert.co.z - pivot) * 0.945
            if vert.co.z > 1.610:
                vert.co.x *= 1.018

# Bring mouth/nose up with the shortened face.
for name, dz in [('Nose',0.008),('Smile',0.012),('Blush_-1',0.006),('Blush_1',0.006)]:
    obj = bpy.data.objects.get(name)
    if obj:
        obj.location.z += dz

# Eyes get a subtle downward shift to restore the concept's large forehead/young face.
for side in (-1,1):
    for prefix in ['EyeWhite','Iris','Pupil','EyeGlint']:
        obj = bpy.data.objects.get(f'{prefix}_{side}')
        if obj:
            obj.location.z -= 0.004
for name in ['UpperLidL','UpperLidR','BrowL','BrowR']:
    obj = bpy.data.objects.get(name)
    if obj:
        obj.location.z -= 0.004

# -----------------------------------------------------------------------------
# ARMS — less puff, cleaner rolled sleeve transition.
# -----------------------------------------------------------------------------
for side in (-1,1):
    s = float(side)
    remove_many([
        f'Sleeve_{side}',f'RolledSleeve_{side}',f'Forearm_{side}',f'HandV53_{side}'
    ] + [f'V53FingerCrease_{side}_{i}' for i in range(3)])

    soft_tube(f'Sleeve_{side}', [
        (0.198*s,-0.004,1.356,0.060,0.057),
        (0.222*s,-0.012,1.295,0.062,0.058),
        (0.241*s,-0.022,1.225,0.059,0.055),
        (0.250*s,-0.032,1.160,0.055,0.052),
        (0.248*s,-0.039,1.115,0.052,0.049),
    ], SHIRT, 22)
    soft_tube(f'RolledSleeve_{side}', [
        (0.248*s,-0.039,1.120,0.055,0.052),
        (0.246*s,-0.043,1.090,0.058,0.054),
        (0.241*s,-0.047,1.060,0.053,0.049),
    ], SHIRT_SHADOW, 22)
    soft_tube(f'Forearm_{side}', [
        (0.239*s,-0.050,1.052,0.041,0.037),
        (0.237*s,-0.060,0.980,0.039,0.035),
        (0.230*s,-0.073,0.910,0.036,0.032),
        (0.221*s,-0.084,0.850,0.033,0.029),
    ], SKIN, 20)
    relaxed_hand(f'HandV54_{side}', side, (0.216*s,-0.102,0.787))

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
print(f'Exported Lembah Sari Character V5.4 concept silhouette candidate to {OUT_PATH}')
