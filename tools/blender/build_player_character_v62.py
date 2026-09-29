import bpy
import math
import os

# Lembah Sari Character V6.2 — natural hand contour pass.
# Candidate only. Keeps V6.1 proportions/arms and replaces the last symmetric
# capsule hands with one-piece asymmetric forms that include a thumb bulge.

BASE = os.path.join(os.path.dirname(__file__), "build_player_character_v61.py")
exec(compile(open(BASE, "r", encoding="utf-8").read(), BASE, "exec"), globals(), globals())


def build_hand(name, side, material):
    s = float(side)
    cx, cy = 0.223*s, -0.071
    # z, rx, ry, outer_shift. Outer shift creates an integrated thumb-side bulge.
    rings = [
        (0.875,0.026,0.019,0.000),
        (0.858,0.030,0.021,0.002),
        (0.838,0.034,0.022,0.006),
        (0.817,0.037,0.023,0.010),
        (0.796,0.039,0.023,0.012),
        (0.776,0.037,0.022,0.009),
        (0.758,0.033,0.020,0.005),
        (0.744,0.027,0.017,0.002),
        (0.735,0.018,0.012,0.000),
    ]
    sides = 36
    verts, faces = [], []
    for z, rx, ry, outward in rings:
        ox = outward * s
        for i in range(sides):
            a = math.tau*i/sides
            # Slightly flatten inner side while retaining round outer/thumb side.
            xwave = math.cos(a)
            x = cx + ox + xwave*rx
            if xwave * s < -0.35:
                x = cx + ox + xwave*rx*0.92
            verts.append((x, cy + math.sin(a)*ry, z))
    for r in range(len(rings)-1):
        a0,b0=r*sides,(r+1)*sides
        for i in range(sides):
            j=(i+1)%sides
            faces.append((a0+i,a0+j,b0+j,b0+i))
    faces.append(tuple(reversed(range(sides))))
    end=(len(rings)-1)*sides
    faces.append(tuple(end+i for i in range(sides)))
    mesh=bpy.data.meshes.new(name+'Mesh')
    mesh.from_pydata(verts,[],faces)
    mesh.update()
    obj=bpy.data.objects.new(name,mesh)
    bpy.context.collection.objects.link(obj)
    obj.parent=ROOT
    obj.data.materials.append(material)
    for p in obj.data.polygons:
        p.use_smooth=True
    bev=obj.modifiers.new('HandSoftness','BEVEL')
    bev.width=0.0038
    bev.segments=3
    bpy.context.view_layer.objects.active=obj
    try:
        bpy.ops.object.modifier_apply(modifier=bev.name)
    except Exception:
        pass
    return obj


for side in (-1,1):
    old=bpy.data.objects.get(f'HandV61_{side}')
    if old:
        bpy.data.objects.remove(old,do_unlink=True)
    hand=build_hand(f'HandV62_{side}',side,SKIN)
    if hand:
        hand.rotation_euler.z=math.radians(-1.0*side)

# Export candidate only.
bpy.ops.object.select_all(action='DESELECT')
ROOT.select_set(True)
for obj in ROOT.children_recursive:
    obj.select_set(True)
bpy.context.view_layer.objects.active=ROOT
bpy.ops.export_scene.gltf(filepath=OUT_PATH,export_format='GLB',use_selection=True,export_apply=True,export_yup=True)
print(f'Exported Lembah Sari Character V6.2 natural-hand candidate to {OUT_PATH}')
