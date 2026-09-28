import math
import os
import sys

import bpy

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

# Continue from all accepted response gates through aged bamboo. This pass
# changes only the compacted-earth village path and short house-wear strip.
import build_hero_scene_v5_bamboo_response  # noqa: F401,E402
import build_hero_scene_v5_ridge_texture as ridge_export  # noqa: E402
import build_hero_scene_v5_ground_texture as ground  # noqa: E402

OUT_PATH = os.path.abspath(
    os.environ.get(
        "LEMBAH_HERO_OUT",
        os.path.join(os.getcwd(), "assets", "models", "hero_scene_v5.glb"),
    )
)
os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)

TARGETS = ("V5VillagePath", "V5HouseWear")


def clamp(value, lo=0.0, hi=1.0):
    return max(lo, min(hi, value))


def dirt_height(u, v, phase=0.17):
    """Compacted earth relief aligned with the accepted broad dirt/streak albedo."""
    tau = math.pi * 2.0
    broad = (
        math.sin((u * 1.25 + v * 0.80 + phase) * tau) * 0.44
        + math.sin((u * 2.40 - v * 1.15 + 0.31) * tau) * 0.25
        + math.sin((u * 5.2 + v * 4.1 + 0.13) * tau) * 0.10
    )
    travel = -abs(math.sin((v * 7.0 + u * 0.65 + phase) * tau)) * 0.10
    grit = (
        math.sin((u * 18.0 + v * 11.0 + 0.37) * tau)
        * math.sin((u * 13.0 - v * 19.0 + 0.11) * tau)
    ) * 0.035
    return broad + travel + grit


def build_dirt_normal(name, size=256, derivative_strength=1.30):
    rows = []
    step = 1.0 / float(size)
    for py in range(size):
        v = py / float(size - 1)
        row = bytearray()
        for px in range(size):
            u = px / float(size - 1)
            h_l = dirt_height((u - step) % 1.0, v)
            h_r = dirt_height((u + step) % 1.0, v)
            h_d = dirt_height(u, (v - step) % 1.0)
            h_u = dirt_height(u, (v + step) % 1.0)
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
        raise RuntimeError("Generated village-dirt normal PNG is suspiciously small: %s" % path)
    image = bpy.data.images.load(path, check_existing=False)
    image.name = name
    image.colorspace_settings.name = "Non-Color"
    return image


def response_material(source, normal_image):
    material = source.copy()
    material.name = "V5 Village Dirt Surface Response"
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    shader = nodes.get("Principled BSDF") or next(
        (node for node in nodes if node.type == "BSDF_PRINCIPLED"), None
    )
    if shader is None:
        raise RuntimeError("Village-dirt source material has no Principled shader")

    tex = nodes.new("ShaderNodeTexImage")
    tex.name = "V5 Village Dirt Normal Texture"
    tex.image = normal_image
    tex.interpolation = "Linear"
    tex.extension = "REPEAT"

    normal = nodes.new("ShaderNodeNormalMap")
    normal.name = "V5 Village Dirt Normal"
    normal.space = "TANGENT"
    normal.inputs["Strength"].default_value = 0.30
    links.new(tex.outputs["Color"], normal.inputs["Color"])
    links.new(normal.outputs["Normal"], shader.inputs["Normal"])

    # Compacted village soil stays dry and very matte; the response only breaks
    # up broad grazing light so the path no longer reads as a flat painted strip.
    shader.inputs["Roughness"].default_value = 0.91
    if "Specular IOR Level" in shader.inputs:
        shader.inputs["Specular IOR Level"].default_value = 0.11
    elif "Specular" in shader.inputs:
        shader.inputs["Specular"].default_value = 0.11
    if "Metallic" in shader.inputs:
        shader.inputs["Metallic"].default_value = 0.0
    return material


objects = []
source = None
for name in TARGETS:
    obj = bpy.data.objects.get(name)
    if obj is None or obj.type != "MESH" or obj.hide_render:
        raise RuntimeError("Expected visible village-dirt mesh: %s" % name)
    if len(obj.data.materials) != 1 or obj.data.materials[0] is None:
        raise RuntimeError("Unexpected material layout on village-dirt mesh: %s" % name)
    current = obj.data.materials[0]
    if not current.name.startswith("V5 Textured Village Dirt"):
        raise RuntimeError("Unexpected village-dirt source material on %s: %s" % (name, current.name))
    source = source or current
    objects.append(obj)

normal_image = build_dirt_normal("Lembah Village Dirt Surface Normal")
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
    "Village dirt response gate exported to %s (objects=%d; compacted-earth relief only)"
    % (OUT_PATH, len(objects))
)
