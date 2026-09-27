import bpy
import math
import os

# Lembah Sari - Main House 2.5D hero asset generator.
# The house is intentionally designed for a fixed 3/4 orthographic camera:
# broad facade, compressed depth, oversized eaves, graphic material blocks.

OUT_PATH = os.path.abspath(os.environ.get("LEMBAH_HOUSE_OUT", "assets/models/house_main_01.glb"))
os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)


def mat(name, color, roughness=0.92, emission=0.035):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1.0)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (*color, 1.0)
        bsdf.inputs["Roughness"].default_value = roughness
        if "Specular" in bsdf.inputs:
            bsdf.inputs["Specular"].default_value = 0.22
        if "Specular IOR Level" in bsdf.inputs:
            bsdf.inputs["Specular IOR Level"].default_value = 0.22
        if "Emission" in bsdf.inputs:
            bsdf.inputs["Emission"].default_value = (*color, 1.0)
        if "Emission Color" in bsdf.inputs:
            bsdf.inputs["Emission Color"].default_value = (*color, 1.0)
        if "Emission Strength" in bsdf.inputs:
            bsdf.inputs["Emission Strength"].default_value = emission
    return m


# Graphic palette: warm village wood + terracotta + muted teal accents.
MAT_PANEL = mat("Sun Warm Timber Panel", (0.50, 0.29, 0.14))
MAT_PANEL_LIGHT = mat("Honey Timber Panel", (0.66, 0.40, 0.19))
MAT_FRAME = mat("Deep Teak Frame", (0.21, 0.105, 0.048))
MAT_FRAME_SOFT = mat("Warm Teak Frame", (0.32, 0.16, 0.07))
MAT_TERRA = mat("Soft Terracotta", (0.57, 0.19, 0.105), 0.95)
MAT_TERRA_LIGHT = mat("Sunlit Terracotta", (0.72, 0.30, 0.16), 0.95)
MAT_TERRA_DARK = mat("Terracotta Shadow", (0.40, 0.12, 0.07), 0.95)
MAT_GLASS = mat("Muted Teal Window", (0.20, 0.45, 0.46), 0.70, 0.055)
MAT_BAMBOO = mat("Dry Bamboo", (0.58, 0.48, 0.22), 0.96)
MAT_STONE = mat("Warm Foundation Stone", (0.40, 0.35, 0.28), 0.98)
MAT_CLAY = mat("Clay Pot", (0.65, 0.25, 0.12), 0.96)
MAT_LEAF = mat("Porch Plant Green", (0.23, 0.48, 0.20), 0.94)
MAT_CLOTH_A = mat("Faded Coral Cloth", (0.68, 0.31, 0.24), 0.98)
MAT_CLOTH_B = mat("Warm Cream Cloth", (0.82, 0.70, 0.49), 0.98)


def apply_material(obj, material):
    obj.data.materials.append(material)


def box(name, location, dimensions, material, rotation=(0, 0, 0), bevel=0.045):
    bpy.ops.mesh.primitive_cube_add(location=location, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dimensions
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel > 0:
        mod = obj.modifiers.new("Soft graphic edge", "BEVEL")
        mod.width = bevel
        mod.segments = 2
        mod.limit_method = 'ANGLE'
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=mod.name)
    apply_material(obj, material)
    return obj


def cylinder(name, location, radius, depth, material, rotation=(0, 0, 0), vertices=12, bevel=0.02):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=location, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    if bevel > 0:
        mod = obj.modifiers.new("Soft graphic edge", "BEVEL")
        mod.width = bevel
        mod.segments = 2
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=mod.name)
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


# -----------------------------------------------------------------------------
# PROPORTION RULE: wide facade, shallow body. This is deliberate forced
# perspective for the game's fixed 3/4 camera and is not intended as a realistic
# architectural model.
# -----------------------------------------------------------------------------
HOUSE_W = 7.60
HOUSE_D = 2.95
BODY_H = 2.65
FRONT_Y = -(HOUSE_D * 0.5)

# Raised base / silhouette.
box("StoneFooting", (0.0, 0.05, 0.24), (8.00, 3.45, 0.48), MAT_STONE, bevel=0.09)
box("RaisedWoodBase", (0.0, 0.00, 0.56), (7.62, 3.15, 0.30), MAT_FRAME, bevel=0.06)
box("HouseBody", (0.0, 0.04, 2.00), (7.28, HOUSE_D, BODY_H), MAT_PANEL, bevel=0.09)

# Front wall panel bands create a hand-painted/illustrative read rather than one
# flat rectangular wall. They are deliberately broad and visible at game scale.
for i, z in enumerate((1.02, 1.38, 1.74, 2.10, 2.46, 2.82)):
    panel_mat = MAT_PANEL_LIGHT if i % 2 == 0 else MAT_PANEL
    box(f"FacadePanel_{i}", (0.0, FRONT_Y - 0.055, z), (7.05, 0.075, 0.27), panel_mat, bevel=0.018)

