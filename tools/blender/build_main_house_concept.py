import bpy
import math
import os

OUT_PATH = os.path.abspath(os.environ.get("LEMBAH_HOUSE_OUT", "assets/models/house_main_01.glb"))
os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)


def mat(name, color, roughness=0.94):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1.0)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (*color, 1.0)
        bsdf.inputs["Roughness"].default_value = roughness
        if "Specular" in bsdf.inputs:
            bsdf.inputs["Specular"].default_value = 0.18
        if "Specular IOR Level" in bsdf.inputs:
            bsdf.inputs["Specular IOR Level"].default_value = 0.18
    return m


WOOD = mat("Warm timber", (0.32, 0.16, 0.065))
WOOD_LIGHT = mat("Honey timber", (0.48, 0.26, 0.105))
WOOD_DARK = mat("Deep teak", (0.115, 0.045, 0.018))
BAMBOO = mat("Bamboo", (0.48, 0.39, 0.16))
ROOF = mat("Terracotta", (0.34, 0.055, 0.022))
ROOF_LIGHT = mat("Terracotta highlight", (0.50, 0.115, 0.042))
ROOF_DARK = mat("Terracotta shade", (0.21, 0.03, 0.012))
GLASS = mat("Muted teal glass", (0.12, 0.34, 0.35), 0.72)
STONE = mat("Foundation", (0.29, 0.26, 0.22), 0.98)
CLAY = mat("Clay pot", (0.47, 0.14, 0.055), 0.96)
LEAF = mat("Porch green", (0.17, 0.36, 0.14), 0.94)
CLOTH = mat("Faded coral", (0.55, 0.20, 0.14), 0.98)


def apply_mat(obj, material):
    obj.data.materials.append(material)


def box(name, loc, dims, material, rot=(0, 0, 0), bevel=0.04):
    bpy.ops.mesh.primitive_cube_add(location=loc, rotation=rot)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dims
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel > 0:
        mod = obj.modifiers.new("soft edge", "BEVEL")
        mod.width = bevel
        mod.segments = 2
        mod.limit_method = 'ANGLE'
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=mod.name)
    apply_mat(obj, material)
    return obj


def cyl(name, loc, radius, depth, material, rot=(0, 0, 0), vertices=12, bevel=0.018):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=loc, rotation=rot)
    obj = bpy.context.object
    obj.name = name
    if bevel > 0:
        mod = obj.modifiers.new("soft edge", "BEVEL")
        mod.width = bevel
        mod.segments = 2
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=mod.name)
    apply_mat(obj, material)
    return obj


def ico(name, loc, scale, material):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=1.0, location=loc)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    apply_mat(obj, material)
    return obj


