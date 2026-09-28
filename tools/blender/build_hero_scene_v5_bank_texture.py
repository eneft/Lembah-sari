import math
import os
import struct
import sys
import zlib

import bpy

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

# Start from the last visually accepted environment gate. Importing this module
# builds the complete accepted scene and exports it once; this gate then changes
# only V5StreamBank and re-exports the same scene.
import build_hero_scene_v5_ridge_texture  # noqa: F401,E402

OUT_PATH = os.path.abspath(
    os.environ.get(
        "LEMBAH_HERO_OUT",
        os.path.join(os.getcwd(), "assets", "models", "hero_scene_v5.glb"),
    )
)
os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)


def clamp(value, lo=0.0, hi=1.0):
    return max(lo, min(hi, value))


def mix(a, b, t):
    return a + (b - a) * t


def linear_to_srgb(value):
    value = clamp(value)
    if value <= 0.0031308:
        return value * 12.92
    return 1.055 * (value ** (1.0 / 2.4)) - 0.055


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


def build_bank_image(name, phase=0.0, size=256):
    """Bake broad damp-earth variation for the river bank only."""
    tau = math.pi * 2.0
    dark = (0.075, 0.042, 0.018)
    mid = (0.165, 0.092, 0.036)
    light = (0.285, 0.180, 0.072)
    moss = (0.075, 0.165, 0.050)
    dry = (0.350, 0.245, 0.120)
    rows = []

    for py in range(size):
        v = py / float(size - 1)
        row = bytearray()
        for px in range(size):
            u = px / float(size - 1)

            broad = (
                math.sin((u * 1.55 + v * 1.05 + phase) * tau) * 0.125
                + math.sin((u * 3.15 - v * 2.25 + 0.27) * tau) * 0.060
                + math.sin((u * 7.2 + v * 5.4 + 0.61) * tau) * 0.020
            )
            t = clamp(0.47 + broad)
            if t < 0.50:
                q = t / 0.50
                rgb = tuple(mix(dark[c], mid[c], q) for c in range(3))
            else:
                q = (t - 0.50) / 0.50
                rgb = tuple(mix(mid[c], light[c], q) for c in range(3))

            # Soft green moisture islands break the old continuous tan strip but
            # remain subordinate to the foliage along the stream.
            moss_field = (
                math.sin((u * 2.0 - v * 1.45 + 0.34 + phase) * tau) * 0.68
                + math.sin((u * 4.2 + v * 3.1 + 0.73) * tau) * 0.25
            )
            moss_amount = clamp((moss_field - 0.48) / 0.42)
            moss_amount = moss_amount * moss_amount * 0.24
            rgb = tuple(mix(rgb[c], moss[c], moss_amount) for c in range(3))

            # Sparse warmer patches suggest exposed, drier soil without turning
            # the bank back into a bright cartoon outline.
            dry_field = clamp((math.sin((u * 2.8 + v * 3.6 + 0.17) * tau) - 0.76) / 0.24)
            rgb = tuple(mix(rgb[c], dry[c], dry_field * 0.08) for c in range(3))

            encoded = tuple(linear_to_srgb(channel) for channel in rgb)
            row.extend(int(round(clamp(channel) * 255.0)) for channel in encoded)
        rows.append(row)

    path = os.path.join("/tmp", name.lower().replace(" ", "_") + ".png")
    write_rgb_png(path, size, size, rows)
    if os.path.getsize(path) <= 1024:
        raise RuntimeError("Generated stream-bank PNG is suspiciously small: %s" % path)
    image = bpy.data.images.load(path, check_existing=False)
    image.name = name
    image.colorspace_settings.name = "sRGB"
    return image


def bank_material(name, source, image):
    material = source.copy()
    material.name = name
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    shader = nodes.get("Principled BSDF") or next(
        (node for node in nodes if node.type == "BSDF_PRINCIPLED"), None
    )
    if shader is None:
        raise RuntimeError("Stream-bank material has no Principled shader")

    base_socket = shader.inputs.get("Base Color")
    for link in list(links):
        if link.to_node == shader and link.to_socket == base_socket:
            links.remove(link)
    tex = nodes.new("ShaderNodeTexImage")
    tex.image = image
    tex.interpolation = "Linear"
    tex.extension = "REPEAT"
    links.new(tex.outputs["Color"], base_socket)

    shader.inputs["Roughness"].default_value = 0.98
    if "Specular IOR Level" in shader.inputs:
        shader.inputs["Specular IOR Level"].default_value = 0.08
    elif "Specular" in shader.inputs:
        shader.inputs["Specular"].default_value = 0.08
    if "Metallic" in shader.inputs:
        shader.inputs["Metallic"].default_value = 0.0
    if "Emission Strength" in shader.inputs:
        shader.inputs["Emission Strength"].default_value = 0.0
    return material


def world_planar_uv(obj, world_scale=2.35):
    mesh = obj.data
    if not mesh.vertices:
        raise RuntimeError("V5StreamBank has no vertices")
    layer = mesh.uv_layers.get("UVMap") or mesh.uv_layers.new(name="UVMap")
    inv = 1.0 / world_scale
    for poly in mesh.polygons:
        for loop_index in poly.loop_indices:
            vertex = mesh.vertices[mesh.loops[loop_index].vertex_index]
            layer.data[loop_index].uv = (vertex.co.x * inv, vertex.co.y * inv)


bank = bpy.data.objects.get("V5StreamBank")
if bank is None or bank.type != "MESH":
    raise RuntimeError("Expected V5StreamBank mesh is missing")
if not bank.data.materials:
    raise RuntimeError("V5StreamBank has no source material")

image = build_bank_image("Lembah Damp Stream Bank", phase=0.23)
material = bank_material("V5 Textured Damp Stream Bank", bank.data.materials[0], image)
world_planar_uv(bank, world_scale=2.35)
bank.data.materials.clear()
bank.data.materials.append(material)

# Preserve every object already accepted by the ridge gate; only the stream-bank
# material/UVs differ in this export.
bpy.ops.object.select_all(action="SELECT")
bpy.ops.export_scene.gltf(
    filepath=OUT_PATH,
    export_format="GLB",
    use_selection=True,
    export_apply=True,
    export_yup=True,
)
print("Stream bank earth texture gate exported to %s (%s -> %s)" % (OUT_PATH, bank.name, material.name))
