import bpy
import math
import os

# Lembah Sari - Character Rework V2
# Concept target: warm stylized young village farmer / explorer.
# Production goal: one coherent GLB asset, matte game-ready materials,
# readable from the fixed gameplay camera, no Godot primitive mannequin parts.

OUT_PATH = os.path.abspath(os.environ.get("LEMBAH_CHARACTER_OUT", "assets/models/player_character_v2.glb"))
os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)


def mat(name, color, roughness=0.92, specular=0.18):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1.0)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (*color, 1.0)
        bsdf.inputs["Roughness"].default_value = roughness
        if "Specular IOR Level" in bsdf.inputs:
            bsdf.inputs["Specular IOR Level"].default_value = specular
        elif "Specular" in bsdf.inputs:
            bsdf.inputs["Specular"].default_value = specular
    return m


MAT_SKIN = mat("Skin Warm Peach", (0.83, 0.56, 0.38), 0.88, 0.12)
MAT_SKIN_BLUSH = mat("Cheek Warmth", (0.93, 0.46, 0.38), 0.90, 0.10)
MAT_HAIR = mat("Hair Deep Chestnut", (0.115, 0.055, 0.032), 0.96, 0.10)
MAT_HAIR_LIGHT = mat("Hair Warm Highlight", (0.22, 0.095, 0.045), 0.94, 0.10)
MAT_SHIRT = mat("Shirt Warm Cream", (0.83, 0.76, 0.61), 0.96, 0.10)
MAT_OVERALL = mat("Overall Moss Olive", (0.29, 0.35, 0.18), 0.96, 0.09)
MAT_OVERALL_DARK = mat("Overall Deep Moss", (0.20, 0.26, 0.13), 0.97, 0.08)
MAT_OVERALL_LIGHT = mat("Overall Rolled Cuff", (0.39, 0.43, 0.25), 0.96, 0.08)
MAT_SCARF = mat("Neckerchief Terracotta", (0.67, 0.24, 0.11), 0.95, 0.08)
MAT_BOOT = mat("Boot Dark Leather", (0.20, 0.105, 0.060), 0.97, 0.08)
MAT_BOOT_LIGHT = mat("Boot Leather Highlight", (0.31, 0.17, 0.085), 0.96, 0.09)
MAT_BAG = mat("Backpack Weathered Leather", (0.33, 0.19, 0.095), 0.97, 0.08)
MAT_BAG_LIGHT = mat("Backpack Canvas Highlight", (0.47, 0.30, 0.14), 0.96, 0.08)
MAT_METAL = mat("Muted Brass Hardware", (0.55, 0.37, 0.12), 0.82, 0.28)
MAT_EYE_WHITE = mat("Eye Warm White", (0.93, 0.90, 0.82), 0.88, 0.16)
MAT_EYE = mat("Eye Deep Brown", (0.14, 0.055, 0.025), 0.84, 0.20)
MAT_PUPIL = mat("Eye Pupil", (0.028, 0.018, 0.014), 0.88, 0.16)
MAT_MOUTH = mat("Mouth Soft Brown", (0.22, 0.055, 0.035), 0.94, 0.08)
MAT_LEAF = mat("Leaf Charm", (0.20, 0.38, 0.16), 0.95, 0.08)

ROOT = bpy.data.objects.new("LembahSariCharacterV2", None)
bpy.context.collection.objects.link(ROOT)


def finish(obj, material=None, parent=True):
    if material is not None and hasattr(obj.data, 'materials'):
        obj.data.materials.append(material)
    if parent:
        obj.parent = ROOT
    return obj


def bevel(obj, width=0.015, segments=2):
    mod = obj.modifiers.new("Soft form", "BEVEL")
    mod.width = width
    mod.segments = segments
    mod.limit_method = 'ANGLE'
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=mod.name)
    return obj


def box(name, loc, dims, material, rot=(0, 0, 0), bevel_width=0.02):
    bpy.ops.mesh.primitive_cube_add(location=loc, rotation=rot)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dims
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel_width:
        bevel(obj, bevel_width, 3)
    return finish(obj, material)


def ellipsoid(name, loc, scale, material, subdivisions=2, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=subdivisions, radius=1.0, location=loc, rotation=rot)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return finish(obj, material)


def uv_ellipsoid(name, loc, scale, material, segments=24, rings=12, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings, radius=1.0, location=loc, rotation=rot)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return finish(obj, material)


