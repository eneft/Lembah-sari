import math
import os
import sys

import bpy

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

# Install every accepted material gate through bridge wood without exporting.
# This pass remains isolated to the rice paddies until the actual render is good.
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
    # Shallower, earthier water than the river. The first paddy gate stayed too
    # cyan from game distance and competed with the stream.
    dark = (0.055, 0.155, 0.115)
    mid = (0.115, 0.285, 0.185)
    light = (0.220, 0.420, 0.270)
    mud = (0.245, 0.155, 0.060)

    for py in range(size):
        v = py / float(size - 1)
        row = bytearray()
        for px in range(size):
            u = px / float(size - 1)
            broad = (
                math.sin((u * 2.1 + v * 3.0 + phase) * tau) * 0.075
                + math.sin((u * 5.0 - v * 4.0 + 0.31) * tau) * 0.032
            )
            ripple = (
                math.sin((u * 14.0 + v * 9.0 + 0.23) * tau)
                * math.sin((u * 8.0 - v * 13.0 + phase) * tau)
            ) * 0.009
            t = ground._clamp(0.48 + broad + ripple)
            if t < 0.50:
                q = t / 0.50
                rgb = tuple(ground._mix(dark[c], mid[c], q) for c in range(3))
            else:
                q = (t - 0.50) / 0.50
                rgb = tuple(ground._mix(mid[c], light[c], q) for c in range(3))

            muddy = ground._clamp((math.sin((u * 3.3 + v * 2.7 + 0.57) * tau) - 0.62) / 0.38) * 0.075
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
    dark = (0.085, 0.042, 0.016)
    mid = (0.185, 0.100, 0.038)
    light = (0.300, 0.185, 0.068)
    moss = (0.095, 0.205, 0.052)

    for py in range(size):
        v = py / float(size - 1)
        row = bytearray()
        for px in range(size):
            u = px / float(size - 1)
            soil = (
                math.sin((u * 3.0 + v * 2.1 + phase) * tau) * 0.12
                + math.sin((u * 7.0 - v * 5.2 + 0.33) * tau) * 0.048
                + math.sin((u * 17.0 + v * 13.0 + 0.17) * tau) * 0.015
            )
            t = ground._clamp(0.49 + soil)
            if t < 0.50:
                q = t / 0.50
                rgb = tuple(ground._mix(dark[c], mid[c], q) for c in range(3))
            else:
                q = (t - 0.50) / 0.50
                rgb = tuple(ground._mix(mid[c], light[c], q) for c in range(3))

            moss_mask = ground._clamp((math.sin((u * 4.1 - v * 3.5 + 0.72) * tau) - 0.67) / 0.33) * 0.12
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


def _flat_rice_material(name, color):
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    shader = material.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = (*color, 1.0)
    shader.inputs["Roughness"].default_value = 0.91
    if "Specular IOR Level" in shader.inputs:
        shader.inputs["Specular IOR Level"].default_value = 0.13
    elif "Specular" in shader.inputs:
        shader.inputs["Specular"].default_value = 0.13
    return material


def _polish_rice_clumps():
    rice_materials = [
        _flat_rice_material("V5 Young Rice Deep", (0.120, 0.330, 0.060)),
        _flat_rice_material("V5 Young Rice", (0.185, 0.455, 0.080)),
        _flat_rice_material("V5 Young Rice Sun", (0.270, 0.555, 0.105)),
    ]

    originals = [
        obj for obj in list(bpy.context.scene.objects)
        if obj.type == "MESH" and obj.name.startswith("V5Rice_")
    ]
    if not originals:
        raise RuntimeError("No V5 rice clumps found for paddy polish")

    for index, obj in enumerate(originals):
        # Separate the mesh data only once so nearby clumps can carry slightly
        # different greens instead of one flat wheat material everywhere.
        obj.data = obj.data.copy()
        obj.data.materials.clear()
        obj.data.materials.append(rice_materials[index % len(rice_materials)])

        # Add one close companion clump to break the sparse stake-like rows seen
        # in the first paddy review. Offsets remain small so planting rows still
        # read intentionally from the 3/4 camera.
        extra = obj.copy()
        extra.data = obj.data
        extra.name = "V5RiceDense_%03d" % index
        angle = (index * 2.399963229728653) + 0.45
        radius = 0.13 + (index % 3) * 0.025
        extra.location.x += math.cos(angle) * radius
        extra.location.y += math.sin(angle) * radius
        extra.scale = tuple(component * (0.90 + (index % 4) * 0.025) for component in obj.scale)
        extra.rotation_euler.z += math.radians(((index * 17) % 18) - 9)
        bpy.context.collection.objects.link(extra)


def textured_rice_fields(wheat_t, grass_t):
    _PREVIOUS_RICE(wheat_t, grass_t)

    water_image = _build_paddy_water("Lembah Paddy Shallow Water", phase=0.21)
    bund_image = _build_bund_earth("Lembah Paddy Bund Earth", phase=0.43)
    water_mat = _material("V5 Textured Paddy Water", water_image, 0.40, 0.22)
    bund_mat = _material("V5 Textured Paddy Bund", bund_image, 0.97, 0.10)

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

    _polish_rice_clumps()


base.build_rice_fields = textured_rice_fields
_REAL_MAIN()
