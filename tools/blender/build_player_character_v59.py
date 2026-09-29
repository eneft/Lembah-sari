import bpy
import math
import os

# Lembah Sari Character V5.9 — final hand silhouette pass.
# Candidate only. Keeps the accepted V5.8 face/hair/body direction and replaces
# the last lumpy hand construction with a single continuous tapered hand mesh.

BASE = os.path.join(os.path.dirname(__file__), "build_player_character_v58.py")
exec(compile(open(BASE, "r", encoding="utf-8").read(), BASE, "exec"), globals(), globals())


def hand_body(name, side, material):
    s = float(side)
    cx, cy = 0.220*s, -0.104
    # One continuous organic form from wrist to rounded finger end.
    # Each ring: z, x-radius, y-radius, x-offset, y-offset.
    rings = [
        (0.858, 0.027, 0.023, 0.000,  0.000),
        (0.840, 0.034, 0.026, 0.001*s, -0.002),
        (0.812, 0.041, 0.030, 0.002*s, -0.004),
        (0.780, 0.042, 0.030, 0.003*s, -0.005),
        (0.748, 0.038, 0.028, 0.003*s, -0.005),
        (0.724, 0.031, 0.025, 0.002*s, -0.004),
        (0.710, 0.021, 0.019, 0.001*s, -0.002),
    ]
    sides = 28
    verts, faces = [], []
    for z, rx, ry, ox, oy in rings:
        for i in range(sides):
            a = math.tau * i / sides
            verts.append((cx + ox + math.cos(a)*rx,
                          cy + oy + math.sin(a)*ry,
                          z))
    for r in range(len(rings)-1):
        a0 = r*sides
        b0 = (r+1)*sides
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

    bevel = obj.modifiers.new('HandSoftness', 'BEVEL')
    bevel.width = 0.004
    bevel.segments = 2
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    try:
        bpy.ops.object.modifier_apply(modifier=bevel.name)
    except Exception:
        pass
    return obj


for side in (-1, 1):
    s = float(side)
    remove_many([f'HandV58_{side}'])
    body = hand_body(f'V59HandBody_{side}', side, SKIN)

    # Small thumb volume, deeply embedded so it reads as a natural thumb bump,
    # not as a separate attached cylinder/sphere.
    thumb_name = f'V59Thumb_{side}'
    uv(thumb_name, (0.220*s + 0.034*s, -0.116, 0.785),
       (0.018, 0.016, 0.030), SKIN, 22, 14,
       rot=(0, math.radians(10*s), math.radians(22*s)))
    hand = fuse_meshes([body.name, thumb_name], f'HandV59_{side}', SKIN, 0.0032)
    if hand:
        hand.rotation_euler.z = math.radians(-2*s)
        hand.scale.x *= 1.01
        hand.scale.y *= 0.98

# Slightly soften eyebrow dominance after V5.8's smaller eyes.
for name in ['BrowL', 'BrowR']:
    brow = bpy.data.objects.get(name)
    if brow and hasattr(brow.data, 'bevel_depth'):
        brow.data.bevel_depth *= 0.90

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
print(f'Exported Lembah Sari Character V5.9 unified-hand candidate to {OUT_PATH}')
