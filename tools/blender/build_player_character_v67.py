import bpy
import math
import os

# Lembah Sari Character V6.7 — layered rounded-fringe correction.
# Candidate only. Keeps V6.6 body/arm/hand/trouser proportions, rejects the
# visor-like V6.6 front mass, and replaces it with overlapping short hair locks.

BASE = os.path.join(os.path.dirname(__file__), "build_player_character_v66.py")
exec(compile(open(BASE, "r", encoding="utf-8").read(), BASE, "exec"), globals(), globals())


def remove_many(names):
    for name in names:
        obj = bpy.data.objects.get(name)
        if obj:
            bpy.data.objects.remove(obj, do_unlink=True)


def rounded_lock(name, sections, material, ring_sides=14):
    """Short volumetric hair lock with a rounded, non-pointed end."""
    verts, faces = [], []
    for x, y, z, width, depth in sections:
        for i in range(ring_sides):
            a = math.tau * i / ring_sides
            verts.append((x + math.cos(a) * width,
                          y + math.sin(a) * depth,
                          z))
    for r in range(len(sections) - 1):
        a0 = r * ring_sides
        b0 = (r + 1) * ring_sides
        for i in range(ring_sides):
            j = (i + 1) % ring_sides
            faces.append((a0 + i, a0 + j, b0 + j, b0 + i))
    faces.append(tuple(reversed(range(ring_sides))))
    end = (len(sections) - 1) * ring_sides
    faces.append(tuple(end + i for i in range(ring_sides)))

    mesh = bpy.data.meshes.new(name + 'Mesh')
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.parent = ROOT
    obj.data.materials.append(material)
    for p in obj.data.polygons:
        p.use_smooth = True
    bev = obj.modifiers.new('RoundedLockEdge', 'BEVEL')
    bev.width = 0.0055
    bev.segments = 3
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    try:
        bpy.ops.object.modifier_apply(modifier=bev.name)
    except Exception:
        pass
    return obj


remove_many(['V66FrontSweep', 'V66SideAccent'])
recolor(HAIR, (0.038, 0.011, 0.0045))
recolor(HAIR_WARM, (0.074, 0.021, 0.008))

# Main hero sweep: broad at the embedded crown root, then bends left/down.
rounded_lock('V67HeroSweep', [
    ( 0.075, -0.058, 1.952, 0.067, 0.032),
    ( 0.038, -0.091, 1.938, 0.067, 0.031),
    (-0.008, -0.120, 1.916, 0.060, 0.028),
    (-0.060, -0.144, 1.892, 0.047, 0.023),
    (-0.105, -0.157, 1.874, 0.027, 0.017),
], HAIR_WARM)

# Left support lock overlaps the hero sweep but ends higher/shorter.
rounded_lock('V67LeftLock', [
    (-0.036, -0.056, 1.946, 0.050, 0.027),
    (-0.074, -0.087, 1.929, 0.047, 0.025),
    (-0.112, -0.116, 1.906, 0.039, 0.021),
    (-0.145, -0.137, 1.885, 0.023, 0.015),
], HAIR)

# Center/right lock gives layered depth without creating a separate hard plate.
rounded_lock('V67CenterLock', [
    (0.118, -0.046, 1.944, 0.054, 0.029),
    (0.098, -0.083, 1.925, 0.052, 0.027),
    (0.069, -0.116, 1.902, 0.044, 0.023),
    (0.033, -0.143, 1.880, 0.027, 0.016),
], HAIR)

# Small right framing lock merges into the temple and keeps the side silhouette.
rounded_lock('V67RightLock', [
    (0.153, -0.033, 1.928, 0.046, 0.026),
    (0.163, -0.070, 1.907, 0.043, 0.024),
    (0.159, -0.103, 1.883, 0.034, 0.020),
    (0.145, -0.128, 1.861, 0.021, 0.014),
], HAIR_WARM)

# Slightly fuller cap helps the roots disappear into one coherent mass.
cap = bpy.data.objects.get('V60HairCap')
if cap:
    cap.scale.x *= 1.018
    cap.scale.y *= 1.025

# Final candidate export only. Gameplay asset remains untouched.
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
print(f'Exported Lembah Sari Character V6.7 layered-fringe candidate to {OUT_PATH}')
