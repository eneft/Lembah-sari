import bpy
import math
import os

# Lembah Sari Character V5.3 — silhouette/anatomy rebuild.
# Candidate only. V5.2 fixed the giant tuft but became too helmet-like.
# V5.3 uses a fused base cap plus crisp tapered locks, a real hand outline,
# and gently bent sleeves/forearms to approach the concept turnaround.

BASE = os.path.join(os.path.dirname(__file__), "build_player_character_v52.py")
exec(compile(open(BASE, "r", encoding="utf-8").read(), BASE, "exec"), globals(), globals())


def remove_many(names):
    for name in names:
        obj = bpy.data.objects.get(name)
        if obj:
            bpy.data.objects.remove(obj, do_unlink=True)


def fuse_base(names, new_name, material, voxel=0.010):
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
        print('V5.3 base fuse fallback:', exc)
    return obj


def sculpt_hand(name, side, center):
    # One beveled hand mesh with four subtle fingertip lobes and an integrated
    # thumb contour. No floating finger primitives.
    s = float(side)
    cx, y, cz = center
    local = [
        (-0.036, 0.060), (0.030, 0.060),
        (0.041, 0.045), (0.048, 0.023), (0.056, 0.005),
        (0.052,-0.014), (0.041,-0.026),
        (0.036,-0.047), (0.028,-0.061), (0.017,-0.067),
        (0.008,-0.061), (-0.002,-0.071), (-0.013,-0.063),
        (-0.024,-0.070), (-0.034,-0.060), (-0.043,-0.062),
        (-0.052,-0.049), (-0.054,-0.028), (-0.050,-0.003),
        (-0.047, 0.024),
    ]
    outline = [(cx + dx*s, cz + dz) for dx, dz in local]
    return solid_patch(name, outline, y, SKIN, 0.058, 0.012)


# -----------------------------------------------------------------------------
# HAIR — replace V5.2 helmet with organic base + readable tapered clumps.
# -----------------------------------------------------------------------------
remove_many(['HairV52Unified'])
recolor(HAIR, (0.115, 0.045, 0.020))
recolor(HAIR_WARM, (0.205, 0.075, 0.026))

uv('V53Cap', (0.0, 0.045, 1.858), (0.207, 0.160, 0.166), HAIR, 48, 28)
uv('V53Back', (0.0, 0.115, 1.800), (0.194, 0.151, 0.142), HAIR, 42, 24)
uv('V53TempleL', (-0.182, -0.002, 1.815), (0.050, 0.043, 0.110), HAIR, 26, 16,
   rot=(math.radians(3),0,math.radians(-7)))
uv('V53TempleR', (0.185, 0.004, 1.820), (0.049, 0.042, 0.105), HAIR, 26, 16,
   rot=(math.radians(3),0,math.radians(8)))
fuse_base(['V53Cap','V53Back','V53TempleL','V53TempleR'], 'HairV53Base', HAIR, 0.010)

# Dominant asymmetrical fringe: broad at root, pointed at end, all roots sunk
# into the cap. This is intentionally close to the concept's carved clumps.
path_lock('V53FringeHero',
    [(-0.150,-0.055,1.972),(-0.112,-0.105,1.930),(-0.055,-0.145,1.875)],
    [(0.080,0.052),(0.069,0.046),(0.052,0.036)],
    (0.010,-0.177,1.785), HAIR_WARM, 14)
path_lock('V53FringeCenter',
    [(-0.040,-0.060,1.985),(-0.012,-0.112,1.940),(0.008,-0.150,1.892)],
    [(0.066,0.046),(0.055,0.040),(0.042,0.031)],
    (0.030,-0.176,1.820), HAIR, 14)
path_lock('V53FringeRight',
    [(0.060,-0.052,1.975),(0.105,-0.095,1.940),(0.132,-0.132,1.900)],
    [(0.055,0.041),(0.046,0.035),(0.034,0.027)],
    (0.164,-0.160,1.845), HAIR_WARM, 12)
path_lock('V53SideLeft',
    [(-0.185,-0.010,1.905),(-0.203,-0.048,1.865),(-0.205,-0.080,1.820)],
    [(0.043,0.035),(0.036,0.030),(0.028,0.024)],
    (-0.198,-0.105,1.755), HAIR, 12)

# Low crown locks: directional movement without one huge vertical spike.
path_lock('V53TopLeft',
    [(-0.100,0.020,1.982),(-0.138,0.010,2.010),(-0.166,0.000,2.018)],
    [(0.055,0.040),(0.045,0.034),(0.032,0.025)],
    (-0.198,-0.012,2.010), HAIR_WARM, 12)
path_lock('V53TopCenter',
    [(-0.012,0.018,1.995),(0.012,0.006,2.025),(0.034,-0.004,2.035)],
    [(0.048,0.037),(0.039,0.031),(0.028,0.023)],
    (0.062,-0.016,2.025), HAIR, 12)