# Timber frame reads strongly from a fixed camera.
for x in (-3.45, -2.30, -1.12, 0.05, 1.22, 2.38, 3.45):
    box("FrontPost", (x, FRONT_Y - 0.12, 2.00), (0.14, 0.16, 2.72), MAT_FRAME, bevel=0.028)
box("FrontTopBeam", (0.0, FRONT_Y - 0.12, 3.23), (7.12, 0.17, 0.19), MAT_FRAME, bevel=0.03)
box("FrontBottomBeam", (0.0, FRONT_Y - 0.12, 0.86), (7.12, 0.17, 0.17), MAT_FRAME_SOFT, bevel=0.03)

# Side wall is deliberately simpler: only enough geometry to sell the 3/4 view.
for y in (-0.92, 0.0, 0.92):
    box("SidePostL", (-3.65, y, 2.00), (0.15, 0.13, 2.60), MAT_FRAME, bevel=0.025)
    box("SidePostR", (3.65, y, 2.00), (0.15, 0.13, 2.60), MAT_FRAME, bevel=0.025)

# Asymmetrical facade: slightly off-center door and two generous windows.
door_x = -0.55
box("DoorFrame", (door_x, FRONT_Y - 0.17, 1.77), (1.30, 0.19, 2.28), MAT_FRAME, bevel=0.045)
box("DoorPanel", (door_x, FRONT_Y - 0.28, 1.73), (1.05, 0.10, 2.05), MAT_FRAME_SOFT, bevel=0.045)
for z in (1.17, 1.72, 2.27):
    box("DoorInset", (door_x, FRONT_Y - 0.345, z), (0.78, 0.045, 0.32), MAT_PANEL_LIGHT, bevel=0.02)

for wx in (-2.45, 1.82):
    box("WindowOuterFrame", (wx, FRONT_Y - 0.18, 2.08), (1.52, 0.18, 1.52), MAT_FRAME, bevel=0.04)
    box("WindowGlass", (wx, FRONT_Y - 0.29, 2.08), (1.20, 0.065, 1.20), MAT_GLASS, bevel=0.025)
    box("WindowMullionV", (wx, FRONT_Y - 0.335, 2.08), (0.065, 0.045, 1.14), MAT_PANEL_LIGHT, bevel=0.014)
    box("WindowMullionH", (wx, FRONT_Y - 0.335, 2.08), (1.14, 0.045, 0.065), MAT_PANEL_LIGHT, bevel=0.014)
    # Wide open shutters exaggerate the facade silhouette.
    box("ShutterL", (wx - 0.86, FRONT_Y - 0.26, 2.08), (0.55, 0.09, 1.30), MAT_FRAME_SOFT,
        rotation=(0, 0, math.radians(12)), bevel=0.035)
    box("ShutterR", (wx + 0.86, FRONT_Y - 0.26, 2.08), (0.55, 0.09, 1.30), MAT_FRAME_SOFT,
        rotation=(0, 0, math.radians(-12)), bevel=0.035)

# Broad gable roof. Ridge runs along X so the elevated camera sees a large,
# graphic terracotta roof plane similar to the concept illustration.
roof_angle = math.radians(31.0)
roof_width = 8.45
roof_half_depth = 2.72
ridge_z = 4.56
front_roof_y = -1.17
back_roof_y = 1.17
box("RoofFront", (0.0, front_roof_y, 3.88), (roof_width, roof_half_depth, 0.20), MAT_TERRA,
    rotation=(roof_angle, 0, 0), bevel=0.07)
box("RoofBack", (0.0, back_roof_y, 3.88), (roof_width, roof_half_depth, 0.20), MAT_TERRA_DARK,
    rotation=(-roof_angle, 0, 0), bevel=0.07)
cylinder("RoofRidge", (0.0, 0.0, ridge_z), 0.13, 8.10, MAT_TERRA_LIGHT,
         rotation=(0, math.radians(90), 0), vertices=16, bevel=0.025)

# Tile rows on the front roof plane: horizontal graphic bands, not realistic
# individual tiles. This is intentional for the semi-2D read.
for i in range(7):
    t = (i + 0.5) / 7.0
    y = -0.24 - t * 2.05
    z = 4.43 - t * 1.33
    box("FrontTileBand", (0.0, y, z), (8.22, 0.085, 0.085), MAT_TERRA_LIGHT,
        rotation=(roof_angle, 0, 0), bevel=0.018)

# Strong fascia trims make the roof read as a single illustrated silhouette.
box("FrontEaveFascia", (0.0, -2.48, 3.16), (8.50, 0.15, 0.22), MAT_FRAME, bevel=0.035)
box("BackEaveFascia", (0.0, 2.48, 3.16), (8.50, 0.15, 0.22), MAT_FRAME_SOFT, bevel=0.035)

# Porch is wide and shallow, visually part of the facade rather than a separate
# 3D volume.
porch_y = FRONT_Y - 0.88
box("PorchFloor", (0.0, porch_y, 0.82), (6.55, 1.34, 0.22), MAT_FRAME_SOFT, bevel=0.055)
for x in (-2.82, 2.82):
    box("PorchPost", (x, porch_y - 0.38, 2.00), (0.17, 0.17, 2.48), MAT_FRAME, bevel=0.035)
