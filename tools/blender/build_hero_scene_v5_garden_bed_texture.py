import math
import os
import struct
import sys
import zlib

import bpy

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

# Build the accepted scene through the young-rice gate. This pass changes only
# KitchenGardenBed_0/1; garden plants, flowers and bamboo stay untouched.
import build_hero_scene_v5_rice_texture  # noqa: F401,E402

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


def build_bed_image(name, phase=0.0, size=256):
    """Bake damp cultivated soil with broad compost and moss undertones."""
    tau = math.pi * 2.0
    dark = (0.070, 0.032, 0.012)
    mid = (0.145, 0.068, 0.026)
    light = (0.255, 0.140, 0.055)
    compost = (0.095, 0.055, 0.026)
    moss = (0.070, 0.135, 0.035)
    rows = []

    for py in range(size):
        v = py / float(size - 1)
        row = bytearray()
        for px in range(size):
            u = px / float(size - 1)
            broad = (
                math.sin((u * 1.75 + v * 1.15 + phase) * tau) * 0.140
                + math.sin((u * 3.60 - v * 2.55 + 0.31) * tau) * 0.060
                + math.sin((u * 8.4 + v * 6.2 + 0.67) * tau) * 0.018
            )
            t = clamp(0.47 + broad)
            if t < 0.50:
                q = t / 0.50
                rgb = tuple(mix(dark[c], mid[c], q) for c in range(3))
            else:
                q = (t - 0.50) / 0.50
                rgb = tuple(mix(mid[c], light[c], q) for c in range(3))

            compost_field = clamp(
                (math.sin((u * 2.2 + v * 3.1 + 0.51 + phase) * tau) - 0.55)
                / 0.45
            )
            rgb = tuple(mix(rgb[c], compost[c], compost_field * 0.16) for c in range(3))

            # Very restrained green at damp edges; the bed must still read as soil.
            moss_field = (
                math.sin((u * 1.3 - v * 1.7 + 0.18) * tau) * 0.66
                + math.sin((u * 3.0 + v * 2.1 + phase) * tau) * 0.24
            )
            moss_amount = clamp((moss_field - 0.58) / 0.32) * 0.10
            rgb = tuple(mix(rgb[c], moss[c], moss_amount) for c in range(3))

            encoded = tuple(linear_to_srgb(channel) for channel in rgb)
            row.extend(int(round(clamp(channel) * 255.0)) for channel in encoded)
        rows.append(row)

    path = os.path.join("/tmp", name.lower().replace(" ", "_") + ".png")
    write_rgb_png(path, size, size, rows)
    if os.path.getsize(path) <= 1024:
        raise RuntimeError("Generated garden-bed PNG is suspiciously small: %s" % path)
    image = bpy.data.images.load(path, check_existing=False)
    image.name = name
    image.colorspace_settings.name = "sRGB"
    return image


def bed_material(source, image):
    material = source.copy()
    material.name = "V5 Textured Kitchen Garden Earth"
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    shader = nodes.get("Principled BSDF") or next(
        (node for node in nodes if node.type == "BSDF_PRINCIPLED"), None
    )
    if shader is None:
        raise RuntimeError("Kitchen garden source material has no Principled shader")
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
        shader.inputs["Specular IOR Level"].default_value = 0.06
    elif "Specular" in shader.inputs:
        shader.inputs["Specular"].default_value = 0.06
    if "Metallic" in shader.inputs:
        shader.inputs["Metallic"].default_value = 0.0
    return material


def planar_uv(obj, repeats=1.0):
    mesh = obj.data
    if not mesh.vertices:
        raise RuntimeError("Kitchen garden bed has no vertices: %s" % obj.name)
    layer = mesh.uv_layers.get("UVMap") or mesh.uv_layers.new(name="UVMap")
    min_x = min(vertex.co.x for vertex in mesh.vertices)
    max_x = max(vertex.co.x for vertex in mesh.vertices)
    min_y = min(vertex.co.y for vertex in mesh.vertices)
    max_y = max(vertex.co.y for vertex in mesh.vertices)
    dx = max(max_x - min_x, 1e-6)
    dy = max(max_y - min_y, 1e-6)
    for poly in mesh.polygons:
        for loop_index in poly.loop_indices:
            vertex = mesh.vertices[mesh.loops[loop_index].vertex_index]
            u = ((vertex.co.x - min_x) / dx) * repeats
            v = ((vertex.co.y - min_y) / dy) * repeats
            layer.data[loop_index].uv = (u, v)


beds = [
    obj for obj in bpy.context.scene.objects
    if obj.type == "MESH" and obj.name.startswith("KitchenGardenBed_") and not obj.hide_render
]
if len(beds) != 2:
    raise RuntimeError("Expected exactly 2 visible KitchenGardenBed meshes, got %d" % len(beds))

image = build_bed_image("Lembah Cultivated Kitchen Garden Earth", phase=0.27)
source = beds[0].data.materials[0] if beds[0].data.materials else None
if source is None:
    raise RuntimeError("KitchenGardenBed_0 has no source material")
material = bed_material(source, image)

for index, bed in enumerate(sorted(beds, key=lambda obj: obj.name)):
    planar_uv(bed, repeats=1.55 + index * 0.12)
    bed.data.materials.clear()
    bed.data.materials.append(material)

# Preserve every accepted object and transform. Only the two garden-bed material
# slots and their UVs differ in this export.
bpy.ops.object.select_all(action="SELECT")
bpy.ops.export_scene.gltf(
    filepath=OUT_PATH,
    export_format="GLB",
    use_selection=True,
    export_apply=True,
    export_yup=True,
)
print("Kitchen garden bed earth texture gate exported to %s (beds=%d)" % (OUT_PATH, len(beds)))
