import math
import os
import random
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


def _inset_polygon(polygon, factor):
    cx = sum(p[0] for p in polygon) / len(polygon)
    cy = sum(p[1] for p in polygon) / len(polygon)
    return [(cx + (x - cx) * factor, cy + (y - cy) * factor) for x, y in polygon]


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
    # Uneven widths stop the shoreline reading as two perfectly parallel bands.
    bank_widths = [3.18, 3.00, 3.12, 2.92, 3.02, 2.82, 2.91, 2.70, 2.68, 2.46, 2.50]
    wet_widths = [2.46, 2.38, 2.42, 2.29, 2.32, 2.23, 2.20, 2.08, 1.98, 1.85, 1.80]
    water_widths = [2.08, 1.98, 2.02, 1.88, 1.92, 1.80, 1.78, 1.67, 1.60, 1.48, 1.43]
    base.ribbon("V5StreamBank", stream_pts, bank_widths, base.MAT_SOIL, -0.075, 0.16)
    # Thin damp margin visually blends soil into water instead of a hard cut.
    base.ribbon("V5WetBank", stream_pts, wet_widths, MAT_MUD, -0.048, 0.10)
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

    # Bank stones are arranged as a few irregular clusters. Large anchors get
    # smaller companions so nothing reads as an evenly spaced row of props.
    rocks = [
        (-10.72,-6.18,0.60,14),(-10.22,-6.42,0.34,-22),(-9.78,-6.08,0.29,31),
        (-7.95,-6.16,0.53,27),(-7.48,-6.43,0.31,-14),
        (-4.72,-5.72,0.57,23),(-4.20,-5.98,0.33,-26),(-3.76,-5.64,0.26,11),
        (-0.42,-5.17,0.52,10),(0.06,-5.42,0.28,-18),
        (3.34,-4.47,0.57,18),(3.86,-4.63,0.31,-11),
        (6.67,-4.20,0.55,-16),(7.17,-3.95,0.30,24),
        (9.95,-3.06,0.48,-8),(10.42,-2.82,0.27,17),
    ]
    for i, (x, y, s, r) in enumerate(rocks):
        base.place(rock_t, f"V5RiverRock_{i}", (x, y, 0.045), s, r)

    # Reeds concentrate around stone clusters and quiet inside bends, leaving
    # occasional open shoreline so the bank does not become a continuous hedge.
    reeds = [
        (-11.28,-5.95),(-10.86,-6.56),(-10.35,-5.91),(-9.92,-6.70),
        (-8.48,-5.88),(-8.03,-6.54),(-7.58,-5.96),
        (-5.18,-5.50),(-4.78,-6.18),(-4.32,-5.48),(-3.88,-6.13),
        (-2.02,-5.37),(-1.44,-5.83),(-0.70,-5.02),(-0.18,-5.65),
        (2.75,-4.33),(3.28,-4.93),(3.92,-4.17),
        (6.18,-3.83),(6.72,-4.48),(7.34,-3.67),
        (9.18,-3.27),(9.74,-2.73),(10.45,-3.05),
    ]
    for i, (x, y) in enumerate(reeds):
        scale = 0.44 + (i % 5) * 0.055
        base.place(grass_t, f"V5BankGrass_{i}", (x, y, 0.035), scale, i * 23)

    lilies = [
        (-9.4,-6.67,0.33),(-7.0,-6.42,0.30),(-4.7,-6.10,0.32),
        (-1.65,-5.62,0.31),(1.8,-5.18,0.33),(7.15,-3.55,0.30),(9.45,-2.98,0.28),
    ]
    for i, (x, y, s) in enumerate(lilies):
        base.place(lilypad_t, f"V5Lily_{i}", (x, y, 0.07), s, i * 41)


