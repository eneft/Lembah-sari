import bpy
import math
import os
from mathutils import Vector

# Lembah Sari - Character Rework V2.2
# Approved concept target: warm stylized young village farmer / explorer.
# This pass moves the model closer to the approved sheet with taller proportions,
# a smaller face-head, pointed layered hair locks, organic clothes, and compact gear.

OUT_PATH = os.path.abspath(os.environ.get("LEMBAH_CHARACTER_OUT", "assets/models/player_character_v2.glb"))
os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)

bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)


def mat(name, color, roughness=0.94, specular=0.12):
    material = bpy.data.materials.new(name)
    material.diffuse_color = (*color, 1.0)
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (*color, 1.0)
        bsdf.inputs["Roughness"].default_value = roughness
        if "Metallic" in bsdf.inputs:
            bsdf.inputs["Metallic"].default_value = 0.0
        if "Specular IOR Level" in bsdf.inputs:
            bsdf.inputs["Specular IOR Level"].default_value = specular
        elif "Specular" in bsdf.inputs:
            bsdf.inputs["Specular"].default_value = specular
    return material


MAT_SKIN = mat("Skin Warm Peach", (0.52, 0.31, 0.20), 0.89, 0.12)
MAT_SKIN_BLUSH = mat("Cheek Warmth", (0.58, 0.18, 0.14), 0.93, 0.06)
MAT_HAIR = mat("Hair Deep Chestnut", (0.035, 0.014, 0.008), 0.97, 0.07)
MAT_HAIR_LIGHT = mat("Hair Warm Edge", (0.070, 0.024, 0.011), 0.96, 0.07)
MAT_SHIRT = mat("Shirt Warm Cream", (0.56, 0.48, 0.34), 0.97, 0.07)
MAT_OVERALL = mat("Overall Moss Olive", (0.12, 0.17, 0.065), 0.98, 0.06)
MAT_OVERALL_DARK = mat("Overall Deep Moss", (0.075, 0.105, 0.040), 0.98, 0.05)
MAT_OVERALL_LIGHT = mat("Overall Rolled Cuff", (0.19, 0.22, 0.10), 0.98, 0.05)
MAT_SCARF = mat("Neckerchief Terracotta", (0.42, 0.115, 0.042), 0.97, 0.06)
MAT_BOOT = mat("Boot Dark Leather", (0.065, 0.026, 0.012), 0.98, 0.06)
MAT_BOOT_LIGHT = mat("Boot Leather Edge", (0.13, 0.052, 0.020), 0.97, 0.06)
MAT_BAG = mat("Backpack Weathered Leather", (0.13, 0.060, 0.025), 0.98, 0.06)
MAT_BAG_LIGHT = mat("Backpack Canvas Edge", (0.24, 0.115, 0.045), 0.97, 0.06)
MAT_METAL = mat("Muted Brass Hardware", (0.34, 0.20, 0.055), 0.84, 0.20)
MAT_EYE_WHITE = mat("Eye Warm White", (0.66, 0.61, 0.50), 0.90, 0.12)
MAT_EYE = mat("Eye Deep Brown", (0.070, 0.022, 0.010), 0.88, 0.13)
MAT_PUPIL = mat("Eye Pupil", (0.008, 0.004, 0.003), 0.92, 0.08)
MAT_MOUTH = mat("Mouth Soft Brown", (0.12, 0.025, 0.018), 0.95, 0.06)
MAT_LEAF = mat("Leaf Charm", (0.075, 0.20, 0.055), 0.97, 0.05)

ROOT = bpy.data.objects.new("LembahSariCharacterV2", None)
bpy.context.collection.objects.link(ROOT)


def finish(obj, material=None):
    if material is not None and hasattr(obj.data, "materials"):
        obj.data.materials.append(material)
    obj.parent = ROOT
    return obj


def smooth(obj):
    if obj.type == "MESH":
        for poly in obj.data.polygons:
            poly.use_smooth = True
    return obj


def bevel(obj, width=0.012, segments=2):
    mod = obj.modifiers.new("Soft tailored edge", "BEVEL")
    mod.width = width
    mod.segments = segments
    mod.limit_method = "ANGLE"
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=mod.name)
    return obj


def rounded_box(name, loc, dims, material, rot=(0, 0, 0), bevel_width=0.02):
    bpy.ops.mesh.primitive_cube_add(location=loc, rotation=rot)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dims
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel_width > 0:
        bevel(obj, bevel_width, 3)
    return finish(obj, material)


