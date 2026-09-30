import bpy
import math
import os
from mathutils import Vector

# Lembah Sari Character V7.2 — clean chin + organic fringe correction.
# Candidate only. Body/outfit/hands remain inherited from V7.1/V6.8.
# This pass aggressively removes lower-face debris and replaces the V7.1 fused
# hair shell with smooth overlapping volumetric locks so the forehead no longer
# shows serrated/slab-like overlap artifacts.

BASE = os.path.join(os.path.dirname(__file__), "build_player_character_v71.py")
exec(compile(open(BASE, "r", encoding="utf-8").read(), BASE, "exec"), globals(), globals())


def remove_obj(name):
    obj = bpy.data.objects.get(name)
    if obj:
        bpy.data.objects.remove(obj, do_unlink=True)


def curve_points_world(obj):
    pts = []
    if obj.type != 'CURVE':
        return pts
    for spline in obj.data.splines:
        if spline.type == 'BEZIER':
            pts.extend(obj.matrix_world @ bp.co for bp in spline.bezier_points)
        else:
            for p in spline.points:
                pts.append(obj.matrix_world @ Vector((p.co.x, p.co.y, p.co.z)))
    return pts


def world_bbox(obj):
    return [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]


def organic_lock(name, sections, material, sides=18):
    """Rounded volumetric hair lock; broad root, soft tapered end, no flat sheet."""
    verts, faces = [], []
    for x, y, z, rx, ry in sections:
        for i in range(sides):
            a = math.tau * i / sides
            verts.append((x + math.cos(a) * rx,
                          y + math.sin(a) * ry,
                          z))
    for r in range(len(sections) - 1):
        a0 = r * sides
        b0 = (r + 1) * sides
        for i in range(sides):
            j = (i + 1) % sides
            faces.append((a0 + i, a0 + j, b0 + j, b0 + i))
    faces.append(tuple(reversed(range(sides))))
    end = (len(sections) - 1) * sides
    faces.append(tuple(end + i for i in range(sides)))

    mesh = bpy.data.meshes.new(name + 'Mesh')
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.parent = ROOT
    obj.data.materials.append(material)
    for poly in obj.data.polygons:
        poly.use_smooth = True

    bevel = obj.modifiers.new('V72LockRoundness', 'BEVEL')
    bevel.width = 0.006
    bevel.segments = 3
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    try:
        bpy.ops.object.modifier_apply(modifier=bevel.name)
    except Exception as exc:
        print('V7.2 lock bevel fallback:', name, exc)
    return obj


# -----------------------------------------------------------------------------
# LOWER-FACE HYGIENE — V7.1 proved the visible chin strokes were not removed by
# the old name-based cleanup. Remove anything that physically intersects the
# front/central chin zone, regardless of legacy name, except intentional face.
# -----------------------------------------------------------------------------
protected_meshes = {
    'HeadV70', 'Nose', 'Blush_-1', 'Blush_1',
    'EyeWhite_-1', 'EyeWhite_1', 'Iris_-1', 'Iris_1',
    'Pupil_-1', 'Pupil_1', 'EyeGlint_-1', 'EyeGlint_1',
    'Ear_-1', 'Ear_1', 'EarInner_-1', 'EarInner_1',
}

# Curves: anything except Smile that crosses the lower-face acceptance box is debris.
for obj in list(bpy.data.objects):
    if obj.type != 'CURVE' or obj.name == 'Smile':
        continue
    pts = curve_points_world(obj)
    if any(abs(p.x) < 0.155 and p.y < -0.120 and 1.535 < p.z < 1.695 for p in pts):
        print('V7.2 removing lower-face curve debris:', obj.name)
        bpy.data.objects.remove(obj, do_unlink=True)

# Meshes: remove small legacy ornaments/intersections physically living in chin zone.
for obj in list(bpy.data.objects):
    if obj.type != 'MESH' or obj.name in protected_meshes:
        continue
    try:
        pts = world_bbox(obj)
    except Exception:
        continue
    min_x, max_x = min(p.x for p in pts), max(p.x for p in pts)
    min_y, max_y = min(p.y for p in pts), max(p.y for p in pts)
    min_z, max_z = min(p.z for p in pts), max(p.z for p in pts)
    # Require the whole object to be face-sized/small and overlap the front chin.
    small = (max_x - min_x) < 0.32 and (max_z - min_z) < 0.22
    overlaps_chin = (max_x > -0.155 and min_x < 0.155 and
                     min_y < -0.120 and max_z > 1.535 and min_z < 1.690)
    if small and overlaps_chin:
        print('V7.2 removing lower-face mesh debris:', obj.name)
        bpy.data.objects.remove(obj, do_unlink=True)