def v5_rice_fields(wheat_t, grass_t):
    # Hand-shaped stepped paddies. Water sits inset from the earthen shelf, bunds
    # vary in width, and planting uses deterministic jitter rather than a perfect grid.
    _hide_named_prefixes(("PaddyBund_", "PaddyWater_", "Rice_", "V4Paddy_", "V4Bund", "V4Rice_"))

    fields = [
        [(3.42,0.26),(4.62,0.18),(6.22,0.34),(6.78,0.92),(6.62,1.62),(5.88,2.18),(4.20,2.12),(3.34,1.48)],
        [(5.32,2.34),(6.46,2.25),(8.18,2.46),(9.02,3.02),(9.12,3.70),(8.54,4.38),(6.76,4.36),(5.58,3.92),(5.06,3.18)],
        [(7.04,4.56),(8.28,4.54),(10.12,4.80),(10.82,5.48),(10.68,6.20),(9.86,6.78),(8.20,6.72),(7.12,6.36),(6.66,5.48)],
        [(2.02,4.42),(3.16,4.36),(4.58,4.54),(5.22,5.04),(5.20,5.66),(4.62,6.28),(3.12,6.32),(2.10,6.02),(1.58,5.40)],
    ]
    levels = [0.055, 0.115, 0.185, 0.250]

    for idx, poly in enumerate(fields):
        z = levels[idx]
        water_poly = _inset_polygon(poly, 0.86)

        # Earthen terrace mass extends down toward the base terrain instead of
        # presenting the paddy as a thin floating board.
        shelf_thickness = z + 0.075
        _polygon_surface(
            f"V5PaddyEarth_{idx}", poly, z - 0.035, MAT_MUD,
            shelf_thickness, 0.12,
        )

        # Shallow water remains just above the shelf and leaves a readable mud rim.
        _polygon_surface(
            f"V5PaddyWater_{idx}", water_poly, z + 0.008,
            base.MAT_WATER_SHALLOW, 0.018, 0.045,
        )

        outline = poly + [poly[0]]
        bund_widths = [
            0.30 + 0.055 * ((edge * 3 + idx * 2) % 4)
            for edge in range(len(outline))
        ]
        base.ribbon(
            f"V5PaddyBund_{idx}", outline, bund_widths,
            base.MAT_SOIL, z + 0.072, 0.10,
        )

        # Organic rows: keep cultivation readable, but introduce small positional
        # offsets, occasional gaps and scale/rotation variation.
        rng = random.Random(20261006 + idx * 97)
        min_x = min(p[0] for p in water_poly); max_x = max(p[0] for p in water_poly)
        min_y = min(p[1] for p in water_poly); max_y = max(p[1] for p in water_poly)

        row = 0
        y = min_y + 0.34
        while y <= max_y - 0.18:
            col = 0
            x = min_x + 0.31 + (0.12 if row % 2 else 0.0)
            while x <= max_x - 0.18:
                px = x + rng.uniform(-0.075, 0.075)
                py = y + rng.uniform(-0.055, 0.055)
                # Sparse missing clumps keep rows from reading like a stamped grid.
                if _inside_polygon(px, py, water_poly) and rng.random() > 0.09:
                    scale = rng.uniform(0.265, 0.345)
                    rotation = rng.uniform(-20.0, 20.0)
                    base.place(
                        wheat_t, f"V5Rice_{idx}_{row}_{col}",
                        (px, py, z + 0.115), scale, rotation,
                    )
                x += 0.57 + rng.uniform(-0.025, 0.025)
                col += 1
            y += 0.52 + rng.uniform(-0.025, 0.025)
            row += 1

    # Low grass softens selected corners and level changes without outlining every
    # paddy continuously.
    terrace_grass = [
        (2.20,3.98,0.49),(3.55,4.26,0.54),(5.12,4.24,0.47),
        (6.16,4.54,0.56),(7.72,4.38,0.48),(9.08,4.48,0.53),
        (10.48,4.70,0.46),(6.62,6.80,0.52),(8.18,6.94,0.48),
        (9.66,6.90,0.56),(3.10,6.42,0.47),(4.74,6.18,0.52),
    ]
    for i, (x, y, scale) in enumerate(terrace_grass):
        base.place(grass_t, f"V5PaddyGrass_{i}", (x, y, 0.055), scale, i * 29)




