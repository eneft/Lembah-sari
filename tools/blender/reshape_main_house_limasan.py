import math
import os

import bpy
from mathutils import Vector

# Geometry-only gate: replace the old two-plane gable silhouette with a
# four-plane Javanese limasan (hip) roof while preserving the existing
# terracotta material families. Downstream albedo/normal response gates remain
# authoritative for the roof surface.

IN_PATH = os.path.abspath(
    os.environ.get("LEMBAH_HOUSE_IN", "assets/models/house_main_01.glb")
)
OUT_PATH = os.path.abspath(os.environ.get("LEMBAH_HOUSE_OUT", IN_PATH))
os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)

if not os.path.exists(IN_PATH):
    raise RuntimeError("Missing house GLB for limasan geometry gate: %s" % IN_PATH)

bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=IN_PATH)


def find_material(prefix):
    for material in bpy.data.materials:
        if material.name.startswith(prefix):
            return material
    raise RuntimeError("Required house material not found: %s" % prefix)


MAT_TERRA = find_material("Soft Terracotta")
MAT_TERRA_LIGHT = find_material("Sunlit Terracotta")
MAT_TERRA_DARK = find_material("Terracotta Shadow")
MAT_FRAME = find_material("Deep Teak Frame")
MAT_FRAME_SOFT = find_material("Warm Teak Frame")


def apply_material(obj, material):
    obj.data.materials.append(material)


def delete_old_roof():
    prefixes = (
        "RoofFront",
        "RoofBack",
        "RoofRidge",
        "FrontTileBand",
        "FrontEaveFascia",
        "BackEaveFascia",
        "LimasanRoof",
        "LimasanHipCap",
        "LimasanSideEaveFascia",
    )
    removed = 0
    for obj in list(bpy.context.scene.objects):
        if any(obj.name.startswith(prefix) for prefix in prefixes):
            bpy.data.objects.remove(obj, do_unlink=True)
            removed += 1
    if removed < 4:
        raise RuntimeError(
            "Limasan gate did not find the expected legacy gable roof objects (removed=%d)"
            % removed
        )
    return removed


def roof_panel(name, vertices, material, thickness=0.16, bevel=0.035):
    mesh = bpy.data.meshes.new(name + "Mesh")
    mesh.from_pydata(vertices, [], [list(range(len(vertices)))])
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    apply_material(obj, material)

    solidify = obj.modifiers.new("Limasan tile body", "SOLIDIFY")
    solidify.thickness = thickness
    solidify.offset = 0.0
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.modifier_apply(modifier=solidify.name)

    if bevel > 0.0:
        bevel_mod = obj.modifiers.new("Soft limasan edge", "BEVEL")
        bevel_mod.width = bevel
        bevel_mod.segments = 2
        bevel_mod.limit_method = "ANGLE"
        bpy.ops.object.modifier_apply(modifier=bevel_mod.name)
    obj.select_set(False)
    return obj


def box(name, location, dimensions, material, rotation=(0.0, 0.0, 0.0), bevel=0.02):
    bpy.ops.mesh.primitive_cube_add(location=location, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dimensions
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel > 0.0:
        bevel_mod = obj.modifiers.new("Soft graphic edge", "BEVEL")
        bevel_mod.width = bevel
        bevel_mod.segments = 2
        bevel_mod.limit_method = "ANGLE"
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=bevel_mod.name)
    apply_material(obj, material)
    return obj


def cylinder_between(name, start, end, radius, material, vertices=14, bevel=0.016):
    start_v = Vector(start)
    end_v = Vector(end)
    direction = end_v - start_v
    length = direction.length
    if length <= 0.0001:
        raise RuntimeError("Zero-length limasan cap: %s" % name)
    midpoint = (start_v + end_v) * 0.5
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=vertices,
        radius=radius,
        depth=length,
        location=midpoint,
    )
    obj = bpy.context.object
    obj.name = name
    obj.rotation_mode = "QUATERNION"
    obj.rotation_quaternion = direction.to_track_quat("Z", "Y")
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    if bevel > 0.0:
        bevel_mod = obj.modifiers.new("Soft cap edge", "BEVEL")
        bevel_mod.width = bevel
        bevel_mod.segments = 2
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=bevel_mod.name)
    apply_material(obj, material)
    return obj


removed_count = delete_old_roof()

