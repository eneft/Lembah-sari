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
    # Concept pass: one readable S-curve ties the porch to a right-side bridge.
    # Keep the path broad near the house, then taper naturally toward the crossing.
    path_pts = [
        (-4.75, 1.20), (-4.30, 0.40), (-3.55, -0.45), (-2.45, -1.20),
        (-1.05, -1.78), (0.55, -2.20), (2.25, -2.72), (3.85, -3.35),
        (5.45, -4.08),
    ]
    path_widths = [0.92, 1.02, 1.12, 1.22, 1.28, 1.26, 1.18, 1.08, 0.96]
    base.ribbon("V5VillagePath", path_pts, path_widths, base.MAT_SOIL_LIGHT, 0.035, 0.13)

    # The foreground river is calmer and more horizontal than the previous diagonal.
    # It still bends toward the bridge so the crossing reads as part of the same route.
    stream_pts = [
        (-12.0, -7.05), (-9.4, -6.86), (-6.8, -6.55), (-4.1, -6.18),
        (-1.35, -5.78), (1.35, -5.33), (3.70, -4.80), (5.45, -4.08),
        (7.85, -3.42), (10.1, -2.86), (12.0, -2.42),
    ]
    bank_widths = [3.10, 3.05, 2.98, 2.94, 2.90, 2.88, 2.82, 2.74, 2.62, 2.52, 2.46]
    water_widths = [2.05, 2.02, 1.96, 1.91, 1.88, 1.84, 1.78, 1.70, 1.60, 1.50, 1.44]
    base.ribbon("V5StreamBank", stream_pts, bank_widths, base.MAT_SOIL, -0.075, 0.16)
    base.ribbon("V5StreamWater", stream_pts, water_widths, base.MAT_WATER, 0.005, 0.12)

    # Crossing pushed to the right edge, matching the approved concept composition.
    center = Vector((5.45, -4.08))
    tangent = Vector((7.85 - 3.70, -3.42 - (-4.80))).normalized()
    crossing = Vector((-tangent.y, tangent.x)).normalized()
    plank_angle = math.atan2(tangent.y, tangent.x)
    deck_len = 3.05
    for i in range(12):
        offset = -deck_len * 0.5 + i * (deck_len / 11.0)
        p = center + crossing * offset
        arch = math.sin(i / 11.0 * math.pi) * 0.14
        base.box(
            f"V5BridgePlank_{i}", (p.x, p.y, 0.31 + arch), (2.16, 0.27, 0.14),
            base.MAT_WOOD, rot=(0, 0, plank_angle), bevel=0.045,
        )

    for side_sign in (-1.0, 1.0):
        rail_center = center + tangent * (0.95 * side_sign)
        rail_points = []
        for k in range(3):
            off = -deck_len * 0.42 + k * deck_len * 0.42
            p = rail_center + crossing * off
            base.cylinder(
                f"V5BridgePost_{side_sign}_{k}", (p.x, p.y, 0.86),
                0.068, 1.22, base.MAT_WOOD_DARK, vertices=10, bevel=0.02,
            )
            rail_points.append((p.x, p.y))
        _segment_box("V5BridgeRail", rail_points[0], rail_points[-1], 1.20, 0.095, 0.095, base.MAT_WOOD_DARK)

    # A natural, landscaped bank: rocks are grouped rather than evenly scattered.
    rocks = [
        (-10.7,-6.20,0.58,14),(-9.7,-7.30,0.42,-20),(-8.15,-6.05,0.50,28),
        (-6.25,-6.95,0.46,-12),(-4.65,-5.70,0.54,24),(-2.70,-6.42,0.43,-18),
        (-0.45,-5.18,0.50,11),(1.65,-5.85,0.42,-28),(3.30,-4.45,0.55,18),
        (6.65,-4.25,0.52,-16),(8.25,-3.05,0.48,26),(10.25,-3.18,0.44,-9),
    ]
    for i, (x, y, s, r) in enumerate(rocks):
        base.place(rock_t, f"V5RiverRock_{i}", (x, y, 0.045), s, r)

    reeds = [
        (-11.2,-6.00),(-10.0,-7.55),(-8.8,-5.95),(-7.2,-7.15),(-5.7,-5.82),
        (-4.1,-6.72),(-2.0,-5.45),(-0.7,-6.02),(1.2,-4.92),(2.8,-5.20),
        (4.25,-4.02),(6.65,-4.32),(7.55,-3.05),(9.15,-3.36),(10.55,-2.72),
    ]
    for i, (x, y) in enumerate(reeds):
        base.place(grass_t, f"V5BankGrass_{i}", (x, y, 0.035), 0.50 + (i % 4) * 0.05, i * 23)

    lilies = [
        (-9.4,-6.67,0.33),(-7.0,-6.42,0.30),(-4.7,-6.10,0.32),
        (-1.65,-5.62,0.31),(1.8,-5.18,0.33),(7.15,-3.55,0.30),(9.45,-2.98,0.28),
    ]
    for i, (x, y, s) in enumerate(lilies):
        base.place(lilypad_t, f"V5Lily_{i}", (x, y, 0.07), s, i * 41)


