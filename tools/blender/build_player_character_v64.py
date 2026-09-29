import bpy
import os

# Lembah Sari Character V6.4 — clean hand + safe fringe correction.
# IMPORTANT: branches from V6.2, not V6.3, because V6.3 scaled fringe meshes
# around world origin and pulled the hair down over the eyes.

BASE = os.path.join(os.path.dirname(__file__), "build_player_character_v62.py")
exec(compile(open(BASE, "r", encoding="utf-8").read(), BASE, "exec"), globals(), globals())


def hand_outline(name, side):
    s = float(side)
    cx = 0.223 * s
    # Top aligns with V6.1/V6.2 forearm wrist at ~0.872.
    cz = 0.805
    local = [
        (-0.021,  0.067),
        ( 0.021,  0.067),
        ( 0.028,  0.048),
        ( 0.030,  0.028),
        ( 0.042,  0.014),
        ( 0.043, -0.003),
        ( 0.036, -0.016),
        ( 0.029, -0.021),
        ( 0.029, -0.045),
        ( 0.023, -0.061),
        ( 0.014, -0.069),
        ( 0.005, -0.065),
        (-0.002, -0.071),
        (-0.011, -0.066),
        (-0.020, -0.068),
        (-0.028, -0.058),
        (-0.033, -0.043),
        (-0.034, -0.022),
        (-0.032,  0.008),
        (-0.028,  0.040),
    ]
    pts = [(cx + dx*s, cz + dz) for dx, dz in local]
    obj = patch(name, pts, -0.071, SKIN, thickness=0.038, radius=0.006)
    if obj and obj.type == 'MESH':
        for p in obj.data.polygons:
            p.use_smooth = True
        bev = obj.modifiers.new('HandSoftness', 'BEVEL')
        bev.width = 0.0032
        bev.segments = 3
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        try:
            bpy.ops.object.modifier_apply(modifier=bev.name)
        except Exception:
            pass
    return obj


for side in (-1, 1):
    old = bpy.data.objects.get(f'HandV62_{side}')
    if old:
        bpy.data.objects.remove(old, do_unlink=True)
    hand_outline(f'HandV64_{side}', side)

# Reduce fringe bulk around each mesh's own center, then move it slightly UP.
# This avoids V6.3's world-origin scale regression.
def compact_mesh(name, sx=1.0, sz=1.0, dz=0.0):
    obj = bpy.data.objects.get(name)
    if not obj or obj.type != 'MESH' or not obj.data.vertices:
        return
    xs = [v.co.x for v in obj.data.vertices]
    zs = [v.co.z for v in obj.data.vertices]
    cx = (min(xs) + max(xs)) * 0.5
    cz = (min(zs) + max(zs)) * 0.5
    for v in obj.data.vertices:
        v.co.x = cx + (v.co.x - cx) * sx
        v.co.z = cz + (v.co.z - cz) * sz + dz

compact_mesh('V60FringeMain', 0.98, 0.91, 0.015)
compact_mesh('V60FringeLeft', 0.96, 0.92, 0.012)
compact_mesh('V60FringeRight', 0.96, 0.92, 0.012)

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
print(f'Exported Lembah Sari Character V6.4 corrected-hand candidate to {OUT_PATH}')
