import os
import sys

import bpy

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

import build_hero_scene as base

# Load the full V5 composition as a library pass without exporting it yet.
_REAL_MAIN = base.main
base.main = lambda: None
import build_hero_scene_v5 as v5
base.main = _REAL_MAIN

_V5_GROUND = base.build_ground


def _terrain_ridge(name, y, heights, material, depth):
    """Build a grounded rolling landform with a real footprint, not a floating strip."""
    count = len(heights)
    x0 = -16.5
    step = 33.0 / float(count - 1)
    row_ys = (y - depth * 0.72, y, y + depth * 0.72)
    row_factors = (0.10, 1.0, 0.12)
    verts = []
    for row_y, factor in zip(row_ys, row_factors):
        for i, height in enumerate(heights):
            x = x0 + i * step
            edge_fade = min(1.0, i / 1.7, (count - 1 - i) / 1.7)
            z = -0.24 + height * factor * max(0.15, edge_fade)
            verts.append((x, row_y, z))

    faces = []
    for row in range(2):
        start = row * count
        next_start = (row + 1) * count
        for i in range(count - 1):
            faces.append((start + i, start + i + 1, next_start + i + 1, next_start + i))

    mesh = bpy.data.meshes.new(name + "Mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    base.apply_mat(obj, material)

    solid = obj.modifiers.new("Landform body", "SOLIDIFY")
    solid.thickness = 0.48
    bevel = obj.modifiers.new("Landform softness", "BEVEL")
    bevel.width = 0.20
    bevel.segments = 3
    for poly in obj.data.polygons:
        poly.use_smooth = True
    return obj


def polished_v5_ground():
    _V5_GROUND()

    # The first V5 render proved the composition, but its horizon read as stacked ribbons.
    # Hide those review meshes and replace them with grounded rolling terrain masses.
    v5._hide_named_prefixes(("V5FarRidge", "V5MidRidge", "V5NearRidge"))

    _terrain_ridge(
        "V5FarLandform", 16.6,
        [0.72,1.05,1.42,1.15,1.92,1.46,2.22,1.55,2.02,1.34,1.74,1.08,0.72],
        v5.MAT_RIDGE_FAR, 5.8,
    )
    _terrain_ridge(
        "V5MidLandform", 13.4,
        [0.55,0.88,1.24,0.92,1.58,1.10,1.48,0.92,1.62,1.02,1.32,0.82,0.54],
        v5.MAT_RIDGE_MID, 4.5,
    )
    _terrain_ridge(
        "V5NearLandform", 10.8,
        [0.42,0.70,0.98,0.72,1.16,0.78,1.08,0.70,1.20,0.76,0.96,0.65,0.42],
        v5.MAT_RIDGE_NEAR, 3.5,
    )


base.build_ground = polished_v5_ground
_REAL_MAIN()
