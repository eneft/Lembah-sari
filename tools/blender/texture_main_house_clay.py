import math
import os
import struct
import zlib

import bpy

IN_PATH = os.path.abspath(os.environ.get("LEMBAH_HOUSE_IN", "assets/models/house_main_01.glb"))
OUT_PATH = os.path.abspath(os.environ.get("LEMBAH_HOUSE_OUT", IN_PATH))
os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)

if not os.path.exists(IN_PATH):
    raise RuntimeError("Missing house GLB for clay pot pass: %s" % IN_PATH)

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


def build_clay_image(name, dark, mid, light, phase=0.0, size=256):
    """Bake restrained handmade terracotta variation for small porch pots.

    The pattern is intentionally low contrast: broad fired-clay mottling plus a
    few soft pores. From the game camera it should read as ceramic/clay surface,
    not as noise or stripes.
    """
    tau = math.pi * 2.0
    rows = []
    for py in range(size):
        v = py / float(size - 1)
        row = bytearray()
        for px in range(size):
            u = px / float(size - 1)

            mottled = (
                math.sin((u * 2.7 + v * 1.9 + phase) * tau) * 0.085
                + math.sin((u * 5.6 - v * 4.1 + 0.23 + phase * 0.4) * tau) * 0.040
                + math.sin((u * 11.0 + v * 9.0 + 0.47) * tau) * 0.015
            )
            fired = math.sin((u * 1.15 - v * 2.35 + 0.38 + phase) * tau) * 0.035
            t = clamp(0.50 + mottled + fired)

            if t < 0.50:
                q = t / 0.50
                rgb = tuple(mix(dark[c], mid[c], q) for c in range(3))
            else:
                q = (t - 0.50) / 0.50
                rgb = tuple(mix(mid[c], light[c], q) for c in range(3))

            # A sparse, very soft dark pore field avoids a plastic read without
            # introducing photorealistic speckle noise.
            pore = math.sin((u * 19.0 + v * 17.0 + 0.67) * tau) * math.sin((u * 13.0 - v * 21.0 + 0.17) * tau)
            pore = clamp((pore - 0.82) / 0.18) * 0.025
            pore_tint = (0.20, 0.055, 0.025)
            rgb = tuple(mix(rgb[c], pore_tint[c], pore) for c in range(3))

            encoded = tuple(linear_to_srgb(channel) for channel in rgb)
            row.extend(int(round(clamp(channel) * 255.0)) for channel in encoded)
        rows.append(row)

    path = os.path.join("/tmp", name.lower().replace(" ", "_") + ".png")
    write_rgb_png(path, size, size, rows)
    if os.path.getsize(path) <= 1024:
        raise RuntimeError("Generated clay PNG is suspiciously small: %s" % path)
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


def texture_material(material, image, roughness=0.95):
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    shader = nodes.get("Principled BSDF") or next((node for node in nodes if node.type == "BSDF_PRINCIPLED"), None)
    if shader is None:
        raise RuntimeError("Clay material has no Principled shader: %s" % material.name)

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
        shader.inputs["Specular IOR Level"].default_value = 0.12
    elif "Specular" in shader.inputs:
        shader.inputs["Specular"].default_value = 0.12
    if "Emission Strength" in shader.inputs:
        shader.inputs["Emission Strength"].default_value = 0.0


clay_image = build_clay_image(
    "Lembah Handmade Clay",
    dark=(0.34, 0.095, 0.040),
    mid=(0.56, 0.205, 0.085),
    light=(0.72, 0.330, 0.145),
    phase=0.19,
)

matched_material = False
for material in bpy.data.materials:
    if material.name.startswith("Clay Pot"):
        texture_material(material, clay_image, 0.95)
        matched_material = True

matched_objects = []
for obj in bpy.context.scene.objects:
    if obj.type != "MESH":
        continue
    uses_clay = any(
        slot.material is not None and slot.material.name.startswith("Clay Pot")
        for slot in obj.material_slots
    )
    if uses_clay:
        ensure_uv(obj)
        matched_objects.append(obj.name)

if not matched_material:
    raise RuntimeError("Clay Pot material not found after house GLB import")
if not matched_objects:
    raise RuntimeError("No ClayPot mesh uses the Clay Pot material")

bpy.ops.object.select_all(action="SELECT")
bpy.ops.export_scene.gltf(
    filepath=OUT_PATH,
    export_format="GLB",
    use_selection=True,
    export_apply=True,
    export_yup=True,
)
print("Textured clay pots exported to %s (%s)" % (OUT_PATH, ", ".join(matched_objects)))
