import bpy
import math
import os
from mathutils import Vector

# Lembah Sari - Main House hero asset generator.
# Offline asset production only. Godot receives the exported GLB; gameplay never
# constructs this house from runtime primitives.

OUT_PATH = os.path.abspath(os.environ.get("LEMBAH_HOUSE_OUT", "assets/models/house_main_01.glb"))
os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)


def mat(name, color, roughness=0.72, metallic=0.0):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1.0)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    return m


MAT_WALL = mat("Plaster Warm Cream", (0.72, 0.58, 0.39), 0.88)
MAT_WALL_LIGHT = mat("Lime Wash Highlight", (0.88, 0.76, 0.55), 0.90)
MAT_WOOD_DARK = mat("Dark Teak", (0.19, 0.095, 0.045), 0.78)
MAT_WOOD = mat("Warm Teak", (0.38, 0.20, 0.095), 0.76)
MAT_WOOD_LIGHT = mat("Honey Wood", (0.57, 0.33, 0.16), 0.74)
MAT_TERRA = mat("Terracotta Tile", (0.52, 0.16, 0.095), 0.83)
MAT_TERRA_LIGHT = mat("Sunlit Terracotta", (0.70, 0.27, 0.15), 0.82)
MAT_GLASS = mat("Blue Green Glass", (0.22, 0.52, 0.56), 0.28)
MAT_BAMBOO = mat("Bamboo", (0.52, 0.45, 0.20), 0.84)
MAT_STONE = mat("Foundation Stone", (0.38, 0.34, 0.27), 0.92)
MAT_CLAY = mat("Clay Pot", (0.62, 0.24, 0.12), 0.86)
MAT_LEAF = mat("Plant Green", (0.22, 0.47, 0.19), 0.86)


def apply_material(obj, material):
    obj.data.materials.append(material)


def box(name, location, dimensions, material, rotation=(0, 0, 0), bevel=0.06):
    bpy.ops.mesh.primitive_cube_add(location=location, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dimensions
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel > 0:
        modifier = obj.modifiers.new("Soft edges", "BEVEL")
        modifier.width = bevel
        modifier.segments = 2
        modifier.limit_method = 'ANGLE'
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=modifier.name)
    apply_material(obj, material)
    return obj


def cylinder(name, location, radius, depth, material, rotation=(0, 0, 0), vertices=12, bevel=0.025):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=location, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    if bevel > 0:
        modifier = obj.modifiers.new("Soft edges", "BEVEL")
        modifier.width = bevel
        modifier.segments = 2
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=modifier.name)
    apply_material(obj, material)
    return obj


def sphere(name, location, scale, material):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=1.0, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    apply_material(obj, material)
    return obj


def roof_half(name, side):
    # Ridge runs along Y. Each roof half is a thick, softly beveled slab.
    angle = math.radians(29.0 * side)
    x = 1.74 * side
    z = 4.05
    return box(name, (x, 0.0, z), (4.15, 6.35, 0.22), MAT_TERRA, rotation=(0, angle, 0), bevel=0.08)


# Foundation and body ---------------------------------------------------------
box("StoneFoundation", (0, 0.05, 0.25), (7.55, 5.65, 0.50), MAT_STONE, bevel=0.10)
box("RaisedTimberBase", (0, 0.0, 0.58), (7.05, 5.20, 0.30), MAT_WOOD_DARK, bevel=0.07)
box("HouseBody", (0, 0.05, 2.05), (6.60, 4.70, 2.95), MAT_WALL, bevel=0.13)

# Front face is -Y.
front_y = -2.37
for x in (-2.70, -1.35, 0.0, 1.35, 2.70):
    box(f"FrontStud_{x}", (x, front_y - 0.06, 2.08), (0.13, 0.16, 2.72), MAT_WOOD_DARK, bevel=0.035)
box("FrontBeamTop", (0, front_y - 0.07, 3.27), (6.46, 0.18, 0.17), MAT_WOOD_DARK, bevel=0.035)
box("FrontBeamBottom", (0, front_y - 0.07, 0.90), (6.46, 0.18, 0.16), MAT_WOOD, bevel=0.035)

