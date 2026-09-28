import math
import os
import struct
import zlib

import bpy

IN_PATH = os.path.abspath(os.environ.get("LEMBAH_HOUSE_IN", "assets/models/house_main_01.glb"))
OUT_PATH = os.path.abspath(os.environ.get("LEMBAH_HOUSE_OUT", IN_PATH))
os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)

if not os.path.exists(IN_PATH):
    raise RuntimeError("Missing house GLB for roof response pass: %s" % IN_PATH)

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


def clay_height(u, v, phase=0.0):
    """Handmade clay micro-relief only; modeled roof bands remain the tile form."""
    tau = math.pi * 2.0
    return (
        math.sin((u * 4.6 + v * 2.2 + phase) * tau) * 0.30
        + math.sin((u * 8.2 - v * 5.5 + 0.27 + phase * 0.4) * tau) * 0.20
        + math.sin((u * 15.3 + v * 11.7 + 0.53) * tau) * 0.12
        + math.sin((u * 25.0 - v * 18.0 + phase * 0.7) * tau)
        * math.sin((u * 17.0 + v * 23.0 + 0.21) * tau) * 0.06
    )


def build_clay_normal(name, phase=0.0, size=256, derivative_strength=0.78):
    rows = []
    step = 1.0 / float(size)
    for py in range(size):
        v = py / float(size - 1)
        row = bytearray()
        for px in range(size):
            u = px / float(size - 1)
            h_l = clay_height((u - step) % 1.0, v, phase)
            h_r = clay_height((u + step) % 1.0, v, phase)
            h_d = clay_height(u, (v - step) % 1.0, phase)
            h_u = clay_height(u, (v + step) % 1.0, phase)
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
        raise RuntimeError("Generated roof normal PNG is suspiciously small: %s" % path)
    image = bpy.data.images.load(path, check_existing=False)
    image.name = name
    image.colorspace_settings.name = "Non-Color"
    return image


def add_response(material, image, strength, roughness, specular):
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    shader = nodes.get("Principled BSDF") or next(
        (node for node in nodes if node.type == "BSDF_PRINCIPLED"), None
    )
    if shader is None:
        raise RuntimeError("Terracotta response material has no Principled shader: %s" % material.name)

    tex = nodes.new("ShaderNodeTexImage")
    tex.name = material.name + " Clay Normal Texture"
    tex.image = image
    tex.interpolation = "Linear"
    tex.extension = "REPEAT"

    normal = nodes.new("ShaderNodeNormalMap")
    normal.name = material.name + " Clay Normal"
    normal.space = "TANGENT"
    normal.inputs["Strength"].default_value = strength
    links.new(tex.outputs["Color"], normal.inputs["Color"])
    links.new(normal.outputs["Normal"], shader.inputs["Normal"])

    shader.inputs["Roughness"].default_value = roughness
    if "Specular IOR Level" in shader.inputs:
        shader.inputs["Specular IOR Level"].default_value = specular
    elif "Specular" in shader.inputs:
        shader.inputs["Specular"].default_value = specular


families = {
    "Soft Terracotta": ("Lembah Terracotta Main Clay Normal", 0.10, 0.34, 0.84, 0.16),
    "Sunlit Terracotta": ("Lembah Terracotta Sun Clay Normal", 0.34, 0.31, 0.81, 0.17),
    "Terracotta Shadow": ("Lembah Terracotta Shade Clay Normal", 0.62, 0.27, 0.88, 0.14),
}

images = {}
matched = set()
for prefix, (image_name, phase, strength, roughness, specular) in families.items():
    images[prefix] = build_clay_normal(image_name, phase=phase)

for material in bpy.data.materials:
    for prefix, (_image_name, _phase, strength, roughness, specular) in families.items():
        if material.name.startswith(prefix):
            add_response(material, images[prefix], strength, roughness, specular)
            matched.add(prefix)
            break

missing = [prefix for prefix in families if prefix not in matched]
if missing:
    raise RuntimeError("Terracotta response materials not found: %s" % ", ".join(missing))

bpy.ops.object.select_all(action="SELECT")
bpy.ops.export_scene.gltf(
    filepath=OUT_PATH,
    export_format="GLB",
    use_selection=True,
    export_apply=True,
    export_yup=True,
)
print(
    "Terracotta roof surface response exported to %s (families=%d; albedo/geometry preserved)"
    % (OUT_PATH, len(matched))
)