def triangle_prism(name, half_width, y_front, y_back, z_base, z_peak, material):
    verts = [
        (-half_width, y_front, z_base), (half_width, y_front, z_base), (0.0, y_front, z_peak),
        (-half_width, y_back, z_base), (half_width, y_back, z_base), (0.0, y_back, z_peak),
    ]
    faces = [
        (0, 2, 1), (3, 4, 5),
        (0, 1, 4, 3), (1, 2, 5, 4), (2, 0, 3, 5),
    ]
    mesh = bpy.data.meshes.new(name + "Mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    apply_mat(obj, material)
    return obj


# Forced-perspective proportions for a fixed 3/4 orthographic camera.
W = 7.8
D = 2.75
FRONT = -D * 0.5

# Base and shallow body.
box("Foundation", (0, 0, 0.24), (8.15, 3.20, 0.48), STONE, bevel=0.08)
box("RaisedBase", (0, 0, 0.55), (7.72, 3.00, 0.28), WOOD_DARK, bevel=0.055)
box("Body", (0, 0.03, 1.98), (7.35, D, 2.62), WOOD, bevel=0.075)

# Broad horizontal timber boards = graphic facade, readable like illustration.
for i, z in enumerate((0.98, 1.32, 1.66, 2.00, 2.34, 2.68, 3.02)):
    m = WOOD_LIGHT if i % 2 == 0 else WOOD
    box("FacadeBoard", (0, FRONT - 0.055, z), (7.12, 0.07, 0.255), m, bevel=0.014)

# Dark timber frame.
for x in (-3.48, -2.35, -1.15, 0.05, 1.25, 2.42, 3.48):
    box("FrontPost", (x, FRONT - 0.12, 2.00), (0.135, 0.15, 2.70), WOOD_DARK, bevel=0.025)
box("TopBeam", (0, FRONT - 0.12, 3.21), (7.18, 0.16, 0.18), WOOD_DARK, bevel=0.026)
box("BottomBeam", (0, FRONT - 0.12, 0.86), (7.18, 0.16, 0.16), WOOD_DARK, bevel=0.026)

# Side rhythm only where camera can read it.
for y in (-0.88, 0.0, 0.88):
    box("SidePost", (-3.69, y, 1.98), (0.14, 0.13, 2.56), WOOD_DARK, bevel=0.022)

# Filled timber gable: no empty/white triangle.
triangle_prism("FrontGable", 3.66, FRONT - 0.10, FRONT + 0.12, 3.20, 4.46, WOOD_LIGHT)
box("GableCrossBeam", (0, FRONT - 0.18, 3.25), (7.24, 0.13, 0.16), WOOD_DARK, bevel=0.022)
box("GableKingPost", (0, FRONT - 0.18, 3.82), (0.13, 0.13, 1.18), WOOD_DARK, bevel=0.022)
for x, z in ((-0.42, 3.86), (0.0, 3.94), (0.42, 3.86)):
    box("GableVent", (x, FRONT - 0.185, z), (0.22, 0.045, 0.44), WOOD_DARK, bevel=0.012)

# Asymmetrical facade.
door_x = -0.52
box("DoorFrame", (door_x, FRONT - 0.18, 1.75), (1.28, 0.18, 2.25), WOOD_DARK, bevel=0.04)
box("Door", (door_x, FRONT - 0.29, 1.71), (1.03, 0.095, 2.03), WOOD, bevel=0.04)
for z in (1.18, 1.72, 2.24):
    box("DoorInset", (door_x, FRONT - 0.345, z), (0.77, 0.04, 0.30), WOOD_LIGHT, bevel=0.016)

for wx in (-2.42, 1.86):
    box("WindowFrame", (wx, FRONT - 0.18, 2.04), (1.48, 0.18, 1.46), WOOD_DARK, bevel=0.035)
    box("WindowGlass", (wx, FRONT - 0.285, 2.04), (1.16, 0.055, 1.14), GLASS, bevel=0.02)
    box("MullionV", (wx, FRONT - 0.33, 2.04), (0.06, 0.04, 1.10), WOOD_LIGHT, bevel=0.012)
    box("MullionH", (wx, FRONT - 0.33, 2.04), (1.10, 0.04, 0.06), WOOD_LIGHT, bevel=0.012)
    box("ShutterL", (wx - 0.84, FRONT - 0.26, 2.04), (0.52, 0.085, 1.24), WOOD,
        rot=(0, 0, math.radians(11)), bevel=0.03)
    box("ShutterR", (wx + 0.84, FRONT - 0.26, 2.04), (0.52, 0.085, 1.24), WOOD,
        rot=(0, 0, math.radians(-11)), bevel=0.03)

# Roof ridge runs across facade; camera sees a broad terracotta plane.
roof_angle = math.radians(31)
box("RoofFront", (0, -1.14, 3.86), (8.55, 2.74, 0.20), ROOF, rot=(roof_angle, 0, 0), bevel=0.06)
box("RoofBack", (0, 1.14, 3.86), (8.55, 2.74, 0.20), ROOF_DARK, rot=(-roof_angle, 0, 0), bevel=0.06)
cyl("RoofRidge", (0, 0, 4.55), 0.12, 8.18, ROOF_LIGHT, rot=(0, math.radians(90), 0), vertices=16)

# Graphic tile strips down the visible roof slope.
for x in (-3.65, -2.75, -1.85, -0.95, -0.05, 0.85, 1.75, 2.65, 3.55):
    box("RoofTileRib", (x, -1.14, 3.88), (0.075, 2.62, 0.075), ROOF_LIGHT,
        rot=(roof_angle, 0, 0), bevel=0.014)
box("FrontFascia", (0, -2.48, 3.14), (8.56, 0.14, 0.21), WOOD_DARK, bevel=0.03)

# Shallow veranda integrated with facade.
porch_y = FRONT - 0.88
box("PorchFloor", (0, porch_y, 0.82), (6.62, 1.30, 0.21), WOOD, bevel=0.05)
for x in (-2.86, 2.86):
    box("PorchPost", (x, porch_y - 0.36, 1.98), (0.17, 0.17, 2.43), WOOD_DARK, bevel=0.03)
box("PorchBeam", (0, porch_y - 0.36, 3.10), (5.98, 0.17, 0.17), WOOD_DARK, bevel=0.03)

porch_angle = math.radians(15)
box("PorchRoof", (0, porch_y - 0.46, 3.43), (6.78, 1.50, 0.16), ROOF,
    rot=(porch_angle, 0, 0), bevel=0.05)
for x in (-2.55, -1.70, -0.85, 0, 0.85, 1.70, 2.55):
    box("PorchRoofRib", (x, porch_y - 0.46, 3.46), (0.07, 1.44, 0.07), ROOF_LIGHT,
        rot=(porch_angle, 0, 0), bevel=0.012)

# Offset steps.
box("Step1", (door_x, porch_y - 1.00, 0.43), (2.30, 0.56, 0.18), WOOD_LIGHT, bevel=0.04)
box("Step2", (door_x, porch_y - 0.76, 0.59), (1.92, 0.50, 0.18), WOOD, bevel=0.04)

# Porch rails on edges only.
for side in (-1, 1):
    rx = 2.08 * side
    box("RailTop", (rx, porch_y - 0.58, 1.42), (1.16, 0.085, 0.085), WOOD_LIGHT, bevel=0.018)
    box("RailLow", (rx, porch_y - 0.58, 1.12), (1.16, 0.085, 0.085), WOOD_DARK, bevel=0.018)
    for off in (-0.40, 0, 0.40):
        box("Baluster", (rx + off, porch_y - 0.58, 1.27), (0.065, 0.065, 0.60), WOOD_DARK, bevel=0.012)

# Bench, bamboo screen, hanging cloth: visual storytelling without environment.
box("BenchSeat", (1.82, porch_y + 0.02, 1.07), (1.48, 0.40, 0.13), WOOD_LIGHT, bevel=0.035)
box("BenchBack", (1.82, porch_y + 0.21, 1.48), (1.48, 0.10, 0.66), WOOD, rot=(math.radians(-6), 0, 0), bevel=0.035)
for x in (1.30, 2.34):
    box("BenchLeg", (x, porch_y + 0.02, 0.86), (0.10, 0.28, 0.42), WOOD_DARK, bevel=0.018)

for x in (-3.50, -3.25, -3.00, -2.75):
    cyl("BambooScreen", (x, porch_y - 0.02, 1.72), 0.045, 1.68, BAMBOO, vertices=10)
box("BambooRail", (-3.12, porch_y - 0.02, 1.78), (1.02, 0.08, 0.08), BAMBOO, bevel=0.016)
box("HangingCloth", (3.10, FRONT - 0.22, 2.08), (0.52, 0.05, 0.92), CLOTH, rot=(0, 0, math.radians(-5)), bevel=0.02)

for idx, (px, py, sc) in enumerate([(-3.22, porch_y - 0.58, 1.0), (3.12, porch_y - 0.50, 0.82)]):
    cyl(f"Pot{idx}", (px, py, 0.69), 0.26 * sc, 0.42 * sc, CLAY, vertices=14, bevel=0.025)
    ico(f"Plant{idx}", (px, py, 1.10), (0.38 * sc, 0.28 * sc, 0.33 * sc), LEAF)

# Rafter tips beneath visible eave.
for x in (-3.2, -2.1, -1.0, 0.1, 1.2, 2.3, 3.4):
    box("RafterTip", (x, -2.43, 3.10), (0.11, 0.32, 0.10), WOOD_DARK, bevel=0.015)

bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.gltf(
    filepath=OUT_PATH,
    export_format='GLB',
    use_selection=True,
    export_apply=True,
    export_yup=True,
)
print(f"Exported concept-first Lembah Sari house to {OUT_PATH}")