path_lock('V53TopRight',
    [(0.075,0.025,1.980),(0.112,0.014,2.000),(0.140,0.004,2.004)],
    [(0.043,0.034),(0.035,0.029),(0.026,0.022)],
    (0.174,-0.012,1.990), HAIR_WARM, 12)

# -----------------------------------------------------------------------------
# FACE — give the tapered head more sculpted appeal and readable expression.
# -----------------------------------------------------------------------------
# Slightly narrower lower face, preserving cheek width.
head = bpy.data.objects.get('HeadV5')
if head:
    for vert in head.data.vertices:
        if vert.co.z < 1.655:
            t = max(0.0, min(1.0, (1.655 - vert.co.z) / 0.14))
            vert.co.x *= (1.0 - 0.055*t)

# Replace dot nose with a tiny real volume and lift the smile corners.
remove_many(['Nose','Smile'])
uv('Nose', (0.0,-0.168,1.685), (0.016,0.009,0.014), SKIN, 20, 12,
   rot=(math.radians(-8),0,0))
curve('Smile', [(-0.043,-0.163,1.626),(-0.022,-0.167,1.617),(0.0,-0.168,1.616),
                (0.023,-0.167,1.619),(0.045,-0.162,1.628)], MOUTH, 0.0028)

# Larger concept-like eyes while retaining sclera and a controlled pupil size.
for side in (-1,1):
    for prefix, sx, sz in [
        ('EyeWhite',1.06,1.07),('Iris',1.055,1.06),('Pupil',1.00,1.02),('EyeGlint',1.02,1.02)
    ]:
        obj = bpy.data.objects.get(f'{prefix}_{side}')
        if obj:
            obj.scale.x *= sx
            obj.scale.z *= sz

# Brows get a little closer to the eyes and slightly stronger, as in concept.
for name in ['BrowL','BrowR']:
    obj = bpy.data.objects.get(name)
    if obj:
        obj.location.z -= 0.006
        if hasattr(obj.data, 'bevel_depth'):
            obj.data.bevel_depth *= 1.08

# -----------------------------------------------------------------------------
# ARMS/HANDS — rebuild pose and remove mitten silhouette.
# -----------------------------------------------------------------------------
for side in (-1,1):
    s = float(side)
    remove_many([
        f'Sleeve_{side}', f'RolledSleeve_{side}', f'Forearm_{side}', f'HandV51_{side}',
        f'Thumb_{side}', f'HandCreaseA_{side}', f'HandCreaseB_{side}'
    ] + [f'V51FingerCrease_{side}_{i}' for i in range(3)])

    # Gentle relaxed bend: elbow slightly out, wrist returns inward.
    soft_tube(f'Sleeve_{side}', [
        (0.202*s,-0.004,1.360,0.074,0.068),
        (0.235*s,-0.012,1.300,0.076,0.069),
        (0.258*s,-0.021,1.225,0.072,0.065),
        (0.268*s,-0.030,1.155,0.064,0.059),
        (0.264*s,-0.036,1.110,0.060,0.055),
    ], SHIRT, 22)
    soft_tube(f'RolledSleeve_{side}', [
        (0.264*s,-0.036,1.116,0.063,0.057),
        (0.260*s,-0.040,1.086,0.066,0.059),
        (0.254*s,-0.044,1.055,0.059,0.053),
    ], SHIRT_SHADOW, 22)
    soft_tube(f'Forearm_{side}', [
        (0.252*s,-0.047,1.048,0.046,0.041),
        (0.250*s,-0.056,0.975,0.044,0.039),
        (0.242*s,-0.069,0.905,0.040,0.036),
        (0.232*s,-0.080,0.850,0.036,0.032),
    ], SKIN, 20)

    hand = sculpt_hand(f'HandV53_{side}', side, (0.226*s,-0.100,0.785))
    if hand:
        hand.rotation_euler.y = math.radians(5*s)
        hand.rotation_euler.z = math.radians(-2*s)
    # Three crease hints track the fused hand surface; no separate fingers.
    for idx, off in enumerate((-0.018, 0.0, 0.018)):
        curve(f'V53FingerCrease_{side}_{idx}', [
            (0.226*s + off,-0.131,0.774),
            (0.226*s + off*0.94,-0.132,0.748),
        ], MOUTH, 0.00115)

# Keep trouser silhouette loose but remove rectangular excess.
for side in (-1,1):
    tr = bpy.data.objects.get(f'Trouser_{side}')
    if tr:
        tr.scale.x *= 0.975
        tr.scale.y *= 0.985

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
print(f'Exported Lembah Sari Character V5.3 silhouette/anatomy candidate to {OUT_PATH}')
