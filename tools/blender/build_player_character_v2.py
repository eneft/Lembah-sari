import bpy
import math
import os
from mathutils import Vector

# Lembah Sari - Character Rework V2.4
# Approved master concept: cozy young village farmer / explorer.
# Visual priorities: ~4-head stylized proportion, slim continuous silhouette,
# cream rolled-sleeve shirt, moss overalls, terracotta scarf, chunky boots,
# compact backpack + bedroll, expressive dark eyes, swept chunky brown hair.

OUT_PATH = os.path.abspath(os.environ.get("LEMBAH_CHARACTER_OUT", "assets/models/player_character_v2.glb"))
os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)

bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)


def make_mat(name, rgb, roughness=0.95, specular=0.08):
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


SKIN = make_mat("Skin Warm Peach", (0.50, 0.29, 0.18), 0.90, 0.10)
BLUSH = make_mat("Subtle Blush", (0.53, 0.19, 0.14), 0.94, 0.04)
HAIR = make_mat("Hair Deep Chestnut", (0.030, 0.011, 0.006), 0.97, 0.05)
HAIR_WARM = make_mat("Hair Warm Plane", (0.062, 0.021, 0.009), 0.97, 0.05)
SHIRT = make_mat("Shirt Warm Cream", (0.55, 0.47, 0.33), 0.98, 0.04)
OVERALL = make_mat("Overall Moss Olive", (0.112, 0.160, 0.060), 0.98, 0.04)
OVERALL_DARK = make_mat("Overall Deep Moss", (0.068, 0.096, 0.034), 0.98, 0.04)
CUFF = make_mat("Rolled Trouser Cuff", (0.180, 0.205, 0.090), 0.98, 0.04)
SCARF = make_mat("Neckerchief Terracotta", (0.405, 0.105, 0.035), 0.97, 0.05)
BOOT = make_mat("Boot Dark Leather", (0.045, 0.016, 0.007), 0.98, 0.04)
BOOT_EDGE = make_mat("Boot Warm Leather", (0.100, 0.035, 0.012), 0.97, 0.04)
BAG = make_mat("Backpack Leather", (0.105, 0.043, 0.016), 0.98, 0.04)
BAG_EDGE = make_mat("Backpack Warm Edge", (0.195, 0.085, 0.030), 0.97, 0.04)
BRASS = make_mat("Muted Brass", (0.31, 0.17, 0.045), 0.84, 0.18)
EYE_WHITE = make_mat("Eye Warm White", (0.67, 0.62, 0.52), 0.91, 0.10)
IRIS = make_mat("Eye Deep Brown", (0.052, 0.014, 0.006), 0.88, 0.12)
PUPIL = make_mat("Eye Pupil", (0.005, 0.002, 0.001), 0.93, 0.04)
MOUTH = make_mat("Mouth Brown", (0.095, 0.018, 0.012), 0.95, 0.04)
LEAF = make_mat("Leaf Charm", (0.065, 0.175, 0.045), 0.97, 0.04)

ROOT = bpy.data.objects.new("LembahSariCharacterV2", None)
bpy.context.collection.objects.link(ROOT)


def attach(obj, mat=None):
    if mat is not None and hasattr(obj.data, "materials"):
        obj.data.materials.append(mat)
    obj.parent = ROOT
    return obj


def smooth(obj):
    if obj.type == "MESH":
        for poly in obj.data.polygons:
            poly.use_smooth = True
    return obj


def bevel(obj, width=0.008, segments=2):
    mod = obj.modifiers.new("SoftEdge", "BEVEL")
    mod.width = width
    mod.segments = segments
    mod.limit_method = "ANGLE"
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=mod.name)
    return obj


def rounded_box(name, loc, dims, mat, radius=0.018, rot=(0.0, 0.0, 0.0)):
    bpy.ops.mesh.primitive_cube_add(location=loc, rotation=rot)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dims
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if radius:
        bevel(obj, radius, 3)
    return attach(obj, mat)


def ico(name, loc, scale, mat, subdivisions=2, rot=(0.0, 0.0, 0.0)):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=subdivisions, radius=1.0, location=loc, rotation=rot)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return attach(smooth(obj), mat)


def uv(name, loc, scale, mat, segments=24, rings=14, rot=(0.0, 0.0, 0.0)):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings, radius=1.0, location=loc, rotation=rot)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return attach(smooth(obj), mat)


