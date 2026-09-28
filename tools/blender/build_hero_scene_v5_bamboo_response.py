import math
import os
import sys

import bpy

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

# Continue from all accepted response gates through the paddy bund. This pass
# changes only the aged village bamboo material used by the garden fence.
import build_hero_scene_v5_paddy_bund_response  # noqa: F401,E402
import build_hero_scene_v5_ridge_texture as ridge_export  # noqa: E402
import build_hero_scene_v5_ground_texture as ground  # noqa: E402

OUT_PATH = os.path.abspath(
    os.environ.get(
        "LEMBAH_HERO_OUT",
        os.path.join(os.getcwd(), "assets", "models", "hero_scene_v5.glb"),
    )
)
os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)


def clamp(value, lo=0.0, hi=1.0):
    return max(lo, min(hi, value))


def bamboo_height(u, v, phase=0.23):
    """Soft longitudinal fibre only; geometry already provides bamboo segmentation."""
    tau = math.pi * 2.0
    return (
        math.sin((u * 18.0 + v * 2.2 + 0.31 + phase) * tau) * 0.46
        + math.sin((u * 31.0 - v * 3.0 + phase) * tau) * 0.20
        + math.sin((u * 2.10 + v * 1.35 + phase) * tau) * 0.11
        + math.sin((u * 4.40 - v * 2.30 + 0.27) * tau) * 0.06
    )


def build_bamboo_normal(name, size=256, derivative_strength=1.30):
    rows = []
    step = 1.0 / float(size)
    for py in range(size):
        v = py / float(size - 1)
        row = bytearray()
        for px in range(size):
            u = px / float(size - 1)
            h_l = bamboo_height((u - step) % 1.0, v)
            h_r = bamboo_height((u + step) % 1.0, v)
            h_d = bamboo_height(u, (v - step) % 1.0)
            h_u = bamboo_height(u, (v + step) % 1.0)
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
        raise RuntimeError("Generated aged-bamboo normal PNG is suspiciously small: %s" % path)
    image = bpy.data.images.load(path, check_existing=False)
    image.name = name
    image.colorspace_settings.name = "Non-Color"
    return image


def response_material(source, normal_image):
    material = source.copy()
    material.name = "Lembah Aged Bamboo Surface Response"
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    shader = nodes.get("Principled BSDF") or next(
        (node for node in nodes if node.type == "BSDF_PRINCIPLED"), None
    )
    if shader is None:
        raise RuntimeError("Aged-bamboo source material has no Principled shader")

    tex = nodes.new("ShaderNodeTexImage")
    tex.name = "Lembah Aged Bamboo Fibre Normal Texture"
    tex.image = normal_image
    tex.interpolation = "Linear"
    tex.extension = "REPEAT"

    normal = nodes.new("ShaderNodeNormalMap")
    normal.name = "Lembah Aged Bamboo Fibre Normal"
    normal.space = "TANGENT"
    normal.inputs["Strength"].default_value = 0.34
    links.new(tex.outputs["Color"], normal.inputs["Color"])
    links.new(normal.outputs["Normal"], shader.inputs["Normal"])

    shader.inputs["Roughness"].default_value = 0.88
    if "Specular IOR Level" in shader.inputs:
        shader.inputs["Specular IOR Level"].default_value = 0.12
    elif "Specular" in shader.inputs:
        shader.inputs["Specular"].default_value = 0.12
    if "Metallic" in shader.inputs:
        shader.inputs["Metallic"].default_value = 0.0
    return material


source_materials = [
    material for material in bpy.data.materials
    if material.name.startswith("Lembah Textured Aged Bamboo")
]
if len(source_materials) != 1:
    raise RuntimeError("Expected one aged-bamboo source material, got %d" % len(source_materials))
source = source_materials[0]

users = []
for obj in bpy.context.scene.objects:
    if obj.type != "MESH" or obj.hide_render:
        continue
    for slot_index, slot in enumerate(obj.material_slots):
        if slot.material is source or (
            slot.material is not None and slot.material.name.startswith("Lembah Textured Aged Bamboo")
        ):
            users.append((obj, slot_index))

if not users:
    raise RuntimeError("No visible meshes use the aged-bamboo material")

normal_image = build_bamboo_normal("Lembah Aged Bamboo Fibre Surface Normal")
material = response_material(source, normal_image)
for obj, slot_index in users:
    obj.material_slots[slot_index].material = material

ridge_export.select_v5_export_set()
bpy.ops.export_scene.gltf(
    filepath=OUT_PATH,
    export_format="GLB",
    use_selection=True,
    export_apply=True,
    export_yup=True,
)
print(
    "Aged bamboo response gate exported to %s (material slots=%d; fibre relief only)"
    % (OUT_PATH, len(users))
)