def ellipsoid(name, loc, scale, material, subdivisions=2, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=subdivisions, radius=1.0, location=loc, rotation=rot)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return finish(smooth(obj), material)


def uv_ellipsoid(name, loc, scale, material, segments=24, rings=14, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings, radius=1.0, location=loc, rotation=rot)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return finish(smooth(obj), material)


def cylinder(name, loc, radius, depth, material, rot=(0, 0, 0), vertices=14, bevel_width=0.010):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=loc, rotation=rot)
    obj = bpy.context.object
    obj.name = name
    if bevel_width > 0:
        bevel(obj, bevel_width, 2)
    return finish(smooth(obj), material)


def tapered_segment(name, p1, p2, r1, r2, material, vertices=14, bevel_width=0.010):
    a = Vector(p1)
    b = Vector(p2)
    direction = b - a
    length = direction.length
    midpoint = (a + b) * 0.5
    bpy.ops.mesh.primitive_cone_add(vertices=vertices, radius1=r1, radius2=r2, depth=length, location=midpoint)
    obj = bpy.context.object
    obj.name = name
    obj.rotation_mode = "QUATERNION"
    obj.rotation_quaternion = Vector((0.0, 0.0, 1.0)).rotation_difference(direction.normalized())
    if bevel_width > 0:
        bevel(obj, bevel_width, 2)
    return finish(smooth(obj), material)


