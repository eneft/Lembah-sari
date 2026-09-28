import bpy
import math
import os
from mathutils import Vector

# Lembah Sari — Character Rework V2.6
# Concept-led rebuild: softer face, layered swept hair, tapered torso,
# relaxed arms, loose overalls, stylized mitten hands, chunkier boots,
# and a rounded adventure backpack. Visual asset only until approval.

OUT_PATH = os.path.abspath(os.environ.get("LEMBAH_CHARACTER_OUT", "assets/models/player_character_v2.glb"))
os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)

bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)


def make_mat(name, rgb, roughness=0.96, specular=0.06):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*rgb, 1.0)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (*rgb, 1.0)
        bsdf.inputs["Roughness"].default_value = roughness
        if "Metallic" in bsdf.inputs:
            bsdf.inputs["Metallic"].default_value = 0.0
        if "Specular IOR Level" in bsdf.inputs:
            bsdf.inputs["Specular IOR Level"].default_value = specular
        elif "Specular" in bsdf.inputs:
            bsdf.inputs["Specular"].default_value = specular
    return m


SKIN = make_mat("Skin Peach", (0.78, 0.48, 0.31), 0.91, 0.08)
BLUSH = make_mat("Cheek Blush", (0.72, 0.23, 0.16), 0.95, 0.03)
HAIR = make_mat("Hair Chestnut", (0.042, 0.014, 0.006), 0.97, 0.04)
HAIR_WARM = make_mat("Hair Warm Chestnut", (0.082, 0.028, 0.010), 0.97, 0.04)
SHIRT = make_mat("Shirt Cream", (0.60, 0.52, 0.38), 0.98, 0.03)
SHIRT_SHADOW = make_mat("Shirt Cuff", (0.50, 0.42, 0.29), 0.98, 0.03)
OVERALL = make_mat("Overall Moss", (0.118, 0.142, 0.062), 0.98, 0.03)
OVERALL_DARK = make_mat("Overall Deep Moss", (0.070, 0.086, 0.036), 0.98, 0.03)
OVERALL_CUFF = make_mat("Overall Rolled Cuff", (0.185, 0.185, 0.100), 0.98, 0.03)
SCARF = make_mat("Neckerchief Terracotta", (0.43, 0.115, 0.040), 0.97, 0.04)
BOOT = make_mat("Boot Leather", (0.055, 0.020, 0.009), 0.98, 0.03)
BOOT_EDGE = make_mat("Boot Warm Leather", (0.120, 0.045, 0.016), 0.97, 0.03)
BAG = make_mat("Backpack Leather", (0.115, 0.050, 0.020), 0.98, 0.03)
BAG_EDGE = make_mat("Backpack Edge", (0.205, 0.092, 0.034), 0.98, 0.03)
BRASS = make_mat("Muted Brass", (0.34, 0.19, 0.052), 0.86, 0.14)
EYE_WHITE = make_mat("Eye Ivory", (0.78, 0.71, 0.59), 0.92, 0.08)
IRIS = make_mat("Eye Brown", (0.070, 0.020, 0.007), 0.89, 0.08)
PUPIL = make_mat("Eye Pupil", (0.006, 0.002, 0.001), 0.94, 0.02)
MOUTH = make_mat("Mouth", (0.11, 0.020, 0.014), 0.95, 0.03)
LEAF = make_mat("Leaf Charm", (0.070, 0.175, 0.048), 0.97, 0.03)

ROOT = bpy.data.objects.new("LembahSariCharacterV26", None)
bpy.context.collection.objects.link(ROOT)


def attach(obj, mat=None):
    if mat is not None and hasattr(obj.data, "materials"):
        obj.data.materials.append(mat)
    obj.parent = ROOT
    return obj


def smooth(obj):
    if obj.type == "MESH":
        for p in obj.data.polygons:
            p.use_smooth = True
    return obj


def bevel(obj, width=0.008, segments=2):
    mod = obj.modifiers.new("SoftEdge", "BEVEL")
    mod.width = width
    mod.segments = segments
    mod.limit_method = "ANGLE"
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=mod.name)
    return obj