box("PorchBeam", (0.0, porch_y - 0.38, 3.13), (5.90, 0.17, 0.18), MAT_FRAME, bevel=0.035)

# Lower front awning, broad and simplified.
porch_angle = math.radians(16.0)
box("PorchAwning", (0.0, porch_y - 0.46, 3.47), (6.70, 1.55, 0.16), MAT_TERRA,
    rotation=(porch_angle, 0, 0), bevel=0.055)
for x in (-2.55, -1.70, -0.85, 0.0, 0.85, 1.70, 2.55):
    box("AwningRib", (x, porch_y - 0.46, 3.50), (0.075, 1.48, 0.075), MAT_TERRA_LIGHT,
        rotation=(porch_angle, 0, 0), bevel=0.016)

# Broad, offset steps align with the door.
box("StepLower", (door_x, porch_y - 1.02, 0.44), (2.35, 0.58, 0.18), MAT_PANEL_LIGHT, bevel=0.045)
box("StepUpper", (door_x, porch_y - 0.77, 0.60), (1.95, 0.52, 0.18), MAT_FRAME_SOFT, bevel=0.045)

# Short porch rails only at the outer edges: keeps the doorway readable.
for side in (-1, 1):
    rail_x = 2.10 * side
    box("PorchRailTop", (rail_x, porch_y - 0.60, 1.43), (1.18, 0.09, 0.09), MAT_PANEL_LIGHT, bevel=0.02)
    box("PorchRailLow", (rail_x, porch_y - 0.60, 1.12), (1.18, 0.09, 0.09), MAT_FRAME_SOFT, bevel=0.02)
    for offset in (-0.42, 0.0, 0.42):
        box("PorchBaluster", (rail_x + offset, porch_y - 0.60, 1.28), (0.07, 0.07, 0.62), MAT_FRAME, bevel=0.014)

# Bench and simple household accents.
box("BenchSeat", (1.85, porch_y + 0.04, 1.08), (1.55, 0.43, 0.13), MAT_PANEL_LIGHT, bevel=0.04)
box("BenchBack", (1.85, porch_y + 0.25, 1.50), (1.55, 0.11, 0.70), MAT_FRAME_SOFT,
    rotation=(math.radians(-6), 0, 0), bevel=0.04)
for x in (1.30, 2.40):
    box("BenchLeg", (x, porch_y + 0.03, 0.86), (0.11, 0.30, 0.44), MAT_FRAME, bevel=0.02)

# Bamboo lattice on one side gives a tropical Indonesian identity.
for x in (-3.48, -3.23, -2.98, -2.73):
    cylinder("BambooScreen", (x, porch_y - 0.03, 1.74), 0.047, 1.72, MAT_BAMBOO, vertices=10, bevel=0.014)
box("BambooScreenRailTop", (-3.10, porch_y - 0.03, 2.18), (1.00, 0.085, 0.085), MAT_BAMBOO, bevel=0.02)
box("BambooScreenRailBottom", (-3.10, porch_y - 0.03, 1.28), (1.00, 0.085, 0.085), MAT_BAMBOO, bevel=0.02)

# Two soft cloth planes break the rigid architecture and reinforce the
# illustration-like silhouette.
box("HangingClothA", (3.05, FRONT_Y - 0.24, 2.18), (0.55, 0.055, 1.00), MAT_CLOTH_A,
    rotation=(0, 0, math.radians(-5)), bevel=0.025)
box("HangingClothB", (3.48, FRONT_Y - 0.22, 2.05), (0.42, 0.055, 0.82), MAT_CLOTH_B,
    rotation=(0, 0, math.radians(4)), bevel=0.025)

# Pots and plants frame the porch without relying on environment geometry.
for idx, (px, py, sc) in enumerate([(-3.25, porch_y - 0.62, 1.0), (3.15, porch_y - 0.52, 0.82)]):
    cylinder(f"ClayPot{idx}", (px, py, 0.70), 0.27 * sc, 0.43 * sc, MAT_CLAY, vertices=14, bevel=0.03)
    sphere(f"PlantCrown{idx}", (px, py, 1.13), (0.40 * sc, 0.30 * sc, 0.36 * sc), MAT_LEAF)
    sphere(f"PlantCrownB{idx}", (px + 0.18 * sc, py, 1.26), (0.24 * sc, 0.20 * sc, 0.24 * sc), MAT_LEAF)

# Small rafter ends under front eave create depth without making the body deep.
for x in (-3.2, -2.1, -1.0, 0.1, 1.2, 2.3, 3.4):
    box("RafterTip", (x, -2.43, 3.12), (0.12, 0.34, 0.11), MAT_FRAME, bevel=0.018)

# Export as one GLB. Only the asset is 3D; the presentation camera is orthographic
# to preserve the intended 2.5D concept feel.
bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.gltf(
    filepath=OUT_PATH,
    export_format='GLB',
    use_selection=True,
    export_apply=True,
    export_yup=True,
)

print(f"Exported Lembah Sari 2.5D hero house to {OUT_PATH}")
