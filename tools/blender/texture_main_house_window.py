import math
import os
import struct
import zlib

import bpy

IN_PATH = os.path.abspath(os.environ.get("LEMBAH_HOUSE_IN", "assets/models/house_main_01.glb"))
OUT_PATH = os.path.abspath(os.environ.get("LEMBAH_HOUSE_OUT", IN_PATH))
os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)

if not os.path.exists(IN_PATH):
    raise RuntimeError("Missing house GLB for window-glass pass: %s" % IN_PATH)

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


def build_window_image(name, size=256):
    """Bake stylized village-window color variation for the fixed hero camera.

    The goal is not physically transparent glass. Godot's GLB path stays more
    predictable with an opaque pane, so the texture sells glass through cool
    depth, a restrained sky reflection, faint vertical age streaks, and a
    slightly dusty lower edge. Broad variation survives the gameplay camera
    while avoiding the old flat cyan-card read.
    """
    tau = math.pi * 2.0
    deep = (0.075, 0.255, 0.285)
    mid = (0.135, 0.405, 0.440)
    sky = (0.335, 0.620, 0.635)
    dust = (0.285, 0.360, 0.300)
    rows = []

    for py in range(size):
        v = py / float(size - 1)
        row = bytearray()
        for px in range(size):
            u = px / float(size - 1)

            # Broad cool-depth modulation: enough structure to read as glass,
            # but not enough frequency to become noisy from the game camera.
            broad = (
                math.sin((u * 1.10 + v * 0.72 + 0.17) * tau) * 0.055
                + math.sin((u * 0.42 - v * 1.38 + 0.49) * tau) * 0.030
            )
            t = clamp(0.50 + broad)
            rgb = tuple(mix(deep[c], mid[c], t) for c in range(3))

            # One soft diagonal reflection band. This replaces the flat cyan
            # billboard look without pretending to be a mirror.
            reflection_axis = (u * 0.82 + (1.0 - v) * 0.58)
            reflection = math.exp(-((reflection_axis - 0.78) / 0.16) ** 2) * 0.34
            reflection *= 0.84 + math.sin((u * 1.6 + v * 0.45) * tau) * 0.08
            rgb = tuple(mix(rgb[c], sky[c], clamp(reflection)) for c in range(3))

            # Fine, low-contrast vertical weathering; visible as richness rather
            # than literal stripes at hero distance.
            streak = (
                math.sin((u * 17.0 + 0.31) * tau) * 0.010
                + math.sin((u * 29.0 + v * 1.3 + 0.73) * tau) * 0.006
            )
            rgb = tuple(clamp(channel + streak) for channel in rgb)

            # Slight dusty tint toward the sill anchors the pane in an inhabited
            # tropical village instead of reading as pristine synthetic plastic.
            lower = clamp((v - 0.72) / 0.28)
            dust_noise = 0.50 + math.sin((u * 3.2 + 0.19) * tau) * 0.22
            dust_amount = lower * dust_noise * 0.075
            rgb = tuple(mix(rgb[c], dust[c], dust_amount) for c in range(3))

            encoded = tuple(linear_to_srgb(channel) for channel in rgb)
            row.extend(int(round(clamp(channel) * 255.0)) for channel in encoded)
        rows.append(row)

    path = os.path.join("/tmp", name.lower().replace(" ", "_") + ".png")
    write_rgb_png(path, size, size, rows)
    if os.path.getsize(path) <= 1024:
        raise RuntimeError("Generated window PNG is suspiciously small: %s" % path)
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
    bpy.ops.uv.cube_project(cube_size=1.25, correct_aspect=True)
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
        raise RuntimeError("Window material has no Principled shader: %s" % material.name)

    base_socket = shader.inputs.get("Base Color")
    for link in list(links):
        if link.to_node == shader and link.to_socket == base_socket:
            links.remove(link)

    tex = nodes.new("ShaderNodeTexImage")
    tex.image = image
    tex.interpolation = "Linear"
    tex.extension = "REPEAT"
    links.new(tex.outputs["Color"], base_socket)

    shader.inputs["Roughness"].default_value = 0.44
    if "Specular IOR Level" in shader.inputs:
        shader.inputs["Specular IOR Level"].default_value = 0.32
    elif "Specular" in shader.inputs:
        shader.inputs["Specular"].default_value = 0.32
    if "Metallic" in shader.inputs:
        shader.inputs["Metallic"].default_value = 0.0
    if "Emission Strength" in shader.inputs:
        shader.inputs["Emission Strength"].default_value = 0.0


window_image = build_window_image("Lembah Weathered Teal Window")
matched_materials = []
for material in bpy.data.materials:
    if material.name.startswith("Muted Teal Window"):
        texture_material(material, window_image)
        matched_materials.append(material.name)

if not matched_materials:
    raise RuntimeError("Muted Teal Window material not found after house GLB import")

matched_objects = []
for obj in bpy.context.scene.objects:
    if obj.type != "MESH":
        continue
    uses_window = any(
        slot.material is not None and slot.material.name.startswith("Muted Teal Window")
        for slot in obj.material_slots
    )
    if uses_window:
        ensure_uv(obj)
        matched_objects.append(obj.name)

if not matched_objects:
    raise RuntimeError("No WindowGlass mesh uses the expected Muted Teal Window material")

bpy.ops.object.select_all(action="SELECT")
bpy.ops.export_scene.gltf(
    filepath=OUT_PATH,
    export_format="GLB",
    use_selection=True,
    export_apply=True,
    export_yup=True,
)
print("Textured hero-house window glass exported to %s (%s)" % (OUT_PATH, ", ".join(matched_objects)))