def cylinder(name, loc, radius, depth, material, rot=(0, 0, 0), vertices=12, bevel_width=0.012):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=loc, rotation=rot)
    obj = bpy.context.object
    obj.name = name
    if bevel_width:
        bevel(obj, bevel_width, 2)
    return finish(obj, material)


def cone(name, loc, r1, r2, depth, material, rot=(0, 0, 0), vertices=8):
    bpy.ops.mesh.primitive_cone_add(vertices=vertices, radius1=r1, radius2=r2, depth=depth, location=loc, rotation=rot)
    obj = bpy.context.object
    obj.name = name
    bevel(obj, min(r1 * 0.22, 0.018), 2)
    return finish(obj, material)


def curve_line(name, pts, material, bevel_depth=0.009):
    curve = bpy.data.curves.new(name, type='CURVE')
    curve.dimensions = '3D'
    curve.resolution_u = 2
    curve.bevel_depth = bevel_depth
    curve.bevel_resolution = 3
    spline = curve.splines.new('BEZIER')
    spline.bezier_points.add(len(pts) - 1)
    for bp, co in zip(spline.bezier_points, pts):
        bp.co = co
        bp.handle_left_type = 'AUTO'
        bp.handle_right_type = 'AUTO'
    obj = bpy.data.objects.new(name, curve)
    bpy.context.collection.objects.link(obj)
    return finish(obj, material)


def triangle_cloth(name, verts, material, thickness=0.014):
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
    bevel(obj, 0.008, 2)
    return finish(obj, material)


# Feet / boots: chunky, warm adventure silhouette.
for side in (-1, 1):
    x = 0.135 * side
    box(f"BootFoot_{side}", (x, -0.055, 0.095), (0.205, 0.31, 0.145), MAT_BOOT, bevel_width=0.032)
    box(f"BootToe_{side}", (x, -0.155, 0.108), (0.20, 0.16, 0.115), MAT_BOOT_LIGHT, bevel_width=0.035)
    cylinder(f"BootAnkle_{side}", (x, 0.005, 0.235), 0.092, 0.25, MAT_BOOT, vertices=12, bevel_width=0.015)
    box(f"BootCuff_{side}", (x, 0.005, 0.34), (0.19, 0.17, 0.055), MAT_BOOT_LIGHT, bevel_width=0.018)
    for i in range(3):
        z = 0.155 + i * 0.038
        box(f"BootLace_{side}_{i}", (x, -0.155, z), (0.145, 0.015, 0.012), MAT_BOOT, bevel_width=0.004)

# Loose overall pants.
for side in (-1, 1):
    x = 0.135 * side
    cone(f"PantLeg_{side}", (x, 0.005, 0.505), 0.135, 0.115, 0.39, MAT_OVERALL, vertices=12)
    box(f"PantRolledCuff_{side}", (x, 0.0, 0.345), (0.245, 0.205, 0.085), MAT_OVERALL_LIGHT, bevel_width=0.026)

box("OverallHipBlock", (0, 0.005, 0.68), (0.42, 0.25, 0.23), MAT_OVERALL, bevel_width=0.055)
uv_ellipsoid("ShirtTorso", (0, 0.00, 0.91), (0.255, 0.17, 0.315), MAT_SHIRT, segments=20, rings=12)

# Overall bib, pocket, waist band and straps.
box("OverallWaistBand", (0, -0.158, 0.735), (0.41, 0.055, 0.10), MAT_OVERALL_DARK, bevel_width=0.022)
box("OverallBib", (0, -0.178, 0.93), (0.285, 0.055, 0.33), MAT_OVERALL, bevel_width=0.035)
box("BibPocket", (0, -0.213, 0.93), (0.17, 0.035, 0.13), MAT_OVERALL_DARK, bevel_width=0.022)
box("OverallStrapL", (-0.105, -0.18, 1.115), (0.052, 0.045, 0.32), MAT_OVERALL, rot=(0, 0, math.radians(-8)), bevel_width=0.015)
box("OverallStrapR", (0.105, -0.18, 1.115), (0.052, 0.045, 0.32), MAT_OVERALL, rot=(0, 0, math.radians(8)), bevel_width=0.015)
for side in (-1, 1):
    ellipsoid(f"OverallButton_{side}", (0.10 * side, -0.210, 1.04), (0.022, 0.012, 0.022), MAT_METAL, subdivisions=2)