# Side timber rhythm.
for y in (-1.75, -0.65, 0.50, 1.62):
    box("SideStudL", (-3.31, y, 2.05), (0.15, 0.14, 2.65), MAT_WOOD_DARK, bevel=0.03)
    box("SideStudR", (3.31, y, 2.05), (0.15, 0.14, 2.65), MAT_WOOD_DARK, bevel=0.03)

# Door + windows + shutters ---------------------------------------------------
box("DoorFrame", (0.0, front_y - 0.13, 1.75), (1.32, 0.19, 2.30), MAT_WOOD_DARK, bevel=0.05)
box("DoorPanel", (0.0, front_y - 0.24, 1.72), (1.05, 0.11, 2.10), MAT_WOOD, bevel=0.055)
for z in (1.18, 1.72, 2.26):
    box("DoorInset", (0.0, front_y - 0.31, z), (0.78, 0.055, 0.34), MAT_WOOD_LIGHT, bevel=0.03)

for wx in (-2.0, 2.0):
    box("WindowFrame", (wx, front_y - 0.14, 2.05), (1.32, 0.18, 1.40), MAT_WOOD_DARK, bevel=0.045)
    box("WindowGlass", (wx, front_y - 0.245, 2.05), (1.05, 0.07, 1.12), MAT_GLASS, bevel=0.035)
    box("WindowMullionV", (wx, front_y - 0.29, 2.05), (0.07, 0.05, 1.07), MAT_WOOD_LIGHT, bevel=0.02)
    box("WindowMullionH", (wx, front_y - 0.29, 2.05), (1.02, 0.05, 0.07), MAT_WOOD_LIGHT, bevel=0.02)
    # Open shutters give silhouette and depth.
    box("ShutterL", (wx - 0.76, front_y - 0.26, 2.05), (0.54, 0.10, 1.22), MAT_WOOD, rotation=(0, 0, math.radians(13)), bevel=0.04)
    box("ShutterR", (wx + 0.76, front_y - 0.26, 2.05), (0.54, 0.10, 1.22), MAT_WOOD, rotation=(0, 0, math.radians(-13)), bevel=0.04)

# Roof ------------------------------------------------------------------------
roof_half("RoofLeft", -1)
roof_half("RoofRight", 1)
cylinder("RoofRidge", (0, 0, 5.08), 0.13, 6.20, MAT_TERRA_LIGHT, rotation=(math.radians(90), 0, 0), vertices=16, bevel=0.03)

# Tile ribs on the roof; actual geometry, not texture-only detail.
roof_slope = math.radians(29.0)
for side in (-1, 1):
    for i in range(7):
        # Positions step from ridge to eave.
        t = (i + 0.55) / 7.0
        x = side * (0.38 + t * 3.00)
        z = 4.93 - t * 1.62
        box("TileRib", (x, 0, z), (0.10, 6.30, 0.11), MAT_TERRA_LIGHT, rotation=(0, roof_slope * side, 0), bevel=0.035)

# Eave fascia and decorative gable timber.
for side in (-1, 1):
    box("EaveFascia", (side * 3.47, 0, 3.20), (0.17, 6.26, 0.24), MAT_WOOD_DARK, rotation=(0, roof_slope * side, 0), bevel=0.04)
box("GableCrossBeam", (0, -3.08, 3.35), (6.55, 0.15, 0.17), MAT_WOOD_DARK, bevel=0.035)
box("GableKingPost", (0, -3.09, 4.10), (0.15, 0.15, 1.55), MAT_WOOD_DARK, bevel=0.035)

# Porch -----------------------------------------------------------------------
box("PorchFloor", (0, -3.08, 0.82), (5.55, 1.65, 0.24), MAT_WOOD, bevel=0.07)
for x in (-2.35, 2.35):
    box("PorchPost", (x, -3.63, 2.05), (0.18, 0.18, 2.55), MAT_WOOD_DARK, bevel=0.04)
