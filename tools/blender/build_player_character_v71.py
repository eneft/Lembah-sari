import bpy
import math
import os
from mathutils import Vector

# Lembah Sari Character V7.1 — soft-face + rounded-hair correction.
# Candidate only. Keeps the V7.0 body/outfit/hands, removes any legacy curve
# debris in the face zone, softens the head surface, and replaces the fused
# blade-like V6.8 fringe with a quieter rounded layered hair mass.

BASE = os.path.join(os.path.dirname(__file__), "build_player_character_v70.py")
exec(compile(open(BASE, "r", encoding="utf-8").read(), BASE, "exec"), globals(), globals())


def remove_obj(name):
    obj = bpy.data.objects.get(name)
    if obj:
        bpy.data.objects.remove(obj, do_unlink=True)


def curve_world_points(obj):
    pts = []
    if obj.type != 'CURVE':
        return pts
    for spline in obj.data.splines:
        if spline.type == 'BEZIER':
            for bp in spline.bezier_points:
                pts.append(obj.matrix_world @ bp.co)
        else:
            for p in spline.points:
                co = Vector((p.co.x, p.co.y, p.co.z))
                pts.append(obj.matrix_world @ co)
    return pts


# -----------------------------------------------------------------------------
# FACE HYGIENE — remove every leftover curve that physically lives around the
# head except the intentional V7 face strokes. This kills old lid/mouth/contour
# debris without touching hand creases, boot laces, straps, or backpack details.
# -----------------------------------------------------------------------------
face_curve_keep = {'UpperLidL', 'UpperLidR', 'BrowL', 'BrowR', 'Smile'}
for obj in list(bpy.data.objects):
    if obj.type != 'CURVE' or obj.name in face_curve_keep:
        continue
    pts = curve_world_points(obj)
    if not pts:
        continue
    min_z = min(p.z for p in pts)
    max_z = max(p.z for p in pts)
    min_y = min(p.y for p in pts)
    max_y = max(p.y for p in pts)
    max_x = max(abs(p.x) for p in pts)
    if min_z > 1.48 and max_z < 2.12 and min_y < 0.14 and max_y < 0.22 and max_x < 0.34:
        print('V7.1 removing legacy face-zone curve:', obj.name)
        bpy.data.objects.remove(obj, do_unlink=True)


# -----------------------------------------------------------------------------
# HEAD — smooth the custom V7.0 topology so cheek/jaw transitions stop reading
# faceted in the close-up acceptance camera.
# -----------------------------------------------------------------------------
head = bpy.data.objects.get('HeadV70')
if head and head.type == 'MESH':
    for poly in head.data.polygons:
        poly.use_smooth = True
    sub = head.modifiers.new('V71FaceSubdivision', 'SUBSURF')
    sub.subdivision_type = 'CATMULL_CLARK'
    sub.levels = 1
    sub.render_levels = 1
    bpy.context.view_layer.objects.active = head
    head.select_set(True)
    try:
        bpy.ops.object.modifier_apply(modifier=sub.name)
    except Exception as exc:
        print('V7.1 face subsurf fallback:', exc)
    relax = head.modifiers.new('V71FaceRelax', 'SMOOTH')
    relax.factor = 0.22
    relax.iterations = 2
    bpy.context.view_layer.objects.active = head
    head.select_set(True)
    try:
        bpy.ops.object.modifier_apply(modifier=relax.name)
    except Exception as exc:
        print('V7.1 face relax fallback:', exc)
    for poly in head.data.polygons:
        poly.use_smooth = True


# -----------------------------------------------------------------------------
# EYES / NOSE / MOUTH — warmer, slightly larger eyes; nose sits almost flush
# with the face rather than reading as a pasted sphere.
# -----------------------------------------------------------------------------
for side in (-1, 1):
    eye = bpy.data.objects.get(f'EyeWhite_{side}')
    iris = bpy.data.objects.get(f'Iris_{side}')
    pupil = bpy.data.objects.get(f'Pupil_{side}')
    glint = bpy.data.objects.get(f'EyeGlint_{side}')
    if eye:
        eye.scale.x *= 1.075
        eye.scale.z *= 1.085
        eye.location.z += 0.002
    if iris:
        iris.scale.x *= 1.075
        iris.scale.z *= 1.080
        iris.location.z += 0.002
    if pupil:
        pupil.scale.x *= 1.055
        pupil.scale.z *= 1.060
        pupil.location.z += 0.002
    if glint:
        glint.scale *= 1.05
        glint.location.z += 0.003

