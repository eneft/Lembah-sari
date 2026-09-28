import math
import os
import sys

import bpy

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

# Continue from every accepted response gate through the damp stream bank. This
# pass changes only the visible hero tree/palm/bush leaf materials; grass,
# flowers, rice, garden plants, geometry, placement and lighting stay untouched.
import build_hero_scene_v5_bank_response  # noqa: F401,E402
import build_hero_scene_v5_ridge_texture as ridge_export  # noqa: E402
import build_hero_scene_v5_ground_texture as ground  # noqa: E402

OUT_PATH = os.path.abspath(
    os.environ.get(
        "LEMBAH_HERO_OUT",
        os.path.join(os.getcwd(), "assets", "models", "hero_scene_v5.glb"),
    )
)
os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)

TARGET_PREFIXES = ("HeroTree_", "HeroPalm_", "HeroBush_")
LEAF_PREFIXES = ("Green", "DarkGreen")


def clamp(value, lo=0.0, hi=1.0):
    return max(lo, min(hi, value))


def foliage_height(u, v, phase=0.21):
    """Broad leaf-cluster relief that survives the fixed hero camera calmly."""
    tau = math.pi * 2.0
    broad = (
        math.sin((u * 1.70 + v * 1.05 + phase) * tau) * 0.34
        + math.sin((u * 3.25 - v * 2.30 + 0.31) * tau) * 0.16
    )
    folds = (
        math.sin((u * 6.40 + v * 1.35 + 0.57) * tau) * 0.070
        + math.sin((u * 2.10 + v * 6.80 + 0.11) * tau) * 0.045
    )
    return broad + folds


def build_foliage_normal(name, phase=0.21, size=256, derivative_strength=4.8):
    rows = []
    step = 1.0 / float(size)
    for py in range(size):
        v = py / float(size - 1)
        row = bytearray()
        for px in range(size):
            u = px / float(size - 1)
            h_l = foliage_height((u - step) % 1.0, v, phase)
            h_r = foliage_height((u + step) % 1.0, v, phase)
            h_d = foliage_height(u, (v - step) % 1.0, phase)
            h_u = foliage_height(u, (v + step) % 1.0, phase)
            dx = (h_r - h_l) * derivative_strength
            dy = (h_u - h_d) * derivative_strength
            nx, ny, nz = -dx, -dy, 1.0
            length = math.sqrt(nx * nx + ny * ny + nz * nz) or 1.0
            nx /= length
            ny /= length
            nz /= length
            row.extend(
                (
                    int(round(clamp(nx * 0.5 + 0.5) * 255.0)),
                    int(round(clamp(ny * 0.5 + 0.5) * 255.0)),
                    int(round(clamp(nz * 0.5 + 0.5) * 255.0)),
                )
            )
        rows.append(row)

    path = os.path.join("/tmp", name.lower().replace(" ", "_") + ".png")
    ground._write_rgb_png(path, size, size, rows)
    if os.path.getsize(path) <= 1024:
        raise RuntimeError("Generated tropical-foliage normal PNG is suspiciously small: %s" % path)
    image = bpy.data.images.load(path, check_existing=False)
    image.name = name
    image.colorspace_settings.name = "Non-Color"
    return image


def response_material(source, normal_image):
    material = source.copy()
    material.name = "V5 Tropical Foliage Surface Response " + source.name
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    shader = nodes.get("Principled BSDF") or next(
        (node for node in nodes if node.type == "BSDF_PRINCIPLED"), None
    )
    if shader is None:
        raise RuntimeError("Tropical foliage source material has no Principled shader: %s" % source.name)

    tex = nodes.new("ShaderNodeTexImage")
    tex.name = "V5 Tropical Foliage Normal Texture"
    tex.image = normal_image
    tex.interpolation = "Linear"
    tex.extension = "REPEAT"

    normal = nodes.new("ShaderNodeNormalMap")
    normal.name = "V5 Tropical Foliage Normal"
    normal.space = "TANGENT"
    normal.inputs["Strength"].default_value = 0.34
    links.new(tex.outputs["Color"], normal.inputs["Color"])
    links.new(normal.outputs["Normal"], shader.inputs["Normal"])

    # Leaves should catch soft morning light, but remain matte enough to avoid a
    # waxy/plastic canopy. The normal stays broad so low-poly facets remain calm.
    shader.inputs["Roughness"].default_value = 0.82
    if "Specular IOR Level" in shader.inputs:
        shader.inputs["Specular IOR Level"].default_value = 0.16
    elif "Specular" in shader.inputs:
        shader.inputs["Specular"].default_value = 0.16
    if "Metallic" in shader.inputs:
        shader.inputs["Metallic"].default_value = 0.0
    return material


targets = [
    obj
    for obj in bpy.context.scene.objects
    if obj.type == "MESH"
    and not obj.hide_render
    and obj.name.startswith(TARGET_PREFIXES)
]
if not targets:
    raise RuntimeError("No visible HeroTree/HeroPalm/HeroBush meshes found for foliage response")

meshes = {obj.data.as_pointer(): obj.data for obj in targets}
sources = []
seen_sources = set()
for mesh in meshes.values():
    for current in mesh.materials:
        if current is None or not current.name.startswith(LEAF_PREFIXES):
            continue
        key = current.as_pointer()
        if key in seen_sources:
            continue
        seen_sources.add(key)
        sources.append(current)

if not sources:
    raise RuntimeError("No Green/DarkGreen leaf materials found on hero foliage meshes")

normal_image = build_foliage_normal("Lembah Tropical Foliage Surface Normal")
replacements = {source.as_pointer(): response_material(source, normal_image) for source in sources}
replaced = 0
for mesh in meshes.values():
    for index, current in enumerate(mesh.materials):
        if current is None:
            continue
        replacement = replacements.get(current.as_pointer())
        if replacement is not None:
            mesh.materials[index] = replacement
            replaced += 1

if replaced == 0:
    raise RuntimeError("Tropical foliage response material replacement affected no slots")

ridge_export.select_v5_export_set()
bpy.ops.export_scene.gltf(
    filepath=OUT_PATH,
    export_format="GLB",
    use_selection=True,
    export_apply=True,
    export_yup=True,
)
print(
    "Tropical foliage surface response gate exported to %s (objects=%d; meshes=%d; source materials=%d; slots=%d)"
    % (OUT_PATH, len(targets), len(meshes), len(sources), replaced)
)