def uv(name, loc, scale, mat, segments=28, rings=16, rot=(0.0, 0.0, 0.0)):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings, radius=1.0, location=loc, rotation=rot)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return attach(smooth(obj), mat)


def ico(name, loc, scale, mat, subdivisions=2, rot=(0.0, 0.0, 0.0)):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=subdivisions, radius=1.0, location=loc, rotation=rot)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return attach(smooth(obj), mat)


def rounded_box(name, loc, dims, mat, radius=0.025, rot=(0.0, 0.0, 0.0)):
    bpy.ops.mesh.primitive_cube_add(location=loc, rotation=rot)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dims
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if radius:
        bevel(obj, radius, 3)
    return attach(obj, mat)


def tapered(name, p1, p2, r1, r2, mat, vertices=24, edge=0.007):
    a = Vector(p1)
    b = Vector(p2)
    d = b - a
    bpy.ops.mesh.primitive_cone_add(vertices=vertices, radius1=r1, radius2=r2, depth=d.length, location=(a + b) * 0.5)
    obj = bpy.context.object
    obj.name = name
    obj.rotation_mode = "QUATERNION"
    obj.rotation_quaternion = Vector((0.0, 0.0, 1.0)).rotation_difference(d.normalized())
    if edge:
        bevel(obj, edge, 2)
    return attach(smooth(obj), mat)


def cyl(name, loc, radius, depth, mat, rot=(0.0, 0.0, 0.0), vertices=24, edge=0.006):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=loc, rotation=rot)
    obj = bpy.context.object
    obj.name = name
    if edge:
        bevel(obj, edge, 2)
    return attach(smooth(obj), mat)


def profile(name, rings, mat, segments=28):
    verts, faces = [], []
    for z, rx, ry, cx, cy in rings:
        for i in range(segments):
            a = math.tau * i / segments
            verts.append((cx + math.cos(a) * rx, cy + math.sin(a) * ry, z))
    for r in range(len(rings) - 1):
        for i in range(segments):
            n = (i + 1) % segments
            a = r * segments + i
            b = r * segments + n
            c = (r + 1) * segments + n
            d = (r + 1) * segments + i
            faces.append((a, b, c, d))
    faces.append(tuple(reversed(range(segments))))
    top = (len(rings) - 1) * segments
    faces.append(tuple(top + i for i in range(segments)))
    mesh = bpy.data.meshes.new(name + "Mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    return attach(smooth(obj), mat)


def patch(name, outline_xz, y, mat, thickness=0.012, radius=0.006):
    mesh = bpy.data.meshes.new(name + "Mesh")
    mesh.from_pydata([(x, y, z) for x, z in outline_xz], [], [tuple(range(len(outline_xz)))])
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    solid = obj.modifiers.new("Thickness", "SOLIDIFY")
    solid.thickness = thickness
    solid.offset = 0.0
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=solid.name)
    if radius:
        bevel(obj, radius, 2)
    return attach(obj, mat)


def cloth_triangle(name, pts, mat, thickness=0.009):
    mesh = bpy.data.meshes.new(name + "Mesh")
    mesh.from_pydata(pts, [], [(0, 1, 2)])
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    solid = obj.modifiers.new("Thickness", "SOLIDIFY")
    solid.thickness = thickness
    solid.offset = 0.0
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=solid.name)
    bevel(obj, 0.004, 2)
    return attach(obj, mat)


def curve(name, pts, mat, radius=0.006):
    data = bpy.data.curves.new(name, "CURVE")
    data.dimensions = "3D"
    data.resolution_u = 3
    data.bevel_depth = radius
    data.bevel_resolution = 3
    spline = data.splines.new("BEZIER")
    spline.bezier_points.add(len(pts) - 1)
    for bp, co in zip(spline.bezier_points, pts):
        bp.co = co
        bp.handle_left_type = "AUTO"
        bp.handle_right_type = "AUTO"
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    return attach(obj, mat)


def hair_blob(name, loc, scale, rot, warm=False):
    return uv(name, loc, scale, HAIR_WARM if warm else HAIR, 24, 14, rot)


