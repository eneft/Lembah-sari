import bpy
import math
import os
from mathutils import Vector

# Lembah Sari - Character Rework V2.1
# Approved concept target: warm stylized young village farmer / explorer.
# This pass prioritizes silhouette, 4-ish-head proportions, organic clothing,
# chunky dark hair, olive overalls, terracotta scarf, leather boots/backpack.

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


# Colors are authored darker than the original V2 because Godot's studio lighting
# previously washed the concept palette into cream/yellow.
MAT_SKIN = mat("Skin Warm Peach", (0.52, 0.31, 0.20), 0.89, 0.12)
MAT_SKIN_BLUSH = mat("Cheek Warmth", (0.67, 0.22, 0.17), 0.91, 0.08)
MAT_HAIR = mat("Hair Deep Chestnut", (0.035, 0.014, 0.008), 0.97, 0.07)
MAT_HAIR_LIGHT = mat("Hair Warm Edge", (0.075, 0.027, 0.012), 0.96, 0.07)
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


def hair_clump(name, loc, scale, rot, material, tip_drop=0.0):
    root = ellipsoid(name + "Root", loc, scale, material, subdivisions=2, rot=rot)
    if tip_drop > 0.0:
        # Small pointed continuation prevents the previous rounded 'ram horn' read.
        tip_loc = (loc[0], loc[1] - scale[1] * 0.22, loc[2] - scale[2] * 0.64)
        bpy.ops.mesh.primitive_cone_add(
            vertices=8,
            radius1=0.012,
            radius2=max(scale[0] * 0.62, 0.025),
            depth=tip_drop,
            location=tip_loc,
            rotation=rot,
        )
        tip = bpy.context.object
        tip.name = name + "Tip"
        bevel(tip, 0.008, 2)
        finish(smooth(tip), material)
    return root


# -----------------------------------------------------------------------------
# PROPORTIONS
# The previous pass was too squat. V2.1 lengthens torso/legs while keeping the
# readable larger head. Face-head height is ~0.45 m against ~1.76 m total.
# -----------------------------------------------------------------------------

# Boots: rounded adventure boots, not rectangular mannequin feet.
for side in (-1, 1):
    x = 0.135 * side
    rounded_box(f"BootSole_{side}", (x, -0.055, 0.045), (0.205, 0.315, 0.055), MAT_BOOT, bevel_width=0.025)
    uv_ellipsoid(f"BootFoot_{side}", (x, -0.065, 0.115), (0.105, 0.165, 0.085), MAT_BOOT_LIGHT, segments=18, rings=10)
    profile_tube(
        f"BootAnkle_{side}",
        [
            (0.115, 0.090, 0.083, x, 0.005),
            (0.205, 0.094, 0.086, x, 0.008),
            (0.300, 0.100, 0.090, x, 0.006),
        ],
        MAT_BOOT,
        16,
    )
    profile_tube(
        f"BootCuff_{side}",
        [
            (0.285, 0.105, 0.095, x, 0.005),
            (0.315, 0.112, 0.100, x, 0.005),
            (0.345, 0.106, 0.095, x, 0.005),
        ],
        MAT_BOOT_LIGHT,
        16,
    )
    for i in range(3):
        z = 0.155 + i * 0.040
        curve_line(
            f"BootLace_{side}_{i}",
            [(x - 0.065, -0.158, z), (x, -0.170, z + 0.008), (x + 0.065, -0.158, z)],
            MAT_BOOT,
            0.006,
        )

# Loose overall trousers with visible rolled cuffs.
for side in (-1, 1):
    x = 0.138 * side
    profile_tube(
        f"PantLeg_{side}",
        [
            (0.325, 0.118, 0.105, x, 0.008),
            (0.410, 0.130, 0.115, x, 0.005),
            (0.555, 0.138, 0.124, x, 0.003),
            (0.690, 0.145, 0.132, x, 0.0),
        ],
        MAT_OVERALL,
        18,
    )
    profile_tube(
        f"PantRoll_{side}",
        [
            (0.305, 0.128, 0.113, x, 0.006),
            (0.338, 0.134, 0.118, x, 0.006),
            (0.370, 0.128, 0.112, x, 0.006),
        ],
        MAT_OVERALL_LIGHT,
        18,
    )

# Organic hips/waist and shirt torso.
profile_tube(
    "OverallHipWaist",
    [
        (0.620, 0.235, 0.155, 0.0, 0.0),
        (0.700, 0.245, 0.160, 0.0, 0.0),
        (0.785, 0.230, 0.153, 0.0, 0.0),
        (0.835, 0.218, 0.148, 0.0, 0.0),
    ],
    MAT_OVERALL,
    20,
)
profile_tube(
    "ShirtTorso",
    [
        (0.790, 0.220, 0.145, 0.0, 0.0),
        (0.900, 0.245, 0.158, 0.0, 0.0),
        (1.045, 0.265, 0.165, 0.0, 0.0),
        (1.165, 0.248, 0.154, 0.0, 0.0),
        (1.205, 0.215, 0.142, 0.0, 0.0),
    ],
    MAT_SHIRT,
    20,
)

