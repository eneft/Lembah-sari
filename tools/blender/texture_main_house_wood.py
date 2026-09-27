import math
import os
import struct
import zlib

import bpy

IN_PATH = os.path.abspath(os.environ.get("LEMBAH_HOUSE_IN", "assets/models/house_main_01.glb"))
OUT_PATH = os.path.abspath(os.environ.get("LEMBAH_HOUSE_OUT", IN_PATH))
os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)

if not os.path.exists(IN_PATH):
    raise RuntimeError("Missing house GLB for timber pass: %s" % IN_PATH)

bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=IN_PATH)


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
    return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF)


def write_rgb_png(path, width, height, rows):
    raw = bytearray()
    for row in rows:
        raw.append(0)
        raw.extend(row)
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    payload = b"\x89PNG\r\n\x1a\n" + png_chunk(b"IHDR", ihdr) + png_chunk(b"IDAT", zlib.compress(bytes(raw), 9)) + png_chunk(b"IEND", b"")
    with open(path, "wb") as handle:
        handle.write(payload)


def build_wood_image(name, dark, mid, light, phase=0.0, size=256):
    tau = math.pi * 2.0
    rows = []
    for py in range(size):
        v = py / float(size - 1)
        row = bytearray()
        for px in range(size):
            u = px / float(size - 1)

            # Long timber grain with a small warped component. It is deliberately
            # stylized: readable at game scale but without photographic noise.
            warp = math.sin((u * 1.8 + v * 0.55 + phase) * tau) * 0.055
            grain = (
                math.sin((v * 8.0 + warp + phase) * tau) * 0.14
                + math.sin((v * 17.0 + u * 1.25 + 0.21) * tau) * 0.055
                + math.sin((v * 33.0 - u * 0.65 + 0.37) * tau) * 0.020
            )
            board = math.sin((u * 2.2 + phase * 0.5) * tau) * 0.055
            t = clamp(0.50 + grain + board)
            if t < 0.50:
                q = t / 0.50
                rgb = tuple(mix(dark[c], mid[c], q) for c in range(3))
            else:
                q = (t - 0.50) / 0.50
                rgb = tuple(mix(mid[c], light[c], q) for c in range(3))

            encoded = tuple(linear_to_srgb(channel) for channel in rgb)
            row.extend(int(round(clamp(channel) * 255.0)) for channel in encoded)
        rows.append(row)

    path = os.path.join("/tmp", name.lower().replace(" ", "_") + ".png")
    write_rgb_png(path, size, size, rows)
    if os.path.getsize(path) <= 1024:
        raise RuntimeError("Generated timber PNG is suspiciously small: %s" % path)
    image = bpy.data.images.load(path, check_existing=False)
    image.name = name
    image.colorspace_settings.name = "sRGB"
    return image


def ensure_uv(obj):
    if obj.type != "MESH":
        return
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.cube_project(cube_size=1.8, correct_aspect=True)
    bpy.ops.object.mode_set(mode="OBJECT")
    obj.select_set(False)


def texture_material(material, image, roughness):
    if material is None:
        return
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    shader = nodes.get("Principled BSDF")
    if shader is None:
        shader = next((node for node in nodes if node.type == "BSDF_PRINCIPLED"), None)
    if shader is None:
        return

    for link in list(links):
        if link.to_node == shader and link.to_socket == shader.inputs.get("Base Color"):
            links.remove(link)

    tex = nodes.new("ShaderNodeTexImage")
    tex.image = image
    tex.interpolation = "Linear"
    tex.extension = "REPEAT"
    links.new(tex.outputs["Color"], shader.inputs["Base Color"])
    shader.inputs["Roughness"].default_value = roughness
    if "Specular IOR Level" in shader.inputs:
        shader.inputs["Specular IOR Level"].default_value = 0.18
    elif "Specular" in shader.inputs:
        shader.inputs["Specular"].default_value = 0.18
    if "Emission Strength" in shader.inputs:
        shader.inputs["Emission Strength"].default_value = 0.0


# Separate timber families retain the original visual hierarchy: warm wall boards,
# lighter honey details, and darker structural teak.
images = {
    "Sun Warm Timber Panel": build_wood_image(
        "Lembah Warm Timber",
        dark=(0.255, 0.120, 0.045), mid=(0.410, 0.225, 0.085), light=(0.555, 0.330, 0.135), phase=0.08,
    ),
    "Honey Timber Panel": build_wood_image(
        "Lembah Honey Timber",
        dark=(0.335, 0.175, 0.065), mid=(0.535, 0.320, 0.125), light=(0.690, 0.455, 0.205), phase=0.31,
    ),
    "Deep Teak Frame": build_wood_image(
        "Lembah Deep Teak",
        dark=(0.085, 0.035, 0.014), mid=(0.165, 0.075, 0.028), light=(0.250, 0.125, 0.050), phase=0.54,
    ),
    "Warm Teak Frame": build_wood_image(
        "Lembah Warm Teak",
        dark=(0.125, 0.055, 0.020), mid=(0.245, 0.115, 0.042), light=(0.360, 0.190, 0.075), phase=0.73,
    ),
}

roughness = {
    "Sun Warm Timber Panel": 0.88,
    "Honey Timber Panel": 0.86,
    "Deep Teak Frame": 0.90,
    "Warm Teak Frame": 0.88,
}

matched = set()
for material in bpy.data.materials:
    for prefix, image in images.items():
        if material.name.startswith(prefix):
            texture_material(material, image, roughness[prefix])
            matched.add(prefix)
            break

for obj in bpy.context.scene.objects:
    if obj.type != "MESH":
        continue
    uses_textured_wood = any(
        slot.material is not None and any(slot.material.name.startswith(prefix) for prefix in images)
        for slot in obj.material_slots
    )
    if uses_textured_wood:
        ensure_uv(obj)

missing = [name for name in images if name not in matched]
if missing:
    raise RuntimeError("House timber materials not found after GLB import: %s" % ", ".join(missing))

bpy.ops.object.select_all(action="SELECT")
bpy.ops.export_scene.gltf(
    filepath=OUT_PATH,
    export_format="GLB",
    use_selection=True,
    export_apply=True,
    export_yup=True,
)
print("Textured timber hero house exported to %s" % OUT_PATH)
