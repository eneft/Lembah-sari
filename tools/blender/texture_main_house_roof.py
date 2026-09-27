import math
import os
import struct
import zlib

import bpy

IN_PATH = os.path.abspath(os.environ.get("LEMBAH_HOUSE_IN", "assets/models/house_main_01.glb"))
OUT_PATH = os.path.abspath(os.environ.get("LEMBAH_HOUSE_OUT", IN_PATH))
os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)

if not os.path.exists(IN_PATH):
    raise RuntimeError("Missing house GLB for roof pass: %s" % IN_PATH)

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
    data = b"\x89PNG\r\n\x1a\n" + png_chunk(b"IHDR", ihdr) + png_chunk(b"IDAT", zlib.compress(bytes(raw), 9)) + png_chunk(b"IEND", b"")
    with open(path, "wb") as handle:
        handle.write(data)


def build_terracotta_image(name, dark, mid, light, phase=0.0, size=256):
    """Bake gentle clay color variation, avoiding photographic micro-noise."""
    tau = math.pi * 2.0
    rows = []
    for py in range(size):
        v = py / float(size - 1)
        row = bytearray()
        for px in range(size):
            u = px / float(size - 1)
            broad = (
                math.sin((u * 1.8 + v * 0.9 + phase) * tau) * 0.15
                + math.sin((u * 3.6 - v * 2.2 + 0.27) * tau) * 0.075
                + math.sin((u * 7.0 + v * 5.2 + 0.53) * tau) * 0.030
            )
            age = math.sin((u * 11.0 - v * 9.0 + phase * 0.7) * tau) * 0.018
            t = clamp(0.50 + broad + age)
            if t < 0.50:
                q = t / 0.50
                rgb = tuple(mix(dark[c], mid[c], q) for c in range(3))
            else:
                q = (t - 0.50) / 0.50
                rgb = tuple(mix(mid[c], light[c], q) for c in range(3))

            # Sparse sun-faded clay patches keep the roof handmade rather than flat.
            fade = clamp((math.sin((u * 4.1 + v * 3.3 + 0.42) * tau) - 0.76) / 0.24) * 0.035
            faded = (0.62, 0.27, 0.14)
            rgb = tuple(mix(rgb[c], faded[c], fade) for c in range(3))
            encoded = tuple(linear_to_srgb(channel) for channel in rgb)
            row.extend(int(round(clamp(channel) * 255.0)) for channel in encoded)
        rows.append(row)

    path = os.path.join("/tmp", name.lower().replace(" ", "_") + ".png")
    write_rgb_png(path, size, size, rows)
    if os.path.getsize(path) <= 1024:
        raise RuntimeError("Generated terracotta PNG is suspiciously small: %s" % path)
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
    bpy.ops.uv.cube_project(cube_size=2.2, correct_aspect=True)
    bpy.ops.object.mode_set(mode="OBJECT")
    obj.select_set(False)


def texture_material(material, image, roughness):
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    shader = nodes.get("Principled BSDF") or next((n for n in nodes if n.type == "BSDF_PRINCIPLED"), None)
    if shader is None:
        raise RuntimeError("Terracotta material has no Principled shader: %s" % material.name)

    base_socket = shader.inputs.get("Base Color")
    for link in list(links):
        if link.to_node == shader and link.to_socket == base_socket:
            links.remove(link)

    tex = nodes.new("ShaderNodeTexImage")
    tex.image = image
    tex.interpolation = "Linear"
    tex.extension = "REPEAT"
    links.new(tex.outputs["Color"], base_socket)
    shader.inputs["Roughness"].default_value = roughness
    if "Specular IOR Level" in shader.inputs:
        shader.inputs["Specular IOR Level"].default_value = 0.17
    elif "Specular" in shader.inputs:
        shader.inputs["Specular"].default_value = 0.17
    if "Emission Strength" in shader.inputs:
        shader.inputs["Emission Strength"].default_value = 0.0


families = {
    "Soft Terracotta": (
        build_terracotta_image("Lembah Terracotta Main", (0.30, 0.075, 0.035), (0.50, 0.145, 0.065), (0.67, 0.255, 0.115), 0.10),
        0.91,
    ),
    "Sunlit Terracotta": (
        build_terracotta_image("Lembah Terracotta Sun", (0.39, 0.105, 0.045), (0.61, 0.215, 0.095), (0.76, 0.345, 0.155), 0.34),
        0.89,
    ),
    "Terracotta Shadow": (
        build_terracotta_image("Lembah Terracotta Shade", (0.20, 0.045, 0.025), (0.34, 0.085, 0.040), (0.48, 0.145, 0.070), 0.62),
        0.93,
    ),
}

matched = set()
for material in bpy.data.materials:
    for prefix, (image, roughness) in families.items():
        if material.name.startswith(prefix):
            texture_material(material, image, roughness)
            matched.add(prefix)
            break

for obj in bpy.context.scene.objects:
    if obj.type != "MESH":
        continue
    if any(
        slot.material is not None and any(slot.material.name.startswith(prefix) for prefix in families)
        for slot in obj.material_slots
    ):
        ensure_uv(obj)

missing = [prefix for prefix in families if prefix not in matched]
if missing:
    raise RuntimeError("House roof materials not found after GLB import: %s" % ", ".join(missing))

bpy.ops.object.select_all(action="SELECT")
bpy.ops.export_scene.gltf(
    filepath=OUT_PATH,
    export_format="GLB",
    use_selection=True,
    export_apply=True,
    export_yup=True,
)
print("Textured terracotta hero house exported to %s" % OUT_PATH)
