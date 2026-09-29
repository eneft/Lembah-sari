import bpy
import math
import os
from mathutils import Vector

# Lembah Sari Character V5.1 — corrective sculpt pass on V5 organic rebuild.
# Candidate only. Fixes the V5.0 studio findings: round face, central fringe gap,
# undersized flat hands and balloon sleeves.

BASE = os.path.join(os.path.dirname(__file__), "build_player_character_v50.py")
exec(compile(open(BASE, "r", encoding="utf-8").read(), BASE, "exec"), globals(), globals())


def remove_many(names):
    for name in names:
        obj = bpy.data.objects.get(name)
        if obj:
            bpy.data.objects.remove(obj, do_unlink=True)


def join_and_voxel_fuse_local(names, new_name, material, voxel=0.008):
    objs = [bpy.data.objects.get(n) for n in names]
    objs = [o for o in objs if o and o.type == 'MESH']
    if not objs:
        return None
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    obj = objs[0]
    obj.name = new_name
    obj.data.materials.clear()
    obj.data.materials.append(material)
    for poly in obj.data.polygons:
        poly.use_smooth = True
    try:
        obj.data.remesh_voxel_size = voxel
        obj.data.remesh_voxel_adaptivity = 0.0
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        bpy.ops.object.voxel_remesh()
        for poly in obj.data.polygons:
            poly.use_smooth = True
    except Exception as exc:
        print('V5.1 voxel fuse fallback:', exc)
    return obj


# -----------------------------------------------------------------------------
# FACE: elongate and narrow V5 head for a less doll-like, more concept profile.
# -----------------------------------------------------------------------------
head = bpy.data.objects.get('HeadV5')
if head:
    pivot_z = 1.735
    for vert in head.data.vertices:
        vert.co.x *= 0.955
        vert.co.y *= 0.970
        vert.co.z = pivot_z + (vert.co.z - pivot_z) * 1.050

# Reposition/scale facial features to follow the longer face.
for side in (-1, 1):
    for prefix in ['EyeWhite', 'Iris', 'Pupil', 'EyeGlint']:
        obj = bpy.data.objects.get(f'{prefix}_{side}')
        if obj:
            obj.location.z += 0.010
    eye = bpy.data.objects.get(f'EyeWhite_{side}')
    iris = bpy.data.objects.get(f'Iris_{side}')
    if eye:
        eye.scale.x *= 1.055
        eye.scale.z *= 1.025
    if iris:
        iris.scale.x *= 1.035
        iris.scale.z *= 1.025
for name in ['UpperLidL','UpperLidR','BrowL','BrowR']:
    obj = bpy.data.objects.get(name)
    if obj:
        obj.location.z += 0.010
nose = bpy.data.objects.get('Nose')
if nose:
    nose.location.z += 0.002
smile = bpy.data.objects.get('Smile')
if smile:
    smile.location.z -= 0.004

# -----------------------------------------------------------------------------
# HAIR: close the forehead gap and add broad concept-like swept clumps, then
# fuse them back into one coherent mass.
# -----------------------------------------------------------------------------
solid_patch('V51ForeheadSweep', [
    (-0.125,1.982),(-0.040,2.006),(0.050,1.990),(0.105,1.945),
    (0.090,1.895),(0.050,1.842),(0.010,1.800),(-0.025,1.835),
    (-0.055,1.895),(-0.100,1.935)
], -0.174, HAIR, 0.056, 0.014)

loft_lock('V51HeroSweep', [
    (-0.185,-0.045,1.995,0.070,0.043),
    (-0.130,-0.085,2.025,0.076,0.044),
    (-0.065,-0.115,2.018,0.070,0.040),
    (-0.005,-0.145,1.965,0.052,0.034),
    (0.035,-0.165,1.900,0.018,0.014),
], HAIR, 16)
loft_lock('V51SideSweepL', [
    (-0.185,-0.010,1.930,0.060,0.040),
    (-0.205,-0.050,1.885,0.058,0.038),
    (-0.198,-0.085,1.825,0.045,0.032),
    (-0.180,-0.105,1.775,0.012,0.010),
], HAIR, 14)
loft_lock('V51SideSweepR', [
    (0.105,-0.015,1.960,0.052,0.036),
    (0.155,-0.045,1.930,0.052,0.035),
    (0.188,-0.070,1.885,0.043,0.030),
    (0.194,-0.085,1.835,0.011,0.009),
], HAIR, 14)

