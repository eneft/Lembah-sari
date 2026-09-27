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


def _build_rock_texture(name, phase=0.0, size=256):
    """Bake one warm-stone texture with irregular integrated moss.

    Rock_Moss_3 separates stone and moss into polygon material bands. Keeping
    those slots visibly different made the review render look striped. We bake
    moss into one continuous texture instead, then use that same material for
    both source slots so the original polygon boundaries disappear.
    """
    tau = math.pi * 2.0
    rows = []
    stone_dark = (0.115, 0.125, 0.120)
    stone_mid = (0.245, 0.255, 0.235)
    stone_light = (0.390, 0.385, 0.335)
    moss_dark = (0.035, 0.085, 0.028)
    moss_mid = (0.075, 0.155, 0.050)
    moss_light = (0.130, 0.235, 0.080)

    for py in range(size):
        v = py / float(size - 1)
        row = bytearray()
        for px in range(size):
            u = px / float(size - 1)

            stone_wave = (
                math.sin((u * 2.4 + v * 1.9 + phase) * tau) * 0.095
                + math.sin((u * 5.1 - v * 3.5 + 0.21) * tau) * 0.045
                + math.sin((u * 12.0 + v * 8.0 + 0.37) * tau)
                * math.sin((u * 7.0 - v * 11.0 + phase) * tau) * 0.014
            )
            stone_t = ground._clamp(0.50 + stone_wave)
            if stone_t < 0.50:
                q = stone_t / 0.50
                rgb = tuple(ground._mix(stone_dark[c], stone_mid[c], q) for c in range(3))
            else:
                q = (stone_t - 0.50) / 0.50
                rgb = tuple(ground._mix(stone_mid[c], stone_light[c], q) for c in range(3))

            # Two broad fields make moss form soft, asymmetrical islands rather
            # than following the model's polygon bands. Fine variation only
            # roughens those islands slightly; it never becomes noisy speckles.
            moss_field = (
                math.sin((u * 1.65 + v * 1.15 + 0.18 + phase) * tau) * 0.58
                + math.sin((u * 2.75 - v * 2.10 + 0.47) * tau) * 0.30
                + math.sin((u * 6.0 + v * 4.8 + 0.31) * tau) * 0.08
            )
            moss_amount = ground._clamp((moss_field - 0.34) / 0.42)
            # Keep moss selective so the stone still reads first from game scale.
            moss_amount = moss_amount * moss_amount * 0.72
            moss_t = ground._clamp(0.50 + math.sin((u * 4.3 + v * 3.6 + phase) * tau) * 0.12)
            if moss_t < 0.50:
                q = moss_t / 0.50
                moss_rgb = tuple(ground._mix(moss_dark[c], moss_mid[c], q) for c in range(3))
            else:
                q = (moss_t - 0.50) / 0.50
                moss_rgb = tuple(ground._mix(moss_mid[c], moss_light[c], q) for c in range(3))
            rgb = tuple(ground._mix(rgb[c], moss_rgb[c], moss_amount) for c in range(3))

            # A tiny warm mineral tint prevents cold concrete-gray stones.
            warmth = ground._clamp((math.sin((u * 3.7 + v * 4.6 + 0.73) * tau) - 0.88) / 0.12) * 0.025
            warm_tint = (0.315, 0.250, 0.165)
            rgb = tuple(ground._mix(rgb[c], warm_tint[c], warmth) for c in range(3))

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


def _copy_textured_material(source, name, image, roughness=0.96, specular=0.09):
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
    rock_indices = []
    moss_indices = []
    stone_source = None
    for index, source in enumerate(list(rock_t.data.materials)):
        if source is None:
            continue
        if source.name.startswith("Rock"):
            rock_indices.append(index)
            stone_source = stone_source or source
        elif source.name.startswith("Green"):
            moss_indices.append(index)

    if not rock_indices:
        raise RuntimeError("Rock_Moss_3 stone material slot was not found")
    if not moss_indices:
        raise RuntimeError("Rock_Moss_3 moss material slot was not found")

    image = _build_rock_texture("Lembah Natural Mossy River Stone", phase=0.18)
    unified = _copy_textured_material(
        stone_source,
        "Lembah Unified Natural Mossy Stone",
        image,
        roughness=0.96,
        specular=0.09,
    )

    # Deliberately assign exactly the same material to both original polygon
    # groups. This removes the horizontal/faceted moss stripes seen in review #19.
    for index in rock_indices + moss_indices:
        rock_t.data.materials[index] = unified


def textured_rocks(tree_t, palm_t, bush_t, grass_t, flower_t, rock_t):
    _texture_rock_template(rock_t)
    _PREVIOUS_FOLIAGE(tree_t, palm_t, bush_t, grass_t, flower_t, rock_t)


base.build_foliage = textured_rocks
_REAL_MAIN()
