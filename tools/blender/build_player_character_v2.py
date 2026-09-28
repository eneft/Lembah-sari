import bpy
import math
import os
from mathutils import Vector

# Lembah Sari - Character Rework V2.3
# Master reference: approved cozy farmer/explorer concept sheet.
# Goal of this pass: remove the assembled/mannequin read.  Clothing and body
# use continuous tapered profiles, the head has an actual jaw/chin silhouette,
# sleeves overlap the shoulders naturally, and hair is layered/asymmetric.

OUT_PATH = os.path.abspath(os.environ.get("LEMBAH_CHARACTER_OUT", "assets/models/player_character_v2.glb"))
os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)

bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)


def material(name, rgb, roughness=0.94, specular=0.10):
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


# Dark-authored values compensate the GL-compatibility review renderer while
# retaining the approved cream / moss / terracotta / brown palette.
SKIN = material("Skin Warm Peach", (0.50, 0.29, 0.18), 0.90, 0.10)
BLUSH = material("Skin Blush", (0.56, 0.16, 0.12), 0.94, 0.05)
HAIR = material("Hair Deep Chestnut", (0.032, 0.012, 0.007), 0.97, 0.06)
HAIR_EDGE = material("Hair Warm Edge", (0.070, 0.025, 0.011), 0.96, 0.06)
SHIRT = material("Shirt Warm Cream", (0.55, 0.47, 0.33), 0.98, 0.05)
OVERALL = material("Overall Moss Olive", (0.115, 0.165, 0.062), 0.98, 0.05)
OVERALL_DARK = material("Overall Deep Moss", (0.070, 0.100, 0.036), 0.98, 0.04)
OVERALL_CUFF = material("Overall Rolled Cuff", (0.185, 0.215, 0.095), 0.98, 0.04)
SCARF = material("Neckerchief Terracotta", (0.41, 0.11, 0.038), 0.97, 0.05)
BOOT = material("Boot Dark Leather", (0.060, 0.023, 0.010), 0.98, 0.05)
BOOT_EDGE = material("Boot Leather Edge", (0.125, 0.048, 0.018), 0.97, 0.05)
BAG = material("Backpack Weathered Leather", (0.125, 0.055, 0.022), 0.98, 0.05)
BAG_EDGE = material("Backpack Canvas Edge", (0.225, 0.105, 0.040), 0.97, 0.05)
BRASS = material("Muted Brass Hardware", (0.33, 0.19, 0.050), 0.84, 0.18)
EYE_WHITE = material("Eye Warm White", (0.67, 0.62, 0.51), 0.91, 0.10)
EYE_BROWN = material("Eye Deep Brown", (0.063, 0.019, 0.008), 0.89, 0.10)
PUPIL = material("Eye Pupil", (0.007, 0.003, 0.002), 0.93, 0.05)
MOUTH = material("Mouth Soft Brown", (0.105, 0.021, 0.015), 0.95, 0.05)
LEAF = material("Leaf Charm", (0.070, 0.190, 0.050), 0.97, 0.04)

ROOT = bpy.data.objects.new("LembahSariCharacterV2", None)
bpy.context.collection.objects.link(ROOT)


def finish(obj, mat=None):
    if mat is not None and hasattr(obj.data, "materials"):
        obj.data.materials.append(mat)
    obj.parent = ROOT
    return obj


def smooth(obj):
    if obj.type == "MESH":
        for p in obj.data.polygons:
            p.use_smooth = True
    return obj


def bevel(obj, width=0.01, segments=2):
    mod = obj.modifiers.new("Soft edge", "BEVEL")
    mod.width = width
    mod.segments = segments
    mod.limit_method = "ANGLE"
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=mod.name)
    return obj


def rounded_box(name, loc, dims, mat, rot=(0.0, 0.0, 0.0), radius=0.02):
    bpy.ops.mesh.primitive_cube_add(location=loc, rotation=rot)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dims
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if radius:
        bevel(obj, radius, 3)
    return finish(obj, mat)


