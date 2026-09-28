import math
import os
import sys

import bpy

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

# Continue strictly from the accepted bridge-response gate. This pass changes
# only the shared natural mossy-stone material; geometry, transforms and albedo stay locked.
import build_hero_scene_v5_bridge_response  # noqa: F401,E402
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


def stone_height(u, v, phase=0.0):
    """Broad weathered stone relief with softer moss-scale breakup."""
    tau = math.pi * 2.0
    broad = (
        math.sin((u * 2.35 + v * 1.85 + phase) * tau) * 0.46
        + math.sin((u * 5.05 - v * 3.45 + 0.21) * tau) * 0.24
        + math.sin((u * 9.8 + v * 7.3 + 0.37) * tau) * 0.09
    )
    weather = (
        math.sin((u * 15.0 + v * 10.5 + phase * 0.7) * tau)
        * math.sin((u * 8.5 - v * 13.5 + 0.43) * tau)
    ) * 0.055
    return broad + weather


def build_stone_normal(name, phase=0.0, size=256, derivative_strength=0.95):
    rows = []
    step = 1.0 / float(size)
    for py in range(size):
        v = py / float(size - 1)
        row = bytearray()
        for px in range(size):
            u = px / float(size - 1)
            h_l = stone_height((u - step) % 1.0, v, phase)
            h_r = stone_height((u + step) % 1.0, v, phase)
            h_d = stone_height(u, (v - step) % 1.0, phase)
            h_u = stone_height(u, (v + step) % 1.0, phase)
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
        raise RuntimeError("Generated mossy-stone normal PNG is suspiciously small: %s" % path)
    image = bpy.data.images.load(path, check_existing=False)
    image.name = name
    image.colorspace_settings.name = "Non-Color"
    return image


def response_material(source, normal_image):
    material = source.copy()
    material.name = "V5 Natural Mossy Stone Surface Response"
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    shader = nodes.get("Principled BSDF") or next(
        (node for node in nodes if node.type == "BSDF_PRINCIPLED"), None
    )
    if shader is None:
        raise RuntimeError("Mossy-stone source material has no Principled shader")

    tex = nodes.new("ShaderNodeTexImage")
    tex.name = "V5 Mossy Stone Normal Texture"
    tex.image = normal_image
    tex.interpolation = "Linear"
    tex.extension = "REPEAT"

    normal = nodes.new("ShaderNodeNormalMap")
    normal.name = "V5 Mossy Stone Normal"
    normal.space = "TANGENT"
    normal.inputs["Strength"].default_value = 0.38
    links.new(tex.outputs["Color"], normal.inputs["Color"])
    links.new(normal.outputs["Normal"], shader.inputs["Normal"])

    # Natural river stones remain strongly matte; this only gives grazing light
    # enough response to reveal their weathered shape from the fixed camera.
    shader.inputs["Roughness"].default_value = 0.90
    if "Specular IOR Level" in shader.inputs:
        shader.inputs["Specular IOR Level"].default_value = 0.14
    elif "Specular" in shader.inputs:
        shader.inputs["Specular"].default_value = 0.14
    if "Metallic" in shader.inputs:
        shader.inputs["Metallic"].default_value = 0.0
    return material


rock_objects = []
source = None
for obj in bpy.context.scene.objects:
    if obj.type != "MESH" or obj.hide_render:
        continue
    for slot in obj.material_slots:
        material = slot.material
        if material is not None and material.name.startswith("Lembah Unified Natural Mossy Stone"):
            rock_objects.append(obj)
            source = source or material
            break

if source is None:
    raise RuntimeError("Accepted natural mossy-stone material was not found")
if len(rock_objects) < 10:
    raise RuntimeError("Expected many visible mossy-stone objects, got %d" % len(rock_objects))

normal_image = build_stone_normal("Lembah Natural Mossy Stone Normal", phase=0.18)
material = response_material(source, normal_image)

for obj in rock_objects:
    for index, slot in enumerate(obj.material_slots):
        if slot.material is not None and slot.material.name.startswith("Lembah Unified Natural Mossy Stone"):
            obj.material_slots[index].material = material

ridge_export.select_v5_export_set()
bpy.ops.export_scene.gltf(
    filepath=OUT_PATH,
    export_format="GLB",
    use_selection=True,
    export_apply=True,
    export_yup=True,
)
print(
    "Natural mossy-stone response gate exported to %s (objects=%d; normal response only)"
    % (OUT_PATH, len(rock_objects))
)
