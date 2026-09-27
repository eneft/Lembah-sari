import math
import os
import struct
import zlib

import bpy

IN_PATH = os.path.abspath(os.environ.get("LEMBAH_HOUSE_IN", "assets/models/house_main_01.glb"))
OUT_PATH = os.path.abspath(os.environ.get("LEMBAH_HOUSE_OUT", IN_PATH))
os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)

if not os.path.exists(IN_PATH):
    raise RuntimeError("Missing house GLB for porch plant pass: %s" % IN_PATH)

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
    data = (
        b"\x89PNG\r\n\x1a\n"
        + png_chunk(b"IHDR", ihdr)
        + png_chunk(b"IDAT", zlib.compress(bytes(raw), 9))
        + png_chunk(b"IEND", b"")
    )
    with open(path, "wb") as handle:
        handle.write(data)


def build_plant_image(name, size=256):
    """Bake broad tropical leaf-cluster color variation for the porch plants.

    The plant crowns are tiny at the fixed gameplay camera, so this texture uses
    large dark/mid/sunlit masses rather than veins, speckles, or photographic
    noise. The palette stays warm-natural and deliberately separates the porch
    plants from both the deep timber facade and the cooler surrounding foliage.
    """
    tau = math.pi * 2.0
    deep = (0.035, 0.120, 0.025)
    shade = (0.070, 0.220, 0.040)
    leaf = (0.125, 0.355, 0.065)
    sun = (0.245, 0.495, 0.105)
    warm = (0.360, 0.505, 0.105)
    rows = []

    for py in range(size):
        v = py / float(size - 1)
        row = bytearray()
        for px in range(size):
            u = px / float(size - 1)

            # Large overlapping masses survive the small on-screen crown size.
            broad = (
                math.sin((u * 1.30 + v * 0.92 + 0.13) * tau) * 0.20
                + math.sin((u * 2.35 - v * 1.55 + 0.47) * tau) * 0.11
                + math.sin((u * 3.60 + v * 2.20 + 0.71) * tau) * 0.045
            )
            # Slightly brighter toward the upper half, like a porch plant catching sun.
            upper_light = (1.0 - v) * 0.13
            t = clamp(0.50 + broad + upper_light)

            if t < 0.34:
                q = t / 0.34
                rgb = tuple(mix(deep[c], shade[c], q) for c in range(3))
            elif t < 0.68:
                q = (t - 0.34) / 0.34
                rgb = tuple(mix(shade[c], leaf[c], q) for c in range(3))
            else:
                q = (t - 0.68) / 0.32
                rgb = tuple(mix(leaf[c], sun[c], q) for c in range(3))

            # A few broad warm leaf clusters prevent the crown reading as a flat
            # cool-green ball without introducing yellow neon or tiny texture noise.
            warm_field = (
                math.sin((u * 1.75 + v * 1.30 + 0.28) * tau) * 0.72
                + math.sin((u * 3.05 - v * 1.95 + 0.62) * tau) * 0.28
            )
            warm_amount = clamp((warm_field - 0.42) / 0.50) * 0.18
            rgb = tuple(mix(rgb[c], warm[c], warm_amount) for c in range(3))

            # Soft lower shade gives the rounded crown a stronger graphic read.
            lower = clamp((v - 0.58) / 0.42) * 0.12
            rgb = tuple(mix(rgb[c], deep[c], lower) for c in range(3))

            encoded = tuple(linear_to_srgb(channel) for channel in rgb)
            row.extend(int(round(clamp(channel) * 255.0)) for channel in encoded)
        rows.append(row)

    path = os.path.join("/tmp", name.lower().replace(" ", "_") + ".png")
    write_rgb_png(path, size, size, rows)
    if os.path.getsize(path) <= 1024:
        raise RuntimeError("Generated porch plant PNG is suspiciously small: %s" % path)
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
    bpy.ops.uv.smart_project(angle_limit=math.radians(66.0), island_margin=0.03)
    bpy.ops.object.mode_set(mode="OBJECT")
    obj.select_set(False)


def texture_material(material, image):
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    shader = nodes.get("Principled BSDF") or next(
        (node for node in nodes if node.type == "BSDF_PRINCIPLED"), None
    )
    if shader is None:
        raise RuntimeError("Porch plant material has no Principled shader: %s" % material.name)

    base_socket = shader.inputs.get("Base Color")
    for link in list(links):
        if link.to_node == shader and link.to_socket == base_socket:
            links.remove(link)

    tex = nodes.new("ShaderNodeTexImage")
    tex.image = image
    tex.interpolation = "Linear"
    tex.extension = "REPEAT"
    links.new(tex.outputs["Color"], base_socket)

    shader.inputs["Roughness"].default_value = 0.94
    if "Specular IOR Level" in shader.inputs:
        shader.inputs["Specular IOR Level"].default_value = 0.10
    elif "Specular" in shader.inputs:
        shader.inputs["Specular"].default_value = 0.10
    if "Metallic" in shader.inputs:
        shader.inputs["Metallic"].default_value = 0.0
    if "Emission Strength" in shader.inputs:
        shader.inputs["Emission Strength"].default_value = 0.0


plant_image = build_plant_image("Lembah Porch Plant Broad Leaf")
matched_materials = []
for material in bpy.data.materials:
    if material.name.startswith("Porch Plant Green"):
        texture_material(material, plant_image)
        matched_materials.append(material.name)

if not matched_materials:
    raise RuntimeError("Porch Plant Green material not found after house GLB import")

matched_objects = []
for obj in bpy.context.scene.objects:
    if obj.type != "MESH":
        continue
    uses_plant = any(
        slot.material is not None and slot.material.name.startswith("Porch Plant Green")
        for slot in obj.material_slots
    )
    if uses_plant:
        ensure_uv(obj)
        matched_objects.append(obj.name)

if not matched_objects:
    raise RuntimeError("No porch plant crown mesh uses the Porch Plant Green material")

bpy.ops.object.select_all(action="SELECT")
bpy.ops.export_scene.gltf(
    filepath=OUT_PATH,
    export_format="GLB",
    use_selection=True,
    export_apply=True,
    export_yup=True,
)
print("Textured porch plants exported to %s (%s)" % (OUT_PATH, ", ".join(matched_objects)))
