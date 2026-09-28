import math
import os
import sys

import bpy

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

# Build every accepted albedo gate first. This response pass is intentionally
# limited to V5StreamWater: same geometry, same albedo texture and UVs.
import build_hero_scene_v5_garden_bed_texture  # noqa: F401,E402
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
    """Low-amplitude, directional river ripples in the existing UV space."""
    tau = math.pi * 2.0
    return (
        math.sin((u * 1.70 + v * 6.20 + phase) * tau) * 0.56
        + math.sin((u * 3.60 - v * 10.80 + 0.27) * tau) * 0.28
        + math.sin((u * 8.50 + v * 15.50 + 0.61) * tau) * 0.10
    )


def build_water_normal(name, phase=0.0, size=256, strength=1.55):
    """Bake a real tangent-space normal PNG so the response survives glTF."""
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
        raise RuntimeError("Generated river normal PNG is suspiciously small: %s" % path)

    image = bpy.data.images.load(path, check_existing=False)
    image.name = name
    image.colorspace_settings.name = "Non-Color"
    return image


def add_surface_response(source, normal_image):
    material = source.copy()
    material.name = "V5 River Water Surface Response"
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    shader = nodes.get("Principled BSDF") or next(
        (node for node in nodes if node.type == "BSDF_PRINCIPLED"), None
    )
    if shader is None:
        raise RuntimeError("River-water material has no Principled shader")

    # Preserve the accepted albedo network exactly; only add a tangent-space
    # normal map and slightly refine the already-authored water response values.
    tex = nodes.new("ShaderNodeTexImage")
    tex.name = "V5 River Ripple Normal Texture"
    tex.image = normal_image
    tex.interpolation = "Linear"
    tex.extension = "REPEAT"

    normal = nodes.new("ShaderNodeNormalMap")
    normal.name = "V5 River Ripple Normal"
    normal.space = "TANGENT"
    normal.inputs["Strength"].default_value = 0.34
    links.new(tex.outputs["Color"], normal.inputs["Color"])
    links.new(normal.outputs["Normal"], shader.inputs["Normal"])

    shader.inputs["Roughness"].default_value = 0.20
    if "Specular IOR Level" in shader.inputs:
        shader.inputs["Specular IOR Level"].default_value = 0.38
    elif "Specular" in shader.inputs:
        shader.inputs["Specular"].default_value = 0.38
    if "Metallic" in shader.inputs:
        shader.inputs["Metallic"].default_value = 0.0
    return material


water = bpy.data.objects.get("V5StreamWater")
if water is None or water.type != "MESH":
    raise RuntimeError("Expected V5StreamWater mesh is missing")
if not water.data.materials or water.data.materials[0] is None:
    raise RuntimeError("V5StreamWater has no accepted source material")
if not water.data.materials[0].name.startswith("V5 Textured River Water"):
    raise RuntimeError(
        "River response must start from accepted albedo material, got: %s"
        % water.data.materials[0].name
    )

normal_image = build_water_normal("Lembah River Ripple Normal", phase=0.19)
material = add_surface_response(water.data.materials[0], normal_image)
water.data.materials.clear()
water.data.materials.append(material)

# Preserve the accepted Ridge selection guard. Never select-all after the ridge
# gate because hidden legacy horizon meshes are not runtime-hidden by glTF.
ridge_export.select_v5_export_set()
bpy.ops.export_scene.gltf(
    filepath=OUT_PATH,
    export_format="GLB",
    use_selection=True,
    export_apply=True,
    export_yup=True,
)
print(
    "River water response gate exported to %s (%s -> %s; tangent normal + response only)"
    % (OUT_PATH, water.name, material.name)
)
