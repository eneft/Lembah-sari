import math
import os
import sys

import bpy

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

# Install accepted gates through the rice paddies without exporting. This pass
# changes only Quaternius vegetation materials (leaf greens + natural trunks).
import build_hero_scene as base
_REAL_MAIN = base.main
base.main = lambda: None
import build_hero_scene_v5_paddy_texture as paddy_pass
base.main = _REAL_MAIN

_PREVIOUS_FOLIAGE = base.build_foliage
ground = paddy_pass.ground


def _build_leaf_texture(name, dark, mid, light, phase=0.0, size=192):
    tau = math.pi * 2.0
    rows = []
    for py in range(size):
        v = py / float(size - 1)
        row = bytearray()
        for px in range(size):
            u = px / float(size - 1)
            # Keep the canopy lush but quieter than the first pass. Broad variation
            # should read as natural leaf clusters, not lime bands or noisy facets.
            mottling = (
                math.sin((u * 3.6 + v * 2.8 + phase) * tau) * 0.070
                + math.sin((u * 7.3 - v * 5.5 + 0.29) * tau) * 0.030
                + math.sin((u * 14.0 + v * 11.0 + 0.51) * tau) * 0.008
            )
            t = ground._clamp(0.50 + mottling)
            if t < 0.50:
                q = t / 0.50
                rgb = tuple(ground._mix(dark[c], mid[c], q) for c in range(3))
            else:
                q = (t - 0.50) / 0.50
                rgb = tuple(ground._mix(mid[c], light[c], q) for c in range(3))

            # Tiny warm highlights stop the foliage from going gray without
            # pushing it into neon yellow-green.
            sun = ground._clamp((math.sin((u * 5.1 + v * 6.7 + 0.81 + phase) * tau) - 0.84) / 0.16) * 0.020
            warm = (0.235, 0.385, 0.075)
            rgb = tuple(ground._mix(rgb[c], warm[c], sun) for c in range(3))
            encoded = tuple(ground._linear_to_srgb(channel) for channel in rgb)
            row.extend(int(round(ground._clamp(channel) * 255.0)) for channel in encoded)
        rows.append(row)

    path = os.path.join("/tmp", name.lower().replace(" ", "_") + ".png")
    ground._write_rgb_png(path, size, size, rows)
    if os.path.getsize(path) <= 1024:
        raise RuntimeError("Generated foliage PNG is suspiciously small: %s" % path)
    image = bpy.data.images.load(path, check_existing=False)
    image.name = name
    image.colorspace_settings.name = "sRGB"
    return image


def _build_trunk_texture(name, phase=0.0, size=192):
    tau = math.pi * 2.0
    rows = []
    dark = (0.065, 0.027, 0.012)
    mid = (0.135, 0.062, 0.025)
    light = (0.235, 0.120, 0.045)
    for py in range(size):
        v = py / float(size - 1)
        row = bytearray()
        for px in range(size):
            u = px / float(size - 1)
            grain = (
                math.sin((u * 13.0 + v * 1.2 + phase) * tau) * 0.045
                + math.sin((u * 27.0 - v * 0.8 + 0.31) * tau) * 0.014
                + math.sin((u * 4.0 + v * 3.0 + 0.62) * tau) * 0.028
            )
            t = ground._clamp(0.50 + grain)
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
        raise RuntimeError("Generated trunk PNG is suspiciously small: %s" % path)
    image = bpy.data.images.load(path, check_existing=False)
    image.name = name
    image.colorspace_settings.name = "sRGB"
    return image


def _apply_image_to_material(material, image, roughness, specular):
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    shader = nodes.get("Principled BSDF") or next((n for n in nodes if n.type == "BSDF_PRINCIPLED"), None)
    if shader is None:
        return False

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
        shader.inputs["Specular IOR Level"].default_value = specular
    elif "Specular" in shader.inputs:
        shader.inputs["Specular"].default_value = specular
    return True


def _texture_quaternius_materials():
    dark_leaf = _build_leaf_texture(
        "Lembah Tropical Deep Leaf",
        dark=(0.030, 0.095, 0.022),
        mid=(0.058, 0.175, 0.034),
        light=(0.105, 0.260, 0.050),
        phase=0.14,
    )
    leaf = _build_leaf_texture(
        "Lembah Tropical Leaf",
        dark=(0.050, 0.145, 0.030),
        mid=(0.090, 0.245, 0.048),
        light=(0.155, 0.345, 0.070),
        phase=0.42,
    )
    wood = _build_trunk_texture("Lembah Tropical Trunk", phase=0.23)

    matched = {"DarkGreen": 0, "Green": 0, "Wood": 0}
    for material in bpy.data.materials:
        if material.name.startswith("DarkGreen"):
            if _apply_image_to_material(material, dark_leaf, 0.92, 0.12):
                matched["DarkGreen"] += 1
        elif material.name.startswith("Green"):
            if _apply_image_to_material(material, leaf, 0.90, 0.13):
                matched["Green"] += 1
        elif material.name.startswith("Wood"):
            if _apply_image_to_material(material, wood, 0.94, 0.10):
                matched["Wood"] += 1

    missing = [key for key, count in matched.items() if count == 0]
    if missing:
        raise RuntimeError("Expected Quaternius foliage materials were not found: %s" % ", ".join(missing))


def textured_foliage(tree_t, palm_t, bush_t, grass_t, flower_t, rock_t):
    _PREVIOUS_FOLIAGE(tree_t, palm_t, bush_t, grass_t, flower_t, rock_t)
    _texture_quaternius_materials()


base.build_foliage = textured_foliage
_REAL_MAIN()
