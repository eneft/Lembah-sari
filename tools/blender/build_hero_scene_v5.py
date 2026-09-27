import math
import os
import sys

import bpy
from mathutils import Vector

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

# Install every previous art pass without allowing their module-level main() calls
# to export intermediate files. Then apply this composition rebuild once.
import build_hero_scene as base
_REAL_MAIN = base.main
base.main = lambda: None
import build_hero_scene_polish  # noqa: F401
import build_hero_scene_v4  # noqa: F401
base.main = _REAL_MAIN

_V4_GROUND = base.build_ground
_V4_RICE = base.build_rice_fields
_V4_FOLIAGE = base.build_foliage

MAT_GRASS_DEEP = base.mat("V5 Deep Tropical Grass", (0.115, 0.285, 0.095), 0.96)
MAT_GRASS_WARM = base.mat("V5 Warm Meadow Grass", (0.245, 0.420, 0.135), 0.94)
MAT_RIDGE_NEAR = base.mat("V5 Ridge Near", (0.255, 0.390, 0.245), 0.99)
MAT_RIDGE_MID = base.mat("V5 Ridge Mid", (0.350, 0.475, 0.330), 0.99)
MAT_RIDGE_FAR = base.mat("V5 Ridge Far", (0.465, 0.565, 0.435), 1.0)
MAT_MUD = base.mat("V5 Wet Earth", (0.235, 0.145, 0.070), 0.97)


def _hide_named_prefixes(prefixes):
    for obj in list(bpy.data.objects):
        if any(obj.name.startswith(prefix) for prefix in prefixes):
            obj.hide_render = True


def _smooth(obj):
    if obj is not None and obj.type == "MESH":
        for poly in obj.data.polygons:
            poly.use_smooth = True


def _polygon_surface(name, points, z, material, thickness=0.055, bevel=0.05):
    verts = [(x, y, z) for x, y in points]
    mesh = bpy.data.meshes.new(name + "Mesh")
    mesh.from_pydata(verts, [], [tuple(range(len(verts)))])
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    base.apply_mat(obj, material)
    solid = obj.modifiers.new("Natural thickness", "SOLIDIFY")
    solid.thickness = thickness
    if bevel > 0:
        bev = obj.modifiers.new("Soft organic edge", "BEVEL")
        bev.width = bevel
        bev.segments = 2
    return obj


def _ridge_mesh(name, y, heights, material, depth=3.0):
    # A terrain silhouette, not stretched spheres: two rolling rows form a soft ridge.
    count = len(heights)
    x0 = -15.5
    step = 31.0 / float(count - 1)
    verts = []
    for row, yy in enumerate((y - depth * 0.5, y + depth * 0.5)):
        row_scale = 1.0 if row == 0 else 0.72
        for i, h in enumerate(heights):
            x = x0 + i * step
            verts.append((x, yy, -0.28 + h * row_scale))
    faces = []
    for i in range(count - 1):
        a = i
        b = i + 1
        c = count + i + 1
        d = count + i
        faces.append((a, b, c, d))
    mesh = bpy.data.meshes.new(name + "Mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    base.apply_mat(obj, material)
    solid = obj.modifiers.new("Ridge depth", "SOLIDIFY")
    solid.thickness = 0.34
    bev = obj.modifiers.new("Ridge softness", "BEVEL")
    bev.width = 0.22
    bev.segments = 3
    _smooth(obj)
    return obj


def _inside_polygon(x, y, polygon):
    inside = False
    j = len(polygon) - 1
    for i in range(len(polygon)):
        xi, yi = polygon[i]
        xj, yj = polygon[j]
        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / ((yj - yi) or 1e-6) + xi):
            inside = not inside
        j = i
    return inside


def _segment_box(name, a, b, z, width, height, material):
    ax, ay = a
    bx, by = b
    dx = bx - ax
    dy = by - ay
    length = math.sqrt(dx * dx + dy * dy)
    angle = math.atan2(dy, dx)
    return base.box(
        name,
        ((ax + bx) * 0.5, (ay + by) * 0.5, z),
        (length, width, height),
        material,
        rot=(0, 0, angle),
        bevel=min(width * 0.35, 0.06),
    )


