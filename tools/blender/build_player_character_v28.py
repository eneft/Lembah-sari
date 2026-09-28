import bpy
import math
import os
from mathutils import Vector

# V2.8 refinement layer over V2.7.
# Main goals: concept-like swept tapered hair, relaxed bent arms,
# narrower overall bib, readable cargo pocket, softer facial accents.

BASE = os.path.join(os.path.dirname(__file__), "build_player_character_v27.py")
exec(compile(open(BASE, "r", encoding="utf-8").read(), BASE, "exec"), globals(), globals())


def remove_obj(name):
    obj = bpy.data.objects.get(name)
    if obj:
        bpy.data.objects.remove(obj, do_unlink=True)


def path_lock(name, centers, radii, tip, mat, ring_segments=10):
    verts = []
    faces = []
    points = [Vector(p) for p in centers]
    tip_v = Vector(tip)
    for i, center in enumerate(points):
        if i == 0:
            tangent = points[1] - center
        elif i == len(points) - 1:
            tangent = tip_v - points[i - 1]
        else:
            tangent = points[i + 1] - points[i - 1]
        tangent.normalize()
        ref = Vector((0.0, 1.0, 0.0))
        if abs(tangent.dot(ref)) > 0.88:
            ref = Vector((1.0, 0.0, 0.0))
        axis1 = tangent.cross(ref).normalized()
        axis2 = tangent.cross(axis1).normalized()
        rx, ry = radii[i]
        for j in range(ring_segments):
            a = math.tau * j / ring_segments
            off = axis1 * (math.cos(a) * rx) + axis2 * (math.sin(a) * ry)
            verts.append(tuple(center + off))
    for r in range(len(points) - 1):
        a0 = r * ring_segments
        a1 = (r + 1) * ring_segments
        for j in range(ring_segments):
            n = (j + 1) % ring_segments
            faces.append((a0 + j, a1 + j, a1 + n, a0 + n))
    last = (len(points) - 1) * ring_segments
    tip_i = len(verts)
    verts.append(tuple(tip_v))
    for j in range(ring_segments):
        n = (j + 1) % ring_segments
        faces.append((last + j, tip_i, last + n))
    mesh = bpy.data.meshes.new(name + "Mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    return attach(smooth(obj), mat)


# -----------------------------------------------------------------------------
# HAIR: remove oval fringe and build fewer broad tapered locks.
# -----------------------------------------------------------------------------
for name in [
    "BangSweepL", "BangSweepCenter", "BangShortR",
    "TempleSoftL", "TempleSoftR", "CrownMassL", "CrownMassR", "CrownSweep"
]:
    remove_obj(name)

# Keep the rounded back mass, then layer concept-like swept clumps over it.
path_lock(
    "ConceptBangLeft",
    [(-0.125, -0.052, 1.795), (-0.145, -0.100, 1.755), (-0.150, -0.145, 1.700)],
    [(0.073, 0.047), (0.064, 0.042), (0.050, 0.034)],
    (-0.157, -0.181, 1.585), HAIR_WARM,
)
path_lock(
    "ConceptBangCenter",
    [(-0.050, -0.058, 1.815), (-0.055, -0.112, 1.770), (-0.045, -0.153, 1.720)],
    [(0.070, 0.045), (0.061, 0.040), (0.047, 0.032)],
    (-0.026, -0.185, 1.620), HAIR,
)
path_lock(
    "ConceptBangRight",
    [(0.035, -0.050, 1.802), (0.066, -0.095, 1.765), (0.090, -0.132, 1.725)],
    [(0.058, 0.041), (0.050, 0.036), (0.038, 0.029)],
    (0.128, -0.171, 1.665), HAIR_WARM,
)
path_lock(
    "ConceptSideLeft",
    [(-0.175, -0.005, 1.720), (-0.190, -0.038, 1.680), (-0.194, -0.067, 1.640)],
    [(0.040, 0.034), (0.034, 0.030), (0.026, 0.023)],
    (-0.195, -0.095, 1.580), HAIR,
)
path_lock(
    "ConceptSideRight",
    [(0.170, 0.005, 1.710), (0.185, -0.025, 1.675), (0.190, -0.052, 1.640)],
    [(0.036, 0.032), (0.031, 0.028), (0.024, 0.022)],
    (0.190, -0.082, 1.590), HAIR,
)

# Top sweep stays low and sideways instead of standing as spikes.
path_lock(
    "ConceptTopLeft",
    [(-0.090, 0.020, 1.800), (-0.125, 0.015, 1.825), (-0.155, 0.008, 1.838)],
    [(0.055, 0.041), (0.046, 0.036), (0.034, 0.027)],
    (-0.190, -0.005, 1.842), HAIR_WARM,
)
path_lock(
    "ConceptTopCenter",
    [(-0.010, 0.010, 1.820), (0.018, 0.005, 1.842), (0.045, 0.000, 1.850)],
    [(0.052, 0.040), (0.043, 0.034), (0.032, 0.026)],
    (0.082, -0.006, 1.842), HAIR,
)
path_lock(
    "ConceptTopRight",
    [(0.072, 0.018, 1.797), (0.105, 0.012, 1.816), (0.132, 0.004, 1.822)],
    [(0.045, 0.036), (0.038, 0.031), (0.029, 0.024)],
    (0.164, -0.007, 1.807), HAIR_WARM,
)

# -----------------------------------------------------------------------------
# ARMS: rebuild with a gentle forward/inward bend like the concept turnaround.
# -----------------------------------------------------------------------------
for side in (-1, 1):
    for prefix in ["Sleeve", "RolledSleeve", "Forearm", "Palm", "Thumb"]:
        remove_obj(f"{prefix}_{side}")

for side in (-1, 1):
    s = float(side)
    shoulder = Vector((0.188*s, -0.002, 1.270))
    elbow = Vector((0.248*s, -0.028, 1.085))
    cuff = Vector((0.242*s, -0.040, 1.018))
    wrist = Vector((0.207*s, -0.082, 0.805))
    palm = Vector((0.197*s, -0.095, 0.718))
    tapered(f"Sleeve_{side}", shoulder, elbow, 0.078, 0.066, SHIRT, 24, 0.007)
    tapered(f"RolledSleeve_{side}", elbow, cuff, 0.070, 0.066, SHIRT_SHADOW, 24, 0.006)
    tapered(f"Forearm_{side}", cuff, wrist, 0.049, 0.041, SKIN, 22, 0.006)
    uv(f"Palm_{side}", tuple(palm), (0.044, 0.032, 0.071), SKIN, 20, 12,
       rot=(0.0, math.radians(8*s), math.radians(-4*s)))
    uv(f"Thumb_{side}", (palm.x + 0.029*s, palm.y - 0.008, palm.z + 0.004),
       (0.016, 0.014, 0.029), SKIN, 16, 10,
       rot=(0.0, math.radians(16*s), math.radians(18*s)))

# -----------------------------------------------------------------------------
# OVERALL: narrower bib/pocket and visible waist seam.
# -----------------------------------------------------------------------------
for name, sx in [("OverallBib", 0.90), ("BibPocket", 0.88)]:
    obj = bpy.data.objects.get(name)
    if obj:
        obj.scale.x *= sx

for side in (-1, 1):
    strap = bpy.data.objects.get(f"OverallStrap_{side}")
    button = bpy.data.objects.get(f"BibButton_{side}")
    if strap:
        strap.scale.x *= 0.92
    if button:
        button.location.x *= 0.92

curve("OverallWaistSeam", [(-0.150, -0.137, 0.985), (0.0, -0.151, 0.978), (0.150, -0.137, 0.985)], OVERALL_DARK, 0.005)
for side in (-1, 1):
    ico(f"WaistButton_{side}", (0.135*side, -0.145, 0.990), (0.013, 0.006, 0.013), BRASS, 2)

cargo = bpy.data.objects.get("CargoPocketV27")
if cargo:
    cargo.location.y -= 0.085
cargo_btn = bpy.data.objects.get("CargoButtonV27")
if cargo_btn:
    cargo_btn.location.y -= 0.082

# Pants get a little more loose through thigh, without widening the boots.
for side in (-1, 1):
    leg = bpy.data.objects.get(f"Trouser_{side}")
    if leg:
        leg.scale.x *= 1.045
        leg.scale.y *= 1.025

# -----------------------------------------------------------------------------
# FACE polish: subtler blush, slightly lower brows, warmer smile.
# -----------------------------------------------------------------------------
BLUSH.diffuse_color = (0.62, 0.26, 0.20, 1.0)
if BLUSH.use_nodes:
    bsdf = BLUSH.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.62, 0.26, 0.20, 1.0)
for side in (-1, 1):
    blush = bpy.data.objects.get(f"Blush_{side}")
    if blush:
        blush.scale.x *= 0.82
        blush.scale.z *= 0.80

# Final export.
bpy.ops.object.select_all(action="DESELECT")
ROOT.select_set(True)
for obj in ROOT.children_recursive:
    obj.select_set(True)
bpy.context.view_layer.objects.active = ROOT
bpy.ops.export_scene.gltf(
    filepath=OUT_PATH,
    export_format="GLB",
    use_selection=True,
    export_apply=True,
    export_yup=True,
)
print(f"Exported Lembah Sari Character Rework V2.8 to {OUT_PATH}")
