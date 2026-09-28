import math
import os
import struct
import zlib

import bpy

IN_PATH = os.path.abspath(os.environ.get("LEMBAH_HOUSE_IN", "assets/models/house_main_01.glb"))
OUT_PATH = os.path.abspath(os.environ.get("LEMBAH_HOUSE_OUT", IN_PATH))
os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)

if not os.path.exists(IN_PATH):
    raise RuntimeError("Missing house GLB for foundation response pass: %s" % IN_PATH)

bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=IN_PATH)


def clamp(value, lo=0.0, hi=1.0):
    return max(lo, min(hi, value))


def png_chunk(kind, payload):
    return (
        struct.pack(">I", len(payload))
        + kind
        + payload
        + struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF)
    )


def write_rgb_png(path, width, height, rows):
    raw = bytearray()
    for row in rows:
        raw.append(0)
        raw.extend(row)
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    payload = (
        b"\x89PNG\r\n\x1a\n"
        + png_chunk(b"IHDR", ihdr)
        + png_chunk(b"IDAT", zlib.compress(bytes(raw), 9))
        + png_chunk(b"IEND", b"")
    )
    with open(path, "wb") as handle:
        handle.write(payload)


def stone_height(u, v):
    """Broad irregular footing relief aligned with the accepted warm-stone map."""
    tau = math.pi * 2.0
    broad = (
        math.sin((u * 0.95 + v * 0.58 + 0.11) * tau) * 0.42
        + math.sin((u * 1.90 - v * 1.18 + 0.39) * tau) * 0.25
        + math.sin((u * 3.25 + v * 1.60 + 0.73) * tau) * 0.12
    )
    mineral = math.sin((u * 6.8 - v * 4.2 + 0.33) * tau) * 0.055
    grain = (
        math.sin((u * 15.0 + v * 12.0 + 0.17) * tau)
        * math.sin((u * 11.0 - v * 17.0 + 0.51) * tau)
    ) * 0.028
    return broad + mineral + grain


def build_stone_normal(name, size=256, derivative_strength=1.75):
    rows = []
    step = 1.0 / float(size)
    for py in range(size):
        v = py / float(size - 1)
        row = bytearray()
        for px in range(size):
            u = px / float(size - 1)
            h_l = stone_height((u - step) % 1.0, v)
            h_r = stone_height((u + step) % 1.0, v)
            h_d = stone_height(u, (v - step) % 1.0)
            h_u = stone_height(u, (v + step) % 1.0)
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
    write_rgb_png(path, size, size, rows)
    if os.path.getsize(path) <= 1024:
        raise RuntimeError("Generated foundation normal PNG is suspiciously small: %s" % path)
    image = bpy.data.images.load(path, check_existing=False)
    image.name = name
    image.colorspace_settings.name = "Non-Color"
    return image


def add_response(material, image):
    material.name = "Warm Foundation Stone Surface Response"
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    shader = nodes.get("Principled BSDF") or next(
        (node for node in nodes if node.type == "BSDF_PRINCIPLED"), None
    )
    if shader is None:
        raise RuntimeError("Foundation response material has no Principled shader")

    tex = nodes.new("ShaderNodeTexImage")
    tex.name = "Foundation Stone Normal Texture"
    tex.image = image
    tex.interpolation = "Linear"
    tex.extension = "REPEAT"

    normal = nodes.new("ShaderNodeNormalMap")
    normal.name = "Foundation Stone Normal"
    normal.space = "TANGENT"
    normal.inputs["Strength"].default_value = 0.48
    links.new(tex.outputs["Color"], normal.inputs["Color"])
    links.new(normal.outputs["Normal"], shader.inputs["Normal"])

    # Keep the footing dry and very matte; response exists to break the long
    # flat strip under the house, not to make the stone polished.
    shader.inputs["Roughness"].default_value = 0.93
    if "Specular IOR Level" in shader.inputs:
        shader.inputs["Specular IOR Level"].default_value = 0.09
    elif "Specular" in shader.inputs:
        shader.inputs["Specular"].default_value = 0.09
    if "Metallic" in shader.inputs:
        shader.inputs["Metallic"].default_value = 0.0


image = build_stone_normal("Lembah Warm Foundation Stone Surface Normal")
matched = []
for material in bpy.data.materials:
    if material.name.startswith("Warm Foundation Stone"):
        add_response(material, image)
        matched.append(material.name)

if not matched:
    raise RuntimeError("Warm Foundation Stone material not found for response pass")

bpy.ops.object.select_all(action="SELECT")
bpy.ops.export_scene.gltf(
    filepath=OUT_PATH,
    export_format="GLB",
    use_selection=True,
    export_apply=True,
    export_yup=True,
)
print(
    "House foundation stone surface response exported to %s (materials=%d; stone relief only)"
    % (OUT_PATH, len(matched))
)
