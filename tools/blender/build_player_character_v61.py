import bpy
import math
import os

# Lembah Sari Character V6.1 — proportion and arm continuity pass.
# Candidate only. Fixes the V6.0 review: oversized head, cuff-ring segmentation,
# mitten-like hands, and bulky upper sleeves.

BASE = os.path.join(os.path.dirname(__file__), "build_player_character_v60.py")
exec(compile(open(BASE, "r", encoding="utf-8").read(), BASE, "exec"), globals(), globals())


def scale_loc_and_size(obj, pivot=(0.0, 0.0, 1.75), factor=0.94):
    if not obj:
        return
    px, py, pz = pivot
    obj.location.x = px + (obj.location.x - px) * factor
    obj.location.y = py + (obj.location.y - py) * factor
    obj.location.z = pz + (obj.location.z - pz) * factor
    obj.scale.x *= factor
    obj.scale.y *= factor
    obj.scale.z *= factor


# -----------------------------------------------------------------------------
# HEAD — reduce overall ensemble while preserving expression and relative layout.
# -----------------------------------------------------------------------------
head = bpy.data.objects.get('HeadV57')
if head and head.type == 'MESH':
    pz = 1.75
    for v in head.data.vertices:
        v.co.x *= 0.94
        v.co.y *= 0.94
        v.co.z = pz + (v.co.z - pz) * 0.94

feature_names = ['Nose','Smile','BrowL','BrowR','UpperLidL','UpperLidR']
for side in (-1, 1):
    feature_names += [
        f'EyeWhite_{side}', f'Iris_{side}', f'Pupil_{side}', f'EyeGlint_{side}',
        f'Blush_{side}', f'Ear_{side}'
    ]
for n in feature_names:
    scale_loc_and_size(bpy.data.objects.get(n), factor=0.94)

for n in ['V60HairCap','V60HairBack','V60FringeMain','V60FringeLeft','V60FringeRight','V60TempleL','V60TempleR']:
    scale_loc_and_size(bpy.data.objects.get(n), factor=0.95)

# -----------------------------------------------------------------------------
# ARMS — remove visual cuff ring and shorten the hands.
# -----------------------------------------------------------------------------
for side in (-1, 1):
    s = float(side)
    for n in [f'Sleeve_{side}', f'RolledSleeve_{side}', f'Forearm_{side}', f'HandV60_{side}']:
        obj = bpy.data.objects.get(n)
        if obj:
            bpy.data.objects.remove(obj, do_unlink=True)

    # Single cloth sleeve taper. The last ring acts as the rolled edge without
    # a separate donut/cuff object.
    soft_tube(f'Sleeve_{side}', [
        (0.194*s,-0.005,1.352,0.064,0.058),
        (0.213*s,-0.010,1.302,0.065,0.058),
        (0.229*s,-0.016,1.245,0.061,0.055),
        (0.238*s,-0.021,1.188,0.056,0.050),
        (0.239*s,-0.026,1.138,0.052,0.047),
        (0.237*s,-0.030,1.103,0.050,0.045),
    ], SHIRT, 24)

    # A tiny cloth trim band integrated close to the forearm instead of a ring.
    soft_tube(f'SleeveTrim_{side}', [
        (0.237*s,-0.030,1.106,0.052,0.046),
        (0.236*s,-0.032,1.086,0.051,0.045),
        (0.235*s,-0.034,1.070,0.047,0.041),
    ], SHIRT_SHADOW, 24)

    soft_tube(f'Forearm_{side}', [
        (0.234*s,-0.036,1.066,0.042,0.036),
        (0.231*s,-0.043,1.010,0.040,0.034),
        (0.228*s,-0.050,0.958,0.037,0.031),
        (0.225*s,-0.057,0.910,0.033,0.028),
        (0.223*s,-0.064,0.872,0.028,0.023),
    ], SKIN, 24)

    # Shorter relaxed hand; keep a gentle taper, no separate thumb geometry.
    cx, cy = 0.223*s, -0.071
    rings = [
        (0.875,0.027,0.020,0.000),
        (0.858,0.031,0.022,0.001*s),
        (0.836,0.035,0.023,0.002*s),
        (0.812,0.037,0.024,0.002*s),
        (0.788,0.036,0.023,0.002*s),
        (0.767,0.032,0.021,0.001*s),
        (0.750,0.026,0.018,0.000),
        (0.740,0.017,0.013,0.000),
    ]
    sides = 32
    verts, faces = [], []
    for z, rx, ry, ox in rings:
        for i in range(sides):
            a = math.tau*i/sides
            verts.append((cx+ox+math.cos(a)*rx,
                          cy+math.sin(a)*ry,
                          z))
    for r in range(len(rings)-1):
        a0,b0=r*sides,(r+1)*sides
        for i in range(sides):
            j=(i+1)%sides
            faces.append((a0+i,a0+j,b0+j,b0+i))
    faces.append(tuple(reversed(range(sides))))
    end=(len(rings)-1)*sides
    faces.append(tuple(end+i for i in range(sides)))
    mesh=bpy.data.meshes.new(f'HandV61_{side}Mesh')
    mesh.from_pydata(verts,[],faces); mesh.update()
    hand=bpy.data.objects.new(f'HandV61_{side}',mesh)
    bpy.context.collection.objects.link(hand)
    hand.parent=ROOT
    hand.data.materials.append(SKIN)
    for p in hand.data.polygons: p.use_smooth=True
    bev=hand.modifiers.new('HandSoftness','BEVEL'); bev.width=0.004; bev.segments=3
    bpy.context.view_layer.objects.active=hand
    try: bpy.ops.object.modifier_apply(modifier=bev.name)
    except Exception: pass

# Slightly narrow the torso one more step after shrinking the head.
shirt = bpy.data.objects.get('ShirtTorso')
if shirt:
    shirt.scale.x *= 0.97
bib = bpy.data.objects.get('OverallBib')
if bib:
    bib.scale.x *= 0.98

# Export candidate only.
bpy.ops.object.select_all(action='DESELECT')
ROOT.select_set(True)
for obj in ROOT.children_recursive:
    obj.select_set(True)
bpy.context.view_layer.objects.active = ROOT
bpy.ops.export_scene.gltf(filepath=OUT_PATH, export_format='GLB', use_selection=True, export_apply=True, export_yup=True)
print(f'Exported Lembah Sari Character V6.1 proportion/continuity candidate to {OUT_PATH}')