# Limasan proportions tuned for the locked 3/4 hero camera. The ridge is
# deliberately short; all four eave corners rise toward its two endpoints.
EAVE_X = 4.25
EAVE_Y = 2.48
EAVE_Z = 3.16
RIDGE_HALF = 2.15
RIDGE_Z = 4.56

front_left = (-EAVE_X, -EAVE_Y, EAVE_Z)
front_right = (EAVE_X, -EAVE_Y, EAVE_Z)
back_left = (-EAVE_X, EAVE_Y, EAVE_Z)
back_right = (EAVE_X, EAVE_Y, EAVE_Z)
ridge_left = (-RIDGE_HALF, 0.0, RIDGE_Z)
ridge_right = (RIDGE_HALF, 0.0, RIDGE_Z)

# Four actual roof planes: two trapezoids + two hip triangles.
roof_panel(
    "LimasanRoofFront",
    [front_left, front_right, ridge_right, ridge_left],
    MAT_TERRA,
)
roof_panel(
    "LimasanRoofBack",
    [back_left, ridge_left, ridge_right, back_right],
    MAT_TERRA_DARK,
)
roof_panel(
    "LimasanRoofLeftHip",
    [front_left, ridge_left, back_left],
    MAT_TERRA,
)
roof_panel(
    "LimasanRoofRightHip",
    [front_right, back_right, ridge_right],
    MAT_TERRA_DARK,
)

# Wuwung is now a short central ridge, unlike the old full-width gable ridge.
cylinder_between(
    "RoofRidge",
    ridge_left,
    ridge_right,
    0.13,
    MAT_TERRA_LIGHT,
    vertices=16,
    bevel=0.025,
)

# Small terracotta hip caps make the four-way roof construction readable at the
# game camera without turning the roof into a noisy realistic tile model.
for index, (corner, ridge_end) in enumerate(
    (
        (front_left, ridge_left),
        (back_left, ridge_left),
        (front_right, ridge_right),
        (back_right, ridge_right),
    )
):
    cylinder_between(
        "LimasanHipCap_%d" % index,
        corner,
        ridge_end,
        0.075,
        MAT_TERRA_LIGHT,
        vertices=12,
        bevel=0.014,
    )

# Front tile bands narrow toward the short ridge; the old equal-width bands were
# a strong gable cue. Geometry stays stylized and readable at 1280x720.
roof_angle = math.atan2(RIDGE_Z - EAVE_Z, EAVE_Y)
for i in range(7):
    t = (i + 1.0) / 8.0  # 0 = ridge, 1 = front eave
    y = -t * (EAVE_Y - 0.10)
    z = RIDGE_Z - t * (RIDGE_Z - EAVE_Z - 0.04)
    width = (RIDGE_HALF * 2.0) + t * ((EAVE_X * 2.0 - 0.28) - RIDGE_HALF * 2.0)
    box(
        "FrontTileBand",
        (0.0, y, z),
        (width, 0.085, 0.085),
        MAT_TERRA_LIGHT,
        rotation=(roof_angle, 0.0, 0.0),
        bevel=0.018,
    )

# Four eave fascias close the silhouette on every side, another key limasan cue.
box(
    "FrontEaveFascia",
    (0.0, -EAVE_Y, EAVE_Z),
    (EAVE_X * 2.0, 0.15, 0.22),
    MAT_FRAME,
    bevel=0.035,
)
box(
    "BackEaveFascia",
    (0.0, EAVE_Y, EAVE_Z),
    (EAVE_X * 2.0, 0.15, 0.22),
    MAT_FRAME_SOFT,
    bevel=0.035,
)
box(
    "LimasanSideEaveFasciaLeft",
    (-EAVE_X, 0.0, EAVE_Z),
    (0.15, EAVE_Y * 2.0, 0.22),
    MAT_FRAME,
    bevel=0.035,
)
box(
    "LimasanSideEaveFasciaRight",
    (EAVE_X, 0.0, EAVE_Z),
    (0.15, EAVE_Y * 2.0, 0.22),
    MAT_FRAME_SOFT,
    bevel=0.035,
)

# Export the corrected house. Texture and surface-response passes execute after
# this gate in CI and therefore remain unchanged/authoritative.
bpy.ops.object.select_all(action="SELECT")
bpy.ops.export_scene.gltf(
    filepath=OUT_PATH,
    export_format="GLB",
    use_selection=True,
    export_apply=True,
    export_yup=True,
)

print(
    "Reshaped main house to Javanese limasan roof: %s (legacy roof objects removed=%d)"
    % (OUT_PATH, removed_count)
)
