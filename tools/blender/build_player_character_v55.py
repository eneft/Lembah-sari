import bpy
import math
import os
from mathutils import Vector

# Lembah Sari Character V5.5 — face/hair/hand convergence pass.
# Candidate only. Smaller layered hair clumps, richer concept eyes, and
# voxel-fused palm + four fingers + thumb for an actual hand silhouette.

BASE = os.path.join(os.path.dirname(__file__), "build_player_character_v54.py")
exec(compile(open(BASE, "r", encoding="utf-8").read(), BASE, "exec"), globals(), globals())


def remove_many(names):
    for name in names:
        obj = bpy.data.objects.get(name)
        if obj:
            bpy.data.objects.remove(obj, do_unlink=True)


def fuse_meshes(names, new_name, material, voxel=0.0045):
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
    for p in obj.data.polygons:
        p.use_smooth = True
    try:
        obj.data.remesh_voxel_size = voxel
        obj.data.remesh_voxel_adaptivity = 0.0
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        bpy.ops.object.voxel_remesh()
        for p in obj.data.polygons:
            p.use_smooth = True
    except Exception as exc:
        print('V5.5 fuse fallback:', exc)
    bevel = obj.modifiers.new('SoftHandEdge', 'BEVEL')
    bevel.width = voxel * 0.55
    bevel.segments = 2
    bpy.context.view_layer.objects.active = obj
    try:
        bpy.ops.object.modifier_apply(modifier=bevel.name)
    except Exception:
        pass
    return obj


# -----------------------------------------------------------------------------
# HAIR — replace V5.4 large sheets with more numerous, smaller concept clumps.
# -----------------------------------------------------------------------------
remove_many([
    'V54HairCap','V54HairBack','V54BangHero','V54BangCenter','V54BangRight',
    'V54SideLeft','V54SideRight','V54CrownL','V54CrownM','V54CrownR'
])
recolor(HAIR, (0.032,0.010,0.005))
recolor(HAIR_WARM, (0.075,0.024,0.010))

uv('V55HairCap', (0.0,0.052,1.858), (0.202,0.157,0.162), HAIR, 48, 28)
uv('V55HairBack', (0.0,0.119,1.798), (0.192,0.148,0.140), HAIR, 42, 24)

# Main front sweep broken into natural overlapping locks.
solid_patch('V55BangOuterL', [
    (-0.210,1.952),(-0.180,1.987),(-0.136,1.994),(-0.105,1.968),
    (-0.112,1.918),(-0.135,1.862),(-0.164,1.808),(-0.192,1.772),
    (-0.208,1.815),(-0.218,1.886)
], -0.166, HAIR, 0.046, 0.011)
solid_patch('V55BangHero', [
    (-0.165,1.995),(-0.115,2.018),(-0.060,2.005),(-0.018,1.966),
    (0.012,1.916),(0.018,1.866),(-0.002,1.818),(-0.026,1.790),
    (-0.050,1.828),(-0.085,1.875),(-0.128,1.925)
], -0.172, HAIR_WARM, 0.052, 0.012)
solid_patch('V55BangMid', [
    (-0.065,2.010),(-0.018,2.030),(0.030,2.015),(0.060,1.982),
    (0.065,1.940),(0.052,1.895),(0.030,1.855),(0.010,1.830),
    (-0.006,1.870),(-0.025,1.930)
], -0.170, HAIR, 0.048, 0.011)
solid_patch('V55BangMidR', [
    (0.015,2.018),(0.060,2.026),(0.104,2.005),(0.125,1.972),
    (0.120,1.930),(0.102,1.890),(0.078,1.862),(0.060,1.890),
    (0.050,1.945)
], -0.166, HAIR_WARM, 0.045, 0.011)
solid_patch('V55BangRight', [
    (0.090,2.000),(0.137,2.002),(0.177,1.980),(0.204,1.946),
    (0.207,1.905),(0.194,1.868),(0.174,1.840),(0.153,1.862),
    (0.137,1.910)
], -0.158, HAIR, 0.043, 0.010)

# Side and crown clumps remain compact and directional.
solid_patch('V55SideL', [
    (-0.215,1.918),(-0.190,1.940),(-0.160,1.916),(-0.165,1.865),
    (-0.180,1.812),(-0.200,1.770),(-0.218,1.747),(-0.225,1.805)
], -0.150, HAIR, 0.042, 0.010)
solid_patch('V55SideR', [
    (0.170,1.930),(0.200,1.918),(0.220,1.885),(0.218,1.845),
    (0.207,1.810),(0.190,1.780),(0.176,1.805),(0.168,1.852)
], -0.148, HAIR, 0.040, 0.010)