# Shirt sleeves + arms, subtly bent inward to echo the concept pose.
for side in (-1, 1):
    x = 0.31 * side
    upper_rot = (math.radians(4), math.radians(-5 * side), math.radians(12 * side))
    cylinder(f"Sleeve_{side}", (x, 0.0, 1.00), 0.108, 0.285, MAT_SHIRT, rot=upper_rot, vertices=12, bevel_width=0.018)
    cylinder(f"Forearm_{side}", (0.345 * side, -0.055, 0.78), 0.070, 0.31, MAT_SKIN,
             rot=(math.radians(-8), math.radians(8 * side), math.radians(11 * side)), vertices=12, bevel_width=0.014)
    uv_ellipsoid(f"Hand_{side}", (0.355 * side, -0.105, 0.63), (0.085, 0.065, 0.10), MAT_SKIN, segments=16, rings=10)

cylinder("Neck", (0, 0.0, 1.17), 0.085, 0.14, MAT_SKIN, vertices=12, bevel_width=0.012)

# Terracotta neckerchief.
cylinder("ScarfWrap", (0, 0.0, 1.19), 0.112, 0.09, MAT_SCARF, vertices=16, bevel_width=0.010)
ellipsoid("ScarfKnot", (0, -0.132, 1.155), (0.065, 0.045, 0.055), MAT_SCARF, subdivisions=2)
triangle_cloth("ScarfTailL", [(-0.02, -0.150, 1.13), (-0.11, -0.148, 0.98), (0.005, -0.150, 1.00)], MAT_SCARF)
triangle_cloth("ScarfTailR", [(0.02, -0.151, 1.13), (0.12, -0.150, 1.02), (0.015, -0.151, 0.98)], MAT_SCARF)

# Face: large but human stylized head, readable eyes, soft cheeks.
uv_ellipsoid("Head", (0, -0.012, 1.39), (0.255, 0.215, 0.255), MAT_SKIN, segments=28, rings=16)
for side in (-1, 1):
    uv_ellipsoid(f"Ear_{side}", (0.245 * side, -0.005, 1.39), (0.055, 0.035, 0.075), MAT_SKIN, segments=14, rings=8)
    uv_ellipsoid(f"Cheek_{side}", (0.132 * side, -0.212, 1.33), (0.045, 0.012, 0.028), MAT_SKIN_BLUSH, segments=12, rings=8)
    x = 0.092 * side
    uv_ellipsoid(f"EyeWhite_{side}", (x, -0.214, 1.425), (0.062, 0.018, 0.077), MAT_EYE_WHITE, segments=16, rings=10)
    uv_ellipsoid(f"Iris_{side}", (x, -0.229, 1.425), (0.038, 0.011, 0.050), MAT_EYE, segments=14, rings=8)
    uv_ellipsoid(f"Pupil_{side}", (x, -0.238, 1.422), (0.019, 0.007, 0.028), MAT_PUPIL, segments=12, rings=8)
    uv_ellipsoid(f"EyeHighlight_{side}", (x - 0.010 * side, -0.244, 1.447), (0.008, 0.004, 0.010), MAT_EYE_WHITE, segments=10, rings=6)

curve_line("BrowL", [(-0.145, -0.226, 1.515), (-0.09, -0.239, 1.535), (-0.035, -0.228, 1.520)], MAT_HAIR, 0.010)
curve_line("BrowR", [(0.035, -0.228, 1.520), (0.09, -0.239, 1.535), (0.145, -0.226, 1.515)], MAT_HAIR, 0.010)
ellipsoid("Nose", (0, -0.232, 1.365), (0.030, 0.018, 0.028), MAT_SKIN, subdivisions=2)
curve_line("Smile", [(-0.055, -0.231, 1.305), (0, -0.242, 1.290), (0.060, -0.231, 1.308)], MAT_MOUTH, 0.008)

