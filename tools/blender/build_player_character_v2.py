import bpy
import math
import os
from mathutils import Vector

# Lembah Sari — Character Rework V2.5
# Master reference: approved cozy village farmer/explorer concept sheet.
# This pass removes the rigid prototype read with a relaxed A-pose, continuous
# clothing silhouettes, curved bib/pockets, smaller shoulders, organic hands,
# and swept tapered hair locks.

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
BLUSH = make_mat("Subtle Blush", (0.54, 0.18, 0.13), 0.94, 0.04)
HAIR = make_mat("Hair Deep Chestnut", (0.030, 0.011, 0.006), 0.97, 0.05)
HAIR_WARM = make_mat("Hair Warm Plane", (0.066, 0.023, 0.010), 0.97, 0.05)
SHIRT = make_mat("Shirt Warm Cream", (0.55, 0.47, 0.33), 0.98, 0.04)
OVERALL = make_mat("Overall Moss Olive", (0.112, 0.160, 0.060), 0.98, 0.04)
OVERALL_DARK = make_mat("Overall Deep Moss", (0.067, 0.095, 0.034), 0.98, 0.04)
OVERALL_LIGHT = make_mat("Overall Worn Edge", (0.162, 0.195, 0.080), 0.98, 0.04)
SCARF = make_mat("Neckerchief Terracotta", (0.405, 0.105, 0.035), 0.97, 0.05)
BOOT = make_mat("Boot Dark Leather", (0.045, 0.016, 0.007), 0.98, 0.04)
BOOT_EDGE = make_mat("Boot Warm Leather", (0.105, 0.037, 0.013), 0.97, 0.04)
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


def patch(name, outline_xz, y, mat, thickness=0.012, radius=0.008):
    # Front-facing cloth patch. The polygon silhouette is intentionally tailored
    # rather than rectangular, so the bib/pocket follows the body shape.
    verts = [(x, y, z) for x, z in outline_xz]
    mesh = bpy.data.meshes.new(name + "Mesh")
    mesh.from_pydata(verts, [], [tuple(range(len(verts)))])
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    solid = obj.modifiers.new("ClothThickness", "SOLIDIFY")
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
    solid = obj.modifiers.new("ClothThickness", "SOLIDIFY")
    solid.thickness = thickness
    solid.offset = 0.0
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=solid.name)
    bevel(obj, 0.004, 2)
    return attach(obj, mat)