def v5_ground():
    _V4_GROUND()

    # Remove every sphere/capsule horizon from older passes. The new horizon is made
    # from three continuous terrain ridges with atmospheric value separation.
    _hide_named_prefixes(("BackHill", "FarHill", "HazeRidge", "MidRidge"))
    _ridge_mesh(
        "V5FarRidge", 16.2,
        [1.0, 1.45, 1.20, 2.05, 1.55, 2.35, 1.65, 2.10, 1.35, 1.70, 1.05],
        MAT_RIDGE_FAR, 4.4,
    )
    _ridge_mesh(
        "V5MidRidge", 13.0,
        [0.75, 1.35, 1.05, 1.80, 1.15, 1.60, 1.00, 1.72, 1.08, 1.42, 0.70],
        MAT_RIDGE_MID, 3.4,
    )
    _ridge_mesh(
        "V5NearRidge", 10.6,
        [0.55, 1.00, 0.72, 1.28, 0.82, 1.18, 0.70, 1.30, 0.78, 1.05, 0.52],
        MAT_RIDGE_NEAR, 2.8,
    )

    # Break up the uninterrupted lawn with irregular tonal islands and earth wear.
    grass_patches = [
        [(-9.2, -2.0), (-7.4, -2.7), (-5.6, -2.1), (-5.1, -0.9), (-7.3, -0.4)],
        [(-1.0, 5.1), (1.6, 4.8), (3.0, 5.7), (2.0, 7.0), (-0.7, 6.5)],
        [(6.6, -0.2), (9.6, -0.5), (10.7, 1.0), (9.1, 2.0), (6.8, 1.4)],
    ]
    for i, poly in enumerate(grass_patches):
        _polygon_surface(f"V5GrassPatch_{i}", poly, -0.105, MAT_GRASS_DEEP if i != 1 else MAT_GRASS_WARM, 0.025, 0.10)

    wear = [(-5.0, 1.45), (-4.1, 0.55), (-3.35, -0.50), (-2.15, -1.65)]
    base.ribbon("V5HouseWear", wear, [0.50, 0.64, 0.72, 0.66], MAT_MUD, -0.02, 0.08)