# BOOTS — broader toe and slightly shorter shaft, closer to the concept sheet.
for side in (-1, 1):
    s = float(side)
    x = 0.112 * s
    uv(f"BootToe_{side}", (x, -0.105, 0.120), (0.103, 0.160, 0.080), BOOT_EDGE, 22, 12)
    rounded_box(f"BootSole_{side}", (x, -0.055, 0.050), (0.205, 0.300, 0.055), BOOT, 0.025)
    profile(f"BootShaft_{side}", [
        (0.095, 0.082, 0.075, x, 0.010),
        (0.205, 0.083, 0.076, x, 0.008),
        (0.320, 0.087, 0.079, x, 0.004),
        (0.355, 0.092, 0.082, x, 0.004),
    ], BOOT, 22)
    for i in range(3):
        z = 0.165 + i * 0.042
        curve(f"BootLace_{side}_{i}", [(x - 0.050, -0.165, z), (x, -0.176, z + 0.006), (x + 0.050, -0.165, z)], BOOT, 0.0045)

# LOOSE TROUSERS — fuller thigh, taper to rolled cuffs.
for side in (-1, 1):
    s = float(side)
    x = 0.112 * s
    profile(f"Trouser_{side}", [
        (0.350, 0.100, 0.094, x, 0.004),
        (0.470, 0.106, 0.099, x, 0.003),
        (0.630, 0.118, 0.108, x, 0.002),
        (0.790, 0.126, 0.113, x, 0.001),
        (0.875, 0.120, 0.109, x, 0.000),
    ], OVERALL, 26)
    profile(f"TrouserCuff_{side}", [
        (0.340, 0.110, 0.101, x, 0.004),
        (0.372, 0.119, 0.107, x, 0.004),
        (0.405, 0.109, 0.100, x, 0.004),
    ], OVERALL_CUFF, 24)

profile("OverallHips", [
    (0.800, 0.205, 0.142, 0.0, 0.000),
    (0.875, 0.214, 0.148, 0.0, 0.000),
    (0.945, 0.205, 0.142, 0.0, -0.002),
    (1.000, 0.180, 0.129, 0.0, -0.003),
], OVERALL, 28)

# SHIRT TORSO — tapered at the waist, softer shoulders.
profile("ShirtTorso", [
    (0.950, 0.177, 0.125, 0.0, -0.001),
    (1.050, 0.188, 0.130, 0.0, -0.002),
    (1.165, 0.205, 0.137, 0.0, -0.002),
    (1.275, 0.214, 0.140, 0.0, -0.001),
    (1.345, 0.184, 0.128, 0.0, 0.000),
], SHIRT, 28)

patch("OverallBib", [
    (-0.112, 1.305), (0.112, 1.305), (0.110, 1.215),
    (0.098, 1.100), (0.078, 1.020), (-0.078, 1.020),
    (-0.098, 1.100), (-0.110, 1.215),
], -0.146, OVERALL, 0.014, 0.010)
patch("BibPocket", [
    (-0.064, 1.180), (0.064, 1.180), (0.060, 1.105),
    (0.032, 1.085), (-0.032, 1.085), (-0.060, 1.105),
], -0.161, OVERALL_DARK, 0.010, 0.006)
for side in (-1, 1):
    s = float(side)
    curve(f"OverallStrap_{side}", [(0.125*s, -0.126, 1.337), (0.112*s, -0.151, 1.265), (0.095*s, -0.166, 1.195)], OVERALL, 0.015)
    ico(f"BibButton_{side}", (0.095*s, -0.178, 1.200), (0.014, 0.006, 0.014), BRASS, 2)

# Relaxed arms, following the body instead of reading as separate toy pieces.
for side in (-1, 1):
    s = float(side)
    shoulder = Vector((0.188*s, -0.002, 1.270))
    elbow = Vector((0.252*s, -0.012, 1.075))
    cuff = Vector((0.250*s, -0.018, 1.015))
    wrist = Vector((0.225*s, -0.054, 0.790))
    palm = Vector((0.218*s, -0.065, 0.710))
    tapered(f"Sleeve_{side}", shoulder, elbow, 0.073, 0.064, SHIRT, 24, 0.007)
    tapered(f"RolledSleeve_{side}", elbow, cuff, 0.069, 0.066, SHIRT_SHADOW, 24, 0.006)
    tapered(f"Forearm_{side}", cuff, wrist, 0.049, 0.041, SKIN, 22, 0.006)
    uv(f"Palm_{side}", tuple(palm), (0.043, 0.034, 0.068), SKIN, 20, 12, rot=(0.0, math.radians(7*s), math.radians(-2*s)))
    uv(f"Thumb_{side}", (palm.x + 0.029*s, palm.y - 0.008, palm.z + 0.005), (0.017, 0.015, 0.030), SKIN, 16, 10, rot=(0.0, math.radians(15*s), math.radians(18*s)))

