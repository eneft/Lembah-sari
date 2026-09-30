import bpy
import os

# Lembah Sari Character V6.6 — final silhouette polish candidate.
# Candidate only. Keeps the accepted V6.5 structural body/arm/trouser rebuild,
# then fixes the two remaining visual blockers: strip-like fringe and long hands.

BASE = os.path.join(os.path.dirname(__file__), "build_player_character_v65.py")
exec(compile(open(BASE, "r", encoding="utf-8").read(), BASE, "exec"), globals(), globals())


def remove_many(names):
    for name in names:
        obj = bpy.data.objects.get(name)
        if obj:
            bpy.data.objects.remove(obj, do_unlink=True)


# -----------------------------------------------------------------------------
# HAIR — one broad rounded front mass rather than multiple strip-like locks.
# It overlaps the cap and temples so the front reads as a coherent haircut.
# -----------------------------------------------------------------------------
remove_many(['V65FringeSweep', 'V65FringeLeft', 'V65FringeRight'])
recolor(HAIR, (0.040, 0.012, 0.005))
recolor(HAIR_WARM, (0.078, 0.023, 0.009))

front = rounded_patch('V66FrontSweep', [
    (-0.188, 1.903),
    (-0.160, 1.934),
    (-0.112, 1.958),
    (-0.052, 1.968),
    ( 0.012, 1.960),
    ( 0.076, 1.940),
    ( 0.132, 1.908),
    ( 0.163, 1.878),
    ( 0.145, 1.852),
    ( 0.094, 1.865),
    ( 0.040, 1.883),
    (-0.018, 1.897),
    (-0.074, 1.889),
    (-0.126, 1.870),
    (-0.168, 1.858),
    (-0.190, 1.872),
], -0.150, HAIR_WARM, 0.062)
if front:
    # Slight backward tilt lets the cap and fringe blend instead of appearing
    # as a plate sitting on the forehead.
    front.rotation_euler.x = 0.035

# One soft side accent gives asymmetry without reintroducing a three-piece fringe.
side = rounded_patch('V66SideAccent', [
    (0.094, 1.930),
    (0.137, 1.926),
    (0.172, 1.903),
    (0.187, 1.874),
    (0.181, 1.842),
    (0.160, 1.818),
    (0.137, 1.832),
    (0.121, 1.866),
], -0.145, HAIR, 0.052)
if side:
    side.rotation_euler.x = 0.025

# -----------------------------------------------------------------------------
# HANDS — shorten only the palm/finger portion while preserving the continuous
# V6.5 forearm/wrist topology. No seams or new hand pieces are introduced.
# -----------------------------------------------------------------------------
for side in (-1, 1):
    arm = bpy.data.objects.get(f'ArmHandV65_{side}')
    if arm and arm.type == 'MESH':
        wrist_z = 0.870
        for v in arm.data.vertices:
            if v.co.z < wrist_z:
                v.co.z = wrist_z - (wrist_z - v.co.z) * 0.83

# Tiny lower-body refinement: keep relaxed thighs, slightly narrow only the cuffs.
for side in (-1, 1):
    cuff = bpy.data.objects.get(f'TrouserCuff_{side}') or bpy.data.objects.get(f'Cuff_{side}')
    if cuff:
        cuff.scale.x *= 0.97

# Final candidate export only. Gameplay V6.4 stays untouched until acceptance.
bpy.ops.object.select_all(action='DESELECT')
ROOT.select_set(True)
for obj in ROOT.children_recursive:
    obj.select_set(True)
bpy.context.view_layer.objects.active = ROOT
bpy.ops.export_scene.gltf(
    filepath=OUT_PATH,
    export_format='GLB',
    use_selection=True,
    export_apply=True,
    export_yup=True,
)
print(f'Exported Lembah Sari Character V6.6 silhouette-polish candidate to {OUT_PATH}')