def v5_path_stream_bridge(rock_t, grass_t, lilypad_t):
    # The path arcs from the left-hand house toward an off-centre bridge.
    path_pts = [
        (-4.8, 1.15), (-4.2, 0.15), (-3.25, -0.95), (-2.05, -2.05),
        (-0.65, -3.00), (0.75, -3.65), (2.20, -4.12),
    ]
    base.ribbon("V5VillagePath", path_pts, [0.92, 1.02, 1.18, 1.28, 1.34, 1.22, 1.05], base.MAT_SOIL_LIGHT, 0.035, 0.13)

    # Strong diagonal/meander gives the frame a leading line instead of splitting it in half.
    stream_pts = [
        (-12.0, -7.35), (-9.2, -6.75), (-6.3, -6.28), (-3.5, -5.60),
        (-0.6, -4.92), (2.25, -4.12), (4.9, -3.38), (7.4, -2.52),
        (9.7, -1.70), (12.0, -0.82),
    ]
    bank_widths = [3.35, 3.18, 3.02, 3.10, 2.98, 3.06, 2.92, 2.78, 2.62, 2.50]
    water_widths = [2.15, 2.00, 1.88, 1.96, 1.84, 1.92, 1.78, 1.66, 1.55, 1.44]
    base.ribbon("V5StreamBank", stream_pts, bank_widths, base.MAT_SOIL, -0.075, 0.16)
    base.ribbon("V5StreamWater", stream_pts, water_widths, base.MAT_WATER, 0.005, 0.12)

    # Bridge crossing is right of centre and rotated to the diagonal water flow.
    center = Vector((2.25, -4.12))
    tangent = Vector((4.9 - (-0.6), -3.38 - (-4.92))).normalized()
    crossing = Vector((-tangent.y, tangent.x)).normalized()
    plank_angle = math.atan2(tangent.y, tangent.x)
    deck_len = 2.75
    for i in range(11):
        offset = -deck_len * 0.5 + i * (deck_len / 10.0)
        p = center + crossing * offset
        arch = math.sin(i / 10.0 * math.pi) * 0.17
        base.box(
            f"V5BridgePlank_{i}", (p.x, p.y, 0.32 + arch), (2.12, 0.28, 0.14),
            base.MAT_WOOD, rot=(0, 0, plank_angle), bevel=0.045,
        )

    side = tangent * 0.93
    for side_sign in (-1.0, 1.0):
        rail_center = center + tangent * (0.93 * side_sign)
        rail_points = []
        for k in range(3):
            off = -deck_len * 0.42 + k * deck_len * 0.42
            p = rail_center + crossing * off
            base.cylinder(f"V5BridgePost_{side_sign}_{k}", (p.x, p.y, 0.88), 0.07, 1.25, base.MAT_WOOD_DARK, vertices=10, bevel=0.02)
            rail_points.append((p.x, p.y))
        _segment_box("V5BridgeRail", rail_points[0], rail_points[-1], 1.23, 0.10, 0.10, base.MAT_WOOD_DARK)

    rocks = [
        (-10.2,-6.15,0.56,15),(-8.0,-7.15,0.48,-18),(-6.0,-5.42,0.52,26),
        (-3.6,-6.35,0.45,-22),(-1.0,-4.25,0.50,14),(4.6,-4.02,0.54,-24),
        (6.8,-2.05,0.47,28),(9.3,-2.35,0.44,-10),
    ]
    for i, (x, y, s, r) in enumerate(rocks):
        base.place(rock_t, f"V5RiverRock_{i}", (x, y, 0.045), s, r)

    banks = [
        (-10.8,-5.7),(-9.2,-7.6),(-7.1,-5.5),(-5.5,-6.9),(-3.0,-4.8),(-1.7,-5.9),
        (0.2,-4.0),(3.8,-4.35),(5.3,-2.75),(7.1,-3.15),(8.2,-1.65),(10.3,-2.05),
    ]
    for i, (x, y) in enumerate(banks):
        base.place(grass_t, f"V5BankGrass_{i}", (x, y, 0.035), 0.52 + (i % 4) * 0.055, i * 23)

    lilies = [(-8.7,-6.55,0.34),(-5.2,-5.85,0.31),(-2.0,-5.15,0.33),(5.8,-3.05,0.31),(8.5,-2.05,0.29)]
    for i, (x, y, s) in enumerate(lilies):
        base.place(lilypad_t, f"V5Lily_{i}", (x, y, 0.07), s, i * 41)


def v5_rice_fields(wheat_t, grass_t):
    # Hide the rectangular paddies from prior passes and replace them with irregular
    # hand-shaped terraces. This removes the obvious grid/diorama read.
    _hide_named_prefixes(("PaddyBund_", "PaddyWater_", "Rice_", "V4Paddy_", "V4Bund", "V4Rice_"))

    fields = [
        [(3.2,0.0),(6.3,0.15),(7.0,1.15),(6.15,2.25),(3.65,2.20),(2.85,1.15)],
        [(5.55,2.55),(8.9,2.75),(9.65,3.85),(8.75,4.90),(5.75,4.60),(5.05,3.55)],
        [(7.25,5.05),(10.75,5.35),(11.15,6.50),(9.85,7.45),(7.00,7.15),(6.55,6.10)],
        [(2.2,4.7),(5.2,4.95),(5.75,5.95),(4.65,6.85),(2.05,6.55),(1.55,5.60)],
    ]
    for idx, poly in enumerate(fields):
        z = 0.055 + idx * 0.035
        _polygon_surface(f"V5PaddyWater_{idx}", poly, z, base.MAT_WATER_SHALLOW, 0.065, 0.09)
        outline = poly + [poly[0]]
        base.ribbon(f"V5PaddyBund_{idx}", outline, [0.32] * len(outline), base.MAT_SOIL, z + 0.075, 0.09)

        min_x = min(p[0] for p in poly); max_x = max(p[0] for p in poly)
        min_y = min(p[1] for p in poly); max_y = max(p[1] for p in poly)
        row = 0
        y = min_y + 0.38
        while y <= max_y - 0.22:
            col = 0
            x = min_x + 0.35 + (0.12 if row % 2 else 0.0)
            while x <= max_x - 0.20:
                if _inside_polygon(x, y, poly):
                    scale = 0.285 + ((row + col + idx) % 4) * 0.018
                    base.place(wheat_t, f"V5Rice_{idx}_{row}_{col}", (x, y, z + 0.11), scale, ((row * 17 + col * 11 + idx * 23) % 34) - 17)
                x += 0.58
                col += 1
            y += 0.54
            row += 1

    for i, (x, y) in enumerate([(2.4,3.9),(4.4,4.35),(6.2,5.0),(8.7,4.75),(10.5,4.9),(6.5,7.5),(9.3,7.65)]):
        base.place(grass_t, f"V5PaddyGrass_{i}", (x, y, 0.04), 0.50 + (i % 3) * 0.045, i * 29)