hair = join_and_voxel_fuse_local(
    ['HairV5Unified','V51ForeheadSweep','V51HeroSweep','V51SideSweepL','V51SideSweepR'],
    'HairV51Unified', HAIR, voxel=0.009
)
if hair:
    hair.scale.x *= 1.020

# -----------------------------------------------------------------------------
# HANDS: replace V5 flat small result with rounded palm sculpt + integrated thumb.
# -----------------------------------------------------------------------------
for side in (-1, 1):
    s = float(side)
    remove_many([
        f'HandV5_{side}', f'HandCreaseA_{side}', f'HandCreaseB_{side}',
        f'V51Palm_{side}', f'V51Thumb_{side}'
    ])
    cx = 0.238 * s
    cy = -0.096
    cz = 0.790
    profile(f'V51Palm_{side}', [
        (cz+0.058,0.034,0.029,cx,cy),
        (cz+0.030,0.044,0.034,cx,cy-0.002),
        (cz+0.000,0.048,0.036,cx,cy-0.004),
        (cz-0.032,0.046,0.035,cx,cy-0.006),
        (cz-0.058,0.040,0.032,cx,cy-0.006),
        (cz-0.074,0.027,0.025,cx,cy-0.005),
    ], SKIN, 32)
    thumb_pos = (cx + 0.043*s, cy-0.012, cz-0.002)
    uv(f'V51Thumb_{side}', thumb_pos, (0.020,0.019,0.038), SKIN, 22, 14,
       rot=(0, math.radians(8*s), math.radians(24*s)))
    hand = join_and_voxel_fuse_local([f'V51Palm_{side}',f'V51Thumb_{side}'],
                                     f'HandV51_{side}', SKIN, voxel=0.0055)
    if hand:
        hand.scale.x *= 1.045
        hand.scale.z *= 1.030
    # Finger/knuckle hints stay graphic, not separate geometry.
    for idx, off in enumerate((-0.020, 0.0, 0.020)):
        curve(f'V51FingerCrease_{side}_{idx}', [
            (cx + off, cy-0.037, cz-0.010),
            (cx + off*0.95, cy-0.038, cz-0.037),
        ], MOUTH, 0.00115)

# -----------------------------------------------------------------------------
# SLEEVES: remove the balloon silhouette while keeping soft rolled cloth.
# -----------------------------------------------------------------------------
for side in (-1,1):
    sleeve = bpy.data.objects.get(f'Sleeve_{side}')
    cuff = bpy.data.objects.get(f'RolledSleeve_{side}')
    forearm = bpy.data.objects.get(f'Forearm_{side}')
    if sleeve:
        sleeve.scale.x *= 0.80
        sleeve.scale.y *= 0.84
        sleeve.scale.z *= 1.035
        sleeve.location.x *= 0.96
    if cuff:
        cuff.scale.x *= 0.86
        cuff.scale.y *= 0.88
        cuff.location.x *= 0.97
    if forearm:
        forearm.scale.x *= 0.94
        forearm.scale.y *= 0.94
        forearm.location.x *= 0.98

# Slightly reduce the huge trouser column read while keeping relaxed bagginess.
for side in (-1,1):
    tr = bpy.data.objects.get(f'Trouser_{side}')
    if tr:
        tr.scale.x *= 0.955
        tr.scale.y *= 0.970

# Export V5.1 candidate only.
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
print(f'Exported Lembah Sari Character V5.1 corrective candidate to {OUT_PATH}')