def ellipsoid(name, loc, scale, mat, subdivisions=2, rot=(0.0, 0.0, 0.0)):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=subdivisions, radius=1.0, location=loc, rotation=rot)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return finish(smooth(obj), mat)


def uv_ellipsoid(name, loc, scale, mat, segments=24, rings=14, rot=(0.0, 0.0, 0.0)):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings, radius=1.0, location=loc, rotation=rot)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return finish(smooth(obj), mat)


def cylinder(name, loc, radius, depth, mat, rot=(0.0, 0.0, 0.0), vertices=16, edge=0.008):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=loc, rotation=rot)
    obj = bpy.context.object
    obj.name = name
    if edge:
        bevel(obj, edge, 2)
    return finish(smooth(obj), mat)


def profile_mesh(name, rings, mat, segments=20):
    # rings: z, rx, ry, cx, cy.  This is used for torso, trousers, boots and
    # the face so silhouettes can taper organically instead of stacking boxes.
    verts = []
    faces = []
    for z, rx, ry, cx, cy in rings:
        for i in range(segments):
            a = math.tau * float(i) / float(segments)
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
    return finish(smooth(obj), mat)


def segment(name, p1, p2, r1, r2, mat, vertices=16, edge=0.008):
    a = Vector(p1)
    b = Vector(p2)
    direction = b - a
    mid = (a + b) * 0.5
    bpy.ops.mesh.primitive_cone_add(vertices=vertices, radius1=r1, radius2=r2, depth=direction.length, location=mid)
    obj = bpy.context.object
    obj.name = name
    obj.rotation_mode = "QUATERNION"
    obj.rotation_quaternion = Vector((0.0, 0.0, 1.0)).rotation_difference(direction.normalized())
    if edge:
        bevel(obj, edge, 2)
    return finish(smooth(obj), mat)


def curve(name, pts, mat, radius=0.007):
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
    return finish(obj, mat)


def cloth_triangle(name, points, mat, thickness=0.010):
    mesh = bpy.data.meshes.new(name + "Mesh")
    mesh.from_pydata(points, [], [(0, 1, 2)])
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    solid = obj.modifiers.new("Cloth thickness", "SOLIDIFY")
    solid.thickness = thickness
    solid.offset = 0.0
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=solid.name)
    bevel(obj, 0.005, 2)
    return finish(obj, mat)