def v5_foliage(tree_t, palm_t, bush_t, grass_t, flower_t, rock_t):
    _V4_FOLIAGE(tree_t, palm_t, bush_t, grass_t, flower_t, rock_t)

    # Dense overlapping vegetation creates foreground/mid/background layers without
    # blocking the path -> bridge -> paddy sightline.
    palms = [
        (-9.8,3.0,0.82,12),(-7.5,5.7,0.72,-18),(-4.8,7.4,0.66,18),
        (5.2,8.1,0.68,-20),(8.6,7.8,0.75,22),(10.7,3.8,0.72,-12),
    ]
    trees = [
        (-11.0,0.4,0.84,-10),(-8.8,7.6,0.72,18),(-1.7,8.6,0.62,-14),
        (3.5,8.8,0.64,10),(10.8,6.4,0.74,-20),(11.2,0.5,0.76,14),
    ]
    for i, (x, y, s, r) in enumerate(palms):
        base.place(palm_t, f"V5Palm_{i}", (x, y, 0), s, r)
    for i, (x, y, s, r) in enumerate(trees):
        base.place(tree_t, f"V5Tree_{i}", (x, y, 0), s, r)

    bush_spots = [
        (-9.8,-3.2),(-8.6,-3.8),(-7.2,-3.45),(-6.2,-2.9),
        (-5.6,3.7),(-4.7,4.15),(-3.4,4.55),(-2.2,4.75),(-0.8,4.85),
        (1.0,5.0),(2.7,5.15),(4.2,5.0),(6.1,4.8),(7.8,-0.6),(8.8,-0.2),(9.7,0.4),
        (10.3,-3.0),(9.1,-3.6),(7.8,-3.8),
    ]
    for i, (x, y) in enumerate(bush_spots):
        base.place(bush_t, f"V5Bush_{i}", (x, y, 0.025), 0.48 + (i % 4) * 0.045, i * 31)

    grass_spots = [
        (-11.0,-7.9),(-9.7,-8.1),(-8.4,-7.8),(-6.7,-7.6),(-5.0,-7.4),
        (-3.2,-7.1),(0.0,-6.5),(3.6,-5.3),(5.1,-4.7),(6.8,-4.1),(8.5,-3.5),(10.2,-2.8),
        (-6.2,2.8),(-5.5,3.3),(-2.8,3.7),(0.2,4.0),(2.5,4.1),(4.7,4.25),
    ]
    for i, (x, y) in enumerate(grass_spots):
        base.place(grass_t, f"V5Grass_{i}", (x, y, 0.025), 0.50 + (i % 5) * 0.045, i * 19)

    flower_spots = [(-6.0,-1.0),(-5.3,-1.7),(-4.5,-2.4),(-2.5,-2.6),(0.0,-2.5),(1.3,-2.8),(4.9,-2.0),(6.1,-1.6)]
    for i, (x, y) in enumerate(flower_spots):
        base.place(flower_t, f"V5Flower_{i}", (x, y, 0.03), 0.38 + (i % 3) * 0.05, i * 37)


base.build_ground = v5_ground
base.build_path_stream_bridge = v5_path_stream_bridge
base.build_rice_fields = v5_rice_fields
base.build_foliage = v5_foliage
_REAL_MAIN()
