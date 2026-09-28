import bpy
import os
from mathutils import Matrix, Vector

# Lembah Sari Character V3.0 proportion pass.
# Preserve the V2.9 design language but match the approved master concept more closely:
# less chibi, smaller head/eyes, longer body, same swept hair/outfit/gear identity.

BASE = os.path.join(os.path.dirname(__file__), "build_player_character_v29.py")
exec(compile(open(BASE, "r", encoding="utf-8").read(), BASE, "exec"), globals(), globals())


def world_scale_about(obj, pivot, sx, sy, sz):
    p = Vector(pivot)
    transform = Matrix.Translation(p) @ Matrix.Diagonal((sx, sy, sz, 1.0)) @ Matrix.Translation(-p)
    obj.matrix_world = transform @ obj.matrix_world


# 1) Lengthen the whole figure slightly from the feet. This moves the silhouette
#    toward the concept's ~4.5-head proportion without changing horizontal bulk.
for obj in list(ROOT.children_recursive):
    world_scale_about(obj, (0.0, 0.0, 0.0), 1.0, 1.0, 1.075)

# After global stretch the approximate face center is around this height.
HEAD_PIVOT = (0.0, 0.0, 1.715)

# 2) Reduce head + face + ears. Hair is reduced a little less so the hairstyle
#    keeps its expressive silhouette.
head_core = ["Head", "Ear_-1", "Ear_1", "Nose", "Smile", "Blush_-1", "Blush_1"]
for name in head_core:
    obj = bpy.data.objects.get(name)
    if obj:
        world_scale_about(obj, HEAD_PIVOT, 0.89, 0.91, 0.89)

# Hair objects from all V2.9 layers. Keep slightly more width/volume than the face.
hair_names = [
    "HairBack", "ConceptSideLeft", "ConceptSideRight",
    "HeroFringeOuterL", "HeroFringeSweep", "HeroFringeShortR",
    "HeroTopSweep", "HeroTopTuft"
]
for name in hair_names:
    obj = bpy.data.objects.get(name)
    if obj:
        world_scale_about(obj, HEAD_PIVOT, 0.93, 0.94, 0.92)

# 3) Eyes were reading too anime/chibi in environment. Reduce all eye pieces
#    around their own centers while retaining readable dark irises.
for side in (-1, 1):
    eye_names = [f"EyeWhite_{side}", f"Iris_{side}", f"Pupil_{side}", f"EyeGlint_{side}"]
    group = [bpy.data.objects.get(n) for n in eye_names]
    group = [o for o in group if o]
    if group:
        center = Vector((0.0, 0.0, 0.0))
        for o in group:
            center += o.matrix_world.translation
        center /= len(group)
        for o in group:
            world_scale_about(o, center, 0.80, 0.84, 0.80)

    # Brows/lids follow the reduced face but stay readable.
    for prefix in ["UpperLid", "Brow"]:
        suffix = "L" if side == -1 else "R"
        obj = bpy.data.objects.get(prefix + suffix)
        if obj:
            world_scale_about(obj, HEAD_PIVOT, 0.90, 0.92, 0.90)

# 4) Slim shirt/waist slightly. The concept has relaxed clothing, but the
#    torso should not read as a toy cylinder.
for name, sx, sy in [
    ("ShirtTorso", 0.94, 0.96),
    ("OverallHips", 0.96, 0.98),
    ("OverallBib", 0.94, 0.98),
    ("BibPocket", 0.94, 0.98),
]:
    obj = bpy.data.objects.get(name)
    if obj:
        obj.scale.x *= sx
        obj.scale.y *= sy

# Slightly reduce arm thickness while retaining the relaxed bent pose.
for side in (-1, 1):
    for prefix in ["Sleeve", "RolledSleeve", "Forearm"]:
        obj = bpy.data.objects.get(f"{prefix}_{side}")
        if obj:
            obj.scale.x *= 0.94
            obj.scale.y *= 0.94
    palm = bpy.data.objects.get(f"Palm_{side}")
    if palm:
        palm.scale *= 0.94

# 5) Give the boots a little more presence like the reference without increasing
#    character height much.
for side in (-1, 1):
    for prefix in ["BootToe", "BootSole", "BootShaft", "BootTongue"]:
        obj = bpy.data.objects.get(f"{prefix}_{side}")
        if obj:
            obj.scale.x *= 1.035
            obj.scale.y *= 1.025

# Re-export V3.0.
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
print(f"Exported Lembah Sari Character V3.0 proportion pass to {OUT_PATH}")
