import math
import os
import sys

import bpy

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

# Install all accepted passes up through river water without exporting. This gate
# changes only the wooden bridge.
import build_hero_scene as base
_REAL_MAIN = base.main
base.main = lambda: None
import build_hero_scene_v5_water_texture as water_pass
base.main = _REAL_MAIN

_PREVIOUS_PATH = base.build_path_stream_bridge
ground = water_pass.ground


def _build_wood_texture(name, dark, mid, light, phase=0.0, size=256):
    tau = math.pi * 2.0
    rows = []
    for py in range(size):
        v = py / float(size - 1)
        row = bytearray()
        for px in range(size):
            u = px / float(size - 1)

            # Long horizontal grain with broad board-to-board tonal movement.
            grain = (
                math.sin((u * 10.0 + v * 0.65 + phase) * tau) * 0.055
                + math.sin((u * 23.0 - v * 1.1 + 0.29) * tau) * 0.020
                + math.sin((u * 4.0 + v * 2.5 + 0.11) * tau) * 0.035
            )
            knot = math.sin((u * 3.1 + v * 5.2 + 0.47 + phase) * tau) * 0.035
            t = ground._clamp(0.50 + grain + knot)

            if t < 0.50:
                q = t / 0.50
                rgb = tuple(ground._mix(dark[c], mid[c], q) for c in range(3))
            else:
                q = (t - 0.50) / 0.50
                rgb = tuple(ground._mix(mid[c], light[c], q) for c in range(3))

            encoded = tuple(ground._linear_to_srgb(channel) for channel in rgb)
            row.extend(int(round(ground._clamp(channel) * 255.0)) for channel in encoded)
        rows.append(row)

    path = os.path.join("/tmp", name.lower().replace(" ", "_") + ".png")
    ground._write_rgb_png(path, size, size, rows)
    if os.path.getsize(path) <= 1024:
        raise RuntimeError("Generated bridge wood PNG is suspiciously small: %s" % path)
    image = bpy.data.images.load(path, check_existing=False)
    image.name = name
    image.colorspace_settings.name = "sRGB"
    return image


def _material(name, image, roughness, specular):
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    nodes.clear()

    output = nodes.new("ShaderNodeOutputMaterial")
    shader = nodes.new("ShaderNodeBsdfPrincipled")
    tex = nodes.new("ShaderNodeTexImage")
    tex.image = image
    tex.interpolation = "Linear"
    tex.extension = "REPEAT"
    links.new(tex.outputs["Color"], shader.inputs["Base Color"])
    shader.inputs["Roughness"].default_value = roughness
    if "Specular IOR Level" in shader.inputs:
        shader.inputs["Specular IOR Level"].default_value = specular
    elif "Specular" in shader.inputs:
        shader.inputs["Specular"].default_value = specular
    links.new(shader.outputs["BSDF"], output.inputs["Surface"])
    return material


def _cube_uv(obj, cube_size=1.0):
    if obj is None or obj.type != "MESH":
        return
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.cube_project(cube_size=cube_size, correct_aspect=True)
    bpy.ops.object.mode_set(mode="OBJECT")
    obj.select_set(False)


def _assign_prefix(prefix, material, cube_size):
    matched = 0
    for obj in bpy.context.scene.objects:
        if obj.type != "MESH" or not obj.name.startswith(prefix):
            continue
        _cube_uv(obj, cube_size)
        obj.data.materials.clear()
        obj.data.materials.append(material)
        matched += 1
    if matched == 0:
        raise RuntimeError("No bridge objects matched prefix: %s" % prefix)


def textured_path_stream_bridge(rock_t, grass_t, lilypad_t):
    _PREVIOUS_PATH(rock_t, grass_t, lilypad_t)

    honey_image = _build_wood_texture(
        "Lembah Bridge Honey Wood",
        dark=(0.205, 0.105, 0.040),
        mid=(0.385, 0.225, 0.095),
        light=(0.575, 0.365, 0.165),
        phase=0.13,
    )
    dark_image = _build_wood_texture(
        "Lembah Bridge Dark Wood",
        dark=(0.080, 0.035, 0.015),
        mid=(0.175, 0.080, 0.030),
        light=(0.290, 0.145, 0.055),
        phase=0.39,
    )

    honey = _material("V5 Textured Bridge Honey Wood", honey_image, 0.88, 0.16)
    dark = _material("V5 Textured Bridge Dark Wood", dark_image, 0.91, 0.14)

    _assign_prefix("V5BridgePlank_", honey, 0.85)
    _assign_prefix("V5BridgePost_", dark, 0.72)
    _assign_prefix("V5BridgeRail", dark, 0.80)


base.build_path_stream_bridge = textured_path_stream_bridge
_REAL_MAIN()
