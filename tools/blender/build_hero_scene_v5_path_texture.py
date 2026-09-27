import math
import os
import sys

import bpy

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

# Install the accepted ground-texture pass without exporting. This pass then
# changes only the walking path / worn earth surface.
import build_hero_scene as base
_REAL_MAIN = base.main
base.main = lambda: None
import build_hero_scene_v5_ground_texture as ground
base.main = _REAL_MAIN

_PREVIOUS_PATH = base.build_path_stream_bridge


def _build_dirt_texture(name, phase=0.0, size=256):
    tau = math.pi * 2.0
    rows = []
    dark = (0.205, 0.115, 0.050)
    mid = (0.355, 0.215, 0.095)
    light = (0.500, 0.335, 0.165)

    for py in range(size):
        v = py / float(size - 1)
        row = bytearray()
        for px in range(size):
            u = px / float(size - 1)

            # Broad compacted-earth variation plus thin soft travel streaks.
            broad = (
                math.sin((u * 1.25 + v * 0.80 + phase) * tau) * 0.19
                + math.sin((u * 2.40 - v * 1.15 + 0.31) * tau) * 0.11
                + math.sin((u * 5.2 + v * 4.1 + 0.13) * tau) * 0.045
            )
            streak = abs(math.sin((v * 7.0 + u * 0.65 + phase) * tau))
            streak = max(0.0, 0.50 - streak) * 0.14
            t = ground._clamp(0.48 + broad - streak)

            if t < 0.50:
                q = t / 0.50
                rgb = tuple(ground._mix(dark[c], mid[c], q) for c in range(3))
            else:
                q = (t - 0.50) / 0.50
                rgb = tuple(ground._mix(mid[c], light[c], q) for c in range(3))

            # Tiny muted stone/dust flecks: enough to break flatness, never photo-noisy.
            fleck = math.sin((u * 29.0 + v * 17.0) * tau) * math.sin((u * 19.0 - v * 31.0) * tau)
            if fleck > 0.82:
                rgb = tuple(ground._mix(rgb[c], (0.44, 0.39, 0.27)[c], 0.16) for c in range(3))

            encoded = tuple(ground._linear_to_srgb(channel) for channel in rgb)
            row.extend(int(round(ground._clamp(channel) * 255.0)) for channel in encoded)
        rows.append(row)

    path = os.path.join("/tmp", name.lower().replace(" ", "_") + ".png")
    ground._write_rgb_png(path, size, size, rows)
    if os.path.getsize(path) <= 1024:
        raise RuntimeError("Generated dirt PNG is suspiciously small: %s" % path)
    image = bpy.data.images.load(path, check_existing=False)
    image.name = name
    image.colorspace_settings.name = "sRGB"
    return image


def textured_path_stream_bridge(rock_t, grass_t, lilypad_t):
    _PREVIOUS_PATH(rock_t, grass_t, lilypad_t)

    dirt_image = _build_dirt_texture("Lembah Village Dirt", phase=0.17)
    dirt_material = ground._textured_material("V5 Textured Village Dirt", dirt_image, 0.97)

    # Only the village walking path changes in this pass. River banks, bridge and
    # water stay exactly as before for later dedicated material reviews.
    ground._assign(bpy.data.objects.get("V5VillagePath"), dirt_material, 2.25)

    # This short worn strip connects the house threshold to the main path and is
    # part of the same compacted-earth material family.
    ground._assign(bpy.data.objects.get("V5HouseWear"), dirt_material, 1.35)


base.build_path_stream_bridge = textured_path_stream_bridge
_REAL_MAIN()
