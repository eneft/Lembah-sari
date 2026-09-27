import math
import os
import struct
import sys
import zlib

import bpy

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

# Load the fully polished V5 composition without exporting it yet. This pass is
# deliberately limited to the ground surface; path/house/roof materials remain
# untouched until this ground pass is visually accepted.
import build_hero_scene as base
_REAL_MAIN = base.main
base.main = lambda: None
import build_hero_scene_v5_polish  # noqa: F401
base.main = _REAL_MAIN

_POLISHED_GROUND = base.build_ground


def _clamp(value, lo=0.0, hi=1.0):
    return max(lo, min(hi, value))


def _mix(a, b, t):
    return a + (b - a) * t


def _linear_to_srgb(value):
    value = _clamp(value)
    if value <= 0.0031308:
        return value * 12.92
    return 1.055 * (value ** (1.0 / 2.4)) - 0.055


def _png_chunk(kind, payload):
    return (
        struct.pack(">I", len(payload))
        + kind
        + payload
        + struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF)
    )


def _write_rgb_png(path, width, height, rows):
    """Write an RGB8 PNG directly with stdlib so Blender cannot zero the pixels."""
    raw = bytearray()
    for row in rows:
        raw.append(0)  # PNG filter: None
        raw.extend(row)
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    payload = (
        b"\x89PNG\r\n\x1a\n"
        + _png_chunk(b"IHDR", ihdr)
        + _png_chunk(b"IDAT", zlib.compress(bytes(raw), 9))
        + _png_chunk(b"IEND", b"")
    )
    with open(path, "wb") as handle:
        handle.write(payload)


def _build_grass_texture(name, dark, mid, light, phase=0.0, size=256):
    """Bake a subtle stylized grass albedo to a real PNG and load it into Blender."""
    tau = math.pi * 2.0
    rows = []
    for py in range(size):
        v = py / float(size - 1)
        row = bytearray()
        for px in range(size):
            u = px / float(size - 1)
            broad = (
                math.sin((u * 1.55 + v * 0.62 + phase) * tau) * 0.25
                + math.sin((u * 0.72 - v * 1.38 + phase * 0.7) * tau) * 0.17
                + math.sin((u * 2.65 + v * 2.15 + 0.19 + phase) * tau) * 0.10
            )
            fine = (
                math.sin((u * 12.0 + v * 7.0 + phase) * tau)
                * math.sin((u * 8.0 - v * 11.0 + 0.31) * tau)
            ) * 0.025
            t = _clamp(0.50 + broad + fine)

            if t < 0.50:
                q = t / 0.50
                rgb = tuple(_mix(dark[c], mid[c], q) for c in range(3))
            else:
                q = (t - 0.50) / 0.50
                rgb = tuple(_mix(mid[c], light[c], q) for c in range(3))

            dry = _clamp((math.sin((u * 3.7 - v * 2.9 + 0.41 + phase) * tau) - 0.68) / 0.32)
            dry *= 0.035
            dry_tint = (0.32, 0.30, 0.11)
            rgb = tuple(_mix(rgb[c], dry_tint[c], dry) for c in range(3))
            encoded = tuple(_linear_to_srgb(channel) for channel in rgb)
            row.extend(int(round(_clamp(channel) * 255.0)) for channel in encoded)
        rows.append(row)

    texture_path = os.path.join("/tmp", name.lower().replace(" ", "_") + ".png")
    _write_rgb_png(texture_path, size, size, rows)
    if os.path.getsize(texture_path) <= 1024:
        raise RuntimeError("Generated grass PNG is suspiciously small: %s" % texture_path)

    image = bpy.data.images.load(texture_path, check_existing=False)
    image.name = name
    image.colorspace_settings.name = "sRGB"
    return image


def _textured_material(name, image, roughness=0.93):
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    nodes.clear()

    output = nodes.new("ShaderNodeOutputMaterial")
    shader = nodes.new("ShaderNodeBsdfPrincipled")
    texture = nodes.new("ShaderNodeTexImage")
    texture.image = image
    texture.interpolation = "Linear"
    texture.extension = "REPEAT"

    shader.inputs["Roughness"].default_value = roughness
    if "Specular IOR Level" in shader.inputs:
        shader.inputs["Specular IOR Level"].default_value = 0.18
    elif "Specular" in shader.inputs:
        shader.inputs["Specular"].default_value = 0.18

    links.new(texture.outputs["Color"], shader.inputs["Base Color"])
    links.new(shader.outputs["BSDF"], output.inputs["Surface"])
    return material


def _planar_uv(obj, repeats=1.0):
    if obj is None or obj.type != "MESH" or not obj.data.vertices:
        return
    mesh = obj.data
    layer = mesh.uv_layers.get("UVMap") or mesh.uv_layers.new(name="UVMap")
    min_x = min(v.co.x for v in mesh.vertices)
    max_x = max(v.co.x for v in mesh.vertices)
    min_y = min(v.co.y for v in mesh.vertices)
    max_y = max(v.co.y for v in mesh.vertices)
    span_x = max(max_x - min_x, 1e-5)
    span_y = max(max_y - min_y, 1e-5)
    for poly in mesh.polygons:
        for loop_index in poly.loop_indices:
            vertex = mesh.vertices[mesh.loops[loop_index].vertex_index]
            u = ((vertex.co.x - min_x) / span_x) * repeats
            v = ((vertex.co.y - min_y) / span_y) * repeats
            layer.data[loop_index].uv = (u, v)


def _assign(obj, material, repeats=1.0):
    if obj is None or obj.type != "MESH":
        return
    _planar_uv(obj, repeats)
    obj.data.materials.clear()
    obj.data.materials.append(material)


def textured_ground():
    _POLISHED_GROUND()

    # Medium lush tropical green: richer than the old flat lawn but still bright
    # enough for the cozy morning palette and fixed elevated camera.
    grass_main = _build_grass_texture(
        "Lembah Grass Main",
        dark=(0.145, 0.300, 0.095),
        mid=(0.235, 0.430, 0.145),
        light=(0.355, 0.555, 0.205),
        phase=0.08,
    )
    grass_deep = _build_grass_texture(
        "Lembah Grass Deep",
        dark=(0.105, 0.245, 0.075),
        mid=(0.175, 0.355, 0.105),
        light=(0.275, 0.465, 0.155),
        phase=0.37,
    )
    grass_warm = _build_grass_texture(
        "Lembah Grass Warm",
        dark=(0.185, 0.320, 0.095),
        mid=(0.275, 0.445, 0.130),
        light=(0.390, 0.565, 0.185),
        phase=0.61,
    )

    mat_main = _textured_material("V5 Textured Tropical Ground", grass_main, 0.94)
    mat_deep = _textured_material("V5 Textured Deep Grass", grass_deep, 0.95)
    mat_warm = _textured_material("V5 Textured Warm Grass", grass_warm, 0.94)

    _assign(bpy.data.objects.get("SculptedVillageGround"), mat_main, 1.0)
    _assign(bpy.data.objects.get("ExtendedVillageGround"), mat_main, 1.35)
    _assign(bpy.data.objects.get("V5GrassPatch_0"), mat_deep, 0.80)
    _assign(bpy.data.objects.get("V5GrassPatch_1"), mat_warm, 0.80)
    _assign(bpy.data.objects.get("V5GrassPatch_2"), mat_deep, 0.80)


base.build_ground = textured_ground
_REAL_MAIN()