# Chunky asymmetric hair silhouette; forehead remains visible.
ellipsoid("HairBackMass", (0, 0.025, 1.545), (0.265, 0.218, 0.205), MAT_HAIR, subdivisions=2)
ellipsoid("HairCrown", (0.02, -0.01, 1.590), (0.225, 0.185, 0.145), MAT_HAIR, subdivisions=2)
hair_specs = [
    ("HairFrontL", (-0.135, -0.175, 1.545), (0.10, 0.06, 0.16), (math.radians(18), math.radians(-12), math.radians(-28)), MAT_HAIR_LIGHT),
    ("HairFrontC", (-0.035, -0.205, 1.575), (0.095, 0.055, 0.19), (math.radians(24), 0, math.radians(-10)), MAT_HAIR),
    ("HairFrontR", (0.085, -0.195, 1.565), (0.10, 0.06, 0.17), (math.radians(22), math.radians(8), math.radians(22)), MAT_HAIR_LIGHT),
    ("HairSideL", (-0.225, -0.085, 1.505), (0.075, 0.07, 0.145), (math.radians(-8), math.radians(8), math.radians(-36)), MAT_HAIR),
    ("HairSideR", (0.225, -0.070, 1.515), (0.078, 0.07, 0.145), (math.radians(-10), math.radians(-8), math.radians(34)), MAT_HAIR),
    ("HairTopL", (-0.085, 0.00, 1.695), (0.075, 0.06, 0.15), (math.radians(-10), math.radians(5), math.radians(-22)), MAT_HAIR_LIGHT),
    ("HairTopC", (0.015, -0.010, 1.715), (0.075, 0.055, 0.14), (math.radians(-5), 0, math.radians(2)), MAT_HAIR),
    ("HairTopR", (0.105, 0.005, 1.685), (0.070, 0.06, 0.135), (math.radians(-8), math.radians(-5), math.radians(26)), MAT_HAIR_LIGHT),
]
for name, loc, scale, rot, material in hair_specs:
    ellipsoid(name, loc, scale, material, subdivisions=2, rot=rot)
cone("HairTipL", (-0.205, -0.06, 1.655), 0.060, 0.012, 0.20, MAT_HAIR, rot=(math.radians(18), math.radians(6), math.radians(-48)), vertices=7)
cone("HairTipR", (0.205, -0.04, 1.645), 0.058, 0.012, 0.18, MAT_HAIR, rot=(math.radians(15), math.radians(-5), math.radians(46)), vertices=7)

# Backpack, bedroll, straps and valley leaf charm.
box("BackpackBody", (0, 0.205, 0.93), (0.39, 0.21, 0.49), MAT_BAG, bevel_width=0.055)
box("BackpackFlap", (0, 0.325, 1.045), (0.35, 0.055, 0.20), MAT_BAG_LIGHT, bevel_width=0.035)
box("BackpackPocket", (0, 0.325, 0.82), (0.25, 0.055, 0.15), MAT_BAG_LIGHT, bevel_width=0.030)
for side in (-1, 1):
    box(f"PackStrapFront_{side}", (0.175 * side, -0.115, 0.98), (0.045, 0.040, 0.47), MAT_BAG,
        rot=(0, 0, math.radians(10 * side)), bevel_width=0.014)
    ellipsoid(f"PackBuckle_{side}", (0.175 * side, -0.141, 0.82), (0.027, 0.012, 0.034), MAT_METAL, subdivisions=2)

cylinder("Bedroll", (0, 0.215, 1.245), 0.105, 0.39, MAT_BAG_LIGHT, rot=(0, math.radians(90), 0), vertices=14, bevel_width=0.015)
cylinder("BedrollBandL", (-0.10, 0.215, 1.245), 0.112, 0.030, MAT_BAG, rot=(0, math.radians(90), 0), vertices=14, bevel_width=0.008)
cylinder("BedrollBandR", (0.10, 0.215, 1.245), 0.112, 0.030, MAT_BAG, rot=(0, math.radians(90), 0), vertices=14, bevel_width=0.008)
curve_line("LeafCharmStem", [(0.205, 0.325, 0.88), (0.245, 0.35, 0.82), (0.265, 0.35, 0.76)], MAT_LEAF, 0.008)
ellipsoid("LeafCharmA", (0.273, 0.350, 0.79), (0.038, 0.012, 0.070), MAT_LEAF, subdivisions=2, rot=(math.radians(8), 0, math.radians(-28)))
ellipsoid("LeafCharmB", (0.235, 0.350, 0.745), (0.034, 0.011, 0.060), MAT_LEAF, subdivisions=2, rot=(math.radians(-8), 0, math.radians(32)))

# Soft normals for stylized lighting.
for obj in list(ROOT.children_recursive):
    if obj.type == 'MESH':
        for poly in obj.data.polygons:
            poly.use_smooth = True

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

print(f"Exported Lembah Sari Character Rework V2 to {OUT_PATH}")
