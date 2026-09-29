import bpy
import math
import os

# Lembah Sari Character V5.2 — controlled hair + facial appeal pass.
# Candidate only. Replaces the over-tall V5.1 hair tuft with a unified low crown
# and overlapping broad fringe, while preserving V5 organic head/hands.

BASE = os.path.join(os.path.dirname(__file__), "build_player_character_v51.py")
exec(compile(open(BASE, "r", encoding="utf-8").read(), BASE, "exec"), globals(), globals())


def remove_many(names):
    for name in names:
        obj = bpy.data.objects.get(name)
        if obj:
            bpy.data.objects.remove(obj, do_unlink=True)


def fuse(names, new_name, mat, voxel=0.009):
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
    obj.data.materials.append(mat)
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
        print('V5.2 voxel fuse fallback:', exc)
    return obj


# -----------------------------------------------------------------------------
# HAIR: discard V5.1 giant tuft result and rebuild a lower, fuller swept mass.
# -----------------------------------------------------------------------------
remove_many(['HairV51Unified'])

# Core cap/back overlap the entire crown so no bald wedges can appear.
uv('V52HairCap', (0.0, 0.040, 1.862), (0.208, 0.158, 0.170), HAIR, 48, 28)
uv('V52HairBack', (0.0, 0.112, 1.800), (0.192, 0.146, 0.138), HAIR, 42, 24)

# Low top masses give the silhouette movement without vertical spikes.
uv('V52TopL', (-0.090, 0.000, 1.982), (0.112, 0.078, 0.052), HAIR, 30, 18,
   rot=(math.radians(-4), math.radians(-8), math.radians(-12)))
uv('V52TopM', (0.010, -0.006, 1.995), (0.118, 0.079, 0.050), HAIR, 30, 18,
   rot=(math.radians(-4), math.radians(5), math.radians(6)))
uv('V52TopR', (0.102, 0.004, 1.970), (0.098, 0.073, 0.048), HAIR, 28, 16,
   rot=(math.radians(-3), math.radians(10), math.radians(15)))

# Broad overlapping fringe. Every patch intersects the cap and its neighbor,
# so voxel fusion produces one carved hairstyle rather than separate ribbons.
solid_patch('V52FringeHero', [
    (-0.205,1.958),(-0.150,1.988),(-0.090,1.986),(-0.025,1.950),
    (0.035,1.900),(0.060,1.850),(0.044,1.806),(0.010,1.820),
    (-0.040,1.860),(-0.105,1.900),(-0.170,1.925)
], -0.166, HAIR, 0.060, 0.014)
solid_patch('V52FringeMid', [
    (-0.035,1.988),(0.035,1.995),(0.105,1.966),(0.132,1.925),
    (0.115,1.885),(0.080,1.850),(0.043,1.825),(0.018,1.855),
    (-0.006,1.905)
], -0.163, HAIR, 0.058, 0.014)
solid_patch('V52FringeLeft', [
    (-0.210,1.920),(-0.177,1.950),(-0.130,1.935),(-0.120,1.885),
    (-0.137,1.825),(-0.165,1.775),(-0.195,1.750),(-0.210,1.800)
], -0.153, HAIR, 0.052, 0.012)
solid_patch('V52FringeRight', [
    (0.095,1.955),(0.150,1.950),(0.194,1.915),(0.208,1.870),
    (0.198,1.825),(0.172,1.790),(0.145,1.815),(0.122,1.865)
], -0.153, HAIR, 0.052, 0.012)

hair = fuse([
    'V52HairCap','V52HairBack','V52TopL','V52TopM','V52TopR',
    'V52FringeHero','V52FringeMid','V52FringeLeft','V52FringeRight'
], 'HairV52Unified', HAIR, voxel=0.0085)
if hair:
    hair.scale.x *= 1.020
    hair.scale.z *= 0.990

# -----------------------------------------------------------------------------
# FACE: concept has expressive but not googly eyes; enlarge modestly and soften.
# -----------------------------------------------------------------------------
for side in (-1,1):
    eye = bpy.data.objects.get(f'EyeWhite_{side}')
    iris = bpy.data.objects.get(f'Iris_{side}')
    pupil = bpy.data.objects.get(f'Pupil_{side}')
    glint = bpy.data.objects.get(f'EyeGlint_{side}')
    if eye:
        eye.scale.x *= 1.10
        eye.scale.z *= 1.09
    if iris:
        iris.scale.x *= 1.08
        iris.scale.z *= 1.08
    if pupil:
        pupil.scale.x *= 1.04
        pupil.scale.z *= 1.06
    if glint:
        glint.scale *= 1.04

# Stronger concept brows: slightly thicker and lower.
for name in ['BrowL','BrowR']:
    obj = bpy.data.objects.get(name)
    if obj:
        obj.location.z -= 0.005
        if hasattr(obj.data, 'bevel_depth'):
            obj.data.bevel_depth *= 1.10

# Warm the complexion a little closer to the concept palette.
recolor(SKIN, (0.80, 0.49, 0.32))
recolor(BLUSH, (0.78, 0.31, 0.21))

# Slightly larger ears help frame the head like the turnaround.
for side in (-1,1):
    ear = bpy.data.objects.get(f'Ear_{side}')
    if ear:
        ear.scale *= 1.08

# -----------------------------------------------------------------------------
# HAND/SLEEVE cleanup after V5.1.
# -----------------------------------------------------------------------------
for side in (-1,1):
    hand = bpy.data.objects.get(f'HandV51_{side}')
    if hand:
        hand.scale.x *= 0.95
        hand.scale.z *= 1.03
    sleeve = bpy.data.objects.get(f'Sleeve_{side}')
    if sleeve:
        sleeve.scale.x *= 0.91
        sleeve.scale.y *= 0.94
        sleeve.scale.z *= 1.025
    cuff = bpy.data.objects.get(f'RolledSleeve_{side}')
    if cuff:
        cuff.scale.x *= 0.94
        cuff.scale.y *= 0.95

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
print(f'Exported Lembah Sari Character V5.2 hair/facial candidate to {OUT_PATH}')
