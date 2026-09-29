import bpy
import math
import os

# Lembah Sari Character V6.0 — structural silhouette cleanup.
# Candidate only. Rebuilds the visible weak points from the V5.9 phone review:
# segmented arms, lumpy hands, oversized/blocky sleeve mass, and slab-like fringe.

BASE = os.path.join(os.path.dirname(__file__), "build_player_character_v59.py")
exec(compile(open(BASE, "r", encoding="utf-8").read(), BASE, "exec"), globals(), globals())


def remove_if(name):
    obj = bpy.data.objects.get(name)
    if obj:
        bpy.data.objects.remove(obj, do_unlink=True)


def rounded_patch(name, outline, depth_y, material, thickness=0.040):
    obj = solid_patch(name, outline, depth_y, material, thickness, 0.010)
    if obj and obj.type == 'MESH':
        bev = obj.modifiers.new('SoftFringe', 'BEVEL')
        bev.width = 0.006
        bev.segments = 3
        bpy.context.view_layer.objects.active = obj
        try:
            bpy.ops.object.modifier_apply(modifier=bev.name)
        except Exception:
            pass
        for p in obj.data.polygons:
            p.use_smooth = True
    return obj


def hand_silhouette(name, side, material):
    """Single relaxed hand body, narrower at wrist and slightly flattened front/back."""
    s = float(side)
    cx, cy = 0.224*s, -0.076
    rings = [
        # z, width x, depth y, x shift
        (0.862, 0.027, 0.020,  0.000),
        (0.842, 0.031, 0.022,  0.001*s),
        (0.818, 0.036, 0.024,  0.002*s),
        (0.792, 0.039, 0.025,  0.003*s),
        (0.764, 0.040, 0.025,  0.003*s),
        (0.738, 0.037, 0.023,  0.002*s),
        (0.716, 0.030, 0.020,  0.001*s),
        (0.702, 0.020, 0.015,  0.000),
    ]
    sides = 32
    verts, faces = [], []
    for z, rx, ry, ox in rings:
        for i in range(sides):
            a = math.tau * i / sides
            verts.append((cx + ox + math.cos(a)*rx,
                          cy + math.sin(a)*ry,
                          z))
    for r in range(len(rings)-1):
        a0, b0 = r*sides, (r+1)*sides
        for i in range(sides):
            j = (i+1) % sides
            faces.append((a0+i, a0+j, b0+j, b0+i))
    faces.append(tuple(reversed(range(sides))))
    end = (len(rings)-1)*sides
    faces.append(tuple(end+i for i in range(sides)))
    mesh = bpy.data.meshes.new(name+'Mesh')
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.parent = ROOT
    obj.data.materials.append(material)
    for p in obj.data.polygons:
        p.use_smooth = True
    bev = obj.modifiers.new('HandSoftness', 'BEVEL')
    bev.width = 0.0045
    bev.segments = 3
    bpy.context.view_layer.objects.active = obj
    try:
        bpy.ops.object.modifier_apply(modifier=bev.name)
    except Exception:
        pass
    return obj


# -----------------------------------------------------------------------------
# HAIR — shorter broad fringe with fewer hard wedges.
# -----------------------------------------------------------------------------
for n in [
    'V58HairCap','V58HairBack','V58SweepLeft','V58SweepHero','V58SweepRight',
    'V58TempleL','V58TempleR'
]:
    remove_if(n)

recolor(HAIR, (0.040, 0.012, 0.005))
recolor(HAIR_WARM, (0.080, 0.024, 0.009))
uv('V60HairCap', (0.0, 0.045, 1.855), (0.205, 0.151, 0.158), HAIR, 52, 30)
uv('V60HairBack', (0.0, 0.095, 1.795), (0.190, 0.116, 0.134), HAIR, 44, 26)

rounded_patch('V60FringeMain', [
    (-0.182,1.938),(-0.128,1.970),(-0.055,1.978),(0.022,1.947),
    (0.082,1.900),(0.110,1.855),(0.082,1.830),(0.028,1.852),
    (-0.030,1.878),(-0.092,1.908),(-0.148,1.916)
], -0.160, HAIR_WARM, 0.045)
rounded_patch('V60FringeLeft', [
    (-0.205,1.905),(-0.176,1.932),(-0.142,1.916),(-0.145,1.868),
    (-0.158,1.820),(-0.180,1.785),(-0.198,1.802),(-0.210,1.850)
], -0.154, HAIR, 0.040)
rounded_patch('V60FringeRight', [
    (0.070,1.932),(0.122,1.945),(0.170,1.920),(0.195,1.884),
    (0.196,1.842),(0.176,1.810),(0.145,1.826),(0.112,1.860)
], -0.153, HAIR, 0.040)
uv('V60TempleL', (-0.191,-0.012,1.792), (0.041,0.038,0.085), HAIR, 24, 14,
   rot=(math.radians(4),0,math.radians(-7)))
uv('V60TempleR', (0.192,-0.010,1.798), (0.040,0.037,0.082), HAIR_WARM, 24, 14,
   rot=(math.radians(4),0,math.radians(8)))

# -----------------------------------------------------------------------------
# ARMS — rebuild sleeve/cuff/forearm as smooth, narrow transitions.
# -----------------------------------------------------------------------------
for side in (-1, 1):
    s = float(side)
    for n in [f'Sleeve_{side}', f'RolledSleeve_{side}', f'Forearm_{side}', f'HandV59_{side}']:
        remove_if(n)

    # Cloth sleeve: narrower shoulder and tapered cuff, removing the box/bulb read.
    soft_tube(f'Sleeve_{side}', [
        (0.198*s,-0.005,1.355,0.070,0.064),
        (0.220*s,-0.011,1.300,0.071,0.064),
        (0.238*s,-0.017,1.235,0.067,0.060),
        (0.246*s,-0.022,1.170,0.061,0.055),
        (0.244*s,-0.026,1.122,0.057,0.051),
    ], SHIRT, 24)
    soft_tube(f'RolledSleeve_{side}', [
        (0.244*s,-0.026,1.126,0.060,0.053),
        (0.243*s,-0.029,1.095,0.061,0.054),
        (0.240*s,-0.032,1.066,0.055,0.049),
    ], SHIRT_SHADOW, 24)
    # Forearm meets the wrist at the same width/depth as the hand root.
    soft_tube(f'Forearm_{side}', [
        (0.238*s,-0.036,1.058,0.044,0.039),
        (0.234*s,-0.044,1.000,0.042,0.037),
        (0.230*s,-0.052,0.944,0.039,0.034),
        (0.226*s,-0.061,0.895,0.034,0.029),
        (0.224*s,-0.070,0.858,0.028,0.022),
    ], SKIN, 24)
    hand = hand_silhouette(f'HandV60_{side}', side, SKIN)
    if hand:
        hand.rotation_euler.z = math.radians(-1.5*s)

# -----------------------------------------------------------------------------
# BODY — reduce the wide rectangular shirt read without changing outfit identity.
# -----------------------------------------------------------------------------
shirt = bpy.data.objects.get('ShirtTorso')
if shirt:
    shirt.scale.x *= 0.94
    shirt.scale.y *= 0.96
bib = bpy.data.objects.get('OverallBib')
if bib:
    bib.scale.x *= 0.96
hips = bpy.data.objects.get('OverallHips')
if hips:
    hips.scale.x *= 0.97

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
print(f'Exported Lembah Sari Character V6.0 structural cleanup candidate to {OUT_PATH}')
