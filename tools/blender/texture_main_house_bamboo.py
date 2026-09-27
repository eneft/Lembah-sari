import math
import os
import struct
import zlib

import bpy

IN_PATH = os.path.abspath(os.environ.get("LEMBAH_HOUSE_IN", "assets/models/house_main_01.glb"))
OUT_PATH = os.path.abspath(os.environ.get("LEMBAH_HOUSE_OUT", IN_PATH))
os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)

if not os.path.exists(IN_PATH):
    raise RuntimeError("Missing house GLB for bamboo lattice pass: %s" % IN_PATH)

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


def build_bamboo_image(name, size=256):
    """Bake warm dry bamboo variation for the porch lattice.

    The same material is shared by vertical poles and horizontal rails, so this
    deliberately avoids painted node rings. Geometry supplies the segmentation;
    the map adds long soft fibre, sun bleaching, and restrained olive age marks
    that remain readable without turning into stripes at the fixed hero camera.
    """
    tau = math.pi * 2.0
    dark = (0.225, 0.165, 0.055)
    mid = (0.455, 0.355, 0.115)
    light = (0.675, 0.560, 0.225)
    sun = (0.760, 0.665, 0.335)
    olive = (0.185, 0.245, 0.070)
    rows = []

    for py in range(size):
        v = py / float(size - 1)
        row = bytearray()
        for px in range(size):
            u = px / float(size - 1)

            broad = (
                math.sin((u * 1.65 + v * 1.05 + 0.21) * tau) * 0.105
                + math.sin((u * 3.10 - v * 1.75 + 0.48) * tau) * 0.050
            )
            fibre = (
                math.sin((u * 13.0 + v * 1.8 + 0.32) * tau) * 0.020
                + math.sin((u * 27.0 - v * 2.4 + 0.71) * tau) * 0.009
            )
            t = clamp(0.50 + broad + fibre)
            if t < 0.50:
                q = t / 0.50
                rgb = tuple(mix(dark[c], mid[c], q) for c in range(3))
            else:
                q = (t - 0.50) / 0.50
                rgb = tuple(mix(mid[c], light[c], q) for c in range(3))

            # Soft sun-bleached patches help the small lattice stand apart from
            # the dark timber facade without becoming bright yellow plastic.
            sun_field = math.sin((u * 1.20 - v * 1.45 + 0.17) * tau)
            sun_amount = clamp((sun_field - 0.30) / 0.70) * 0.16
            rgb = tuple(mix(rgb[c], sun[c], sun_amount) for c in range(3))

            # Sparse olive age variation ties the porch bamboo to the already
            # accepted garden bamboo while keeping the house screen slightly drier.
            age_field = (
                math.sin((u * 2.35 + v * 2.75 + 0.55) * tau) * 0.68
                + math.sin((u * 4.10 - v * 1.20 + 0.12) * tau) * 0.24
            )
            age_amount = clamp((age_field - 0.58) / 0.30) * 0.11
            rgb = tuple(mix(rgb[c], olive[c], age_amount) for c in range(3))

            encoded = tuple(linear_to_srgb(channel) for channel in rgb)
            row.extend(int(round(clamp(channel) * 255.0)) for channel in encoded)
        rows.append(row)

    path = os.path.join("/tmp", name.lower().replace(" ", "_") + ".png")
    write_rgb_png(path, size, size, rows)
    if os.path.getsize(path) <= 1024:
        raise RuntimeError("Generated house bamboo PNG is suspiciously small: %s" % path)
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
    bpy.ops.uv.smart_project(angle_limit=math.radians(66.0), island_margin=0.025)
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
        raise RuntimeError("House bamboo material has no Principled shader: %s" % material.name)

    base_socket = shader.inputs.get("Base Color")
    for link in list(links):
        if link.to_node == shader and link.to_socket == base_socket:
            links.remove(link)

    tex = nodes.new("ShaderNodeTexImage")
    tex.image = image
    tex.interpolation = "Linear"
    tex.extension = "REPEAT"
    links.new(tex.outputs["Color"], base_socket)

    shader.inputs["Roughness"].default_value = 0.91
    if "Specular IOR Level" in shader.inputs:
        shader.inputs["Specular IOR Level"].default_value = 0.13
    elif "Specular" in shader.inputs:
        shader.inputs["Specular"].default_value = 0.13
    if "Metallic" in shader.inputs:
        shader.inputs["Metallic"].default_value = 0.0
    if "Emission Strength" in shader.inputs:
        shader.inputs["Emission Strength"].default_value = 0.0


bamboo_image = build_bamboo_image("Lembah Dry Porch Bamboo")
matched_materials = []
for material in bpy.data.materials:
    if material.name.startswith("Dry Bamboo"):
        texture_material(material, bamboo_image)
        matched_materials.append(material.name)

if not matched_materials:
    raise RuntimeError("Dry Bamboo material not found after house GLB import")

matched_objects = []
for obj in bpy.context.scene.objects:
    if obj.type != "MESH":
        continue
    uses_bamboo = any(
        slot.material is not None and slot.material.name.startswith("Dry Bamboo")
        for slot in obj.material_slots
    )
    if uses_bamboo:
        ensure_uv(obj)
        matched_objects.append(obj.name)

if not matched_objects:
    raise RuntimeError("No house bamboo lattice mesh uses the Dry Bamboo material")

bpy.ops.object.select_all(action="SELECT")
bpy.ops.export_scene.gltf(
    filepath=OUT_PATH,
    export_format="GLB",
    use_selection=True,
    export_apply=True,
    export_yup=True,
)
print("Textured house bamboo lattice exported to %s (%s)" % (OUT_PATH, ", ".join(matched_objects)))