# -----------------------------------------------------------------------------
# HEAD — subtly taper the lower jaw and preserve fuller cheeks. This keeps the
# concept's youthful face but removes the broad round lower-face read from V7.1.
# -----------------------------------------------------------------------------
head = bpy.data.objects.get('HeadV70')
if head and head.type == 'MESH':
    for v in head.data.vertices:
        z = v.co.z
        if z < 1.625:
            v.co.x *= 0.935
        elif z < 1.675:
            v.co.x *= 0.965
        elif z < 1.775:
            v.co.x *= 1.012
    for poly in head.data.polygons:
        poly.use_smooth = True

# Nose becomes nearly flush: enough light cue to read, never a pasted bead.
remove_obj('Nose')
uv('Nose', (0.0, -0.1668, 1.6885),
   (0.0052, 0.00075, 0.0066), SKIN, 24, 14)


# -----------------------------------------------------------------------------
# HAIR — remove the V7.1 fused lobe result entirely. Rebuild with one quiet cap,
# one back volume, and a handful of rounded swept locks. Locks intentionally stay
# separate but deeply overlap the cap: clean silhouettes without voxel serration.
# -----------------------------------------------------------------------------
remove_obj('HairV71Unified')
for name in [
    'V71HairCap', 'V71HairBack', 'V71TopLeft', 'V71TopCenter', 'V71TopRight',
    'V71FringeLeft', 'V71FringeHero', 'V71FringeRight',
    'V71TempleL', 'V71TempleR',
]:
    remove_obj(name)

recolor(HAIR, (0.040, 0.011, 0.0045))
recolor(HAIR_WARM, (0.067, 0.018, 0.0070))

# Base volumes are intentionally simple and mostly hidden by the locks.
uv('V72HairCap', (0.0, 0.055, 1.895), (0.220, 0.166, 0.158), HAIR, 56, 32)
uv('V72HairBack', (0.0, 0.120, 1.825), (0.201, 0.145, 0.128), HAIR, 48, 28)

# Main diagonal hero sweep: large, soft, concept-like direction.
organic_lock('V72HeroSweep', [
    ( 0.090, -0.035, 2.020, 0.076, 0.038),
    ( 0.052, -0.078, 2.000, 0.076, 0.037),
    ( 0.004, -0.116, 1.970, 0.067, 0.033),
    (-0.052, -0.145, 1.934, 0.053, 0.028),
    (-0.102, -0.162, 1.902, 0.035, 0.022),
    (-0.132, -0.169, 1.884, 0.018, 0.013),
], HAIR_WARM)

# Left support lock merges visually into the hero sweep, ending above the brow.
organic_lock('V72LeftSweep', [
    (-0.060, -0.030, 2.002, 0.061, 0.033),
    (-0.100, -0.070, 1.982, 0.059, 0.031),
    (-0.136, -0.108, 1.950, 0.051, 0.028),
    (-0.165, -0.137, 1.918, 0.039, 0.023),
    (-0.182, -0.150, 1.892, 0.019, 0.013),
], HAIR)

# Right framing lock keeps the forehead open instead of creating a visor.
organic_lock('V72RightSweep', [
    (0.145, -0.020, 1.995, 0.055, 0.031),
    (0.142, -0.062, 1.970, 0.053, 0.029),
    (0.130, -0.101, 1.940, 0.046, 0.026),
    (0.108, -0.130, 1.911, 0.034, 0.021),
    (0.084, -0.145, 1.892, 0.017, 0.012),
], HAIR_WARM)

# Small crown accents sweep sideways/backward and never stand as spikes.
organic_lock('V72CrownLeft', [
    (-0.060, 0.018, 2.015, 0.044, 0.025),
    (-0.092, 0.015, 2.047, 0.034, 0.020),
    (-0.126, 0.012, 2.061, 0.020, 0.014),
    (-0.150, 0.010, 2.058, 0.010, 0.009),
], HAIR_WARM, sides=16)
organic_lock('V72CrownRight', [
    (0.050, 0.020, 2.012, 0.043, 0.024),
    (0.085, 0.016, 2.041, 0.033, 0.019),
    (0.121, 0.011, 2.052, 0.019, 0.013),
    (0.146, 0.008, 2.047, 0.010, 0.008),
], HAIR, sides=16)

# Short side locks frame the ears/cheeks but stay outside the eye region.
organic_lock('V72TempleL', [
    (-0.185, 0.000, 1.922, 0.043, 0.028),
    (-0.202, -0.030, 1.882, 0.038, 0.025),
    (-0.210, -0.055, 1.840, 0.030, 0.021),
    (-0.207, -0.070, 1.804, 0.016, 0.012),
], HAIR, sides=16)
organic_lock('V72TempleR', [
    (0.184, 0.002, 1.922, 0.041, 0.027),
    (0.201, -0.026, 1.884, 0.036, 0.024),
    (0.210, -0.050, 1.844, 0.028, 0.020),
    (0.208, -0.064, 1.810, 0.015, 0.011),
], HAIR_WARM, sides=16)

# Candidate export only. Approved gameplay remains V6.8 until visual acceptance.
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
print(f'Exported Lembah Sari Character V7.2 clean-chin organic-fringe candidate to {OUT_PATH}')
