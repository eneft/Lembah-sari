import math
import os
import sys

import bpy

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

# Continue strictly from every accepted response gate through natural mossy stone.
# This pass changes only the two large tropical-ground meshes; geometry, transforms,
# albedo, paths, paddies, rice and lighting stay locked.
import build_hero_scene_v5_rock_response  # noqa: F401,E402
import build_hero_scene_v5_ridge_texture as ridge_export  # noqa: E402
import build_hero_scene_v5_ground_texture as ground  # noqa: E402

OUT_PATH = os.path.abspath(
    os.environ.get(
        "LEMBAH_HERO_OUT",
        os.path.join(os.getcwd(), "assets", "models", "hero_scene_v5.glb"),
    )
)
os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)

TARGETS = ("SculptedVillageGround", "ExtendedVillageGround")


def clamp(value, lo=0.0, hi=1.0):
    return max(lo, min(hi, value))


def ground_height(u, v, phase=0.0):
    """Broad stylized turf/soil relief that reinforces the accepted ground albedo."""
    tau = math.pi * 2.0
    broad = (
        math.sin((u * 1.55 + v * 0.62 + phase) * tau) * 0.46
        + math.sin((u * 0.72 - v * 1.38 + phase * 0.7) * tau) * 0.30
        + math.sin((u * 2.65 + v * 2.15 + 0.19 + phase) * tau) * 0.16
    )
    fine = (
        math.sin((u * 12.0 + v * 7.0 + phase) * tau)
        * math.sin((u * 8.0 - v * 11.0 + 0.31) * tau)
    ) * 0.045
    return broad + fine


def build_ground_normal(name, phase=0.08, size=256, derivative_strength=1.15):
    rows = []
    step = 1.0 / float(size)
    for py in range(size):
        v = py / float(size - 1)
        row = bytearray()
        for px in range(size):
            u = px / float(size - 1)
            h_l = ground_height((u - step) % 1.0, v, phase)
            h_r = ground_height((u + step) % 1.0, v, phase)
            h_d = ground_height(u, (v - step) % 1.0, phase)
            h_u = ground_height(u, (v + step) % 1.0, phase)
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
        raise RuntimeError("Generated tropical-ground normal PNG is suspiciously small: %s" % path)
    image = bpy.data.images.load(path, check_existing=False)
    image.name = name
    image.colorspace_settings.name = "Non-Color"
    return image


def response_material(source, normal_image):
    material = source.copy()
    material.name = "V5 Tropical Ground Surface Response"
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    shader = nodes.get("Principled BSDF") or next(
        (node for node in nodes if node.type == "BSDF_PRINCIPLED"), None
    )
    if shader is None:
        raise RuntimeError("Tropical-ground source material has no Principled shader")

    tex = nodes.new("ShaderNodeTexImage")
    tex.name = "V5 Tropical Ground Normal Texture"
    tex.image = normal_image
    tex.interpolation = "Linear"
    tex.extension = "REPEAT"

    normal = nodes.new("ShaderNodeNormalMap")
    normal.name = "V5 Tropical Ground Normal"
    normal.space = "TANGENT"
    normal.inputs["Strength"].default_value = 0.30
    links.new(tex.outputs["Color"], normal.inputs["Color"])
    links.new(normal.outputs["Normal"], shader.inputs["Normal"])

    # Keep the ground dry/matte; only enough response for broad grazing-light breakup.
    shader.inputs["Roughness"].default_value = 0.91
    if "Specular IOR Level" in shader.inputs:
        shader.inputs["Specular IOR Level"].default_value = 0.13
    elif "Specular" in shader.inputs:
        shader.inputs["Specular"].default_value = 0.13
    if "Metallic" in shader.inputs:
        shader.inputs["Metallic"].default_value = 0.0
    return material


objects = []
source = None
for name in TARGETS:
    obj = bpy.data.objects.get(name)
    if obj is None or obj.type != "MESH" or obj.hide_render:
        raise RuntimeError("Expected visible tropical-ground mesh: %s" % name)
    if len(obj.data.materials) != 1 or obj.data.materials[0] is None:
        raise RuntimeError("Unexpected material layout on tropical-ground mesh: %s" % name)
    material = obj.data.materials[0]
    if not material.name.startswith("V5 Textured Tropical Ground"):
        raise RuntimeError("Unexpected tropical-ground source material on %s: %s" % (name, material.name))
    source = source or material
    objects.append(obj)

normal_image = build_ground_normal("Lembah Tropical Ground Surface Normal")
material = response_material(source, normal_image)
for obj in objects:
    obj.data.materials.clear()
    obj.data.materials.append(material)

ridge_export.select_v5_export_set()
bpy.ops.export_scene.gltf(
    filepath=OUT_PATH,
    export_format="GLB",
    use_selection=True,
    export_apply=True,
    export_yup=True,
)
print(
    "Tropical ground response gate exported to %s (objects=%d; normal response only)"
    % (OUT_PATH, len(objects))
)
