import bpy
import math
import os
from mathutils import Vector

# Lembah Sari Character V5.0 — organic-mesh rebuild.
# Candidate only. Gameplay remains on the approved V3.2 asset.
# V5 changes the modeling method for the weak areas: a tapered head mesh,
# fused hair mass and fused hands instead of visible primitive/piece assembly.

BASE = os.path.join(os.path.dirname(__file__), "build_player_character_v41.py")
exec(compile(open(BASE, "r", encoding="utf-8").read(), BASE, "exec"), globals(), globals())


def remove_many(names):
    for name in names:
        obj = bpy.data.objects.get(name)
        if obj:
            bpy.data.objects.remove(obj, do_unlink=True)


def set_smooth(obj):
    if obj and getattr(obj, "data", None) and hasattr(obj.data, "polygons"):
        for p in obj.data.polygons:
            p.use_smooth = True


def tapered_head(name, mat):
    # Hand-authored head topology: small chin -> fuller cheeks -> narrower crown.
    # Front is -Y. A slight forward shift through the cheek/mid-face prevents
    # the old feature-stuck-to-an-egg silhouette.
    rings = [
        # z, rx, ry, center_y
        (1.515, 0.060, 0.062, -0.004),
        (1.545, 0.112, 0.095, -0.010),
        (1.590, 0.153, 0.125, -0.014),
        (1.645, 0.181, 0.145, -0.016),
        (1.705, 0.194, 0.157, -0.014),
        (1.770, 0.194, 0.163, -0.008),
        (1.830, 0.184, 0.159,  0.000),
        (1.885, 0.164, 0.148,  0.010),
        (1.930, 0.128, 0.126,  0.017),
        (1.960, 0.070, 0.078,  0.020),
    ]
    sides = 40
    verts = []
    faces = []
    for z, rx, ry, cy in rings:
        for i in range(sides):
            a = math.tau * i / sides
            # Slightly flatten the face plane while preserving cheek roundness.
            sy = math.sin(a)
            y = cy + ry * sy
            if sy < -0.35:
                y += 0.010 * ((-sy - 0.35) / 0.65)
            verts.append((rx * math.cos(a), y, z))
    for r in range(len(rings)-1):
        a0 = r*sides
        b0 = (r+1)*sides
        for i in range(sides):
            j = (i+1) % sides
            faces.append((a0+i, a0+j, b0+j, b0+i))
    faces.append(tuple(reversed(range(sides))))
    top = (len(rings)-1)*sides
    faces.append(tuple(top+i for i in range(sides)))
    mesh = bpy.data.meshes.new(name+"Mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.parent = ROOT
    obj.data.materials.append(mat)
    set_smooth(obj)
    bevel = obj.modifiers.new("HeadSoftness", "BEVEL")
    bevel.width = 0.008
    bevel.segments = 2
    bpy.context.view_layer.objects.active = obj
    try:
        bpy.ops.object.modifier_apply(modifier=bevel.name)
    except Exception:
        pass
    return obj


def join_and_voxel_fuse(names, new_name, material, voxel=0.012):
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
    if len(obj.data.materials) == 0:
        obj.data.materials.append(material)
    else:
        # Hair/skin is intentionally unified to one material after fusion.
        obj.data.materials.clear()
        obj.data.materials.append(material)
    set_smooth(obj)
    # Voxel remesh makes overlaps read as one sculpted mass. Keep a graceful
    # fallback for older Blender builds so CI never corrupts the candidate.
    try:
        obj.data.remesh_voxel_size = voxel
        obj.data.remesh_voxel_adaptivity = 0.0
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        bpy.ops.object.voxel_remesh()
        set_smooth(obj)
    except Exception as exc:
        print("V5 voxel fuse fallback:", exc)
    bevel = obj.modifiers.new("OrganicEdgeSoftness", "BEVEL")
    bevel.width = voxel * 0.60
    bevel.segments = 2
    bpy.context.view_layer.objects.active = obj
    try:
        bpy.ops.object.modifier_apply(modifier=bevel.name)
    except Exception:
        pass
    return obj


# -----------------------------------------------------------------------------
# FACE — replace the old egg head and rebuild features at concept proportions.
# -----------------------------------------------------------------------------
remove_many([
    "Head", "Nose", "Smile", "Blush_-1", "Blush_1",
    "EyeWhite_-1", "EyeWhite_1", "Iris_-1", "Iris_1",
    "Pupil_-1", "Pupil_1", "EyeGlint_-1", "EyeGlint_1",
    "UpperLidL", "UpperLidR", "BrowL", "BrowR",
])
head = tapered_head("HeadV5", SKIN)

# Warm, smaller almond-leaning eye stack. White stays visible but no doll scale.
for side in (-1, 1):
    s = float(side)
    x = 0.073 * s
    uv(f"EyeWhite_{side}", (x, -0.1575, 1.754), (0.048, 0.0055, 0.033), EYE_WHITE, 28, 16)
    uv(f"Iris_{side}", (x + 0.003*s, -0.1625, 1.752), (0.025, 0.0040, 0.026), IRIS, 24, 14)
    uv(f"Pupil_{side}", (x + 0.004*s, -0.1660, 1.751), (0.010, 0.0028, 0.015), PUPIL, 18, 10)
    uv(f"EyeGlint_{side}", (x - 0.004*s, -0.1685, 1.762), (0.0042, 0.0017, 0.0048), EYE_WHITE, 12, 8)

curve("UpperLidL", [(-0.121,-0.159,1.770),(-0.080,-0.164,1.780),(-0.032,-0.160,1.771)], HAIR, 0.0036)
curve("UpperLidR", [(0.032,-0.160,1.771),(0.080,-0.164,1.780),(0.121,-0.159,1.770)], HAIR, 0.0036)
curve("BrowL", [(-0.126,-0.154,1.815),(-0.083,-0.160,1.827),(-0.039,-0.155,1.820)], HAIR, 0.0048)
curve("BrowR", [(0.039,-0.155,1.820),(0.083,-0.160,1.827),(0.126,-0.154,1.815)], HAIR, 0.0048)
# Tiny nose and shallow smile; concept appeal comes from proportions, not facial clutter.
uv("Nose", (0.0, -0.163, 1.685), (0.0050, 0.0030, 0.0070), SKIN, 14, 8)
curve("Smile", [(-0.036,-0.160,1.626),(-0.018,-0.164,1.619),(0.0,-0.165,1.618),(0.019,-0.164,1.621),(0.038,-0.159,1.628)], MOUTH, 0.0024)
for side in (-1,1):
    uv(f"Blush_{side}", (0.121*side,-0.151,1.660), (0.026,0.0025,0.013), BLUSH, 18, 10)

# -----------------------------------------------------------------------------
# HAIR — keep V4.1 silhouette ingredients, then fuse them into ONE sculpt mass.
# -----------------------------------------------------------------------------
hair_source = [
    "HairMass", "HairBack", "HairTopL", "HairTopC", "HairTopR",
    "FringeHero", "FringeLeft", "FringeRight", "SideLockL", "SideLockR",
]
hair = join_and_voxel_fuse(hair_source, "HairV5Unified", HAIR, voxel=0.010)
if hair:
    # Give the concept a broader side sweep and flatter crown without adding pieces.
    hair.scale.x *= 1.035
    hair.scale.z *= 0.985

# -----------------------------------------------------------------------------
# HANDS — add embedded finger volumes, then fuse palm/thumb/fingers into one mesh.
# -----------------------------------------------------------------------------
for side in (-1, 1):
    s = float(side)
    p = Vector((0.222*s, -0.074, 0.775))
    # Four short pads overlap the lower palm so voxel fusion yields one hand.
    finger_names = []
    offsets = (-0.026, -0.009, 0.009, 0.026)
    lengths = (0.034, 0.041, 0.039, 0.031)
    for idx, (off, ln) in enumerate(zip(offsets, lengths)):
        name = f"V5Finger_{side}_{idx}"
        uv(name, (p.x + off, p.y-0.004, p.z-0.047-ln*0.28), (0.0125, 0.0140, ln), SKIN, 20, 12)
        finger_names.append(name)
    # Existing hand crease curves are decorative and should not enter the fuse.
    hand = join_and_voxel_fuse([f"Palm_{side}", f"Thumb_{side}"] + finger_names,
                               f"HandV5_{side}", SKIN, voxel=0.006)
    if hand:
        hand.scale.x *= 1.03
        hand.scale.z *= 0.98

# -----------------------------------------------------------------------------
# BODY SILHOUETTE — stronger concept stance without changing gameplay scale.
# -----------------------------------------------------------------------------
shirt = bpy.data.objects.get("ShirtTorso")
if shirt:
    shirt.scale.x *= 1.035
    shirt.scale.z *= 0.985
bib = bpy.data.objects.get("OverallBib")
if bib:
    bib.scale.x *= 1.025
hips = bpy.data.objects.get("OverallHips")
if hips:
    hips.scale.x *= 1.055
    hips.scale.y *= 1.025
for side in (-1,1):
    tr = bpy.data.objects.get(f"Trouser_{side}")
    if tr:
        tr.scale.x *= 1.070
        tr.scale.y *= 1.045
        tr.scale.z *= 0.995
    sleeve = bpy.data.objects.get(f"Sleeve_{side}")
    if sleeve:
        sleeve.rotation_euler.y += math.radians(2.5*side)

# Export candidate only. Workflow writes this to assets/review/player_character_candidate.glb.
bpy.ops.object.select_all(action="DESELECT")
ROOT.select_set(True)
for obj in ROOT.children_recursive:
    obj.select_set(True)
bpy.context.view_layer.objects.active = ROOT
bpy.ops.export_scene.gltf(
    filepath=OUT_PATH,
    export_format="GLB",
    use_selection=True,
    export_apply=True,
    export_yup=True,
)
print(f"Exported Lembah Sari Character V5.0 organic candidate to {OUT_PATH}")
