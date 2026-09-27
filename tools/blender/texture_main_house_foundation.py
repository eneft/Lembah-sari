import math
import os
import struct
import zlib

import bpy

IN_PATH = os.path.abspath(os.environ.get("LEMBAH_HOUSE_IN", "assets/models/house_main_01.glb"))
OUT_PATH = os.path.abspath(os.environ.get("LEMBAH_HOUSE_OUT", IN_PATH))
os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)

if not os.path.exists(IN_PATH):
    raise RuntimeError("Missing house GLB for foundation stone pass: %s" % IN_PATH)

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


def build_foundation_image(name, size=256):
    """Bake restrained warm stone variation for the low house footing.

    The footing is a thin strip at game scale, so the map uses broad tonal
    patches plus a few soft mineral veins instead of tiny photographic noise or
    hard brick lines. It should read as aged village stone, not concrete or a
    repeated masonry wallpaper.
    """
    tau = math.pi * 2.0
    dark = (0.235, 0.205, 0.165)
    mid = (0.390, 0.345, 0.280)
    light = (0.535, 0.470, 0.365)
    warm = (0.505, 0.385, 0.245)
    cool = (0.285, 0.325, 0.285)
    rows = []

    for py in range(size):
        v = py / float(size - 1)
        row = bytearray()
        for px in range(size):
            u = px / float(size - 1)

            broad = (
                math.sin((u * 1.45 + v * 1.10 + 0.18) * tau) * 0.125
                + math.sin((u * 2.85 - v * 2.10 + 0.47) * tau) * 0.060
                + math.sin((u * 5.25 + v * 3.60 + 0.71) * tau) * 0.024
            )
            t = clamp(0.50 + broad)
            if t < 0.50:
                q = t / 0.50
                rgb = tuple(mix(dark[c], mid[c], q) for c in range(3))
            else:
                q = (t - 0.50) / 0.50
                rgb = tuple(mix(mid[c], light[c], q) for c in range(3))

            # Warm oxidized mineral patches keep the footing tied to the house's
            # timber/terracotta palette without making it orange.
            warm_field = (
                math.sin((u * 1.20 - v * 1.75 + 0.34) * tau) * 0.70
                + math.sin((u * 3.10 + v * 1.15 + 0.12) * tau) * 0.22
            )
            warm_amount = clamp((warm_field - 0.48) / 0.38) * 0.12
            rgb = tuple(mix(rgb[c], warm[c], warm_amount) for c in range(3))

            # Sparse muted cool aging suggests damp tropical exposure near grade.
            cool_field = math.sin((u * 2.20 + v * 3.40 + 0.61) * tau)
            cool_amount = clamp((cool_field - 0.72) / 0.28) * 0.075
            rgb = tuple(mix(rgb[c], cool[c], cool_amount) for c in range(3))

            # Soft mineral vein: wide enough to survive filtering, low contrast
            # enough that it never becomes a cartoon crack pattern.
            vein_axis = v - (0.42 + 0.11 * math.sin((u * 2.1 + 0.23) * tau))
            vein = math.exp(-((vein_axis / 0.030) ** 2)) * 0.075
            rgb = tuple(mix(rgb[c], dark[c], vein) for c in range(3))

            encoded = tuple(linear_to_srgb(channel) for channel in rgb)
            row.extend(int(round(clamp(channel) * 255.0)) for channel in encoded)
        rows.append(row)

    path = os.path.join("/tmp", name.lower().replace(" ", "_") + ".png")
    write_rgb_png(path, size, size, rows)
    if os.path.getsize(path) <= 1024:
        raise RuntimeError("Generated foundation stone PNG is suspiciously small: %s" % path)
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
    bpy.ops.uv.cube_project(cube_size=2.15, correct_aspect=True)
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
        raise RuntimeError("Foundation stone material has no Principled shader: %s" % material.name)

    base_socket = shader.inputs.get("Base Color")
    for link in list(links):
        if link.to_node == shader and link.to_socket == base_socket:
            links.remove(link)

    tex = nodes.new("ShaderNodeTexImage")
    tex.image = image
    tex.interpolation = "Linear"
    tex.extension = "REPEAT"
    links.new(tex.outputs["Color"], base_socket)

    shader.inputs["Roughness"].default_value = 0.96
    if "Specular IOR Level" in shader.inputs:
        shader.inputs["Specular IOR Level"].default_value = 0.09
    elif "Specular" in shader.inputs:
        shader.inputs["Specular"].default_value = 0.09
    if "Metallic" in shader.inputs:
        shader.inputs["Metallic"].default_value = 0.0
    if "Emission Strength" in shader.inputs:
        shader.inputs["Emission Strength"].default_value = 0.0


stone_image = build_foundation_image("Lembah Warm Foundation Stone")
matched_materials = []
for material in bpy.data.materials:
    if material.name.startswith("Warm Foundation Stone"):
        texture_material(material, stone_image)
        matched_materials.append(material.name)

if not matched_materials:
    raise RuntimeError("Warm Foundation Stone material not found after house GLB import")

matched_objects = []
for obj in bpy.context.scene.objects:
    if obj.type != "MESH":
        continue
    uses_stone = any(
        slot.material is not None and slot.material.name.startswith("Warm Foundation Stone")
        for slot in obj.material_slots
    )
    if uses_stone:
        ensure_uv(obj)
        matched_objects.append(obj.name)

if not matched_objects:
    raise RuntimeError("No StoneFooting mesh uses the Warm Foundation Stone material")

bpy.ops.object.select_all(action="SELECT")
bpy.ops.export_scene.gltf(
    filepath=OUT_PATH,
    export_format="GLB",
    use_selection=True,
    export_apply=True,
    export_yup=True,
)
print("Textured foundation stone exported to %s (%s)" % (OUT_PATH, ", ".join(matched_objects)))
