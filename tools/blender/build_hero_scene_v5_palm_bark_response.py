import math
import os
import sys

import bpy

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

# Continue from every accepted response gate through common-tree bark. This pass
# changes only the palm-trunk material shared by the PalmTree_2 placed meshes.
import build_hero_scene_v5_tree_bark_response  # noqa: F401,E402
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


def palm_height(u, v, phase=0.19):
    """Dry palm-fibre relief; broad longitudinal grain with soft age breakup."""
    tau = math.pi * 2.0
    longitudinal = (
        math.sin((u * 9.0 + v * 0.75 + phase) * tau) * 0.42
        + math.sin((u * 19.0 - v * 0.55 + 0.31) * tau) * 0.18
        + math.sin((u * 33.0 + v * 1.10 + 0.57) * tau) * 0.065
    )
    broad = (
        math.sin((u * 2.3 + v * 2.4 + 0.11) * tau) * 0.16
        + math.sin((u * 4.1 - v * 3.2 + 0.46) * tau) * 0.08
    )
    return longitudinal + broad


def build_palm_normal(name, size=256, derivative_strength=1.95):
    rows = []
    step = 1.0 / float(size)
    for py in range(size):
        v = py / float(size - 1)
        row = bytearray()
        for px in range(size):
            u = px / float(size - 1)
            h_l = palm_height((u - step) % 1.0, v)
            h_r = palm_height((u + step) % 1.0, v)
            h_d = palm_height(u, (v - step) % 1.0)
            h_u = palm_height(u, (v + step) % 1.0)
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
        raise RuntimeError("Generated palm-bark normal PNG is suspiciously small: %s" % path)
    image = bpy.data.images.load(path, check_existing=False)
    image.name = name
    image.colorspace_settings.name = "Non-Color"
    return image


def response_material(source, normal_image):
    material = source.copy()
    material.name = "V5 Palm Bark Surface Response"
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    shader = nodes.get("Principled BSDF") or next(
        (node for node in nodes if node.type == "BSDF_PRINCIPLED"), None
    )
    if shader is None:
        raise RuntimeError("Palm-bark source material has no Principled shader")

    tex = nodes.new("ShaderNodeTexImage")
    tex.name = "V5 Palm Bark Normal Texture"
    tex.image = normal_image
    tex.interpolation = "Linear"
    tex.extension = "REPEAT"

    normal = nodes.new("ShaderNodeNormalMap")
    normal.name = "V5 Palm Bark Normal"
    normal.space = "TANGENT"
    normal.inputs["Strength"].default_value = 0.58
    links.new(tex.outputs["Color"], normal.inputs["Color"])
    links.new(normal.outputs["Normal"], shader.inputs["Normal"])

    shader.inputs["Roughness"].default_value = 0.87
    if "Specular IOR Level" in shader.inputs:
        shader.inputs["Specular IOR Level"].default_value = 0.12
    elif "Specular" in shader.inputs:
        shader.inputs["Specular"].default_value = 0.12
    if "Metallic" in shader.inputs:
        shader.inputs["Metallic"].default_value = 0.0
    return material


targets = [
    obj for obj in bpy.context.scene.objects
    if obj.type == "MESH" and not obj.hide_render and obj.name.startswith("HeroPalm_")
]
if not targets:
    raise RuntimeError("No visible HeroPalm_* meshes found for palm bark response")

meshes = {obj.data.name: obj.data for obj in targets}
source = None
for mesh in meshes.values():
    for current in mesh.materials:
        if current is not None and current.name.startswith("Wood.001"):
            source = current
            break
    if source is not None:
        break

if source is None:
    raise RuntimeError("Palm Wood.001 material not found on HeroPalm_* meshes")

normal_image = build_palm_normal("Lembah Palm Bark Surface Normal")
material = response_material(source, normal_image)
replaced = 0
for mesh in meshes.values():
    for index, current in enumerate(mesh.materials):
        if current == source:
            mesh.materials[index] = material
            replaced += 1

if replaced == 0:
    raise RuntimeError("Palm bark material replacement did not affect any mesh slots")

ridge_export.select_v5_export_set()
bpy.ops.export_scene.gltf(
    filepath=OUT_PATH,
    export_format="GLB",
    use_selection=True,
    export_apply=True,
    export_yup=True,
)
print(
    "Palm bark response gate exported to %s (hero palms=%d; slots=%d; trunk relief only)"
    % (OUT_PATH, len(targets), replaced)
)
