import math
import os
import sys

import bpy

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

# Install every accepted material gate through bridge wood without exporting.
# This pass changes only rice-paddy water and earthen bund surfaces.
import build_hero_scene as base
_REAL_MAIN = base.main
base.main = lambda: None
import build_hero_scene_v5_bridge_texture as bridge_pass
base.main = _REAL_MAIN

_PREVIOUS_RICE = base.build_rice_fields
ground = bridge_pass.ground


def _build_paddy_water(name, phase=0.0, size=256):
    tau = math.pi * 2.0
    rows = []
    dark = (0.095, 0.245, 0.205)
    mid = (0.190, 0.405, 0.310)
    light = (0.335, 0.565, 0.410)
    mud = (0.255, 0.180, 0.085)

    for py in range(size):
        v = py / float(size - 1)
        row = bytearray()
        for px in range(size):
            u = px / float(size - 1)
            broad = (
                math.sin((u * 2.1 + v * 3.0 + phase) * tau) * 0.09
                + math.sin((u * 5.0 - v * 4.0 + 0.31) * tau) * 0.040
            )
            ripple = (
                math.sin((u * 14.0 + v * 9.0 + 0.23) * tau)
                * math.sin((u * 8.0 - v * 13.0 + phase) * tau)
            ) * 0.012
            t = ground._clamp(0.48 + broad + ripple)
            if t < 0.50:
                q = t / 0.50
                rgb = tuple(ground._mix(dark[c], mid[c], q) for c in range(3))
            else:
                q = (t - 0.50) / 0.50
                rgb = tuple(ground._mix(mid[c], light[c], q) for c in range(3))

            # Soft muddy undertone hints at shallow flooded soil without making the
            # field brown or photorealistic.
            muddy = ground._clamp((math.sin((u * 3.3 + v * 2.7 + 0.57) * tau) - 0.68) / 0.32) * 0.055
            rgb = tuple(ground._mix(rgb[c], mud[c], muddy) for c in range(3))
            encoded = tuple(ground._linear_to_srgb(channel) for channel in rgb)
            row.extend(int(round(ground._clamp(channel) * 255.0)) for channel in encoded)
        rows.append(row)

    path = os.path.join("/tmp", name.lower().replace(" ", "_") + ".png")
    ground._write_rgb_png(path, size, size, rows)
    if os.path.getsize(path) <= 1024:
        raise RuntimeError("Generated paddy-water PNG is suspiciously small: %s" % path)
    image = bpy.data.images.load(path, check_existing=False)
    image.name = name
    image.colorspace_settings.name = "sRGB"
    return image


def _build_bund_earth(name, phase=0.0, size=256):
    tau = math.pi * 2.0
    rows = []
    dark = (0.105, 0.055, 0.022)
    mid = (0.215, 0.125, 0.050)
    light = (0.340, 0.225, 0.090)
    moss = (0.120, 0.245, 0.065)

    for py in range(size):
        v = py / float(size - 1)
        row = bytearray()
        for px in range(size):
            u = px / float(size - 1)
            soil = (
                math.sin((u * 3.0 + v * 2.1 + phase) * tau) * 0.13
                + math.sin((u * 7.0 - v * 5.2 + 0.33) * tau) * 0.055
                + math.sin((u * 17.0 + v * 13.0 + 0.17) * tau) * 0.018
            )
            t = ground._clamp(0.49 + soil)
            if t < 0.50:
                q = t / 0.50
                rgb = tuple(ground._mix(dark[c], mid[c], q) for c in range(3))
            else:
                q = (t - 0.50) / 0.50
                rgb = tuple(ground._mix(mid[c], light[c], q) for c in range(3))

            moss_mask = ground._clamp((math.sin((u * 4.1 - v * 3.5 + 0.72) * tau) - 0.70) / 0.30) * 0.10
            rgb = tuple(ground._mix(rgb[c], moss[c], moss_mask) for c in range(3))
            encoded = tuple(ground._linear_to_srgb(channel) for channel in rgb)
            row.extend(int(round(ground._clamp(channel) * 255.0)) for channel in encoded)
        rows.append(row)

    path = os.path.join("/tmp", name.lower().replace(" ", "_") + ".png")
    ground._write_rgb_png(path, size, size, rows)
    if os.path.getsize(path) <= 1024:
        raise RuntimeError("Generated paddy-bund PNG is suspiciously small: %s" % path)
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


def textured_rice_fields(wheat_t, grass_t):
    _PREVIOUS_RICE(wheat_t, grass_t)

    water_image = _build_paddy_water("Lembah Paddy Shallow Water", phase=0.21)
    bund_image = _build_bund_earth("Lembah Paddy Bund Earth", phase=0.43)
    water_mat = _material("V5 Textured Paddy Water", water_image, 0.34, 0.28)
    bund_mat = _material("V5 Textured Paddy Bund", bund_image, 0.96, 0.12)

    water_count = 0
    bund_count = 0
    for obj in bpy.context.scene.objects:
        if obj.type != "MESH":
            continue
        if obj.name.startswith("V5PaddyWater_"):
            ground._assign(obj, water_mat, 1.35)
            water_count += 1
        elif obj.name.startswith("V5PaddyBund_"):
            ground._assign(obj, bund_mat, 2.10)
            bund_count += 1

    if water_count != 4:
        raise RuntimeError("Expected 4 V5 paddy-water meshes, got %d" % water_count)
    if bund_count != 4:
        raise RuntimeError("Expected 4 V5 paddy-bund meshes, got %d" % bund_count)


base.build_rice_fields = textured_rice_fields
_REAL_MAIN()
