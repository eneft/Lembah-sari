import math
import os
import struct
import zlib

import bpy

IN_PATH = os.path.abspath(os.environ.get("LEMBAH_HOUSE_IN", "assets/models/house_main_01.glb"))
OUT_PATH = os.path.abspath(os.environ.get("LEMBAH_HOUSE_OUT", IN_PATH))
os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)

if not os.path.exists(IN_PATH):
    raise RuntimeError("Missing house GLB for hanging cloth pass: %s" % IN_PATH)

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


def build_cloth_image(name, dark, mid, light, phase=0.0, size=256):
    """Bake restrained woven color variation for the porch hanging cloth.

    The cloth needs to read from a fixed elevated game camera, so broad faded
    patches lead the look while the weave is deliberately faint. This avoids a
    burlap/photo-texture appearance while still breaking the old flat-color read.
    """
    tau = math.pi * 2.0
    rows = []
    for py in range(size):
        v = py / float(size - 1)
        row = bytearray()
        for px in range(size):
            u = px / float(size - 1)

            fade = (
                math.sin((u * 1.15 + v * 0.72 + phase) * tau) * 0.080
                + math.sin((u * 0.58 - v * 1.65 + 0.31 + phase * 0.7) * tau) * 0.055
                + math.sin((u * 2.25 + v * 2.05 + 0.17) * tau) * 0.022
            )

            # Very small cross-thread influence. At hero distance this should be
            # perceived as fabric richness rather than visible stripes.
            warp = math.sin((u * 38.0 + phase) * tau) * 0.010
            weft = math.sin((v * 44.0 + phase * 0.5) * tau) * 0.008
            t = clamp(0.50 + fade + warp + weft)

            if t < 0.50:
                q = t / 0.50
                rgb = tuple(mix(dark[c], mid[c], q) for c in range(3))
            else:
                q = (t - 0.50) / 0.50
                rgb = tuple(mix(mid[c], light[c], q) for c in range(3))

            # Soft sun-faded vertical banding adds age without dirtying the cloth.
            sun = clamp((math.sin((u * 1.7 + 0.21 + phase) * tau) - 0.40) / 0.60) * 0.035
            sun_tint = tuple(min(1.0, light[c] * 1.05 + 0.015) for c in range(3))
            rgb = tuple(mix(rgb[c], sun_tint[c], sun) for c in range(3))

            encoded = tuple(linear_to_srgb(channel) for channel in rgb)
            row.extend(int(round(clamp(channel) * 255.0)) for channel in encoded)
        rows.append(row)

    path = os.path.join("/tmp", name.lower().replace(" ", "_") + ".png")
    write_rgb_png(path, size, size, rows)
    if os.path.getsize(path) <= 1024:
        raise RuntimeError("Generated cloth PNG is suspiciously small: %s" % path)
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


def texture_material(material, image, roughness=0.975):
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    shader = nodes.get("Principled BSDF") or next((node for node in nodes if node.type == "BSDF_PRINCIPLED"), None)
    if shader is None:
        raise RuntimeError("Cloth material has no Principled shader: %s" % material.name)

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
        shader.inputs["Specular IOR Level"].default_value = 0.10
    elif "Specular" in shader.inputs:
        shader.inputs["Specular"].default_value = 0.10
    if "Emission Strength" in shader.inputs:
        shader.inputs["Emission Strength"].default_value = 0.0


coral_image = build_cloth_image(
    "Lembah Faded Coral Fabric",
    dark=(0.43, 0.155, 0.110),
    mid=(0.62, 0.275, 0.205),
    light=(0.76, 0.405, 0.315),
    phase=0.13,
)
cream_image = build_cloth_image(
    "Lembah Warm Cream Fabric",
    dark=(0.57, 0.445, 0.265),
    mid=(0.76, 0.635, 0.420),
    light=(0.88, 0.785, 0.585),
    phase=0.47,
)

material_images = {
    "Faded Coral Cloth": coral_image,
    "Warm Cream Cloth": cream_image,
}
matched_materials = set()
for material in bpy.data.materials:
    for prefix, image in material_images.items():
        if material.name.startswith(prefix):
            texture_material(material, image)
            matched_materials.add(prefix)
            break

matched_objects = []
for obj in bpy.context.scene.objects:
    if obj.type != "MESH":
        continue
    uses_cloth = any(
        slot.material is not None
        and any(slot.material.name.startswith(prefix) for prefix in material_images)
        for slot in obj.material_slots
    )
    if uses_cloth:
        ensure_uv(obj)
        matched_objects.append(obj.name)

missing = sorted(set(material_images) - matched_materials)
if missing:
    raise RuntimeError("Hanging cloth materials not found after house GLB import: %s" % ", ".join(missing))
if not matched_objects:
    raise RuntimeError("No HangingCloth mesh uses the expected cloth materials")

bpy.ops.object.select_all(action="SELECT")
bpy.ops.export_scene.gltf(
    filepath=OUT_PATH,
    export_format="GLB",
    use_selection=True,
    export_apply=True,
    export_yup=True,
)
print("Textured hanging cloth exported to %s (%s)" % (OUT_PATH, ", ".join(matched_objects)))