# Scarf.
cyl("Neck", (0.0, 0.0, 1.385), 0.061, 0.100, SKIN, vertices=22)
profile("ScarfWrap", [
    (1.340, 0.095, 0.081, 0.0, -0.004),
    (1.368, 0.105, 0.089, 0.0, -0.004),
    (1.397, 0.095, 0.081, 0.0, -0.002),
], SCARF, 24)
ico("ScarfKnot", (0.0, -0.103, 1.343), (0.043, 0.031, 0.038), SCARF, 2)
cloth_triangle("ScarfTailL", [(-0.010, -0.118, 1.332), (-0.070, -0.120, 1.220), (0.003, -0.120, 1.252)], SCARF)
cloth_triangle("ScarfTailR", [(0.010, -0.118, 1.332), (0.073, -0.120, 1.245), (0.006, -0.120, 1.215)], SCARF)

# HEAD — slightly wider upper skull, softer lower face.
profile("Head", [
    (1.410, 0.070, 0.086, 0.0, -0.006),
    (1.438, 0.118, 0.123, 0.0, -0.006),
    (1.492, 0.165, 0.151, 0.0, -0.004),
    (1.558, 0.187, 0.164, 0.0, -0.001),
    (1.628, 0.190, 0.166, 0.0, 0.002),
    (1.692, 0.171, 0.157, 0.0, 0.004),
    (1.733, 0.126, 0.133, 0.0, 0.004),
    (1.752, 0.071, 0.091, 0.0, 0.003),
], SKIN, 32)

for side in (-1, 1):
    s = float(side)
    uv(f"Ear_{side}", (0.184*s, 0.000, 1.565), (0.034, 0.023, 0.050), SKIN, 18, 10)
    uv(f"Blush_{side}", (0.104*s, -0.161, 1.510), (0.022, 0.0020, 0.010), BLUSH, 14, 8)
    x = 0.068*s
    uv(f"EyeWhite_{side}", (x, -0.166, 1.590), (0.044, 0.0042, 0.052), EYE_WHITE, 20, 12)
    uv(f"Iris_{side}", (x, -0.170, 1.588), (0.038, 0.0036, 0.047), IRIS, 18, 12)
    uv(f"Pupil_{side}", (x, -0.173, 1.586), (0.020, 0.0026, 0.029), PUPIL, 16, 10)
    uv(f"EyeGlint_{side}", (x - 0.010*s, -0.176, 1.610), (0.006, 0.0015, 0.008), EYE_WHITE, 10, 6)
curve("UpperLidL", [(-0.108, -0.168, 1.615), (-0.067, -0.174, 1.629), (-0.027, -0.168, 1.614)], HAIR, 0.0045)
curve("UpperLidR", [(0.027, -0.168, 1.614), (0.067, -0.174, 1.629), (0.108, -0.168, 1.615)], HAIR, 0.0045)
curve("BrowL", [(-0.112, -0.160, 1.660), (-0.071, -0.167, 1.672), (-0.034, -0.160, 1.665)], HAIR, 0.006)
curve("BrowR", [(0.034, -0.160, 1.665), (0.071, -0.167, 1.672), (0.112, -0.160, 1.660)], HAIR, 0.006)
ico("Nose", (0.0, -0.166, 1.540), (0.014, 0.006, 0.014), SKIN, 2)
curve("Smile", [(-0.040, -0.164, 1.490), (0.0, -0.171, 1.477), (0.044, -0.164, 1.491)], MOUTH, 0.0042)

