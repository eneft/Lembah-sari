import bpy
import math
import os

OUT_PATH = os.path.abspath(os.environ.get("LEMBAH_HOUSE_OUT", "assets/models/house_main_01.glb"))
os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Lembah Sari hero house — low-poly Indonesian village language.
# Big shapes do the silhouette; painted/procedural materials carry the detail.


def flat_mat(name, color, roughness=0.96):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    if "Specular IOR Level" in bsdf.inputs:
        bsdf.inputs["Specular IOR Level"].default_value = 0.16
    m.diffuse_color = (*color, 1.0)
    return m


def painted_mat(name, dark, light, scale=3.0, detail=2.0, roughness=0.98):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in nt.nodes:
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    tex = nt.nodes.new("ShaderNodeTexNoise")
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    tex.inputs["Scale"].default_value = scale
    tex.inputs["Detail"].default_value = detail
    tex.inputs["Roughness"].default_value = 0.62
    ramp.color_ramp.elements[0].color = (*dark, 1.0)
    ramp.color_ramp.elements[1].color = (*light, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    if "Specular IOR Level" in bsdf.inputs:
        bsdf.inputs["Specular IOR Level"].default_value = 0.14
    nt.links.new(tex.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    m.diffuse_color = (*light, 1.0)
    return m


WOOD = painted_mat("Painted kayu kampung", (0.22, 0.095, 0.032), (0.52, 0.285, 0.105), 2.8, 2.0)
WOOD_DARK = flat_mat("Kayu tua", (0.115, 0.043, 0.014))
WOOD_LIGHT = painted_mat("Kayu madu", (0.38, 0.185, 0.060), (0.67, 0.385, 0.145), 3.6, 1.6)
ROOF = painted_mat("Genteng tanah liat", (0.31, 0.055, 0.018), (0.72, 0.205, 0.065), 4.6, 2.2)
ROOF_DARK = flat_mat("Bayang genteng", (0.23, 0.035, 0.012))
STONE = painted_mat("Pondasi batu", (0.22, 0.20, 0.17), (0.42, 0.39, 0.32), 5.2, 2.0)
GLASS = flat_mat("Kaca hijau kebiruan", (0.10, 0.30, 0.29), 0.72)
BAMBOO = painted_mat("Anyaman bambu", (0.33, 0.255, 0.090), (0.66, 0.54, 0.22), 5.0, 1.6)
CLAY = flat_mat("Pot tanah liat", (0.53, 0.16, 0.045))
LEAF = flat_mat("Daun tropis", (0.14, 0.36, 0.11))


def apply_mat(obj, material):
    obj.data.materials.append(material)


def box(name, loc, dims, material, rot=(0, 0, 0), bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(location=loc, rotation=rot)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dims
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel > 0:
        mod = obj.modifiers.new("single soft edge", "BEVEL")
        mod.width = bevel
        mod.segments = 1
        mod.limit_method = 'ANGLE'
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=mod.name)
    apply_mat(obj, material)
    return obj


def cyl(name, loc, radius, depth, material, vertices=8):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=loc)
    obj = bpy.context.object
    obj.name = name
    apply_mat(obj, material)
    return obj


def ico(name, loc, scale, material):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=1.0, location=loc)
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
    faces = [(0, 2, 1), (3, 4, 5), (0, 1, 4, 3), (1, 2, 5, 4), (2, 0, 3, 5)]
    mesh = bpy.data.meshes.new(name + "Mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    apply_mat(obj, material)
    return obj


# Compact Indonesian kampung proportions — broad eaves, shallow depth, raised terrace.
W = 7.2
D = 2.55
FRONT = -D * 0.5

# Three primary masses only: stone foot, timber body, gable.
box("Pondasi", (0, 0.03, 0.26), (7.65, 2.95, 0.52), STONE, bevel=0.055)
box("BadanRumah", (0, 0.02, 1.92), (7.08, D, 2.65), WOOD, bevel=0.035)
triangle_prism("GevelKayu", 3.54, FRONT - 0.03, FRONT + 0.18, 3.22, 4.20, WOOD_LIGHT)

# Minimal structural accents: enough to read as Indonesian timber construction,
# not enough to turn into high-poly architecture.
for x in (-3.35, 0.0, 3.35):
    box("TiangFasad", (x, FRONT - 0.08, 1.98), (0.15, 0.11, 2.60), WOOD_DARK)
box("BalokAtas", (0, FRONT - 0.09, 3.17), (6.92, 0.12, 0.17), WOOD_DARK)
box("BalokBawah", (0, FRONT - 0.09, 0.72), (6.92, 0.12, 0.15), WOOD_DARK)

# Central wooden door and two generous shuttered windows.
door_x = -0.45
box("KusenPintu", (door_x, FRONT - 0.12, 1.70), (1.30, 0.10, 2.22), WOOD_DARK)
box("PintuKayu", (door_x, FRONT - 0.18, 1.70), (1.06, 0.055, 2.02), WOOD_LIGHT)

for wx in (-2.45, 1.95):
    box("KusenJendela", (wx, FRONT - 0.12, 2.02), (1.50, 0.10, 1.34), WOOD_DARK)
    box("KacaJendela", (wx, FRONT - 0.18, 2.02), (1.18, 0.045, 1.04), GLASS)
    # Indonesian wooden shutters, rendered as two simple slabs.
    box("DaunJendelaKiri", (wx - 0.79, FRONT - 0.16, 2.02), (0.40, 0.055, 1.16), WOOD_LIGHT,
        rot=(0, 0, math.radians(8)))
    box("DaunJendelaKanan", (wx + 0.79, FRONT - 0.16, 2.02), (0.40, 0.055, 1.16), WOOD_LIGHT,
        rot=(0, 0, math.radians(-8)))

# Simple ventilation motif in the timber gable — one graphic cue, no micro-detail.
for x in (-0.36, 0.0, 0.36):
    box("LubangAngin", (x, FRONT - 0.085, 3.68), (0.20, 0.04, 0.42), WOOD_DARK)

# Broad clay-tile roof. Detail belongs to material, not dozens of roof meshes.
roof_angle = math.radians(29)
box("AtapDepan", (0, -1.02, 3.65), (8.15, 2.48, 0.16), ROOF,
    rot=(roof_angle, 0, 0), bevel=0.035)
box("AtapBelakang", (0, 1.02, 3.65), (8.15, 2.48, 0.16), ROOF_DARK,
    rot=(-roof_angle, 0, 0), bevel=0.035)
box("Bubungan", (0, 0.0, 4.33), (7.85, 0.16, 0.18), ROOF, bevel=0.025)
box("LisAtap", (0, -2.18, 3.05), (8.16, 0.12, 0.18), WOOD_DARK)

# Teras depan: a defining Indonesian village-house cue.
porch_y = FRONT - 0.80
box("LantaiTeras", (0, porch_y, 0.70), (6.45, 1.18, 0.18), WOOD_LIGHT, bevel=0.025)
for x in (-2.78, 2.78):
    box("TiangTeras", (x, porch_y - 0.30, 1.88), (0.17, 0.17, 2.36), WOOD_DARK)
box("BalokTeras", (0, porch_y - 0.30, 2.96), (5.70, 0.15, 0.16), WOOD_DARK)

porch_angle = math.radians(13)
box("AtapTeras", (0, porch_y - 0.42, 3.24), (6.48, 1.42, 0.14), ROOF,
    rot=(porch_angle, 0, 0), bevel=0.025)

# Two chunky steps, intentionally simple for mobile readability.
box("AnakTanggaBawah", (door_x, porch_y - 0.92, 0.34), (2.10, 0.58, 0.18), STONE, bevel=0.02)
box("AnakTanggaAtas", (door_x, porch_y - 0.68, 0.52), (1.76, 0.48, 0.18), WOOD_LIGHT, bevel=0.02)

# One woven-bamboo side panel: strong local material cue with almost no geometry.
box("PanelAnyamanBambu", (-3.18, porch_y + 0.05, 1.55), (0.72, 0.05, 1.35), BAMBOO)

# Minimal tropical props. Low-sided primitives; no environment yet.
for idx, px in enumerate((-2.95, 2.95)):
    cyl(f"Pot{idx}", (px, porch_y - 0.43, 0.67), 0.22, 0.34, CLAY, vertices=8)
    ico(f"Tanaman{idx}", (px, porch_y - 0.43, 1.02), (0.34, 0.25, 0.30), LEAF)

# Keep the export block exact: render_main_house_sprite.py removes it when baking PNG.
bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.gltf(
    filepath=OUT_PATH,
    export_format='GLB',
    use_selection=True,
    export_apply=True,
    export_yup=True,
)
print(f"Exported low-poly Indonesian Lembah Sari house to {OUT_PATH}")
