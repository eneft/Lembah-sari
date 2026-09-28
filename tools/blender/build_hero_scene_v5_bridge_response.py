import math
import os
import sys

import bpy

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

# Continue from the accepted paddy-response gate. This pass changes only the
# bridge timber normals; accepted bridge albedo, UVs, geometry and roughness stay locked.
import build_hero_scene_v5_paddy_response  # noqa: F401,E402
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


def height_field(u, v, phase=0.0):
    tau = math.pi * 2.0
    return (
        math.sin((u * 9.5 + v * 0.70 + phase) * tau) * 0.54
        + math.sin((u * 21.0 - v * 1.15 + 0.29) * tau) * 0.20
        + math.sin((u * 4.0 + v * 2.4 + 0.11) * tau) * 0.16
    )


def build_wood_normal(name, phase=0.0, size=256, strength=0.80):
    """Bake restrained wood-grain relief that survives glTF as a normal map."""
    rows = []
    step = 1.0 / float(size)
    for py in range(size):
        v = py / float(size - 1)
        row = bytearray()
        for px in range(size):
            u = px / float(size - 1)
            h_l = height_field((u - step) % 1.0, v, phase)
            h_r = height_field((u + step) % 1.0, v, phase)
            h_d = height_field(u, (v - step) % 1.0, phase)
            h_u = height_field(u, (v + step) % 1.0, phase)
            dx = (h_r - h_l) * strength
            dy = (h_u - h_d) * strength
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
        raise RuntimeError("Generated bridge normal PNG is suspiciously small: %s" % path)
    image = bpy.data.images.load(path, check_existing=False)
    image.name = name
    image.colorspace_settings.name = "Non-Color"
    return image


def add_normal_response(source, normal_image, name, strength):
    material = source.copy()
    material.name = name
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    shader = nodes.get("Principled BSDF") or next(
        (node for node in nodes if node.type == "BSDF_PRINCIPLED"), None
    )
    if shader is None:
        raise RuntimeError("Bridge source material has no Principled shader: %s" % source.name)

    tex = nodes.new("ShaderNodeTexImage")
    tex.name = name + " Normal Texture"
    tex.image = normal_image
    tex.interpolation = "Linear"
    tex.extension = "REPEAT"

    normal = nodes.new("ShaderNodeNormalMap")
    normal.name = name + " Normal"
    normal.space = "TANGENT"
    normal.inputs["Strength"].default_value = strength
    links.new(tex.outputs["Color"], normal.inputs["Color"])
    links.new(normal.outputs["Normal"], shader.inputs["Normal"])
    return material


def bridge_objects(prefix):
    return sorted(
        [
            obj for obj in bpy.context.scene.objects
            if obj.type == "MESH" and obj.name.startswith(prefix) and not obj.hide_render
        ],
        key=lambda obj: obj.name,
    )


planks = bridge_objects("V5BridgePlank_")
posts = bridge_objects("V5BridgePost_")
rails = bridge_objects("V5BridgeRail")
if len(planks) != 11:
    raise RuntimeError("Expected 11 visible bridge planks, got %d" % len(planks))
if len(posts) != 6:
    raise RuntimeError("Expected 6 visible bridge posts, got %d" % len(posts))
if len(rails) != 2:
    raise RuntimeError("Expected 2 visible bridge rails, got %d" % len(rails))

honey_source = planks[0].data.materials[0] if planks[0].data.materials else None
dark_source = posts[0].data.materials[0] if posts[0].data.materials else None
if honey_source is None or dark_source is None:
    raise RuntimeError("Bridge objects are missing accepted source materials")
if not honey_source.name.startswith("V5 Textured Bridge Honey Wood"):
    raise RuntimeError("Unexpected bridge plank material: %s" % honey_source.name)
if not dark_source.name.startswith("V5 Textured Bridge Dark Wood"):
    raise RuntimeError("Unexpected bridge dark material: %s" % dark_source.name)

honey_normal = build_wood_normal("Lembah Bridge Honey Grain Normal", phase=0.13, strength=0.78)
dark_normal = build_wood_normal("Lembah Bridge Dark Grain Normal", phase=0.39, strength=0.72)
honey = add_normal_response(
    honey_source,
    honey_normal,
    "V5 Bridge Honey Wood Surface Response",
    0.24,
)
dark = add_normal_response(
    dark_source,
    dark_normal,
    "V5 Bridge Dark Wood Surface Response",
    0.20,
)

for obj in planks:
    obj.data.materials.clear()
    obj.data.materials.append(honey)
for obj in posts + rails:
    obj.data.materials.clear()
    obj.data.materials.append(dark)

ridge_export.select_v5_export_set()
bpy.ops.export_scene.gltf(
    filepath=OUT_PATH,
    export_format="GLB",
    use_selection=True,
    export_apply=True,
    export_yup=True,
)
print(
    "Bridge wood response gate exported to %s (planks=%d posts=%d rails=%d; normal relief only)"
    % (OUT_PATH, len(planks), len(posts), len(rails))
)