def cyl(name, loc, radius, depth, mat, rot=(0.0, 0.0, 0.0), vertices=18, edge=0.007):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=loc, rotation=rot)
    obj = bpy.context.object
    obj.name = name
    if edge:
        bevel(obj, edge, 2)
    return attach(smooth(obj), mat)


def profile(name, rings, mat, segments=24):
    # ring tuple: z, radius_x, radius_y, center_x, center_y
    verts = []
    faces = []
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


def tapered(name, p1, p2, r1, r2, mat, vertices=18, edge=0.007):
    a = Vector(p1)
    b = Vector(p2)
    delta = b - a
    bpy.ops.mesh.primitive_cone_add(vertices=vertices, radius1=r1, radius2=r2, depth=delta.length, location=(a + b) * 0.5)
    obj = bpy.context.object
    obj.name = name
    obj.rotation_mode = "QUATERNION"
    obj.rotation_quaternion = Vector((0.0, 0.0, 1.0)).rotation_difference(delta.normalized())
    if edge:
        bevel(obj, edge, 2)
    return attach(smooth(obj), mat)


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


def cloth(name, pts, mat, thickness=0.009):
    mesh = bpy.data.meshes.new(name + "Mesh")
    mesh.from_pydata(pts, [], [(0, 1, 2)])
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    solid = obj.modifiers.new("ClothThickness", "SOLIDIFY")
    solid.thickness = thickness
    solid.offset = 0.0
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=solid.name)
    bevel(obj, 0.004, 2)
    return attach(obj, mat)


