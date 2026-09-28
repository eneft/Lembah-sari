import math
import os
import struct
import zlib

import bpy

IN_PATH = os.path.abspath(os.environ.get("LEMBAH_HOUSE_IN", "assets/models/house_main_01.glb"))
OUT_PATH = os.path.abspath(os.environ.get("LEMBAH_HOUSE_OUT", IN_PATH))
os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)

if not os.path.exists(IN_PATH):
    raise RuntimeError("Missing house GLB for timber response pass: %s" % IN_PATH)

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


def wood_height(u, v, phase=0.0):
    """Follow the accepted timber albedo grain so relief reinforces, not fights, it."""
    tau = math.pi * 2.0
    warp = math.sin((u * 1.8 + v * 0.55 + phase) * tau) * 0.055
    return (
        math.sin((v * 8.0 + warp + phase) * tau) * 0.48
        + math.sin((v * 17.0 + u * 1.25 + 0.21) * tau) * 0.20
        + math.sin((v * 33.0 - u * 0.65 + 0.37) * tau) * 0.07
        + math.sin((u * 2.2 + phase * 0.5) * tau) * 0.10
    )


def build_wood_normal(name, phase=0.0, size=256, derivative_strength=1.0):
    rows = []
    step = 1.0 / float(size)
    for py in range(size):
        v = py / float(size - 1)
        row = bytearray()
        for px in range(size):
            u = px / float(size - 1)
            h_l = wood_height((u - step) % 1.0, v, phase)
            h_r = wood_height((u + step) % 1.0, v, phase)
            h_d = wood_height(u, (v - step) % 1.0, phase)
            h_u = wood_height(u, (v + step) % 1.0, phase)
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
        raise RuntimeError("Generated timber normal PNG is suspiciously small: %s" % path)
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
        raise RuntimeError("Timber response material has no Principled shader: %s" % material.name)

    tex = nodes.new("ShaderNodeTexImage")
    tex.name = material.name + " Grain Normal Texture"
    tex.image = image
    tex.interpolation = "Linear"
    tex.extension = "REPEAT"

    normal = nodes.new("ShaderNodeNormalMap")
    normal.name = material.name + " Grain Normal"
    normal.space = "TANGENT"
    normal.inputs["Strength"].default_value = strength
    links.new(tex.outputs["Color"], normal.inputs["Color"])
    links.new(normal.outputs["Normal"], shader.inputs["Normal"])

    # Review #57 proved the normals survived export but were visually too quiet.
    # Increase highlight range while keeping every timber family decisively matte.
    shader.inputs["Roughness"].default_value = roughness
    if "Specular IOR Level" in shader.inputs:
        shader.inputs["Specular IOR Level"].default_value = specular
    elif "Specular" in shader.inputs:
        shader.inputs["Specular"].default_value = specular


families = {
    "Sun Warm Timber Panel": ("Lembah Warm Timber Grain Normal", 0.08, 0.50, 0.74, 0.20),
    "Honey Timber Panel": ("Lembah Honey Timber Grain Normal", 0.31, 0.47, 0.72, 0.21),
    "Deep Teak Frame": ("Lembah Deep Teak Grain Normal", 0.54, 0.42, 0.80, 0.17),
    "Warm Teak Frame": ("Lembah Warm Teak Grain Normal", 0.73, 0.44, 0.78, 0.18),
}

images = {
    prefix: build_wood_normal(image_name, phase=phase)
    for prefix, (image_name, phase, _strength, _roughness, _specular) in families.items()
}
matched = set()
for material in bpy.data.materials:
    for prefix, (_image_name, _phase, strength, roughness, specular) in families.items():
        if material.name.startswith(prefix):
            add_response(material, images[prefix], strength, roughness, specular)
            matched.add(prefix)
            break

missing = [prefix for prefix in families if prefix not in matched]
if missing:
    raise RuntimeError("Timber response materials not found: %s" % ", ".join(missing))

bpy.ops.object.select_all(action="SELECT")
bpy.ops.export_scene.gltf(
    filepath=OUT_PATH,
    export_format="GLB",
    use_selection=True,
    export_apply=True,
    export_yup=True,
)
print(
    "House timber surface response exported to %s (families=%d; readable grain response)"
    % (OUT_PATH, len(matched))
)
