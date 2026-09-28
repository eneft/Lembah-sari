import math
import os
import sys

import bpy

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

# Continue from all accepted response gates through tropical ground. This gate
# changes only the four paddy-bund meshes; paddy water, rice, garden beds and
# bamboo stay untouched.
import build_hero_scene_v5_ground_response  # noqa: F401,E402
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


def bund_height(u, v, phase=0.43):
    tau = math.pi * 2.0
    return (
        math.sin((u * 3.0 + v * 2.1 + phase) * tau) * 0.48
        + math.sin((u * 7.0 - v * 5.2 + 0.33) * tau) * 0.20
        + math.sin((u * 17.0 + v * 13.0 + 0.17) * tau) * 0.065
    )


def build_bund_normal(name, size=256, derivative_strength=1.25):
    rows = []
    step = 1.0 / float(size)
    for py in range(size):
        v = py / float(size - 1)
        row = bytearray()
        for px in range(size):
            u = px / float(size - 1)
            h_l = bund_height((u - step) % 1.0, v)
            h_r = bund_height((u + step) % 1.0, v)
            h_d = bund_height(u, (v - step) % 1.0)
            h_u = bund_height(u, (v + step) % 1.0)
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
        raise RuntimeError("Generated paddy-bund normal PNG is suspiciously small: %s" % path)
    image = bpy.data.images.load(path, check_existing=False)
    image.name = name
    image.colorspace_settings.name = "Non-Color"
    return image


def response_material(source, normal_image):
    material = source.copy()
    material.name = "V5 Paddy Bund Surface Response"
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    shader = nodes.get("Principled BSDF") or next(
        (node for node in nodes if node.type == "BSDF_PRINCIPLED"), None
    )
    if shader is None:
        raise RuntimeError("Paddy-bund source material has no Principled shader")

    tex = nodes.new("ShaderNodeTexImage")
    tex.name = "V5 Paddy Bund Normal Texture"
    tex.image = normal_image
    tex.interpolation = "Linear"
    tex.extension = "REPEAT"

    normal = nodes.new("ShaderNodeNormalMap")
    normal.name = "V5 Paddy Bund Normal"
    normal.space = "TANGENT"
    normal.inputs["Strength"].default_value = 0.34
    links.new(tex.outputs["Color"], normal.inputs["Color"])
    links.new(normal.outputs["Normal"], shader.inputs["Normal"])

    shader.inputs["Roughness"].default_value = 0.94
    if "Specular IOR Level" in shader.inputs:
        shader.inputs["Specular IOR Level"].default_value = 0.10
    elif "Specular" in shader.inputs:
        shader.inputs["Specular"].default_value = 0.10
    if "Metallic" in shader.inputs:
        shader.inputs["Metallic"].default_value = 0.0
    return material


bunds = sorted(
    [
        obj for obj in bpy.context.scene.objects
        if obj.type == "MESH" and obj.name.startswith("V5PaddyBund_") and not obj.hide_render
    ],
    key=lambda obj: obj.name,
)
if len(bunds) != 4:
    raise RuntimeError("Expected 4 visible V5 paddy-bund meshes, got %d" % len(bunds))

source = bunds[0].data.materials[0] if bunds[0].data.materials else None
if source is None or not source.name.startswith("V5 Textured Paddy Bund"):
    raise RuntimeError("Unexpected paddy-bund source material: %s" % (source.name if source else "<missing>"))

normal_image = build_bund_normal("Lembah Paddy Bund Surface Normal")
material = response_material(source, normal_image)
for obj in bunds:
    if not obj.data.materials or not obj.data.materials[0].name.startswith("V5 Textured Paddy Bund"):
        raise RuntimeError("Unexpected material on %s" % obj.name)
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
    "Paddy bund response gate exported to %s (bunds=%d; soil relief only)"
    % (OUT_PATH, len(bunds))
)