def path_lock(name, centers, radii, tip, mat, ring_segments=8):
    # Rounded tapered hair lock following an arbitrary 3D path. Each ring is
    # oriented perpendicular to its local tangent, avoiding the blocky card look.
    verts = []
    faces = []
    points = [Vector(p) for p in centers]
    tip_v = Vector(tip)
    for i, center in enumerate(points):
        if i == 0:
            tangent = points[1] - center
        elif i == len(points) - 1:
            tangent = tip_v - points[i - 1]
        else:
            tangent = points[i + 1] - points[i - 1]
        tangent.normalize()
        ref = Vector((0.0, 1.0, 0.0))
        if abs(tangent.dot(ref)) > 0.88:
            ref = Vector((1.0, 0.0, 0.0))
        axis1 = tangent.cross(ref).normalized()
        axis2 = tangent.cross(axis1).normalized()
        rx, ry = radii[i]
        for j in range(ring_segments):
            a = math.tau * j / ring_segments
            offset = axis1 * (math.cos(a) * rx) + axis2 * (math.sin(a) * ry)
            verts.append(tuple(center + offset))
    for ring in range(len(points) - 1):
        a0 = ring * ring_segments
        a1 = (ring + 1) * ring_segments
        for j in range(ring_segments):
            n = (j + 1) % ring_segments
            faces.append((a0 + j, a1 + j, a1 + n, a0 + n))
    last = (len(points) - 1) * ring_segments
    tip_idx = len(verts)
    verts.append(tuple(tip_v))
    for j in range(ring_segments):
        n = (j + 1) % ring_segments
        faces.append((last + j, tip_idx, last + n))
    mesh = bpy.data.meshes.new(name + "Mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    return attach(smooth(obj), mat)


# -----------------------------------------------------------------------------
# BOOTS — sturdy but rounded, with a narrower shaft than previous passes.
# -----------------------------------------------------------------------------
for side in (-1, 1):
    s = float(side)
    x = 0.108 * s
    uv(f"BootSole_{side}", (x, -0.060, 0.047), (0.092, 0.160, 0.029), BOOT, 20, 12)
    uv(f"BootToe_{side}", (x, -0.098, 0.112), (0.090, 0.148, 0.070), BOOT_EDGE, 22, 12)
    profile(f"BootShaft_{side}", [
        (0.102, 0.074, 0.068, x, 0.005),
        (0.205, 0.078, 0.071, x, 0.005),
        (0.305, 0.083, 0.075, x, 0.003),
        (0.350, 0.088, 0.079, x, 0.003),
    ], BOOT, 20)
    profile(f"BootTop_{side}", [
        (0.334, 0.090, 0.080, x, 0.003),
        (0.362, 0.098, 0.086, x, 0.003),
        (0.390, 0.091, 0.080, x, 0.003),
    ], BOOT_EDGE, 20)
    for i in range(3):
        z = 0.165 + i * 0.039
        curve(f"BootLace_{side}_{i}", [(x - 0.048, -0.159, z), (x, -0.169, z + 0.005), (x + 0.048, -0.159, z)], BOOT, 0.0043)


# -----------------------------------------------------------------------------
# TROUSERS / HIPS — long loose legs, visible rolled cuffs, tapered waist.
# -----------------------------------------------------------------------------
for side in (-1, 1):
    s = float(side)
    x = 0.108 * s
    profile(f"Trouser_{side}", [
        (0.355, 0.092, 0.086, x, 0.004),
        (0.480, 0.099, 0.091, x, 0.003),
        (0.650, 0.106, 0.097, x, 0.001),
        (0.825, 0.113, 0.103, x, 0.000),
    ], OVERALL, 22)
    profile(f"TrouserCuff_{side}", [
        (0.343, 0.103, 0.095, x, 0.003),
        (0.370, 0.111, 0.101, x, 0.003),
        (0.398, 0.104, 0.095, x, 0.003),
    ], OVERALL_LIGHT, 22)

profile("OverallHips", [
    (0.748, 0.178, 0.125, 0.0, 0.000),
    (0.815, 0.197, 0.135, 0.0, 0.000),
    (0.882, 0.201, 0.138, 0.0, 0.000),
    (0.942, 0.188, 0.131, 0.0, -0.002),
    (0.990, 0.169, 0.121, 0.0, -0.002),
], OVERALL, 24)


# -----------------------------------------------------------------------------
# TORSO / BIB — continuous cream torso with a tailored cloth bib.
# -----------------------------------------------------------------------------
profile("ShirtTorso", [
    (0.925, 0.178, 0.123, 0.0, -0.001),
    (1.030, 0.196, 0.131, 0.0, -0.002),
    (1.150, 0.215, 0.138, 0.0, -0.002),
    (1.255, 0.223, 0.140, 0.0, -0.001),
    (1.335, 0.194, 0.130, 0.0, 0.000),
], SHIRT, 24)

patch("OverallBib", [
    (-0.108, 1.300),
    (0.108, 1.300),
    (0.104, 1.145),
    (0.084, 1.010),
    (-0.084, 1.010),
    (-0.104, 1.145),
], -0.145, OVERALL, thickness=0.014, radius=0.010)

patch("BibPocket", [
    (-0.060, 1.170),
    (0.060, 1.170),
    (0.056, 1.090),
    (0.000, 1.072),
    (-0.056, 1.090),
], -0.160, OVERALL_DARK, thickness=0.010, radius=0.006)

for side in (-1, 1):
    s = float(side)
    sx = 0.092 * s
    curve(f"OverallStrap_{side}", [
        (0.125 * s, -0.126, 1.332),
        (0.110 * s, -0.148, 1.260),
        (sx, -0.163, 1.192),
    ], OVERALL, 0.016)
    ico(f"BibButton_{side}", (sx, -0.176, 1.198), (0.015, 0.006, 0.015), BRASS, 2)

# Side cargo pocket follows the left trouser and remains subtle from front view.
patch("CargoPocket", [
    (-0.218, 0.705),
    (-0.165, 0.700),
    (-0.162, 0.590),
    (-0.222, 0.585),
], -0.006, OVERALL_DARK, thickness=0.010, radius=0.006)


# -----------------------------------------------------------------------------
# RELAXED A-POSE ARMS — no shoulder balls, gentle inward forearm bend.
# -----------------------------------------------------------------------------
for side in (-1, 1):
    s = float(side)
    shoulder = Vector((0.198 * s, -0.002, 1.265))
    sleeve_end = Vector((0.278 * s, -0.015, 1.060))
    cuff_end = Vector((0.284 * s, -0.020, 1.015))
    wrist = Vector((0.255 * s, -0.055, 0.790))
    hand_center = Vector((0.248 * s, -0.064, 0.724))

    tapered(f"Sleeve_{side}", shoulder, sleeve_end, 0.078, 0.068, SHIRT, 22, 0.007)
    tapered(f"SleeveRoll_{side}", sleeve_end, cuff_end, 0.073, 0.071, SHIRT, 22, 0.006)
    tapered(f"Forearm_{side}", cuff_end, wrist, 0.052, 0.045, SKIN, 20, 0.006)
    uv(f"Hand_{side}", tuple(hand_center), (0.045, 0.039, 0.066), SKIN, 18, 10, rot=(0.0, math.radians(5.0 * s), math.radians(-3.0 * s)))
    ico(f"Thumb_{side}", (hand_center.x + 0.028 * s, hand_center.y - 0.012, hand_center.z + 0.004), (0.016, 0.017, 0.027), SKIN, 2)


# -----------------------------------------------------------------------------
# NECK / TERRACOTTA NECKERCHIEF.
# -----------------------------------------------------------------------------
cyl("Neck", (0.0, 0.0, 1.373), 0.064, 0.096, SKIN, vertices=20, edge=0.006)
profile("ScarfWrap", [
    (1.333, 0.094, 0.080, 0.0, -0.004),
    (1.359, 0.102, 0.087, 0.0, -0.004),
    (1.385, 0.094, 0.080, 0.0, -0.002),
], SCARF, 22)
ico("ScarfKnot", (0.0, -0.100, 1.338), (0.042, 0.031, 0.037), SCARF, 2)
cloth_triangle("ScarfTailL", [(-0.009, -0.116, 1.328), (-0.066, -0.118, 1.225), (0.003, -0.118, 1.252)], SCARF)
cloth_triangle("ScarfTailR", [(0.009, -0.117, 1.328), (0.070, -0.119, 1.246), (0.006, -0.119, 1.220)], SCARF)


# -----------------------------------------------------------------------------
# HEAD / FACE — oval face, tapered jaw, large dark expressive eyes.
# -----------------------------------------------------------------------------
profile("Head", [
    (1.400, 0.076, 0.090, 0.0, -0.008),
    (1.430, 0.124, 0.128, 0.0, -0.006),
    (1.492, 0.170, 0.155, 0.0, -0.003),
    (1.565, 0.184, 0.161, 0.0, -0.001),
    (1.635, 0.178, 0.157, 0.0, 0.001),
    (1.695, 0.148, 0.142, 0.0, 0.002),
    (1.724, 0.088, 0.105, 0.0, 0.002),
], SKIN, 30)

for side in (-1, 1):
    s = float(side)
    uv(f"Ear_{side}", (0.178 * s, 0.000, 1.558), (0.033, 0.023, 0.048), SKIN, 16, 10)
    uv(f"Blush_{side}", (0.098 * s, -0.158, 1.500), (0.019, 0.0023, 0.009), BLUSH, 12, 8)
    x = 0.066 * s
    uv(f"EyeWhite_{side}", (x, -0.161, 1.580), (0.042, 0.0048, 0.050), EYE_WHITE, 18, 12)
    uv(f"Iris_{side}", (x, -0.166, 1.578), (0.034, 0.0038, 0.043), IRIS, 16, 10)
    uv(f"Pupil_{side}", (x, -0.169, 1.576), (0.017, 0.0028, 0.026), PUPIL, 14, 8)
    uv(f"EyeGlint_{side}", (x - 0.009 * s, -0.172, 1.598), (0.0055, 0.0015, 0.0075), EYE_WHITE, 10, 6)

curve("LidL", [(-0.104, -0.165, 1.602), (-0.066, -0.171, 1.614), (-0.030, -0.165, 1.602)], HAIR, 0.0044)
curve("LidR", [(0.030, -0.165, 1.602), (0.066, -0.171, 1.614), (0.104, -0.165, 1.602)], HAIR, 0.0044)
curve("BrowL", [(-0.108, -0.157, 1.648), (-0.069, -0.164, 1.660), (-0.034, -0.157, 1.652)], HAIR, 0.0058)
curve("BrowR", [(0.034, -0.157, 1.652), (0.069, -0.164, 1.660), (0.108, -0.157, 1.648)], HAIR, 0.0058)
ico("Nose", (0.0, -0.162, 1.530), (0.015, 0.007, 0.015), SKIN, 2)
curve("Smile", [(-0.037, -0.160, 1.481), (0.0, -0.167, 1.470), (0.041, -0.160, 1.483)], MOUTH, 0.0044)


# -----------------------------------------------------------------------------
# HAIR — coherent cap plus rounded tapered clumps, swept asymmetrically.
# -----------------------------------------------------------------------------
ico("HairBack", (0.0, 0.015, 1.680), (0.195, 0.165, 0.150), HAIR, 3)
ico("HairCrown", (-0.010, 0.000, 1.735), (0.172, 0.137, 0.094), HAIR, 2)

# Front fringe: larger mass on character-left, open patch on right forehead.
path_lock("BangOuterL",
          [(-0.155, -0.040, 1.747), (-0.168, -0.095, 1.704), (-0.163, -0.142, 1.657)],
          [(0.041, 0.032), (0.036, 0.028), (0.028, 0.022)],
          (-0.154, -0.174, 1.582), HAIR)
path_lock("BangHeavyL",
          [(-0.105, -0.058, 1.777), (-0.119, -0.110, 1.735), (-0.114, -0.150, 1.685)],
          [(0.050, 0.034), (0.043, 0.030), (0.033, 0.024)],
          (-0.105, -0.182, 1.548), HAIR_WARM)
path_lock("BangCenterL",
          [(-0.045, -0.067, 1.788), (-0.054, -0.118, 1.746), (-0.048, -0.157, 1.699)],
          [(0.052, 0.035), (0.044, 0.031), (0.034, 0.024)],
          (-0.038, -0.184, 1.595), HAIR)
path_lock("BangCenterR",
          [(0.018, -0.064, 1.783), (0.030, -0.113, 1.741), (0.040, -0.150, 1.700)],
          [(0.047, 0.033), (0.040, 0.029), (0.030, 0.022)],
          (0.053, -0.179, 1.620), HAIR_WARM)
path_lock("BangRight",
          [(0.084, -0.048, 1.764), (0.102, -0.093, 1.728), (0.116, -0.130, 1.690)],
          [(0.040, 0.030), (0.034, 0.026), (0.026, 0.020)],
          (0.137, -0.168, 1.620), HAIR)

path_lock("TempleL",
          [(-0.177, -0.003, 1.705), (-0.190, -0.040, 1.666), (-0.195, -0.070, 1.625)],
          [(0.033, 0.029), (0.029, 0.026), (0.022, 0.020)],
          (-0.198, -0.096, 1.555), HAIR)
path_lock("TempleR",
          [(0.174, -0.002, 1.700), (0.186, -0.036, 1.663), (0.191, -0.064, 1.625)],
          [(0.031, 0.028), (0.027, 0.024), (0.021, 0.019)],
          (0.194, -0.090, 1.568), HAIR)

# Crown tufts sweep instead of standing vertically.
path_lock("CrownLeft",
          [(-0.100, 0.010, 1.782), (-0.128, 0.001, 1.810), (-0.152, -0.006, 1.830)],
          [(0.039, 0.031), (0.032, 0.027), (0.024, 0.020)],
          (-0.180, -0.014, 1.842), HAIR_WARM)
path_lock("CrownCenter",
          [(-0.025, -0.002, 1.797), (-0.016, -0.008, 1.835), (0.000, -0.013, 1.864)],
          [(0.041, 0.032), (0.033, 0.027), (0.025, 0.020)],
          (0.022, -0.018, 1.884), HAIR)
path_lock("CrownRight",
          [(0.048, 0.004, 1.785), (0.074, -0.001, 1.812), (0.100, -0.006, 1.832)],
          [(0.037, 0.030), (0.030, 0.025), (0.023, 0.019)],
          (0.130, -0.012, 1.842), HAIR_WARM)
path_lock("BackSweep",
          [(0.120, 0.030, 1.752), (0.148, 0.024, 1.768), (0.173, 0.016, 1.773)],
          [(0.032, 0.028), (0.027, 0.024), (0.021, 0.019)],
          (0.198, 0.006, 1.760), HAIR)


# -----------------------------------------------------------------------------
# BACKPACK / BEDROLL / LEAF CHARM.
# -----------------------------------------------------------------------------
rounded_box("Backpack", (0.0, 0.163, 1.090), (0.278, 0.148, 0.395), BAG, radius=0.058)
rounded_box("BackpackFlap", (0.0, 0.243, 1.190), (0.246, 0.030, 0.128), BAG_EDGE, radius=0.036)
rounded_box("BackpackPocket", (0.0, 0.247, 0.985), (0.174, 0.030, 0.104), BAG_EDGE, radius=0.026)
for side in (-1, 1):
    s = float(side)
    curve(f"PackStrap_{side}", [(0.132 * s, 0.022, 1.295), (0.162 * s, -0.016, 1.108), (0.148 * s, -0.040, 0.945)], BAG, 0.014)
    ico(f"PackBuckle_{side}", (0.152 * s, -0.047, 0.992), (0.016, 0.006, 0.020), BRASS, 2)

cyl("Bedroll", (0.0, 0.172, 1.342), 0.064, 0.274, BAG_EDGE, rot=(0.0, math.radians(90.0), 0.0), vertices=20, edge=0.006)
cyl("BedrollBandL", (-0.073, 0.172, 1.342), 0.069, 0.019, BAG, rot=(0.0, math.radians(90.0), 0.0), vertices=20, edge=0.0035)
cyl("BedrollBandR", (0.073, 0.172, 1.342), 0.069, 0.019, BAG, rot=(0.0, math.radians(90.0), 0.0), vertices=20, edge=0.0035)
curve("LeafStem", [(0.150, 0.250, 1.012), (0.178, 0.270, 0.955), (0.193, 0.270, 0.902)], LEAF, 0.0043)
ico("LeafA", (0.202, 0.270, 0.930), (0.023, 0.006, 0.043), LEAF, 2, rot=(math.radians(8), 0.0, math.radians(-28)))
ico("LeafB", (0.179, 0.270, 0.896), (0.021, 0.006, 0.038), LEAF, 2, rot=(math.radians(-8), 0.0, math.radians(32)))


# Export visual asset only. Gameplay integration remains gated by visual approval.
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
print(f"Exported Lembah Sari Character Rework V2.5 to {OUT_PATH}")