# Overall bib and pocket are thinner and rounded; straps follow torso as curves.
rounded_box("OverallWaistBand", (0, -0.151, 0.805), (0.40, 0.035, 0.095), MAT_OVERALL_DARK, bevel_width=0.025)
rounded_box("OverallBib", (0, -0.169, 0.995), (0.255, 0.035, 0.300), MAT_OVERALL, bevel_width=0.040)
rounded_box("BibPocket", (0, -0.194, 0.985), (0.145, 0.025, 0.110), MAT_OVERALL_DARK, bevel_width=0.026)
for side in (-1, 1):
    sx = 0.105 * side
    curve_line(
        f"OverallStrap_{side}",
        [(0.135 * side, -0.150, 1.190), (0.120 * side, -0.175, 1.105), (sx, -0.185, 1.020)],
        MAT_OVERALL,
        0.022,
    )
    ellipsoid(f"OverallButton_{side}", (sx, -0.207, 1.040), (0.021, 0.010, 0.021), MAT_METAL, subdivisions=2)

# One readable cargo pocket as in the approved concept.
rounded_box("CargoPocket", (-0.248, -0.020, 0.515), (0.045, 0.135, 0.145), MAT_OVERALL_DARK, rot=(0, 0, math.radians(-2)), bevel_width=0.020)
ellipsoid("CargoButton", (-0.272, -0.020, 0.545), (0.010, 0.018, 0.010), MAT_METAL, subdivisions=1)

# Rolled sleeves and natural arm taper.
for side in (-1, 1):
    shoulder = (0.250 * side, 0.0, 1.120)
    elbow = (0.315 * side, -0.018, 0.900)
    wrist = (0.337 * side, -0.055, 0.680)
    tapered_segment(f"Sleeve_{side}", shoulder, elbow, 0.105, 0.092, MAT_SHIRT, 16, 0.014)
    ellipsoid(f"SleeveRoll_{side}", elbow, (0.100, 0.088, 0.050), MAT_SHIRT, subdivisions=2)
    tapered_segment(f"Forearm_{side}", elbow, wrist, 0.070, 0.058, MAT_SKIN, 16, 0.010)
    uv_ellipsoid(f"Hand_{side}", (0.342 * side, -0.070, 0.625), (0.070, 0.060, 0.095), MAT_SKIN, segments=16, rings=10)

# Neck and scarf.
cylinder("Neck", (0, 0.0, 1.215), 0.076, 0.115, MAT_SKIN, vertices=16, bevel_width=0.010)
profile_tube(
    "ScarfWrap",
    [
        (1.175, 0.112, 0.095, 0.0, -0.005),
        (1.205, 0.118, 0.100, 0.0, -0.005),
        (1.235, 0.110, 0.094, 0.0, -0.002),
    ],
    MAT_SCARF,
    18,
)
ellipsoid("ScarfKnot", (0, -0.118, 1.185), (0.055, 0.042, 0.048), MAT_SCARF, subdivisions=2)
triangle_cloth("ScarfTailL", [(-0.015, -0.140, 1.170), (-0.085, -0.142, 1.035), (0.005, -0.142, 1.075)], MAT_SCARF)
triangle_cloth("ScarfTailR", [(0.015, -0.141, 1.170), (0.090, -0.143, 1.070), (0.010, -0.143, 1.035)], MAT_SCARF)

# Head: slightly narrower and longer than V2 to avoid toy/monkey proportions.
uv_ellipsoid("Head", (0, -0.012, 1.430), (0.225, 0.190, 0.235), MAT_SKIN, segments=28, rings=16)
for side in (-1, 1):
    uv_ellipsoid(f"Ear_{side}", (0.218 * side, -0.002, 1.425), (0.045, 0.030, 0.065), MAT_SKIN, segments=14, rings=8)
    uv_ellipsoid(f"Cheek_{side}", (0.122 * side, -0.193, 1.365), (0.040, 0.010, 0.024), MAT_SKIN_BLUSH, segments=12, rings=8)
    x = 0.083 * side
    uv_ellipsoid(f"EyeWhite_{side}", (x, -0.194, 1.455), (0.052, 0.014, 0.063), MAT_EYE_WHITE, segments=16, rings=10)
    uv_ellipsoid(f"Iris_{side}", (x, -0.204, 1.452), (0.033, 0.009, 0.043), MAT_EYE, segments=14, rings=8)
    uv_ellipsoid(f"Pupil_{side}", (x, -0.211, 1.450), (0.016, 0.006, 0.024), MAT_PUPIL, segments=12, rings=8)
    uv_ellipsoid(f"EyeHighlight_{side}", (x - 0.009 * side, -0.216, 1.474), (0.007, 0.003, 0.009), MAT_EYE_WHITE, segments=10, rings=6)

