import math
import os
import sys

import bpy

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

# Continue from every accepted response gate through palm bark. This pass changes
# only V5StreamBank and must preserve the accepted ridge export selection.
import build_hero_scene_v5_palm_bark_response  # noqa: F401,E402
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


def bank_height(u, v, phase=0.23):
    """Soft eroded earth relief with damp clumps; broad enough for hero scale."""
    tau = math.pi * 2.0
    broad = (
        math.sin((u * 1.35 + v * 0.85 + phase) * tau) * 0.40
        + math.sin((u * 2.65 - v * 1.80 + 0.27) * tau) * 0.22
        + math.sin((u * 5.4 + v * 3.6 + 0.61) * tau) * 0.09
    )
    clumps = (
        math.sin((u * 9.5 - v * 7.0 + 0.17) * tau)
        * math.sin((u * 7.0 + v * 10.5 + 0.43) * tau)
    ) * 0.045
    grain = math.sin((u * 17.0 + v * 13.0 + 0.69) * tau) * 0.018
    return broad + clumps + grain


def build_bank_normal(name, size=256, derivative_strength=5.10):
    rows = []
    step = 1.0 / float(size)
    for py in range(size):
        v = py / float(size - 1)
        row = bytearray()
        for px in range(size):
            u = px / float(size - 1)
            h_l = bank_height((u - step) % 1.0, v)
            h_r = bank_height((u + step) % 1.0, v)
            h_d = bank_height(u, (v - step) % 1.0)
            h_u = bank_height(u, (v + step) % 1.0)
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
        raise RuntimeError("Generated stream-bank normal PNG is suspiciously small: %s" % path)
    image = bpy.data.images.load(path, check_existing=False)
    image.name = name
    image.colorspace_settings.name = "Non-Color"
    return image


def response_material(source, normal_image):
    material = source.copy()
    material.name = "V5 Damp Stream Bank Surface Response"
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    shader = nodes.get("Principled BSDF") or next(
        (node for node in nodes if node.type == "BSDF_PRINCIPLED"), None
    )
    if shader is None:
        raise RuntimeError("Stream-bank response source material has no Principled shader")

    tex = nodes.new("ShaderNodeTexImage")
    tex.name = "V5 Damp Stream Bank Normal Texture"
    tex.image = normal_image
    tex.interpolation = "Linear"
    tex.extension = "REPEAT"

    normal = nodes.new("ShaderNodeNormalMap")
    normal.name = "V5 Damp Stream Bank Normal"
    normal.space = "TANGENT"
    normal.inputs["Strength"].default_value = 0.88
    links.new(tex.outputs["Color"], normal.inputs["Color"])
    links.new(normal.outputs["Normal"], shader.inputs["Normal"])

    # The bank is a long, low strip seen at a shallow angle in the hero camera.
    # Keep broad relief readable at game scale and allow a restrained damp-earth
    # response without turning the bank glossy or wet-looking like the river.
    shader.inputs["Roughness"].default_value = 0.86
    if "Specular IOR Level" in shader.inputs:
        shader.inputs["Specular IOR Level"].default_value = 0.16
    elif "Specular" in shader.inputs:
        shader.inputs["Specular"].default_value = 0.16
    if "Metallic" in shader.inputs:
        shader.inputs["Metallic"].default_value = 0.0
    return material


bank = bpy.data.objects.get("V5StreamBank")
if bank is None or bank.type != "MESH":
    raise RuntimeError("Expected V5StreamBank mesh is missing")
if not bank.data.materials:
    raise RuntimeError("V5StreamBank has no source material")

source = next(
    (
        current
        for current in bank.data.materials
        if current is not None and current.name.startswith("V5 Textured Damp Stream Bank")
    ),
    None,
)
if source is None:
    raise RuntimeError("V5 Textured Damp Stream Bank material not found")

normal_image = build_bank_normal("Lembah Damp Stream Bank Surface Normal")
material = response_material(source, normal_image)
replaced = 0
for index, current in enumerate(bank.data.materials):
    if current == source:
        bank.data.materials[index] = material
        replaced += 1
if replaced == 0:
    raise RuntimeError("Stream-bank response material replacement affected no slots")

ridge_export.select_v5_export_set()
bpy.ops.export_scene.gltf(
    filepath=OUT_PATH,
    export_format="GLB",
    use_selection=True,
    export_apply=True,
    export_yup=True,
)
print(
    "Damp stream-bank surface response gate exported to %s (slots=%d; earth relief only)"
    % (OUT_PATH, replaced)
)
