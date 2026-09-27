import math
import os
import sys

import bpy

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

# Install the accepted ground + dirt-path material passes without exporting.
# This gate changes only the main river water; paddy water stays untouched until
# its own review.
import build_hero_scene as base
_REAL_MAIN = base.main
base.main = lambda: None
import build_hero_scene_v5_path_texture as path_pass
base.main = _REAL_MAIN

_PREVIOUS_PATH = base.build_path_stream_bridge
ground = path_pass.ground


def _build_water_texture(name, phase=0.0, size=256):
    tau = math.pi * 2.0
    rows = []
    dark = (0.060, 0.245, 0.285)
    mid = (0.105, 0.410, 0.470)
    light = (0.205, 0.610, 0.650)

    for py in range(size):
        v = py / float(size - 1)
        row = bytearray()
        for px in range(size):
            u = px / float(size - 1)

            # Long soft streaks suggest flow from the elevated game camera.
            long_wave = (
                math.sin((u * 2.0 + v * 6.0 + phase) * tau) * 0.13
                + math.sin((u * 3.2 - v * 10.0 + 0.21) * tau) * 0.065
            )
            ripple = (
                math.sin((u * 11.0 + v * 19.0 + 0.43) * tau)
                * math.sin((u * 5.0 - v * 15.0 + phase) * tau)
            ) * 0.022
            t = ground._clamp(0.47 + long_wave + ripple)

            if t < 0.50:
                q = t / 0.50
                rgb = tuple(ground._mix(dark[c], mid[c], q) for c in range(3))
            else:
                q = (t - 0.50) / 0.50
                rgb = tuple(ground._mix(mid[c], light[c], q) for c in range(3))

            # Rare pale glints, kept broad enough not to become noisy foam.
            glint = ground._clamp((math.sin((u * 7.5 + v * 13.0 + 0.17) * tau) - 0.87) / 0.13)
            glint *= 0.035
            rgb = tuple(ground._mix(rgb[c], (0.48, 0.78, 0.78)[c], glint) for c in range(3))

            encoded = tuple(ground._linear_to_srgb(channel) for channel in rgb)
            row.extend(int(round(ground._clamp(channel) * 255.0)) for channel in encoded)
        rows.append(row)

    texture_path = os.path.join("/tmp", name.lower().replace(" ", "_") + ".png")
    ground._write_rgb_png(texture_path, size, size, rows)
    if os.path.getsize(texture_path) <= 1024:
        raise RuntimeError("Generated river-water PNG is suspiciously small: %s" % texture_path)

    image = bpy.data.images.load(texture_path, check_existing=False)
    image.name = name
    image.colorspace_settings.name = "sRGB"
    return image


def _water_material(name, image):
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

    links.new(texture.outputs["Color"], shader.inputs["Base Color"])
    shader.inputs["Roughness"].default_value = 0.24
    shader.inputs["Metallic"].default_value = 0.0
    if "Specular IOR Level" in shader.inputs:
        shader.inputs["Specular IOR Level"].default_value = 0.34
    elif "Specular" in shader.inputs:
        shader.inputs["Specular"].default_value = 0.34

    links.new(shader.outputs["BSDF"], output.inputs["Surface"])
    return material


def textured_path_stream_bridge(rock_t, grass_t, lilypad_t):
    _PREVIOUS_PATH(rock_t, grass_t, lilypad_t)

    water_image = _build_water_texture("Lembah River Flow", phase=0.13)
    water_material = _water_material("V5 Textured River Water", water_image)

    # Main river only. Bank, bridge, paddy water and vegetation are unchanged.
    ground._assign(bpy.data.objects.get("V5StreamWater"), water_material, 3.25)


base.build_path_stream_bridge = textured_path_stream_bridge
_REAL_MAIN()