box("PorchBeam", (0, -3.63, 3.22), (5.05, 0.19, 0.19), MAT_WOOD_DARK, bevel=0.04)

# Small porch roof with broad overhang.
porch_angle = math.radians(-17)
box("PorchRoof", (0, -3.66, 3.58), (5.80, 2.05, 0.18), MAT_TERRA, rotation=(porch_angle, 0, 0), bevel=0.07)
for i in range(8):
    x = -2.45 + i * 0.70
    box("PorchTileRib", (x, -3.69, 3.63), (0.085, 2.00, 0.09), MAT_TERRA_LIGHT, rotation=(porch_angle, 0, 0), bevel=0.025)

# Steps are broad, asymmetrically dressed by props.
box("Step1", (0, -4.12, 0.47), (2.30, 0.60, 0.20), MAT_WOOD_LIGHT, bevel=0.05)
box("Step2", (0, -3.88, 0.62), (1.92, 0.54, 0.19), MAT_WOOD, bevel=0.05)

# Porch rails.
for x in (-2.25, 2.25):
    for z in (1.20, 1.55):
        box("PorchRail", (x * 0.55, -3.79, z), (2.05, 0.10, 0.10), MAT_WOOD_LIGHT, bevel=0.025)
for x in (-2.22, -1.25, 1.25, 2.22):
    box("PorchBaluster", (x, -3.79, 1.36), (0.09, 0.09, 0.72), MAT_WOOD_DARK, bevel=0.02)

# Bench.
box("BenchSeat", (1.60, -3.20, 1.12), (1.50, 0.50, 0.15), MAT_WOOD_LIGHT, bevel=0.05)
box("BenchBack", (1.60, -2.98, 1.55), (1.50, 0.13, 0.72), MAT_WOOD, rotation=(math.radians(-7), 0, 0), bevel=0.05)
for x in (1.05, 2.15):
    box("BenchLeg", (x, -3.20, 0.88), (0.12, 0.35, 0.48), MAT_WOOD_DARK, bevel=0.03)

# Bamboo side screen makes the house read more Indonesian/tropical.
for x in (-3.55, -3.28, -3.01, -2.74):
    cylinder("BambooScreen", (x, -2.85, 1.75), 0.055, 1.85, MAT_BAMBOO, vertices=10, bevel=0.018)
box("BambooScreenRail", (-3.15, -2.85, 1.80), (1.05, 0.11, 0.10), MAT_BAMBOO, bevel=0.025)

# Pots + plant by porch.
for idx, (px, py, sc) in enumerate([(-2.95, -3.85, 1.0), (2.90, -3.72, 0.82)]):
    cylinder(f"ClayPot{idx}", (px, py, 0.72), 0.28 * sc, 0.45 * sc, MAT_CLAY, vertices=16, bevel=0.035)
    sphere(f"PlantCrown{idx}", (px, py, 1.16), (0.42 * sc, 0.36 * sc, 0.34 * sc), MAT_LEAF)

# A few exposed roof support ends under the eaves.
for y in (-2.40, -1.20, 0.0, 1.20, 2.40):
    box("RafterTipL", (-3.52, y, 3.18), (0.34, 0.13, 0.13), MAT_WOOD_DARK, rotation=(0, roof_slope * -1, 0), bevel=0.025)
    box("RafterTipR", (3.52, y, 3.18), (0.34, 0.13, 0.13), MAT_WOOD_DARK, rotation=(0, roof_slope, 0), bevel=0.025)

# Apply transforms to all mesh objects and export as a single GLB scene.
for obj in bpy.context.scene.objects:
    if obj.type == 'MESH':
        obj.select_set(True)

bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.gltf(
    filepath=OUT_PATH,
    export_format='GLB',
    use_selection=True,
    export_apply=True,
    export_yup=True,
)

print(f"Exported Lembah Sari main house to {OUT_PATH}")