def v5_foliage(tree_t, palm_t, bush_t, grass_t, flower_t, rock_t):
    _V4_FOLIAGE(tree_t, palm_t, bush_t, grass_t, flower_t, rock_t)

    # Remove legacy scatter. This pass builds three readable depth bands:
    # playable foreground clusters, an open house/paddy corridor, and a broken
    # midground vegetation belt that hides the ground-to-backdrop seam.
    _hide_named_prefixes((
        "HeroTree_", "HeroPalm_", "HeroBush_", "HeroGrass_", "WildFlowers_", "HeroRock_",
        "V4Tree_", "V4Palm_", "V4Bush_", "V4Grass_",
    ))

    # Orchard trees use deliberately uneven scale and depth so the left side no
    # longer reads as a repeated row of identical copies.
    trees = [
        (-10.35,0.05,0.82,-9),(-9.05,-0.38,0.67,13),(-7.72,0.42,0.75,-18),
        (-9.62,2.12,0.61,19),(-7.95,2.78,0.70,-11),(-6.72,1.92,0.57,16),
        (9.82,6.12,0.63,-19),(10.76,4.52,0.72,15),
    ]
    # Palms frame the house roof and farm edge, but keep the roof peak and main
    # gameplay path visually open.
    palms = [
        (-9.02,4.72,0.82,9),(-6.72,6.22,0.67,-17),(-2.55,7.72,0.58,12),
        (4.88,7.86,0.62,-15),(7.72,7.22,0.73,18),(10.28,5.28,0.64,-9),
    ]
    for i, (x, y, s, r) in enumerate(trees):
        base.place(tree_t, f"V5Tree_{i}", (x, y, 0), s, r)
    for i, (x, y, s, r) in enumerate(palms):
        base.place(palm_t, f"V5Palm_{i}", (x, y, 0), s, r)

    # Midground transition belt. It is intentionally discontinuous around the
    # house roof and path, with denser masses toward the far left/right edges.
    mid_trees = [
        (-12.2,7.35,0.58,-12),(-10.85,8.25,0.48,15),(-9.42,7.58,0.55,-20),
        (-7.90,8.72,0.44,11),(-5.95,8.92,0.48,-14),
        (5.92,9.02,0.45,16),(7.48,8.48,0.54,-19),(8.92,8.82,0.47,13),
        (10.32,7.92,0.57,-10),(11.62,7.18,0.51,18),
    ]
    mid_palms = [
        (-11.35,9.20,0.44,14),(-8.48,9.55,0.40,-17),
        (6.82,9.62,0.42,15),(9.70,9.30,0.46,-12),
    ]
    mid_bushes = [
        (-12.45,6.55,0.42),(-11.58,6.86,0.50),(-10.62,6.42,0.38),
        (-9.58,6.94,0.46),(-8.72,6.55,0.36),(-7.55,7.18,0.44),
        (-6.32,7.02,0.40),(-4.95,7.42,0.36),
        (4.72,7.55,0.38),(5.88,7.20,0.46),(7.04,7.42,0.40),
        (8.18,7.02,0.48),(9.28,7.30,0.38),(10.42,6.78,0.46),
        (11.50,6.42,0.40),(12.25,6.85,0.36),
    ]
    for i, (x, y, s, r) in enumerate(mid_trees):
        base.place(tree_t, f"V5MidTree_{i}", (x, y, 0), s, r)
    for i, (x, y, s, r) in enumerate(mid_palms):
        base.place(palm_t, f"V5MidPalm_{i}", (x, y, 0), s, r)
    for i, (x, y, s) in enumerate(mid_bushes):
        base.place(bush_t, f"V5MidBush_{i}", (x, y, 0.015), s, (i * 37) % 70 - 35)

    # Foreground shrubs are grouped into loose islands instead of evenly spaced
    # rows. The center stays open for character readability and path navigation.
    bush_spots = [
        (-10.82,-2.18,0.53),(-9.92,-2.78,0.43),(-8.88,-2.08,0.49),
        (-8.02,-3.02,0.39),(-7.02,-2.35,0.55),(-6.12,-2.72,0.42),
        (-5.72,2.78,0.46),(-5.05,3.62,0.39),(-4.08,4.18,0.52),
        (-2.92,4.58,0.41),(-1.62,4.72,0.48),(-0.18,4.90,0.37),
        (1.20,4.96,0.50),(2.58,4.90,0.40),(3.72,4.58,0.46),
        (6.58,-0.48,0.44),(7.52,-0.08,0.53),(8.48,0.56,0.40),
        (9.68,-2.18,0.50),(8.72,-2.88,0.41),(7.52,-3.24,0.47),
    ]
    for i, (x, y, s) in enumerate(bush_spots):
        base.place(bush_t, f"V5Bush_{i}", (x, y, 0.025), s, (i * 31) % 74 - 37)

    # Flowering clusters provide irregular accents rather than a continuous border.
    flowers = [
        (-9.08,-3.12,0.42),(-8.12,-2.72,0.35),(-6.72,-2.88,0.45),
        (-5.48,-0.62,0.38),(-4.82,-1.18,0.44),(-3.62,-1.92,0.35),
        (-2.02,-2.22,0.42),(0.02,-2.06,0.36),(1.52,-2.42,0.45),
        (3.20,-2.82,0.39),(6.38,-1.86,0.43),(7.42,-1.38,0.36),
    ]
    for i, (x, y, s) in enumerate(flowers):
        # "Bush" in the label makes the fixed-camera hybrid renderer use the
        # flowering shrub card while retaining the authored size variation.
        base.place(flower_t, f"V5BushFlower_{i}", (x, y, 0.03), s, i * 37)

    grasses = [
        (-11.2,-7.85),(-9.85,-7.70),(-8.45,-7.42),(-7.05,-7.18),(-5.62,-6.98),
        (-4.05,-6.72),(-2.30,-6.42),(-0.30,-6.02),(1.55,-5.62),(3.45,-5.08),
        (5.05,-4.55),(6.95,-3.98),(8.55,-3.45),(10.10,-2.92),
        (-6.25,2.65),(-5.72,3.10),(-2.80,3.62),(0.15,3.88),(2.65,4.02),(4.75,4.12),
    ]
    for i, (x, y) in enumerate(grasses):
        base.place(grass_t, f"V5Grass_{i}", (x, y, 0.025), 0.46 + (i % 5) * 0.045, i * 19)






base.build_ground = v5_ground
base.build_path_stream_bridge = v5_path_stream_bridge
base.build_rice_fields = v5_rice_fields
base.build_foliage = v5_foliage
_REAL_MAIN()