def lock(name, sections, tip, width, depth, mat):
    verts = []
    faces = []
    for idx, center in enumerate(sections):
        factor = 1.0 - idx * 0.16
        w = width * factor
        d = depth * factor
        cx, cy, cz = center
        verts.extend([
            (cx - w * 0.5, cy - d * 0.5, cz),
            (cx + w * 0.5, cy - d * 0.5, cz),
            (cx + w * 0.5, cy + d * 0.5, cz),
            (cx - w * 0.5, cy + d * 0.5, cz),
        ])
    for sec in range(len(sections) - 1):
        a = sec * 4
        b = (sec + 1) * 4
        faces.extend([
            (a, b, b + 1, a + 1),
            (a + 1, b + 1, b + 2, a + 2),
            (a + 2, b + 2, b + 3, a + 3),
            (a + 3, b + 3, b, a),
        ])
    last = (len(sections) - 1) * 4
    ti = len(verts)
    verts.append(tip)
    faces.extend([
        (last, ti, last + 1),
        (last + 1, ti, last + 2),
        (last + 2, ti, last + 3),
        (last + 3, ti, last),
    ])
    mesh = bpy.data.meshes.new(name + "Mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    bevel(obj, 0.008, 2)
    return attach(smooth(obj), mat)


# ----------------------------------------------------------------------------
# LOWER BODY - longer, narrower legs and hips than V2.3
# ----------------------------------------------------------------------------
for side in (-1, 1):
    x = 0.112 * side
    uv(f"BootSole_{side}", (x, -0.060, 0.048), (0.095, 0.162, 0.030), BOOT, 20, 12)
    uv(f"BootToe_{side}", (x, -0.095, 0.115), (0.093, 0.150, 0.072), BOOT_EDGE, 22, 12)
    profile(f"BootShaft_{side}", [
        (0.100, 0.077, 0.070, x, 0.005),
        (0.205, 0.081, 0.074, x, 0.005),
        (0.310, 0.086, 0.078, x, 0.003),
        (0.355, 0.091, 0.082, x, 0.003),
    ], BOOT, 20)
    profile(f"BootTop_{side}", [
        (0.337, 0.092, 0.082, x, 0.003),
        (0.365, 0.100, 0.088, x, 0.003),
        (0.392, 0.093, 0.082, x, 0.003),
    ], BOOT_EDGE, 20)
    for i in range(3):
        z = 0.170 + i * 0.040
        curve(f"BootLace_{side}_{i}", [(x - 0.050, -0.160, z), (x, -0.170, z + 0.006), (x + 0.050, -0.160, z)], BOOT, 0.0045)

for side in (-1, 1):
    x = 0.112 * side
    profile(f"Trouser_{side}", [
        (0.360, 0.096, 0.088, x, 0.004),
        (0.485, 0.102, 0.093, x, 0.003),
        (0.655, 0.108, 0.099, x, 0.001),
        (0.825, 0.114, 0.104, x, 0.000),
    ], OVERALL, 22)
    profile(f"TrouserCuff_{side}", [
        (0.345, 0.108, 0.098, x, 0.003),
        (0.373, 0.115, 0.103, x, 0.003),
        (0.402, 0.108, 0.097, x, 0.003),
    ], CUFF, 22)

profile("OverallHips", [
    (0.745, 0.184, 0.128, 0.0, 0.000),
    (0.815, 0.202, 0.138, 0.0, 0.000),
    (0.885, 0.204, 0.139, 0.0, 0.000),
    (0.945, 0.190, 0.132, 0.0, -0.002),
    (0.985, 0.173, 0.124, 0.0, -0.002),
], OVERALL, 24)

# ----------------------------------------------------------------------------
# TORSO / OVERALL BIB
# ----------------------------------------------------------------------------
profile("ShirtTorso", [
    (0.925, 0.183, 0.126, 0.0, -0.001),
    (1.030, 0.202, 0.135, 0.0, -0.002),
    (1.155, 0.222, 0.142, 0.0, -0.002),
    (1.275, 0.232, 0.145, 0.0, -0.001),
    (1.350, 0.198, 0.132, 0.0, 0.000),
], SHIRT, 24)

rounded_box("OverallBib", (0.0, -0.148, 1.145), (0.218, 0.024, 0.282), OVERALL, radius=0.038)
rounded_box("BibPocket", (0.0, -0.166, 1.132), (0.122, 0.016, 0.090), OVERALL_DARK, radius=0.022)
for side in (-1, 1):
    sx = 0.092 * side
    curve(f"OverallStrap_{side}", [
        (0.127 * side, -0.125, 1.342),
        (0.110 * side, -0.151, 1.260),
        (sx, -0.168, 1.174),
    ], OVERALL, 0.016)
    ico(f"BibButton_{side}", (sx, -0.183, 1.183), (0.016, 0.007, 0.016), BRASS, 2)

rounded_box("CargoPocket", (-0.207, -0.004, 0.655), (0.030, 0.104, 0.122), OVERALL_DARK, radius=0.016)

# ----------------------------------------------------------------------------
# ARMS - no spherical shoulder pads; sleeves grow naturally out of torso
# ----------------------------------------------------------------------------
for side in (-1, 1):
    s = float(side)
    shoulder = (0.205 * s, -0.002, 1.270)
    sleeve_mid = (0.247 * s, -0.010, 1.145)
    elbow = (0.266 * s, -0.018, 1.020)
    wrist = (0.287 * s, -0.040, 0.790)
    # Small cap only to blend seam, not a puffball.
    ico(f"SleeveBlend_{side}", shoulder, (0.078, 0.078, 0.090), SHIRT, 2)
    tapered(f"Sleeve_{side}", sleeve_mid, elbow, 0.082, 0.073, SHIRT, 20, 0.008)
    ico(f"SleeveRoll_{side}", elbow, (0.080, 0.070, 0.038), SHIRT, 2)
    tapered(f"Forearm_{side}", elbow, wrist, 0.055, 0.047, SKIN, 20, 0.006)
    uv(f"Hand_{side}", (0.289 * s, -0.046, 0.735), (0.050, 0.045, 0.074), SKIN, 18, 10)
    ico(f"Thumb_{side}", (0.319 * s, -0.061, 0.744), (0.019, 0.020, 0.032), SKIN, 2)

# ----------------------------------------------------------------------------
# NECK / SCARF
# ----------------------------------------------------------------------------
cyl("Neck", (0.0, 0.0, 1.382), 0.066, 0.100, SKIN, vertices=20, edge=0.006)
profile("ScarfWrap", [
    (1.342, 0.096, 0.082, 0.0, -0.004),
    (1.369, 0.104, 0.089, 0.0, -0.004),
    (1.395, 0.096, 0.082, 0.0, -0.002),
], SCARF, 22)
ico("ScarfKnot", (0.0, -0.103, 1.346), (0.044, 0.033, 0.039), SCARF, 2)
cloth("ScarfTailL", [(-0.010, -0.120, 1.335), (-0.069, -0.122, 1.225), (0.004, -0.122, 1.255)], SCARF)
cloth("ScarfTailR", [(0.010, -0.121, 1.335), (0.073, -0.123, 1.248), (0.006, -0.123, 1.220)], SCARF)

# ----------------------------------------------------------------------------
# HEAD - oval/jaw silhouette, less toy-like than V2.3
# ----------------------------------------------------------------------------
profile("Head", [
    (1.405, 0.078, 0.092, 0.0, -0.008),
    (1.435, 0.128, 0.132, 0.0, -0.006),
    (1.500, 0.174, 0.159, 0.0, -0.003),
    (1.575, 0.187, 0.164, 0.0, -0.001),
    (1.645, 0.180, 0.160, 0.0, 0.001),
    (1.705, 0.150, 0.145, 0.0, 0.002),
    (1.735, 0.090, 0.108, 0.0, 0.002),
], SKIN, 30)

for side in (-1, 1):
    s = float(side)
    uv(f"Ear_{side}", (0.181 * s, 0.000, 1.565), (0.034, 0.024, 0.050), SKIN, 16, 10)
    # very small, flush blush mark
    uv(f"Blush_{side}", (0.100 * s, -0.162, 1.505), (0.021, 0.0025, 0.010), BLUSH, 12, 8)
    x = 0.068 * s
    uv(f"EyeWhite_{side}", (x, -0.165, 1.585), (0.043, 0.005, 0.052), EYE_WHITE, 18, 12)
    # Iris occupies most of the eye, matching the concept's warm expressive read.
    uv(f"Iris_{side}", (x, -0.170, 1.582), (0.034, 0.004, 0.044), IRIS, 16, 10)
    uv(f"Pupil_{side}", (x, -0.173, 1.580), (0.018, 0.003, 0.027), PUPIL, 14, 8)
    uv(f"EyeGlint_{side}", (x - 0.009 * s, -0.176, 1.603), (0.006, 0.0018, 0.008), EYE_WHITE, 10, 6)

curve("LidL", [(-0.107, -0.169, 1.608), (-0.068, -0.176, 1.620), (-0.031, -0.169, 1.608)], HAIR, 0.0045)
curve("LidR", [(0.031, -0.169, 1.608), (0.068, -0.176, 1.620), (0.107, -0.169, 1.608)], HAIR, 0.0045)
curve("BrowL", [(-0.110, -0.161, 1.656), (-0.070, -0.168, 1.668), (-0.035, -0.161, 1.660)], HAIR, 0.006)
curve("BrowR", [(0.035, -0.161, 1.660), (0.070, -0.168, 1.668), (0.110, -0.161, 1.656)], HAIR, 0.006)
ico("Nose", (0.0, -0.166, 1.534), (0.016, 0.008, 0.016), SKIN, 2)
curve("Smile", [(-0.038, -0.164, 1.485), (0.0, -0.171, 1.474), (0.042, -0.164, 1.487)], MOUTH, 0.0045)

# ----------------------------------------------------------------------------
# HAIR - asymmetrical swept fringe and crown
# ----------------------------------------------------------------------------
ico("HairBack", (0.0, 0.014, 1.690), (0.198, 0.168, 0.151), HAIR, 3)
ico("HairTopMass", (-0.012, 0.000, 1.746), (0.176, 0.140, 0.096), HAIR, 2)

# The concept is swept and uneven: left side carries more mass, right forehead opens.
lock("BangOuterL", [(-0.160, -0.040, 1.753), (-0.170, -0.095, 1.712), (-0.168, -0.140, 1.670)], (-0.160, -0.176, 1.590), 0.070, 0.056, HAIR)
lock("BangHeavyL", [(-0.112, -0.060, 1.785), (-0.126, -0.112, 1.742), (-0.122, -0.151, 1.694)], (-0.112, -0.184, 1.548), 0.086, 0.062, HAIR_WARM)
lock("BangCenterL", [(-0.050, -0.069, 1.795), (-0.058, -0.120, 1.752), (-0.052, -0.158, 1.706)], (-0.043, -0.186, 1.600), 0.090, 0.064, HAIR)
lock("BangCenterR", [(0.020, -0.067, 1.790), (0.032, -0.116, 1.748), (0.042, -0.153, 1.708)], (0.055, -0.181, 1.626), 0.082, 0.060, HAIR_WARM)
lock("BangRight", [(0.092, -0.050, 1.770), (0.108, -0.096, 1.734), (0.121, -0.132, 1.696)], (0.142, -0.170, 1.625), 0.070, 0.055, HAIR)
lock("TempleL", [(-0.180, -0.005, 1.715), (-0.193, -0.043, 1.674), (-0.198, -0.072, 1.630)], (-0.201, -0.098, 1.555), 0.056, 0.052, HAIR)
lock("TempleR", [(0.178, -0.004, 1.705), (0.190, -0.038, 1.668), (0.195, -0.066, 1.630)], (0.198, -0.092, 1.570), 0.052, 0.049, HAIR)

# Swept crown, not vertical spikes.
lock("CrownLeft", [(-0.105, 0.010, 1.790), (-0.132, 0.000, 1.817), (-0.155, -0.007, 1.837)], (-0.180, -0.014, 1.850), 0.065, 0.055, HAIR_WARM)
lock("CrownCenter", [(-0.028, -0.002, 1.804), (-0.018, -0.008, 1.844), (-0.002, -0.013, 1.875)], (0.020, -0.018, 1.895), 0.068, 0.056, HAIR)
lock("CrownRight", [(0.050, 0.004, 1.792), (0.078, -0.002, 1.819), (0.104, -0.007, 1.839)], (0.135, -0.012, 1.850), 0.062, 0.052, HAIR_WARM)
lock("BackSweep", [(0.125, 0.030, 1.760), (0.153, 0.024, 1.775), (0.178, 0.016, 1.780)], (0.202, 0.006, 1.767), 0.054, 0.050, HAIR)

# ----------------------------------------------------------------------------
# BACKPACK - compact and subordinate
# ----------------------------------------------------------------------------
rounded_box("Backpack", (0.0, 0.166, 1.095), (0.286, 0.152, 0.405), BAG, radius=0.060)
rounded_box("BackpackFlap", (0.0, 0.249, 1.198), (0.254, 0.032, 0.132), BAG_EDGE, radius=0.038)
rounded_box("BackpackPocket", (0.0, 0.253, 0.985), (0.182, 0.032, 0.108), BAG_EDGE, radius=0.028)
for side in (-1, 1):
    s = float(side)
    curve(f"PackStrap_{side}", [(0.136 * s, 0.024, 1.305), (0.168 * s, -0.018, 1.110), (0.152 * s, -0.043, 0.940)], BAG, 0.015)
    ico(f"PackBuckle_{side}", (0.157 * s, -0.050, 0.990), (0.017, 0.007, 0.022), BRASS, 2)

cyl("Bedroll", (0.0, 0.175, 1.350), 0.066, 0.284, BAG_EDGE, rot=(0.0, math.radians(90.0), 0.0), vertices=20, edge=0.007)
cyl("BedrollBandL", (-0.075, 0.175, 1.350), 0.071, 0.020, BAG, rot=(0.0, math.radians(90.0), 0.0), vertices=20, edge=0.004)
cyl("BedrollBandR", (0.075, 0.175, 1.350), 0.071, 0.020, BAG, rot=(0.0, math.radians(90.0), 0.0), vertices=20, edge=0.004)
curve("LeafStem", [(0.154, 0.256, 1.015), (0.184, 0.276, 0.955), (0.199, 0.276, 0.900)], LEAF, 0.0045)
ico("LeafA", (0.208, 0.276, 0.930), (0.024, 0.006, 0.045), LEAF, 2, rot=(math.radians(8), 0.0, math.radians(-28)))
ico("LeafB", (0.183, 0.276, 0.895), (0.022, 0.006, 0.040), LEAF, 2, rot=(math.radians(-8), 0.0, math.radians(32)))

# Export visual asset only; gameplay integration remains gated by visual approval.
bpy.ops.object.select_all(action="DESELECT")
ROOT.select_set(True)
for obj in ROOT.children_recursive:
    obj.select_set(True)
bpy.context.view_layer.objects.active = ROOT
bpy.ops.export_scene.gltf(filepath=OUT_PATH, export_format="GLB", use_selection=True, export_apply=True, export_yup=True)
print(f"Exported Lembah Sari Character Rework V2.4 to {OUT_PATH}")