def hair_lock(name, points, width, depth, mat):
    # Curved pointed lock made from several rectangular cross-sections.
    # points contains 3 centres followed by a pointed tip.
    sections = points[:-1]
    tip = points[-1]
    verts = []
    for idx, center in enumerate(sections):
        factor = 1.0 - 0.18 * idx
        w = width * factor
        d = depth * factor
        cx, cy, cz = center
        verts.extend([
            (cx - w * 0.5, cy - d * 0.5, cz),
            (cx + w * 0.5, cy - d * 0.5, cz),
            (cx + w * 0.5, cy + d * 0.5, cz),
            (cx - w * 0.5, cy + d * 0.5, cz),
        ])
    faces = []
    for sec in range(len(sections) - 1):
        s0 = sec * 4
        s1 = (sec + 1) * 4
        faces.extend([
            (s0 + 0, s1 + 0, s1 + 1, s0 + 1),
            (s0 + 1, s1 + 1, s1 + 2, s0 + 2),
            (s0 + 2, s1 + 2, s1 + 3, s0 + 3),
            (s0 + 3, s1 + 3, s1 + 0, s0 + 0),
        ])
    last = (len(sections) - 1) * 4
    tip_i = len(verts)
    verts.append(tip)
    faces.extend([
        (last + 0, tip_i, last + 1),
        (last + 1, tip_i, last + 2),
        (last + 2, tip_i, last + 3),
        (last + 3, tip_i, last + 0),
    ])
    mesh = bpy.data.meshes.new(name + "Mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    bevel(obj, 0.009, 2)
    return finish(smooth(obj), mat)


# -----------------------------------------------------------------------------
# FEET / TROUSERS
# -----------------------------------------------------------------------------

for side in (-1, 1):
    x = 0.120 * side
    # Elliptical sole removes the rectangular slab look of V2.2.
    uv_ellipsoid(f"BootSole_{side}", (x, -0.060, 0.050), (0.102, 0.170, 0.033), BOOT, 18, 10)
    uv_ellipsoid(f"BootToe_{side}", (x, -0.092, 0.120), (0.098, 0.155, 0.075), BOOT_EDGE, 20, 12)
    profile_mesh(
        f"BootShaft_{side}",
        [
            (0.105, 0.083, 0.075, x, 0.006),
            (0.205, 0.087, 0.079, x, 0.006),
            (0.300, 0.092, 0.083, x, 0.004),
            (0.340, 0.098, 0.087, x, 0.004),
        ], BOOT, 18,
    )
    profile_mesh(
        f"BootTop_{side}",
        [
            (0.320, 0.098, 0.087, x, 0.004),
            (0.350, 0.106, 0.093, x, 0.004),
            (0.382, 0.100, 0.088, x, 0.004),
        ], BOOT_EDGE, 18,
    )
    for i in range(3):
        z = 0.165 + i * 0.041
        curve(f"BootLace_{side}_{i}", [(x - 0.055, -0.168, z), (x, -0.177, z + 0.006), (x + 0.055, -0.168, z)], BOOT, 0.005)

for side in (-1, 1):
    x = 0.120 * side
    profile_mesh(
        f"TrouserLeg_{side}",
        [
            (0.350, 0.104, 0.095, x, 0.005),
            (0.470, 0.112, 0.101, x, 0.004),
            (0.620, 0.120, 0.108, x, 0.002),
            (0.775, 0.128, 0.114, x, 0.000),
        ], OVERALL, 20,
    )
    profile_mesh(
        f"RolledCuff_{side}",
        [
            (0.338, 0.116, 0.104, x, 0.004),
            (0.366, 0.123, 0.109, x, 0.004),
            (0.397, 0.116, 0.103, x, 0.004),
        ], OVERALL_CUFF, 20,
    )

# Continuous hip/waist body: no horizontal floating belt block.
profile_mesh(
    "OverallLowerBody",
    [
        (0.695, 0.198, 0.137, 0.0, 0.000),
        (0.760, 0.218, 0.147, 0.0, 0.000),
        (0.835, 0.225, 0.151, 0.0, 0.000),
        (0.900, 0.215, 0.145, 0.0, 0.000),
        (0.945, 0.202, 0.139, 0.0, -0.002),
    ], OVERALL, 22,
)

# Cream shirt torso has shoulder taper and a slightly narrower waist.
profile_mesh(
    "ShirtTorso",
    [
        (0.885, 0.200, 0.134, 0.0, 0.000),
        (0.985, 0.215, 0.142, 0.0, -0.002),
        (1.110, 0.238, 0.151, 0.0, -0.003),
        (1.225, 0.248, 0.154, 0.0, -0.002),
        (1.300, 0.220, 0.141, 0.0, 0.000),
    ], SHIRT, 22,
)

# Bib gently overlaps the lower body.  No separate waist-bar/pouch silhouette.
rounded_box("OverallBib", (0, -0.157, 1.105), (0.232, 0.026, 0.292), OVERALL, radius=0.045)
rounded_box("BibPocket", (0, -0.177, 1.090), (0.132, 0.018, 0.096), OVERALL_DARK, radius=0.025)
for side in (-1, 1):
    sx = 0.098 * side
    curve(
        f"OverallStrap_{side}",
        [(0.136 * side, -0.133, 1.300), (0.120 * side, -0.158, 1.220), (sx, -0.174, 1.135)],
        OVERALL, 0.018,
    )
    ellipsoid(f"BibButton_{side}", (sx, -0.191, 1.145), (0.018, 0.008, 0.018), BRASS, 2)

# Cargo pocket is slim and follows the leg, rather than looking like a box stuck on.
rounded_box("CargoPocket", (-0.224, -0.004, 0.615), (0.035, 0.112, 0.132), OVERALL_DARK, radius=0.018)
ellipsoid("CargoButton", (-0.244, -0.006, 0.640), (0.008, 0.014, 0.008), BRASS, 1)


# -----------------------------------------------------------------------------
# SLEEVES / ARMS / HANDS
# Rounded shoulder caps overlap torso and hide the disconnected-cylinder seam.
# -----------------------------------------------------------------------------

for side in (-1, 1):
    shoulder = (0.226 * side, -0.002, 1.220)
    upper = (0.275 * side, -0.012, 1.095)
    elbow = (0.292 * side, -0.020, 0.975)
    wrist = (0.312 * side, -0.045, 0.760)

    ellipsoid(f"SleeveShoulder_{side}", shoulder, (0.108, 0.100, 0.135), SHIRT, 2)
    segment(f"SleeveUpper_{side}", upper, elbow, 0.092, 0.080, SHIRT, 18, 0.010)
    ellipsoid(f"SleeveRoll_{side}", elbow, (0.090, 0.079, 0.045), SHIRT, 2)
    segment(f"Forearm_{side}", elbow, wrist, 0.061, 0.052, SKIN, 18, 0.008)
    # Slightly tapered hand + thumb nub reads more like a hand than an oval capsule.
    profile_mesh(
        f"Hand_{side}",
        [
            (0.675, 0.053, 0.047, 0.315 * side, -0.050),
            (0.710, 0.061, 0.052, 0.316 * side, -0.055),
            (0.760, 0.055, 0.049, 0.313 * side, -0.050),
        ], SKIN, 16,
    )
    ellipsoid(f"Thumb_{side}", (0.350 * side, -0.070, 0.712), (0.023, 0.025, 0.040), SKIN, 2, rot=(0.0, math.radians(18 * side), 0.0))


# -----------------------------------------------------------------------------
# NECK / SCARF
# -----------------------------------------------------------------------------

cylinder("Neck", (0, 0.0, 1.332), 0.070, 0.106, SKIN, vertices=18, edge=0.008)
profile_mesh(
    "ScarfWrap",
    [
        (1.292, 0.103, 0.087, 0.0, -0.004),
        (1.320, 0.111, 0.093, 0.0, -0.004),
        (1.347, 0.102, 0.086, 0.0, -0.002),
    ], SCARF, 20,
)
ellipsoid("ScarfKnot", (0, -0.110, 1.296), (0.048, 0.036, 0.043), SCARF, 2)
cloth_triangle("ScarfTailL", [(-0.012, -0.129, 1.282), (-0.076, -0.131, 1.165), (0.003, -0.131, 1.198)], SCARF)
cloth_triangle("ScarfTailR", [(0.012, -0.130, 1.282), (0.080, -0.132, 1.188), (0.007, -0.132, 1.158)], SCARF)


# -----------------------------------------------------------------------------
# HEAD / FACE
# A ring-built head gives a jaw, cheeks and forehead instead of a sphere.
# -----------------------------------------------------------------------------

profile_mesh(
    "Head",
    [
        (1.365, 0.090, 0.105, 0.0, -0.010),   # chin
        (1.400, 0.145, 0.145, 0.0, -0.006),
        (1.475, 0.190, 0.171, 0.0, -0.004),   # cheeks
        (1.555, 0.203, 0.177, 0.0, -0.002),
        (1.635, 0.194, 0.171, 0.0, 0.000),
        (1.700, 0.158, 0.153, 0.0, 0.002),
        (1.730, 0.100, 0.118, 0.0, 0.002),
    ], SKIN, 28,
)

for side in (-1, 1):
    uv_ellipsoid(f"Ear_{side}", (0.196 * side, 0.000, 1.545), (0.038, 0.026, 0.055), SKIN, 16, 10)
    # Blush patches are almost flush, no protruding pink balls.
    uv_ellipsoid(f"Blush_{side}", (0.108 * side, -0.174, 1.485), (0.030, 0.0035, 0.015), BLUSH, 12, 8)
    x = 0.074 * side
    uv_ellipsoid(f"EyeWhite_{side}", (x, -0.177, 1.565), (0.043, 0.006, 0.054), EYE_WHITE, 18, 12)
    uv_ellipsoid(f"Iris_{side}", (x, -0.183, 1.561), (0.027, 0.0045, 0.036), EYE_BROWN, 16, 10)
    uv_ellipsoid(f"Pupil_{side}", (x, -0.187, 1.559), (0.013, 0.0035, 0.020), PUPIL, 14, 8)
    uv_ellipsoid(f"EyeHighlight_{side}", (x - 0.007 * side, -0.190, 1.579), (0.0055, 0.002, 0.007), EYE_WHITE, 10, 6)

curve("UpperLidL", [(-0.115, -0.183, 1.591), (-0.074, -0.190, 1.605), (-0.035, -0.183, 1.590)], HAIR, 0.005)
curve("UpperLidR", [(0.035, -0.183, 1.590), (0.074, -0.190, 1.605), (0.115, -0.183, 1.591)], HAIR, 0.005)
curve("BrowL", [(-0.118, -0.176, 1.642), (-0.075, -0.184, 1.654), (-0.038, -0.177, 1.645)], HAIR, 0.0065)
curve("BrowR", [(0.038, -0.177, 1.645), (0.075, -0.184, 1.654), (0.118, -0.176, 1.642)], HAIR, 0.0065)
ellipsoid("Nose", (0.0, -0.180, 1.512), (0.018, 0.009, 0.018), SKIN, 2)
curve("Smile", [(-0.042, -0.179, 1.458), (0.0, -0.187, 1.446), (0.046, -0.179, 1.460)], MOUTH, 0.005)


# -----------------------------------------------------------------------------
# HAIR
# Large back mass + overlapping locks with deliberately different lengths.
# -----------------------------------------------------------------------------

ellipsoid("HairBackMass", (0.0, 0.014, 1.683), (0.212, 0.178, 0.160), HAIR, 3)
ellipsoid("HairCrownMass", (0.010, -0.002, 1.742), (0.188, 0.150, 0.106), HAIR, 2)

front_locks = [
    ("Fringe1", [(-0.172, -0.050, 1.748), (-0.180, -0.105, 1.710), (-0.176, -0.150, 1.665), (-0.170, -0.185, 1.585)], 0.074, 0.060, HAIR),
    ("Fringe2", [(-0.125, -0.068, 1.780), (-0.137, -0.120, 1.738), (-0.132, -0.160, 1.690), (-0.123, -0.193, 1.548)], 0.086, 0.064, HAIR_EDGE),
    ("Fringe3", [(-0.064, -0.075, 1.792), (-0.074, -0.128, 1.752), (-0.070, -0.166, 1.700), (-0.060, -0.197, 1.590)], 0.092, 0.066, HAIR),
    ("Fringe4", [(0.010, -0.076, 1.795), (0.018, -0.130, 1.754), (0.023, -0.168, 1.708), (0.030, -0.196, 1.608)], 0.090, 0.066, HAIR_EDGE),
    ("Fringe5", [(0.083, -0.068, 1.782), (0.095, -0.120, 1.742), (0.104, -0.158, 1.696), (0.116, -0.191, 1.560)], 0.086, 0.064, HAIR),
    ("Fringe6", [(0.150, -0.052, 1.756), (0.164, -0.102, 1.718), (0.170, -0.142, 1.675), (0.180, -0.179, 1.610)], 0.072, 0.058, HAIR),
]
for spec in front_locks:
    hair_lock(*spec)

hair_lock("TempleL", [(-0.193, -0.010, 1.716), (-0.205, -0.047, 1.675), (-0.210, -0.075, 1.625), (-0.215, -0.105, 1.545)], 0.060, 0.056, HAIR)
hair_lock("TempleR", [(0.192, -0.005, 1.710), (0.204, -0.040, 1.670), (0.209, -0.070, 1.625), (0.214, -0.100, 1.558)], 0.058, 0.054, HAIR)

# Swept crown tufts echo the approved messy silhouette instead of vertical spikes.
hair_lock("CrownSweepL", [(-0.110, 0.005, 1.790), (-0.135, -0.004, 1.820), (-0.158, -0.012, 1.842), (-0.185, -0.020, 1.858)], 0.070, 0.060, HAIR_EDGE)
hair_lock("CrownSweepC", [(-0.025, -0.004, 1.807), (-0.020, -0.010, 1.850), (-0.010, -0.016, 1.882), (0.010, -0.020, 1.902)], 0.074, 0.062, HAIR)
hair_lock("CrownSweepR", [(0.060, 0.002, 1.800), (0.088, -0.003, 1.832), (0.115, -0.008, 1.850), (0.145, -0.014, 1.860)], 0.068, 0.058, HAIR_EDGE)
hair_lock("CrownBackR", [(0.135, 0.030, 1.765), (0.168, 0.025, 1.782), (0.190, 0.018, 1.790), (0.215, 0.008, 1.780)], 0.060, 0.055, HAIR)


# -----------------------------------------------------------------------------
# BACKPACK / BEDROLL / LEAF CHARM
# -----------------------------------------------------------------------------

rounded_box("BackpackBody", (0.0, 0.177, 1.060), (0.305, 0.165, 0.420), BAG, radius=0.065)
rounded_box("BackpackFlap", (0.0, 0.267, 1.170), (0.272, 0.034, 0.142), BAG_EDGE, radius=0.042)
rounded_box("BackpackPocket", (0.0, 0.271, 0.940), (0.195, 0.034, 0.118), BAG_EDGE, radius=0.032)
for side in (-1, 1):
    curve(
        f"PackStrap_{side}",
        [(0.145 * side, 0.028, 1.275), (0.180 * side, -0.020, 1.075), (0.162 * side, -0.047, 0.900)],
        BAG, 0.017,
    )
    ellipsoid(f"PackBuckle_{side}", (0.167 * side, -0.055, 0.955), (0.019, 0.008, 0.024), BRASS, 2)

cylinder("Bedroll", (0.0, 0.185, 1.325), 0.070, 0.300, BAG_EDGE, rot=(0.0, math.radians(90.0), 0.0), vertices=18, edge=0.008)
cylinder("BedrollBandL", (-0.080, 0.185, 1.325), 0.076, 0.022, BAG, rot=(0.0, math.radians(90.0), 0.0), vertices=18, edge=0.004)
cylinder("BedrollBandR", (0.080, 0.185, 1.325), 0.076, 0.022, BAG, rot=(0.0, math.radians(90.0), 0.0), vertices=18, edge=0.004)
curve("LeafStem", [(0.164, 0.276, 0.995), (0.195, 0.296, 0.930), (0.211, 0.296, 0.870)], LEAF, 0.005)
ellipsoid("LeafA", (0.220, 0.296, 0.902), (0.027, 0.007, 0.050), LEAF, 2, rot=(math.radians(8), 0.0, math.radians(-28)))
ellipsoid("LeafB", (0.194, 0.296, 0.862), (0.024, 0.007, 0.044), LEAF, 2, rot=(math.radians(-8), 0.0, math.radians(32)))


# Export authored visual asset only. Gameplay collision/logic remain in Godot and
# this asset stays isolated until visual approval.
bpy.ops.object.select_all(action="DESELECT")
ROOT.select_set(True)
for child in ROOT.children_recursive:
    child.select_set(True)
bpy.context.view_layer.objects.active = ROOT

bpy.ops.export_scene.gltf(
    filepath=OUT_PATH,
    export_format="GLB",
    use_selection=True,
    export_apply=True,
    export_yup=True,
)
print(f"Exported Lembah Sari Character Rework V2.3 to {OUT_PATH}")
