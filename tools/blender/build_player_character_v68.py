import bpy
import os

# Lembah Sari Character V6.8 — unified sculpted-hair convergence.
# Candidate only. Keeps the V6.7 body and proportions, then fuses the cap,
# back, temples and layered fringe into one continuous low-noise hair mass.

BASE = os.path.join(os.path.dirname(__file__), "build_player_character_v67.py")
exec(compile(open(BASE, "r", encoding="utf-8").read(), BASE, "exec"), globals(), globals())

recolor(HAIR_WARM, (0.062, 0.018, 0.0065))

hair = join_and_voxel_fuse([
    'V60HairCap',
    'V60HairBack',
    'V60TempleL',
    'V60TempleR',
    'V67HeroSweep',
    'V67LeftLock',
    'V67CenterLock',
    'V67RightLock',
], 'HairV68Unified', HAIR_WARM, voxel=0.0065)

if hair:
    # Very light relaxation removes remesh facets while keeping the directional
    # ridges from the layered fringe readable.
    smooth = hair.modifiers.new('HairSurfaceRelax', 'SMOOTH')
    smooth.factor = 0.28
    smooth.iterations = 2
    bpy.context.view_layer.objects.active = hair
    hair.select_set(True)
    try:
        bpy.ops.object.modifier_apply(modifier=smooth.name)
    except Exception:
        pass
    for poly in hair.data.polygons:
        poly.use_smooth = True

# Final candidate export only. Gameplay remains on the previously promoted V6.4
# until this candidate passes full-body, close-up and gameplay-scale review.
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
print(f'Exported Lembah Sari Character V6.8 unified-hair candidate to {OUT_PATH}')