curve_line("BrowL", [(-0.132, -0.202, 1.532), (-0.083, -0.212, 1.548), (-0.038, -0.202, 1.535)], MAT_HAIR, 0.008)
curve_line("BrowR", [(0.038, -0.202, 1.535), (0.083, -0.212, 1.548), (0.132, -0.202, 1.532)], MAT_HAIR, 0.008)
ellipsoid("Nose", (0, -0.205, 1.400), (0.024, 0.014, 0.022), MAT_SKIN, subdivisions=2)
curve_line("Smile", [(-0.050, -0.207, 1.342), (0.0, -0.217, 1.328), (0.053, -0.207, 1.344)], MAT_MOUTH, 0.006)

# Hair: dark coherent cap with separated chunky clumps. Side 'horn' masses removed.
ellipsoid("HairBack", (0, 0.015, 1.575), (0.232, 0.185, 0.170), MAT_HAIR, subdivisions=3)
ellipsoid("HairCrown", (0.010, -0.005, 1.635), (0.205, 0.160, 0.115), MAT_HAIR, subdivisions=2)

hair_specs = [
    ("BangFarL", (-0.145, -0.155, 1.585), (0.070, 0.045, 0.115), (math.radians(16), math.radians(-4), math.radians(-28)), MAT_HAIR),
    ("BangL", (-0.080, -0.178, 1.610), (0.073, 0.043, 0.130), (math.radians(18), 0.0, math.radians(-17)), MAT_HAIR_LIGHT),
    ("BangC", (-0.010, -0.187, 1.618), (0.075, 0.042, 0.142), (math.radians(20), 0.0, math.radians(-4)), MAT_HAIR),
    ("BangR", (0.072, -0.176, 1.605), (0.071, 0.043, 0.128), (math.radians(18), 0.0, math.radians(18)), MAT_HAIR_LIGHT),
    ("TempleL", (-0.205, -0.073, 1.515), (0.048, 0.050, 0.105), (math.radians(-5), math.radians(5), math.radians(-20)), MAT_HAIR),
    ("TempleR", (0.205, -0.060, 1.520), (0.048, 0.050, 0.105), (math.radians(-5), math.radians(-5), math.radians(20)), MAT_HAIR),
]
for spec in hair_specs:
    hair_clump(*spec, tip_drop=0.070)

# Top silhouette tufts, small enough not to become spikes.
for name, loc, rot in [
    ("TopL", (-0.090, -0.005, 1.705), (math.radians(-5), math.radians(4), math.radians(-30))),
    ("TopC", (0.005, -0.010, 1.725), (math.radians(-5), 0.0, math.radians(-2))),
    ("TopR", (0.090, 0.0, 1.695), (math.radians(-6), math.radians(-4), math.radians(30))),
]:
    hair_clump(name, loc, (0.055, 0.045, 0.095), rot, MAT_HAIR_LIGHT, tip_drop=0.045)

# Backpack: rounded compact body, lower bedroll, readable straps/hardware.
rounded_box("BackpackBody", (0, 0.190, 0.965), (0.345, 0.185, 0.430), MAT_BAG, bevel_width=0.070)
rounded_box("BackpackFlap", (0, 0.292, 1.070), (0.310, 0.040, 0.160), MAT_BAG_LIGHT, bevel_width=0.045)
rounded_box("BackpackPocket", (0, 0.296, 0.835), (0.220, 0.040, 0.135), MAT_BAG_LIGHT, bevel_width=0.035)
for side in (-1, 1):
    curve_line(
        f"PackShoulderStrap_{side}",
        [(0.165 * side, 0.040, 1.160), (0.205 * side, -0.020, 0.970), (0.180 * side, -0.055, 0.800)],
        MAT_BAG,
        0.020,
    )
    ellipsoid(f"PackBuckle_{side}", (0.185 * side, -0.064, 0.850), (0.022, 0.010, 0.028), MAT_METAL, subdivisions=2)

cylinder("Bedroll", (0, 0.205, 1.205), 0.080, 0.335, MAT_BAG_LIGHT, rot=(0, math.radians(90), 0), vertices=16, bevel_width=0.010)
cylinder("BedrollBandL", (-0.090, 0.205, 1.205), 0.086, 0.026, MAT_BAG, rot=(0, math.radians(90), 0), vertices=16, bevel_width=0.006)
cylinder("BedrollBandR", (0.090, 0.205, 1.205), 0.086, 0.026, MAT_BAG, rot=(0, math.radians(90), 0), vertices=16, bevel_width=0.006)
curve_line("LeafCharmStem", [(0.185, 0.300, 0.880), (0.220, 0.320, 0.815), (0.235, 0.320, 0.755)], MAT_LEAF, 0.006)
ellipsoid("LeafCharmA", (0.245, 0.320, 0.790), (0.030, 0.009, 0.056), MAT_LEAF, subdivisions=2, rot=(math.radians(8), 0, math.radians(-28)))
ellipsoid("LeafCharmB", (0.215, 0.320, 0.750), (0.027, 0.009, 0.050), MAT_LEAF, subdivisions=2, rot=(math.radians(-8), 0, math.radians(32)))

# Export all authored pieces as one GLB scene asset. Gameplay/physics stays outside.
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

print(f"Exported Lembah Sari Character Rework V2.1 to {OUT_PATH}")