def v5_rice_fields(wheat_t, grass_t):
    # Deliberate stepped rice terraces on the right side of the composition.
    # Older grid paddies remain suppressed so the result reads as one designed farm.
    _hide_named_prefixes(("PaddyBund_", "PaddyWater_", "Rice_", "V4Paddy_", "V4Bund", "V4Rice_"))

    fields = [
        [(3.55,0.30),(6.35,0.35),(6.85,1.12),(6.30,2.10),(3.75,2.08),(3.18,1.20)],
        [(5.55,2.38),(8.65,2.52),(9.15,3.35),(8.58,4.34),(5.80,4.22),(5.10,3.34)],
        [(7.20,4.58),(10.45,4.82),(10.90,5.80),(10.20,6.72),(7.32,6.58),(6.72,5.52)],
        [(2.05,4.48),(4.88,4.62),(5.28,5.45),(4.72,6.25),(2.12,6.18),(1.62,5.36)],
    ]
    for idx, poly in enumerate(fields):
        z = 0.055 + idx * 0.034
        _polygon_surface(f"V5PaddyWater_{idx}", poly, z, base.MAT_WATER_SHALLOW, 0.065, 0.09)
        outline = poly + [poly[0]]
        base.ribbon(f"V5PaddyBund_{idx}", outline, [0.34] * len(outline), base.MAT_SOIL, z + 0.075, 0.09)

        min_x = min(p[0] for p in poly); max_x = max(p[0] for p in poly)
        min_y = min(p[1] for p in poly); max_y = max(p[1] for p in poly)
        row = 0
        y = min_y + 0.36
        while y <= max_y - 0.20:
            col = 0
            x = min_x + 0.34 + (0.11 if row % 2 else 0.0)
            while x <= max_x - 0.18:
                if _inside_polygon(x, y, poly):
                    scale = 0.28 + ((row + col + idx) % 4) * 0.018
                    base.place(
                        wheat_t, f"V5Rice_{idx}_{row}_{col}", (x, y, z + 0.11),
                        scale, ((row * 17 + col * 11 + idx * 23) % 34) - 17,
                    )
                x += 0.56
                col += 1
            y += 0.52
            row += 1

    terrace_grass = [
        (2.35,3.82),(3.72,4.18),(5.28,4.38),(6.35,4.62),(8.35,4.42),
        (10.35,4.55),(6.55,6.88),(8.05,6.98),(9.70,6.95),
    ]
    for i, (x, y) in enumerate(terrace_grass):
        base.place(grass_t, f"V5PaddyGrass_{i}", (x, y, 0.04), 0.48 + (i % 3) * 0.045, i * 29)


