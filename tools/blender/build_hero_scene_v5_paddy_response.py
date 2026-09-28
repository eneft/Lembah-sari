import math
import os
import sys

import bpy

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

# Continue strictly from the accepted river-response gate. This pass changes
# only V5PaddyWater_0..3 material response; albedo, bunds and rice stay locked.
import build_hero_scene_v5_water_response  # noqa: F401,E402
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
        math.sin((u * 1.55 + v * 2.10 + phase) * tau) * 0.50
        + math.sin((u * 4.20 - v * 3.35 + 0.33) * tau) * 0.22
        + math.sin((u * 8.00 + v * 6.20 + 0.71) * tau) * 0.07
    )


def build_paddy_normal(name, phase=0.0, size=256, strength=0.92):
    """Bake calmer standing-water ripples than the flowing river normal."""
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
        raise RuntimeError("Generated paddy normal PNG is suspiciously small: %s" % path)
    image = bpy.data.images.load(path, check_existing=False)
    image.name = name
    image.colorspace_settings.name = "Non-Color"
    return image


def add_surface_response(source, normal_image):
    material = source.copy()
    material.name = "V5 Paddy Water Surface Response"
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    shader = nodes.get("Principled BSDF") or next(
        (node for node in nodes if node.type == "BSDF_PRINCIPLED"), None
    )
    if shader is None:
        raise RuntimeError("Paddy-water material has no Principled shader")

    tex = nodes.new("ShaderNodeTexImage")
    tex.name = "V5 Paddy Ripple Normal Texture"
    tex.image = normal_image
    tex.interpolation = "Linear"
    tex.extension = "REPEAT"

    normal = nodes.new("ShaderNodeNormalMap")
    normal.name = "V5 Paddy Ripple Normal"
    normal.space = "TANGENT"
    normal.inputs["Strength"].default_value = 0.20
    links.new(tex.outputs["Color"], normal.inputs["Color"])
    links.new(normal.outputs["Normal"], shader.inputs["Normal"])

    shader.inputs["Roughness"].default_value = 0.34
    if "Specular IOR Level" in shader.inputs:
        shader.inputs["Specular IOR Level"].default_value = 0.26
    elif "Specular" in shader.inputs:
        shader.inputs["Specular"].default_value = 0.26
    if "Metallic" in shader.inputs:
        shader.inputs["Metallic"].default_value = 0.0
    return material


paddies = sorted(
    [
        obj for obj in bpy.context.scene.objects
        if obj.type == "MESH" and obj.name.startswith("V5PaddyWater_") and not obj.hide_render
    ],
    key=lambda obj: obj.name,
)
if len(paddies) != 4:
    raise RuntimeError("Expected 4 visible V5 paddy-water meshes, got %d" % len(paddies))
source = paddies[0].data.materials[0] if paddies[0].data.materials else None
if source is None:
    raise RuntimeError("V5PaddyWater_0 has no accepted source material")
if not source.name.startswith("V5 Textured Paddy Water"):
    raise RuntimeError(
        "Paddy response must start from accepted albedo material, got: %s" % source.name
    )

normal_image = build_paddy_normal("Lembah Paddy Calm Ripple Normal", phase=0.23)
material = add_surface_response(source, normal_image)
for paddy in paddies:
    paddy.data.materials.clear()
    paddy.data.materials.append(material)

ridge_export.select_v5_export_set()
bpy.ops.export_scene.gltf(
    filepath=OUT_PATH,
    export_format="GLB",
    use_selection=True,
    export_apply=True,
    export_yup=True,
)
print(
    "Paddy water response gate exported to %s (paddies=%d; calm tangent normal only)"
    % (OUT_PATH, len(paddies))
)