remove_obj('Nose')
uv('Nose', (0.0, -0.1660, 1.689),
   (0.0068, 0.0018, 0.0090), SKIN, 22, 12)

# A softer mouth color prevents the smile from becoming a hard graphic slash.
try:
    recolor(MOUTH, (0.34, 0.075, 0.040))
except Exception:
    pass

# Keep smile geometry but make the curve slightly finer after the close-up pass.
smile = bpy.data.objects.get('Smile')
if smile and smile.type == 'CURVE':
    smile.data.bevel_depth *= 0.84


# -----------------------------------------------------------------------------
# HAIR — replace the long fused blade/slab fringe with large overlapping rounded
# lobes, then voxel-fuse into one sculpted mass. The front stays above the eyes.
# -----------------------------------------------------------------------------
remove_obj('HairV68Unified')

hair_parts = []

def hair_lobe(name, pos, scale, material, rot=(0.0, 0.0, 0.0), seg=36, rings=20):
    uv(name, pos, scale, material, seg, rings, rot=rot)
    hair_parts.append(name)

recolor(HAIR, (0.043, 0.012, 0.0048))
recolor(HAIR_WARM, (0.073, 0.021, 0.0085))

# Quiet continuous cap/back volumes.
hair_lobe('V71HairCap', (0.0, 0.050, 1.895), (0.220, 0.168, 0.160), HAIR, seg=52, rings=30)
hair_lobe('V71HairBack', (0.0, 0.118, 1.835), (0.207, 0.144, 0.130), HAIR, seg=46, rings=26)

# Rounded crown layering — broad low lobes rather than spikes.
hair_lobe('V71TopLeft', (-0.090, 0.010, 2.005), (0.122, 0.074, 0.060), HAIR_WARM,
          rot=(math.radians(-7), math.radians(-7), math.radians(-16)))
hair_lobe('V71TopCenter', (0.005, -0.004, 2.022), (0.115, 0.072, 0.060), HAIR,
          rot=(math.radians(-5), math.radians(7), math.radians(5)))
hair_lobe('V71TopRight', (0.098, 0.006, 1.995), (0.103, 0.069, 0.055), HAIR_WARM,
          rot=(math.radians(-4), math.radians(10), math.radians(17)))

# Short volumetric forehead locks. Their centers stay around z>=1.90 so eyes and
# brows remain open; overlap with the cap hides primitive boundaries after fuse.
hair_lobe('V71FringeLeft', (-0.112, -0.122, 1.936), (0.108, 0.047, 0.052), HAIR,
          rot=(math.radians(-8), math.radians(-7), math.radians(-18)))
hair_lobe('V71FringeHero', (-0.018, -0.142, 1.925), (0.092, 0.044, 0.073), HAIR_WARM,
          rot=(math.radians(-5), math.radians(2), math.radians(-8)))
hair_lobe('V71FringeRight', (0.094, -0.123, 1.940), (0.085, 0.043, 0.050), HAIR,
          rot=(math.radians(-7), math.radians(6), math.radians(17)))

# Compact temples frame the cheeks without covering the eyes.
hair_lobe('V71TempleL', (-0.188, -0.008, 1.838), (0.043, 0.038, 0.088), HAIR,
          rot=(math.radians(5), 0.0, math.radians(-8)), seg=28, rings=16)
hair_lobe('V71TempleR', (0.189, -0.006, 1.842), (0.042, 0.037, 0.085), HAIR_WARM,
          rot=(math.radians(5), 0.0, math.radians(8)), seg=28, rings=16)

hair = join_and_voxel_fuse(hair_parts, 'HairV71Unified', HAIR_WARM, voxel=0.0070)
if hair:
    smooth = hair.modifiers.new('V71HairRelax', 'SMOOTH')
    smooth.factor = 0.30
    smooth.iterations = 2
    bpy.context.view_layer.objects.active = hair
    hair.select_set(True)
    try:
        bpy.ops.object.modifier_apply(modifier=smooth.name)
    except Exception as exc:
        print('V7.1 hair smooth fallback:', exc)
    for poly in hair.data.polygons:
        poly.use_smooth = True


# Candidate export only. V6.8 remains the approved gameplay asset until this
# close-up/full-body/gameplay-scale gate is visually accepted.
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
print(f'Exported Lembah Sari Character V7.1 soft-face candidate to {OUT_PATH}')
