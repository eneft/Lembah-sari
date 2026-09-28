import math
import os
import struct
import zlib

import bpy

IN_PATH = os.path.abspath(os.environ.get("LEMBAH_HOUSE_IN", "assets/models/house_main_01.glb"))
OUT_PATH = os.path.abspath(os.environ.get("LEMBAH_HOUSE_OUT", IN_PATH))
os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)

if not os.path.exists(IN_PATH):
    raise RuntimeError("Missing house GLB for bamboo response pass: %s" % IN_PATH)

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


def bamboo_height(u, v):
    """Soft dry-fibre relief that follows the accepted porch bamboo albedo."""
    tau = math.pi * 2.0
    broad = (
        math.sin((u * 1.45 + v * 0.90 + 0.21) * tau) * 0.30
        + math.sin((u * 2.70 - v * 1.45 + 0.48) * tau) * 0.16
    )
    fibre = (
        math.sin((u * 11.0 + v * 1.45 + 0.32) * tau) * 0.30
        + math.sin((u * 23.0 - v * 2.0 + 0.71) * tau) * 0.13
        + math.sin((u * 37.0 + v * 3.2 + 0.11) * tau) * 0.05
    )
    return broad + fibre


def build_bamboo_normal(name, size=256, derivative_strength=1.85):
    rows = []
    step = 1.0 / float(size)
    for py in range(size):
        v = py / float(size - 1)
        row = bytearray()
        for px in range(size):
            u = px / float(size - 1)
            h_l = bamboo_height((u - step) % 1.0, v)
            h_r = bamboo_height((u + step) % 1.0, v)
            h_d = bamboo_height(u, (v - step) % 1.0)
            h_u = bamboo_height(u, (v + step) % 1.0)
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
        raise RuntimeError("Generated house bamboo normal PNG is suspiciously small: %s" % path)
    image = bpy.data.images.load(path, check_existing=False)
    image.name = name
    image.colorspace_settings.name = "Non-Color"
    return image


def add_response(material, image):
    material.name = "Dry Bamboo Surface Response"
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    shader = nodes.get("Principled BSDF") or next(
        (node for node in nodes if node.type == "BSDF_PRINCIPLED"), None
    )
    if shader is None:
        raise RuntimeError("House bamboo response material has no Principled shader")

    tex = nodes.new("ShaderNodeTexImage")
    tex.name = "Dry Bamboo Fibre Normal Texture"
    tex.image = image
    tex.interpolation = "Linear"
    tex.extension = "REPEAT"

    normal = nodes.new("ShaderNodeNormalMap")
    normal.name = "Dry Bamboo Fibre Normal"
    normal.space = "TANGENT"
    normal.inputs["Strength"].default_value = 0.50
    links.new(tex.outputs["Color"], normal.inputs["Color"])
    links.new(normal.outputs["Normal"], shader.inputs["Normal"])

    # The lattice is small in the fixed hero camera, so response is stronger
    # than the albedo-only pass while remaining clearly dry and matte.
    shader.inputs["Roughness"].default_value = 0.82
    if "Specular IOR Level" in shader.inputs:
        shader.inputs["Specular IOR Level"].default_value = 0.14
    elif "Specular" in shader.inputs:
        shader.inputs["Specular"].default_value = 0.14
    if "Metallic" in shader.inputs:
        shader.inputs["Metallic"].default_value = 0.0


image = build_bamboo_normal("Lembah Dry Porch Bamboo Fibre Normal")
matched = []
for material in bpy.data.materials:
    if material.name.startswith("Dry Bamboo"):
        add_response(material, image)
        matched.append(material.name)

if not matched:
    raise RuntimeError("Dry Bamboo material not found for house bamboo response pass")

bpy.ops.object.select_all(action="SELECT")
bpy.ops.export_scene.gltf(
    filepath=OUT_PATH,
    export_format="GLB",
    use_selection=True,
    export_apply=True,
    export_yup=True,
)
print(
    "House bamboo lattice surface response exported to %s (materials=%d; dry fibre relief)"
    % (OUT_PATH, len(matched))
)