for name, pts, mat_ in [
    ('V55Crown1',[(-0.145,2.000),(-0.118,2.040),(-0.083,2.060),(-0.055,2.047),(-0.075,2.018),(-0.110,1.997)],HAIR_WARM),
    ('V55Crown2',[(-0.060,2.018),(-0.035,2.063),(-0.006,2.084),(0.016,2.068),(0.006,2.034),(-0.024,2.010)],HAIR),
    ('V55Crown3',[(0.005,2.025),(0.036,2.070),(0.068,2.083),(0.090,2.064),(0.072,2.034),(0.038,2.012)],HAIR_WARM),
    ('V55Crown4',[(0.070,2.020),(0.110,2.052),(0.148,2.054),(0.170,2.032),(0.145,2.010),(0.105,2.002)],HAIR),
]:
    solid_patch(name, pts, -0.006, mat_, 0.038, 0.009)

# -----------------------------------------------------------------------------
# FACE — darker glossy eye read + slightly fuller youthful cheek.
# -----------------------------------------------------------------------------
recolor(EYE_WHITE, (0.93,0.88,0.78))
recolor(IRIS, (0.19,0.055,0.015))
recolor(PUPIL, (0.012,0.004,0.002))

head = bpy.data.objects.get('HeadV5')
if head:
    for vert in head.data.vertices:
        if 1.625 < vert.co.z < 1.735:
            vert.co.x *= 1.018
        if vert.co.z < 1.625:
            vert.co.x *= 0.985

for side in (-1,1):
    iris = bpy.data.objects.get(f'Iris_{side}')
    pupil = bpy.data.objects.get(f'Pupil_{side}')
    glint = bpy.data.objects.get(f'EyeGlint_{side}')
    if iris:
        iris.scale.x *= 1.13
        iris.scale.z *= 1.14
    if pupil:
        pupil.scale.x *= 1.12
        pupil.scale.z *= 1.12
    if glint:
        glint.scale *= 1.15

# Slightly soften brow strength/angle by widening the curve objects.
for name in ['BrowL','BrowR']:
    obj = bpy.data.objects.get(name)
    if obj:
        obj.scale.x *= 1.05

# -----------------------------------------------------------------------------
# HANDS — true fused digits, tightly grouped as a relaxed neutral hand.
# -----------------------------------------------------------------------------
for side in (-1,1):
    s = float(side)
    remove_many([f'HandV54_{side}'])
    cx, cy, cz = 0.216*s, -0.104, 0.790
    # Palm ellipsoid is small; fingers overlap it deeply before voxel fusion.
    uv(f'V55Palm_{side}', (cx,cy,cz), (0.036,0.027,0.052), SKIN, 24, 16)
    finger_names = []
    offsets = (-0.025,-0.008,0.009,0.025)
    lengths = (0.050,0.058,0.056,0.047)
    for idx,(off,ln) in enumerate(zip(offsets,lengths)):
        root = Vector((cx + off, cy-0.003, cz-0.032))
        tip = Vector((cx + off*0.96, cy-0.006, cz-0.032-ln))
        nm = f'V55Finger_{side}_{idx}'
        tapered(nm, root, tip, 0.0115, 0.0092, SKIN, 18, 0.0025)
        finger_names.append(nm)
    thumb_root = Vector((cx+0.028*s,cy-0.003,cz+0.005))
    thumb_tip = Vector((cx+0.050*s,cy-0.010,cz-0.023))
    tapered(f'V55Thumb_{side}', thumb_root, thumb_tip, 0.0125,0.0095,SKIN,18,0.0025)
    hand = fuse_meshes([f'V55Palm_{side}',f'V55Thumb_{side}']+finger_names,
                       f'HandV55_{side}',SKIN,0.0042)
    if hand:
        # Keep neutral hand slim and proportional to forearm.
        hand.scale.x *= 0.96
        hand.scale.y *= 0.96

# Sleeve/cuff final reduction to avoid balloon/donut read.
for side in (-1,1):
    sleeve = bpy.data.objects.get(f'Sleeve_{side}')
    cuff = bpy.data.objects.get(f'RolledSleeve_{side}')
    if sleeve:
        sleeve.scale.x *= 0.90
        sleeve.scale.y *= 0.94
    if cuff:
        cuff.scale.x *= 0.90
        cuff.scale.y *= 0.92
        cuff.scale.z *= 0.92

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
print(f'Exported Lembah Sari Character V5.5 convergence candidate to {OUT_PATH}')