def profile_tube(name, rings, material, segments=18):
    # rings: (z, radius_x, radius_y, center_x, center_y)
    verts = []
    faces = []
    for z, rx, ry, cx, cy in rings:
        for i in range(segments):
            angle = (math.tau * i) / segments
            verts.append((cx + math.cos(angle) * rx, cy + math.sin(angle) * ry, z))
    count = len(rings)
    for ring in range(count - 1):
        for i in range(segments):
            nxt = (i + 1) % segments
            a = ring * segments + i
            b = ring * segments + nxt
            c = (ring + 1) * segments + nxt
            d = (ring + 1) * segments + i
            faces.append((a, b, c, d))
    faces.append(tuple(reversed(range(segments))))
    top_start = (count - 1) * segments
    faces.append(tuple(top_start + i for i in range(segments)))
    mesh = bpy.data.meshes.new(name + "Mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    return finish(smooth(obj), material)


def curve_line(name, pts, material, bevel_depth=0.007):
    curve = bpy.data.curves.new(name, type="CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = 3
    curve.bevel_depth = bevel_depth
    curve.bevel_resolution = 3
    spline = curve.splines.new("BEZIER")
    spline.bezier_points.add(len(pts) - 1)
    for bp, co in zip(spline.bezier_points, pts):
        bp.co = co
        bp.handle_left_type = "AUTO"
        bp.handle_right_type = "AUTO"
    obj = bpy.data.objects.new(name, curve)
    bpy.context.collection.objects.link(obj)
    return finish(obj, material)


def triangle_cloth(name, verts, material, thickness=0.012):
    mesh = bpy.data.meshes.new(name + "Mesh")
    mesh.from_pydata(verts, [], [(0, 1, 2)])
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    solid = obj.modifiers.new("Soft cloth thickness", "SOLIDIFY")
    solid.thickness = thickness
    solid.offset = 0.0
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=solid.name)
    bevel(obj, 0.006, 2)
    return finish(obj, material)


def hair_lock(name, root, mid, tip, width, depth, material):
    # Low-poly tapered lock: two softly sized rectangular sections flowing to a point.
    verts = []
    sections = [
        (root, width, depth),
        (mid, width * 0.78, depth * 0.82),
    ]
    for center, w, d in sections:
        cx, cy, cz = center
        verts.extend([
            (cx - w * 0.5, cy - d * 0.5, cz),
            (cx + w * 0.5, cy - d * 0.5, cz),
            (cx + w * 0.5, cy + d * 0.5, cz),
            (cx - w * 0.5, cy + d * 0.5, cz),
        ])
    tip_index = len(verts)
    verts.append(tip)
    faces = [
        (0, 1, 2, 3),
        (0, 4, 5, 1),
        (1, 5, 6, 2),
        (2, 6, 7, 3),
        (3, 7, 4, 0),
        (4, tip_index, 5),
        (5, tip_index, 6),
        (6, tip_index, 7),
        (7, tip_index, 4),
    ]
    mesh = bpy.data.meshes.new(name + "Mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    bevel(obj, 0.010, 2)
    return finish(smooth(obj), material)


# -----------------------------------------------------------------------------
# BODY / CLOTHING - taller, lighter silhouette than V2.1
# -----------------------------------------------------------------------------

for side in (-1, 1):
    x = 0.125 * side
    rounded_box(f"BootSole_{side}", (x, -0.055, 0.045), (0.195, 0.305, 0.052), MAT_BOOT, bevel_width=0.024)
    uv_ellipsoid(f"BootFoot_{side}", (x, -0.065, 0.115), (0.100, 0.160, 0.082), MAT_BOOT_LIGHT, segments=18, rings=10)
    profile_tube(
        f"BootAnkle_{side}",
        [
            (0.115, 0.085, 0.078, x, 0.005),
            (0.210, 0.090, 0.082, x, 0.007),
            (0.305, 0.094, 0.086, x, 0.005),
        ], MAT_BOOT, 16,
    )
    profile_tube(
        f"BootCuff_{side}",
        [
            (0.290, 0.100, 0.090, x, 0.005),
            (0.322, 0.106, 0.095, x, 0.005),
            (0.352, 0.100, 0.090, x, 0.005),
        ], MAT_BOOT_LIGHT, 16,
    )
    for i in range(3):
        z = 0.155 + i * 0.040
        curve_line(
            f"BootLace_{side}_{i}",
            [(x - 0.060, -0.157, z), (x, -0.169, z + 0.007), (x + 0.060, -0.157, z)],
            MAT_BOOT, 0.0055,
        )

for side in (-1, 1):
    x = 0.125 * side
    profile_tube(
        f"PantLeg_{side}",
        [
            (0.335, 0.108, 0.098, x, 0.008),
            (0.445, 0.115, 0.104, x, 0.006),
            (0.610, 0.123, 0.111, x, 0.003),
            (0.770, 0.128, 0.116, x, 0.0),
        ], MAT_OVERALL, 18,
    )
    profile_tube(
        f"PantRoll_{side}",
        [
            (0.315, 0.117, 0.105, x, 0.006),
            (0.348, 0.123, 0.109, x, 0.006),
            (0.380, 0.117, 0.104, x, 0.006),
        ], MAT_OVERALL_LIGHT, 18,
    )

profile_tube(
    "OverallHipWaist",
    [
        (0.700, 0.215, 0.145, 0.0, 0.0),
        (0.775, 0.225, 0.150, 0.0, 0.0),
        (0.855, 0.215, 0.145, 0.0, 0.0),
        (0.925, 0.200, 0.138, 0.0, 0.0),
    ], MAT_OVERALL, 20,
)
profile_tube(
    "ShirtTorso",
    [
        (0.870, 0.205, 0.138, 0.0, 0.0),
        (0.980, 0.225, 0.148, 0.0, 0.0),
        (1.125, 0.245, 0.155, 0.0, 0.0),
        (1.255, 0.232, 0.145, 0.0, 0.0),
        (1.305, 0.200, 0.132, 0.0, 0.0),
    ], MAT_SHIRT, 20,
)

rounded_box("OverallWaistBand", (0, -0.142, 0.905), (0.365, 0.028, 0.052), MAT_OVERALL, bevel_width=0.020)
rounded_box("OverallBib", (0, -0.158, 1.100), (0.240, 0.032, 0.285), MAT_OVERALL, bevel_width=0.038)
rounded_box("BibPocket", (0, -0.181, 1.090), (0.135, 0.022, 0.100), MAT_OVERALL_DARK, bevel_width=0.024)
for side in (-1, 1):
    sx = 0.100 * side
    curve_line(
        f"OverallStrap_{side}",
        [(0.128 * side, -0.140, 1.295), (0.115 * side, -0.162, 1.215), (sx, -0.174, 1.130)],
        MAT_OVERALL, 0.019,
    )
    ellipsoid(f"OverallButton_{side}", (sx, -0.195, 1.145), (0.019, 0.009, 0.019), MAT_METAL, subdivisions=2)

rounded_box("CargoPocket", (-0.224, -0.010, 0.585), (0.040, 0.120, 0.135), MAT_OVERALL_DARK, bevel_width=0.018)
ellipsoid("CargoButton", (-0.246, -0.010, 0.615), (0.009, 0.016, 0.009), MAT_METAL, subdivisions=1)

for side in (-1, 1):
    shoulder = (0.235 * side, 0.0, 1.225)
    elbow = (0.292 * side, -0.018, 0.985)
    wrist = (0.315 * side, -0.050, 0.760)
    tapered_segment(f"Sleeve_{side}", shoulder, elbow, 0.095, 0.082, MAT_SHIRT, 16, 0.013)
    ellipsoid(f"SleeveRoll_{side}", elbow, (0.088, 0.079, 0.045), MAT_SHIRT, subdivisions=2)
    tapered_segment(f"Forearm_{side}", elbow, wrist, 0.063, 0.053, MAT_SKIN, 16, 0.009)
    uv_ellipsoid(f"Hand_{side}", (0.320 * side, -0.064, 0.703), (0.062, 0.054, 0.088), MAT_SKIN, segments=16, rings=10)

cylinder("Neck", (0, 0.0, 1.325), 0.071, 0.108, MAT_SKIN, vertices=16, bevel_width=0.009)
profile_tube(
    "ScarfWrap",
    [
        (1.288, 0.103, 0.088, 0.0, -0.004),
        (1.316, 0.110, 0.094, 0.0, -0.004),
        (1.344, 0.102, 0.087, 0.0, -0.002),
    ], MAT_SCARF, 18,
)
ellipsoid("ScarfKnot", (0, -0.109, 1.292), (0.050, 0.038, 0.044), MAT_SCARF, subdivisions=2)
triangle_cloth("ScarfTailL", [(-0.013, -0.129, 1.278), (-0.078, -0.132, 1.155), (0.004, -0.132, 1.190)], MAT_SCARF)
triangle_cloth("ScarfTailR", [(0.013, -0.130, 1.278), (0.082, -0.132, 1.185), (0.008, -0.132, 1.150)], MAT_SCARF)

# -----------------------------------------------------------------------------
# FACE - smaller head, less doll-like eyes, subtle cheeks, readable smile
# -----------------------------------------------------------------------------

uv_ellipsoid("Head", (0, -0.010, 1.545), (0.205, 0.178, 0.218), MAT_SKIN, segments=30, rings=18)
for side in (-1, 1):
    uv_ellipsoid(f"Ear_{side}", (0.199 * side, -0.002, 1.540), (0.040, 0.027, 0.058), MAT_SKIN, segments=14, rings=8)
    uv_ellipsoid(f"Cheek_{side}", (0.110 * side, -0.180, 1.485), (0.032, 0.008, 0.018), MAT_SKIN_BLUSH, segments=12, rings=8)
    x = 0.076 * side
    uv_ellipsoid(f"EyeWhite_{side}", (x, -0.181, 1.565), (0.046, 0.012, 0.055), MAT_EYE_WHITE, segments=16, rings=10)
    uv_ellipsoid(f"Iris_{side}", (x, -0.190, 1.562), (0.028, 0.008, 0.037), MAT_EYE, segments=14, rings=8)
    uv_ellipsoid(f"Pupil_{side}", (x, -0.196, 1.560), (0.014, 0.005, 0.021), MAT_PUPIL, segments=12, rings=8)
    uv_ellipsoid(f"EyeHighlight_{side}", (x - 0.008 * side, -0.200, 1.582), (0.006, 0.0025, 0.008), MAT_EYE_WHITE, segments=10, rings=6)

curve_line("UpperLidL", [(-0.119, -0.193, 1.590), (-0.077, -0.201, 1.608), (-0.034, -0.192, 1.590)], MAT_HAIR, 0.0055)
curve_line("UpperLidR", [(0.034, -0.192, 1.590), (0.077, -0.201, 1.608), (0.119, -0.193, 1.590)], MAT_HAIR, 0.0055)
curve_line("BrowL", [(-0.122, -0.188, 1.645), (-0.078, -0.196, 1.659), (-0.040, -0.188, 1.648)], MAT_HAIR, 0.007)
curve_line("BrowR", [(0.040, -0.188, 1.648), (0.078, -0.196, 1.659), (0.122, -0.188, 1.645)], MAT_HAIR, 0.007)
ellipsoid("Nose", (0, -0.192, 1.515), (0.021, 0.012, 0.020), MAT_SKIN, subdivisions=2)
curve_line("Smile", [(-0.045, -0.195, 1.462), (0.0, -0.204, 1.449), (0.048, -0.195, 1.464)], MAT_MOUTH, 0.0055)

# -----------------------------------------------------------------------------
# HAIR - coherent dark cap + deliberately pointed, asymmetric locks
# -----------------------------------------------------------------------------

ellipsoid("HairBack", (0, 0.015, 1.685), (0.214, 0.180, 0.160), MAT_HAIR, subdivisions=3)
ellipsoid("HairCrown", (0.005, 0.000, 1.745), (0.190, 0.150, 0.105), MAT_HAIR, subdivisions=2)

bangs = [
    ("BangFarL", (-0.162, -0.072, 1.760), (-0.174, -0.154, 1.690), (-0.170, -0.190, 1.575), 0.088, 0.070, MAT_HAIR),
    ("BangL", (-0.100, -0.082, 1.785), (-0.110, -0.162, 1.705), (-0.120, -0.196, 1.535), 0.098, 0.072, MAT_HAIR_LIGHT),
    ("BangCenter", (-0.025, -0.085, 1.795), (-0.020, -0.166, 1.710), (-0.035, -0.198, 1.585), 0.102, 0.074, MAT_HAIR),
    ("BangR", (0.060, -0.080, 1.785), (0.073, -0.160, 1.705), (0.085, -0.195, 1.550), 0.096, 0.072, MAT_HAIR_LIGHT),
    ("BangFarR", (0.140, -0.065, 1.760), (0.155, -0.145, 1.688), (0.172, -0.186, 1.595), 0.085, 0.068, MAT_HAIR),
]
for args in bangs:
    hair_lock(*args)

hair_lock("TempleL", (-0.188, -0.020, 1.730), (-0.205, -0.080, 1.645), (-0.215, -0.125, 1.535), 0.068, 0.062, MAT_HAIR)
hair_lock("TempleR", (0.188, -0.010, 1.720), (0.205, -0.070, 1.640), (0.212, -0.115, 1.550), 0.066, 0.060, MAT_HAIR)

# Three asymmetric crown locks give the messy concept silhouette without a helmet.
hair_lock("TopLeft", (-0.095, 0.010, 1.800), (-0.115, -0.005, 1.845), (-0.140, -0.018, 1.885), 0.075, 0.065, MAT_HAIR_LIGHT)
hair_lock("TopCenter", (-0.010, -0.005, 1.810), (0.000, -0.012, 1.870), (0.025, -0.020, 1.925), 0.078, 0.066, MAT_HAIR)
hair_lock("TopRight", (0.080, 0.005, 1.800), (0.105, -0.002, 1.845), (0.135, -0.012, 1.875), 0.072, 0.062, MAT_HAIR_LIGHT)

# -----------------------------------------------------------------------------
# BACKPACK / GEAR - compact, rounded and subordinate to the character
# -----------------------------------------------------------------------------

rounded_box("BackpackBody", (0, 0.178, 1.060), (0.320, 0.170, 0.430), MAT_BAG, bevel_width=0.065)
rounded_box("BackpackFlap", (0, 0.272, 1.165), (0.286, 0.038, 0.150), MAT_BAG_LIGHT, bevel_width=0.042)
rounded_box("BackpackPocket", (0, 0.276, 0.935), (0.205, 0.038, 0.125), MAT_BAG_LIGHT, bevel_width=0.032)
for side in (-1, 1):
    curve_line(
        f"PackShoulderStrap_{side}",
        [(0.150 * side, 0.035, 1.275), (0.190 * side, -0.018, 1.070), (0.170 * side, -0.050, 0.890)],
        MAT_BAG, 0.018,
    )
    ellipsoid(f"PackBuckle_{side}", (0.175 * side, -0.060, 0.945), (0.020, 0.009, 0.026), MAT_METAL, subdivisions=2)

cylinder("Bedroll", (0, 0.190, 1.325), 0.073, 0.315, MAT_BAG_LIGHT, rot=(0, math.radians(90), 0), vertices=16, bevel_width=0.009)
cylinder("BedrollBandL", (-0.085, 0.190, 1.325), 0.079, 0.024, MAT_BAG, rot=(0, math.radians(90), 0), vertices=16, bevel_width=0.005)
cylinder("BedrollBandR", (0.085, 0.190, 1.325), 0.079, 0.024, MAT_BAG, rot=(0, math.radians(90), 0), vertices=16, bevel_width=0.005)
curve_line("LeafCharmStem", [(0.172, 0.282, 0.990), (0.205, 0.302, 0.925), (0.220, 0.302, 0.865)], MAT_LEAF, 0.0055)
ellipsoid("LeafCharmA", (0.230, 0.302, 0.900), (0.028, 0.008, 0.052), MAT_LEAF, subdivisions=2, rot=(math.radians(8), 0, math.radians(-28)))
ellipsoid("LeafCharmB", (0.202, 0.302, 0.860), (0.025, 0.008, 0.046), MAT_LEAF, subdivisions=2, rot=(math.radians(-8), 0, math.radians(32)))

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

print(f"Exported Lembah Sari Character Rework V2.2 to {OUT_PATH}")