# HAIR — broad back mass + overlapping swept blobs, no upright spikes.
hair_blob("HairBack", (0.0, 0.030, 1.690), (0.198, 0.168, 0.158), (0.0, 0.0, 0.0))
hair_blob("HairTopL", (-0.070, -0.002, 1.770), (0.115, 0.080, 0.068), (math.radians(-12), math.radians(-14), math.radians(-24)), True)
hair_blob("HairTopC", (0.012, -0.010, 1.792), (0.112, 0.076, 0.064), (math.radians(-8), math.radians(10), math.radians(18)))
hair_blob("HairTopR", (0.088, 0.000, 1.755), (0.100, 0.073, 0.061), (math.radians(-4), math.radians(18), math.radians(32)), True)

# Front swept fringe — layered oval locks that overlap like the concept.
hair_blob("FringeOuterL", (-0.142, -0.105, 1.678), (0.060, 0.042, 0.116), (math.radians(17), math.radians(-8), math.radians(-22)))
hair_blob("FringeHeavyL", (-0.090, -0.126, 1.700), (0.067, 0.044, 0.132), (math.radians(14), math.radians(-4), math.radians(-15)), True)
hair_blob("FringeCenter", (-0.025, -0.139, 1.700), (0.062, 0.041, 0.125), (math.radians(12), math.radians(4), math.radians(7)))
hair_blob("FringeRight", (0.060, -0.127, 1.705), (0.055, 0.039, 0.102), (math.radians(12), math.radians(8), math.radians(24)), True)
hair_blob("SideLockL", (-0.175, -0.035, 1.635), (0.047, 0.041, 0.088), (math.radians(5), 0.0, math.radians(-8)))
hair_blob("SideLockR", (0.173, -0.026, 1.648), (0.043, 0.039, 0.078), (math.radians(3), 0.0, math.radians(12)))

# A few small side/back layers keep the silhouette lively without spikes.
hair_blob("BackLayerL", (-0.146, 0.075, 1.700), (0.070, 0.052, 0.080), (math.radians(-12), math.radians(-14), math.radians(-18)))
hair_blob("BackLayerR", (0.142, 0.080, 1.696), (0.066, 0.050, 0.075), (math.radians(-10), math.radians(12), math.radians(20)), True)

# BACKPACK — rounder body with broad flap and top bedroll.
rounded_box("Backpack", (0.0, 0.175, 1.095), (0.300, 0.170, 0.420), BAG, 0.072)
rounded_box("BackpackFlap", (0.0, 0.270, 1.195), (0.262, 0.038, 0.145), BAG_EDGE, 0.045)
rounded_box("BackpackPocket", (0.0, 0.274, 0.990), (0.185, 0.034, 0.112), BAG_EDGE, 0.032)
for side in (-1, 1):
    s = float(side)
    curve(f"PackStrap_{side}", [(0.135*s, 0.025, 1.310), (0.165*s, -0.012, 1.110), (0.150*s, -0.038, 0.945)], BAG, 0.014)
    ico(f"PackBuckle_{side}", (0.153*s, -0.045, 0.990), (0.016, 0.006, 0.020), BRASS, 2)
cyl("Bedroll", (0.0, 0.188, 1.355), 0.066, 0.290, BAG_EDGE, rot=(0.0, math.radians(90), 0.0), vertices=24)
cyl("BedrollBandL", (-0.078, 0.188, 1.355), 0.071, 0.020, BAG, rot=(0.0, math.radians(90), 0.0), vertices=22, edge=0.004)
cyl("BedrollBandR", (0.078, 0.188, 1.355), 0.071, 0.020, BAG, rot=(0.0, math.radians(90), 0.0), vertices=22, edge=0.004)
curve("LeafStem", [(0.156, 0.278, 1.025), (0.180, 0.294, 0.968), (0.194, 0.294, 0.915)], LEAF, 0.004)
ico("LeafA", (0.203, 0.294, 0.943), (0.024, 0.006, 0.044), LEAF, 2, rot=(math.radians(8), 0.0, math.radians(-28)))
ico("LeafB", (0.181, 0.294, 0.908), (0.022, 0.006, 0.039), LEAF, 2, rot=(math.radians(-8), 0.0, math.radians(32)))

# Export visual review asset only.
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
print(f"Exported Lembah Sari Character Rework V2.6 to {OUT_PATH}")