def v5_foliage(tree_t, palm_t, bush_t, grass_t, flower_t, rock_t):
    _V4_FOLIAGE(tree_t, palm_t, bush_t, grass_t, flower_t, rock_t)

    # Remove legacy scatter. The approved concept uses curated clusters:
    # orchard left, palms framing the roof, low flowering shrubs along the path,
    # and an open visual corridor from porch -> bridge -> paddies.
    _hide_named_prefixes((
        "HeroTree_", "HeroPalm_", "HeroBush_", "HeroGrass_", "WildFlowers_", "HeroRock_",
        "V4Tree_", "V4Palm_", "V4Bush_", "V4Grass_",
    ))

    # Orchard: small fruit-tree grouping on the left instead of unrelated singles.
    trees = [
        (-10.2,0.15,0.78,-8),(-8.55,0.05,0.72,12),(-7.00,0.55,0.68,-16),
        (-9.35,2.20,0.66,18),(-7.75,2.55,0.62,-12),
        (9.85,6.15,0.66,-18),(10.75,4.45,0.60,14),
    ]
    # Palms sit behind the architecture so their crowns frame, not cover, the roof.
    palms = [
        (-8.85,4.65,0.78,10),(-6.55,6.15,0.72,-16),(-2.25,7.65,0.62,12),
        (4.90,7.75,0.64,-16),(7.85,7.10,0.70,18),(10.35,5.15,0.68,-10),
    ]
    for i, (x, y, s, r) in enumerate(trees):
        base.place(tree_t, f"V5Tree_{i}", (x, y, 0), s, r)
    for i, (x, y, s, r) in enumerate(palms):
        base.place(palm_t, f"V5Palm_{i}", (x, y, 0), s, r)

    # Layered shrubs around the house and path. Gaps deliberately expose porch/character.
    bush_spots = [
        (-10.65,-1.75),(-9.70,-2.35),(-8.55,-2.55),(-7.35,-2.35),(-6.25,-1.80),
        (-5.80,2.80),(-5.15,3.55),(-4.20,4.12),(-3.10,4.50),(-1.85,4.68),
        (-0.55,4.82),(0.85,4.92),(2.15,4.92),(3.45,4.72),
        (6.65,-0.35),(7.55,-0.05),(8.45,0.48),
        (9.55,-2.15),(8.60,-2.78),(7.45,-3.18),
    ]
    for i, (x, y) in enumerate(bush_spots):
        base.place(bush_t, f"V5Bush_{i}", (x, y, 0.025), 0.46 + (i % 4) * 0.045, i * 31)

    # Flowering clusters echo the reference without blocking gameplay.
    flowers = [
        (-8.85,-3.05),(-7.85,-2.95),(-6.85,-2.55),
        (-5.55,-0.55),(-4.95,-1.12),(-3.75,-1.82),
        (-1.95,-2.16),(0.10,-2.05),(1.45,-2.35),(3.25,-2.78),
        (6.45,-1.82),(7.35,-1.42),
    ]
    for i, (x, y) in enumerate(flowers):
        # "Bush" in the label makes the fixed-camera hybrid renderer use the
        # flowering shrub card instead of deleting the flower mesh.
        base.place(flower_t, f"V5BushFlower_{i}", (x, y, 0.03), 0.40 + (i % 3) * 0.045, i * 37)

    grasses = [
        (-11.2,-7.85),(-9.85,-7.70),(-8.45,-7.42),(-7.05,-7.18),(-5.62,-6.98),
        (-4.05,-6.72),(-2.30,-6.42),(-0.30,-6.02),(1.55,-5.62),(3.45,-5.08),
        (5.05,-4.55),(6.95,-3.98),(8.55,-3.45),(10.10,-2.92),
        (-6.25,2.65),(-5.72,3.10),(-2.80,3.62),(0.15,3.88),(2.65,4.02),(4.75,4.12),
    ]
    for i, (x, y) in enumerate(grasses):
        base.place(grass_t, f"V5Grass_{i}", (x, y, 0.025), 0.48 + (i % 5) * 0.042, i * 19)




base.build_ground = v5_ground
base.build_path_stream_bridge = v5_path_stream_bridge
base.build_rice_fields = v5_rice_fields
base.build_foliage = v5_foliage
_REAL_MAIN()
