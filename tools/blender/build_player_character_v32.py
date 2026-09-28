import bpy
import os

# V3.2 — targeted correction after V3.1 studio review.
# Preserve V3.1 palette/detail polish, but remove balloon-like sleeves.

BASE = os.path.join(os.path.dirname(__file__), "build_player_character_v31.py")
exec(compile(open(BASE, "r", encoding="utf-8").read(), BASE, "exec"), globals(), globals())

# Slim and lengthen rolled linen sleeves to match the master concept.
for side in (-1, 1):
    sleeve = bpy.data.objects.get(f"Sleeve_{side}")
    cuff = bpy.data.objects.get(f"RolledSleeve_{side}")
    if sleeve:
        sleeve.scale.x *= 0.80
        sleeve.scale.y *= 0.90
        sleeve.scale.z *= 1.08
        sleeve.location.x *= 0.97
    if cuff:
        cuff.scale.x *= 0.88
        cuff.scale.y *= 0.92
        cuff.scale.z *= 0.82
        cuff.location.x *= 0.98

# Keep hands visually connected to the slimmer arm silhouette.
for side in (-1, 1):
    palm = bpy.data.objects.get(f"Palm_{side}")
    thumb = bpy.data.objects.get(f"Thumb_{side}")
    if palm:
        palm.scale.x *= 0.96
        palm.scale.y *= 0.96
    if thumb:
        thumb.scale *= 0.96

# Final V3.2 export.
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
print(f"Exported Lembah Sari Character V3.2 sleeve correction to {OUT_PATH}")
