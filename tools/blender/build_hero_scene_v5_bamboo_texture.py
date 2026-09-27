import math
import os
import sys

import bpy

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

# Install every accepted material gate through rocks without exporting yet.
# This gate is intentionally limited to the garden bamboo fence so each visual
# material is reviewed and fixed before the next element is allowed to move on.
import build_hero_scene as base
_REAL_MAIN = base.main
base.main = lambda: None
import build_hero_scene_v5_rock_texture as rock_pass
base.main = _REAL_MAIN

_PREVIOUS_GARDEN = base.build_garden
ground = rock_pass.ground


def _build_bamboo_texture(name, phase=0.0, size=256):
    """Bake warm, aged bamboo with soft fibre variation.

    We avoid hard horizontal rings in the texture because the same material is
    used by both vertical posts and horizontal rails. The real fence geometry
    provides the segmentation; the texture only adds believable fibre, subtle
    sun bleaching, and a few muted green/brown age marks.
    """
    tau = math.pi * 2.0
    rows = []
    bamboo_dark = (0.245, 0.185, 0.070)
    bamboo_mid = (0.455, 0.365, 0.125)
    bamboo_light = (0.650, 0.545, 0.220)
    green_age = (0.175, 0.245, 0.075)
    dry_age = (0.285, 0.205, 0.090)

    for py in range(size):
        v = py / float(size - 1)
        row = bytearray()
        for px in range(size):
            u = px / float(size - 1)

            broad = (
                math.sin((u * 2.10 + v * 1.35 + phase) * tau) * 0.070
                + math.sin((u * 4.40 - v * 2.30 + 0.27) * tau) * 0.035
            )
            fibre = (
                math.sin((u * 18.0 + v * 2.2 + 0.31) * tau) * 0.018
                + math.sin((u * 31.0 - v * 3.0 + phase) * tau) * 0.009
            )
            t = ground._clamp(0.50 + broad + fibre)

            if t < 0.50:
                q = t / 0.50
                rgb = tuple(ground._mix(bamboo_dark[c], bamboo_mid[c], q) for c in range(3))
            else:
                q = (t - 0.50) / 0.50
                rgb = tuple(ground._mix(bamboo_mid[c], bamboo_light[c], q) for c in range(3))

            # Broad age patches break the plastic/yellow look without creating
            # obvious painted stripes at the fixed gameplay camera distance.
            green_field = (
                math.sin((u * 1.35 - v * 1.85 + 0.57 + phase) * tau) * 0.62
                + math.sin((u * 2.70 + v * 1.20 + 0.14) * tau) * 0.28
            )
            green_amount = ground._clamp((green_field - 0.56) / 0.34) * 0.13
            rgb = tuple(ground._mix(rgb[c], green_age[c], green_amount) for c in range(3))

            dry_field = ground._clamp(
                (math.sin((u * 3.3 + v * 4.1 + 0.72 + phase) * tau) - 0.84) / 0.16
            ) * 0.055
            rgb = tuple(ground._mix(rgb[c], dry_age[c], dry_field) for c in range(3))

            encoded = tuple(ground._linear_to_srgb(channel) for channel in rgb)
            row.extend(int(round(ground._clamp(channel) * 255.0)) for channel in encoded)
        rows.append(row)

    path = os.path.join("/tmp", name.lower().replace(" ", "_") + ".png")
    ground._write_rgb_png(path, size, size, rows)
    if os.path.getsize(path) <= 1024:
        raise RuntimeError("Generated bamboo PNG is suspiciously small: %s" % path)

    image = bpy.data.images.load(path, check_existing=False)
    image.name = name
    image.colorspace_settings.name = "sRGB"
    return image


def _bamboo_material():
    image = _build_bamboo_texture("Lembah Aged Village Bamboo", phase=0.23)
    material = base.MAT_BAMBOO.copy()
    material.name = "Lembah Textured Aged Bamboo"
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    shader = nodes.get("Principled BSDF") or next(
        (node for node in nodes if node.type == "BSDF_PRINCIPLED"), None
    )
    if shader is None:
        nodes.clear()
        output = nodes.new("ShaderNodeOutputMaterial")
        shader = nodes.new("ShaderNodeBsdfPrincipled")
        links.new(shader.outputs["BSDF"], output.inputs["Surface"])

    base_socket = shader.inputs.get("Base Color")
    for link in list(links):
        if link.to_node == shader and link.to_socket == base_socket:
            links.remove(link)

    texture = nodes.new("ShaderNodeTexImage")
    texture.image = image
    texture.interpolation = "Linear"
    texture.extension = "REPEAT"
    links.new(texture.outputs["Color"], base_socket)

    shader.inputs["Roughness"].default_value = 0.92
    if "Specular IOR Level" in shader.inputs:
        shader.inputs["Specular IOR Level"].default_value = 0.12
    elif "Specular" in shader.inputs:
        shader.inputs["Specular"].default_value = 0.12
    return material


def textured_garden(plant_t, flower_t, grass_t):
    previous_bamboo = base.MAT_BAMBOO
    base.MAT_BAMBOO = _bamboo_material()
    try:
        _PREVIOUS_GARDEN(plant_t, flower_t, grass_t)
    finally:
        base.MAT_BAMBOO = previous_bamboo


base.build_garden = textured_garden
_REAL_MAIN()
