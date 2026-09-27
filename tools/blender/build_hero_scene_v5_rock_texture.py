import math
import os
import sys

import bpy

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

# Install every accepted material gate through foliage without exporting yet.
# This pass is intentionally limited to the mossy river/path rocks so we keep
# the sequential visual-review discipline intact.
import build_hero_scene as base
_REAL_MAIN = base.main
base.main = lambda: None
import build_hero_scene_v5_foliage_texture as foliage_pass
base.main = _REAL_MAIN

_PREVIOUS_FOLIAGE = base.build_foliage
ground = foliage_pass.ground


def _build_rock_texture(name, dark, mid, light, phase=0.0, size=192):
    tau = math.pi * 2.0
    rows = []
    for py in range(size):
        v = py / float(size - 1)
        row = bytearray()
        for px in range(size):
            u = px / float(size - 1)
            broad = (
                math.sin((u * 2.7 + v * 2.1 + phase) * tau) * 0.095
                + math.sin((u * 5.4 - v * 3.8 + 0.21) * tau) * 0.048
            )
            grain = (
                math.sin((u * 13.0 + v * 9.0 + 0.37) * tau)
                * math.sin((u * 7.0 - v * 12.0 + phase) * tau)
            ) * 0.018
            t = ground._clamp(0.50 + broad + grain)
            if t < 0.50:
                q = t / 0.50
                rgb = tuple(ground._mix(dark[c], mid[c], q) for c in range(3))
            else:
                q = (t - 0.50) / 0.50
                rgb = tuple(ground._mix(mid[c], light[c], q) for c in range(3))

            # Sparse earthy warmth keeps the stones compatible with the tropical
            # palette instead of reading as cold gray concrete.
            warm = ground._clamp((math.sin((u * 4.2 + v * 5.1 + phase) * tau) - 0.84) / 0.16) * 0.030
            warm_tint = (0.31, 0.255, 0.175)
            rgb = tuple(ground._mix(rgb[c], warm_tint[c], warm) for c in range(3))
            encoded = tuple(ground._linear_to_srgb(channel) for channel in rgb)
            row.extend(int(round(ground._clamp(channel) * 255.0)) for channel in encoded)
        rows.append(row)

    path = os.path.join("/tmp", name.lower().replace(" ", "_") + ".png")
    ground._write_rgb_png(path, size, size, rows)
    if os.path.getsize(path) <= 1024:
        raise RuntimeError("Generated rock PNG is suspiciously small: %s" % path)
    image = bpy.data.images.load(path, check_existing=False)
    image.name = name
    image.colorspace_settings.name = "sRGB"
    return image


def _build_moss_texture(name, phase=0.0, size=192):
    tau = math.pi * 2.0
    rows = []
    dark = (0.030, 0.090, 0.025)
    mid = (0.070, 0.170, 0.045)
    light = (0.135, 0.260, 0.080)
    for py in range(size):
        v = py / float(size - 1)
        row = bytearray()
        for px in range(size):
            u = px / float(size - 1)
            mottle = (
                math.sin((u * 4.8 + v * 3.7 + phase) * tau) * 0.070
                + math.sin((u * 10.0 - v * 8.0 + 0.43) * tau) * 0.025
            )
            t = ground._clamp(0.50 + mottle)
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
        raise RuntimeError("Generated moss PNG is suspiciously small: %s" % path)
    image = bpy.data.images.load(path, check_existing=False)
    image.name = name
    image.colorspace_settings.name = "sRGB"
    return image


def _copy_textured_material(source, name, image, roughness, specular):
    material = source.copy() if source is not None else bpy.data.materials.new(name)
    material.name = name
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    shader = nodes.get("Principled BSDF") or next((n for n in nodes if n.type == "BSDF_PRINCIPLED"), None)
    if shader is None:
        nodes.clear()
        output = nodes.new("ShaderNodeOutputMaterial")
        shader = nodes.new("ShaderNodeBsdfPrincipled")
        links.new(shader.outputs["BSDF"], output.inputs["Surface"])

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
    return material


def _texture_rock_template(rock_t):
    stone_image = _build_rock_texture(
        "Lembah Warm River Stone",
        dark=(0.115, 0.125, 0.120),
        mid=(0.245, 0.255, 0.235),
        light=(0.390, 0.385, 0.335),
        phase=0.18,
    )
    moss_image = _build_moss_texture("Lembah Soft Rock Moss", phase=0.39)

    found_stone = 0
    found_moss = 0
    for index, source in enumerate(list(rock_t.data.materials)):
        if source is None:
            continue
        if source.name.startswith("Rock"):
            rock_t.data.materials[index] = _copy_textured_material(
                source, "Lembah Textured River Stone", stone_image, 0.96, 0.09
            )
            found_stone += 1
        elif source.name.startswith("Green"):
            rock_t.data.materials[index] = _copy_textured_material(
                source, "Lembah Textured Rock Moss", moss_image, 0.94, 0.08
            )
            found_moss += 1

    if found_stone == 0:
        raise RuntimeError("Rock_Moss_3 stone material slot was not found")
    if found_moss == 0:
        raise RuntimeError("Rock_Moss_3 moss material slot was not found")


def textured_rocks(tree_t, palm_t, bush_t, grass_t, flower_t, rock_t):
    # Apply to the shared rock template before placement. Every river/path rock
    # copy then inherits the same accepted material while all other vegetation
    # remains untouched.
    _texture_rock_template(rock_t)
    _PREVIOUS_FOLIAGE(tree_t, palm_t, bush_t, grass_t, flower_t, rock_t)


base.build_foliage = textured_rocks
_REAL_MAIN()
