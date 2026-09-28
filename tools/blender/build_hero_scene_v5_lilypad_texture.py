import math
import os
import struct
import sys
import zlib

import bpy

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

# Build the last visually accepted environment first. This pass is intentionally
# narrow: only the Pink blossom slot on Template_Lilypad is replaced. The Green
# leaf slot stays on the accepted foliage treatment.
import build_hero_scene_v5_flower_texture  # noqa: F401,E402

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


def build_blossom_image(name, phase=0.0, size=192):
    """Bake a muted lotus-rose gradient with broad petal-scale variation."""
    tau = math.pi * 2.0
    dark = (0.185, 0.045, 0.075)
    mid = (0.345, 0.095, 0.155)
    light = (0.535, 0.205, 0.270)
    warm = (0.570, 0.270, 0.205)
    rows = []

    for py in range(size):
        v = py / float(size - 1)
        row = bytearray()
        for px in range(size):
            u = px / float(size - 1)
            broad = (
                math.sin((u * 1.25 + v * 0.95 + phase) * tau) * 0.145
                + math.sin((u * 2.45 - v * 1.65 + 0.29) * tau) * 0.065
                + math.sin((u * 4.10 + v * 3.25 + 0.67) * tau) * 0.022
            )
            t = clamp(0.50 + broad)
            if t < 0.50:
                q = t / 0.50
                rgb = tuple(mix(dark[c], mid[c], q) for c in range(3))
            else:
                q = (t - 0.50) / 0.50
                rgb = tuple(mix(mid[c], light[c], q) for c in range(3))

            warm_field = clamp(
                (math.sin((u * 2.55 + v * 2.20 + 0.41 + phase) * tau) - 0.72)
                / 0.28
            )
            rgb = tuple(mix(rgb[c], warm[c], warm_field * 0.10) for c in range(3))

            encoded = tuple(linear_to_srgb(channel) for channel in rgb)
            row.extend(int(round(clamp(channel) * 255.0)) for channel in encoded)
        rows.append(row)

    path = os.path.join("/tmp", name.lower().replace(" ", "_") + ".png")
    write_rgb_png(path, size, size, rows)
    if os.path.getsize(path) <= 1024:
        raise RuntimeError("Generated lilypad-blossom PNG is suspiciously small: %s" % path)
    image = bpy.data.images.load(path, check_existing=False)
    image.name = name
    image.colorspace_settings.name = "sRGB"
    return image


def blossom_material(source, image):
    material = source.copy()
    material.name = "V5 Textured Lilypad Rose Blossom"
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    shader = nodes.get("Principled BSDF") or next(
        (node for node in nodes if node.type == "BSDF_PRINCIPLED"), None
    )
    if shader is None:
        raise RuntimeError("Lilypad Pink material has no Principled shader")

    base_socket = shader.inputs.get("Base Color")
    for link in list(links):
        if link.to_node == shader and link.to_socket == base_socket:
            links.remove(link)
    tex = nodes.new("ShaderNodeTexImage")
    tex.image = image
    tex.interpolation = "Linear"
    tex.extension = "REPEAT"
    links.new(tex.outputs["Color"], base_socket)

    shader.inputs["Roughness"].default_value = 0.93
    if "Specular IOR Level" in shader.inputs:
        shader.inputs["Specular IOR Level"].default_value = 0.09
    elif "Specular" in shader.inputs:
        shader.inputs["Specular"].default_value = 0.09
    if "Metallic" in shader.inputs:
        shader.inputs["Metallic"].default_value = 0.0
    if "Emission Strength" in shader.inputs:
        shader.inputs["Emission Strength"].default_value = 0.0
    return material


lilypad = bpy.data.objects.get("Template_Lilypad")
if lilypad is None or lilypad.type != "MESH":
    raise RuntimeError("Expected Template_Lilypad mesh is missing")
if not lilypad.data.materials:
    raise RuntimeError("Template_Lilypad has no material slots")

image = build_blossom_image("Lembah Lilypad Rose Blossom", phase=0.31)
matched = 0
for index, source in enumerate(list(lilypad.data.materials)):
    if source is not None and source.name.startswith("Pink"):
        lilypad.data.materials[index] = blossom_material(source, image)
        matched += 1

if matched == 0:
    raise RuntimeError(
        "Expected Template_Lilypad Pink slot was not found; slots=%s"
        % [mat.name if mat else "<None>" for mat in lilypad.data.materials]
    )

# Lilypad instances share Template_Lilypad mesh data, so this slot replacement
# reaches each water blossom while Green leaves and every other asset stay intact.
bpy.ops.object.select_all(action="SELECT")
bpy.ops.export_scene.gltf(
    filepath=OUT_PATH,
    export_format="GLB",
    use_selection=True,
    export_apply=True,
    export_yup=True,
)
print(
    "Lilypad blossom texture gate exported to %s (Pink=%d; Green untouched)"
    % (OUT_PATH, matched)
)
