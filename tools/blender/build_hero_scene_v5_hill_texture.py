import math
import os
import struct
import sys
import zlib

import bpy

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

# Install every accepted texture gate through garden bamboo without exporting.
# This gate changes only the three distant hill masses so the background can be
# reviewed independently before any later material is allowed to move.
import build_hero_scene as base
_REAL_MAIN = base.main
base.main = lambda: None
import build_hero_scene_v5_bamboo_texture  # noqa: F401
base.main = _REAL_MAIN

_PREVIOUS_GROUND = base.build_ground


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


def build_hill_image(name, dark, mid, light, warm, phase=0.0, size=256):
    """Bake broad atmospheric vegetation masses for distant village hills.

    Hills occupy a large silhouette but sit behind the playable scene. Variation
    therefore stays very low-frequency and muted: broad canopy/slope masses, a
    little sun-warmed green, and no leaf detail or photographic speckle.
    """
    tau = math.pi * 2.0
    rows = []

    for py in range(size):
        v = py / float(size - 1)
        row = bytearray()
        for px in range(size):
            u = px / float(size - 1)

            broad = (
                math.sin((u * 0.92 + v * 0.64 + phase) * tau) * 0.205
                + math.sin((u * 1.72 - v * 1.08 + 0.31 + phase * 0.45) * tau) * 0.105
                + math.sin((u * 2.85 + v * 1.55 + 0.67) * tau) * 0.040
            )

            # Keep the lower part fractionally deeper so the silhouette retains
            # weight while the upper areas read as softly sunlit vegetation.
            vertical = (0.5 - v) * 0.10
            t = clamp(0.50 + broad + vertical)
            if t < 0.50:
                q = t / 0.50
                rgb = tuple(mix(dark[c], mid[c], q) for c in range(3))
            else:
                q = (t - 0.50) / 0.50
                rgb = tuple(mix(mid[c], light[c], q) for c in range(3))

            warm_field = (
                math.sin((u * 1.28 - v * 0.76 + 0.21 + phase) * tau) * 0.72
                + math.sin((u * 2.25 + v * 1.30 + 0.56) * tau) * 0.24
            )
            warm_amount = clamp((warm_field - 0.47) / 0.45) * 0.105
            rgb = tuple(mix(rgb[c], warm[c], warm_amount) for c in range(3))

            encoded = tuple(linear_to_srgb(channel) for channel in rgb)
            row.extend(int(round(clamp(channel) * 255.0)) for channel in encoded)
        rows.append(row)

    path = os.path.join("/tmp", name.lower().replace(" ", "_") + ".png")
    write_rgb_png(path, size, size, rows)
    if os.path.getsize(path) <= 1024:
        raise RuntimeError("Generated distant hill PNG is suspiciously small: %s" % path)

    image = bpy.data.images.load(path, check_existing=False)
    image.name = name
    image.colorspace_settings.name = "sRGB"
    return image


def textured_material(name, source_material, image, roughness=0.98):
    material = source_material.copy()
    material.name = name
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    shader = nodes.get("Principled BSDF") or next(
        (node for node in nodes if node.type == "BSDF_PRINCIPLED"), None
    )
    if shader is None:
        raise RuntimeError("Distant hill material has no Principled shader: %s" % material.name)

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
        shader.inputs["Specular IOR Level"].default_value = 0.06
    elif "Specular" in shader.inputs:
        shader.inputs["Specular"].default_value = 0.06
    if "Metallic" in shader.inputs:
        shader.inputs["Metallic"].default_value = 0.0
    if "Emission Strength" in shader.inputs:
        shader.inputs["Emission Strength"].default_value = 0.0
    return material


def ensure_uv(obj):
    if obj is None or obj.type != "MESH":
        return
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(66.0), island_margin=0.025)
    bpy.ops.object.mode_set(mode="OBJECT")
    obj.select_set(False)


def assign(obj, material):
    if obj is None or obj.type != "MESH":
        raise RuntimeError("Expected distant hill mesh was not created")
    ensure_uv(obj)
    obj.data.materials.clear()
    obj.data.materials.append(material)


def textured_ground():
    _PREVIOUS_GROUND()

    deep_image = build_hill_image(
        "Lembah Distant Hill Deep",
        dark=(0.055, 0.145, 0.070),
        mid=(0.105, 0.235, 0.105),
        light=(0.175, 0.330, 0.145),
        warm=(0.245, 0.355, 0.135),
        phase=0.13,
    )
    light_image = build_hill_image(
        "Lembah Distant Hill Sun",
        dark=(0.080, 0.185, 0.080),
        mid=(0.145, 0.285, 0.120),
        light=(0.225, 0.385, 0.165),
        warm=(0.305, 0.405, 0.145),
        phase=0.49,
    )

    deep_mat = textured_material("V5 Textured Distant Hill", base.MAT_HILL, deep_image)
    light_mat = textured_material("V5 Textured Distant Hill Light", base.MAT_HILL_LIGHT, light_image)

    assign(bpy.data.objects.get("BackHillA"), deep_mat)
    assign(bpy.data.objects.get("BackHillB"), light_mat)
    assign(bpy.data.objects.get("BackHillC"), deep_mat)


base.build_ground = textured_ground
_REAL_MAIN()
