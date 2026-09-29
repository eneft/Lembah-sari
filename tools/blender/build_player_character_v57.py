import bpy
import math
import os
from mathutils import Vector

# Lembah Sari Character V5.7 — concept-turnaround convergence.
# Candidate only. Rebuilds the head mesh to a softer youthful silhouette,
# makes the hairstyle strongly asymmetric/swept, and changes the idle hands
# to softly closed sculpted fists like the front turnaround reference.

BASE = os.path.join(os.path.dirname(__file__), "build_player_character_v56.py")
exec(compile(open(BASE, "r", encoding="utf-8").read(), BASE, "exec"), globals(), globals())


def remove_many(names):
    for name in names:
        obj = bpy.data.objects.get(name)
        if obj:
            bpy.data.objects.remove(obj, do_unlink=True)


def rounded_head(name, mat):
    # Youthful concept head: full upper cheeks, gentle taper, short rounded chin.
    rings = [
        (1.545, 0.070, 0.068, -0.004),
        (1.570, 0.120, 0.100, -0.010),
        (1.610, 0.162, 0.128, -0.014),
        (1.660, 0.192, 0.148, -0.016),
        (1.715, 0.207, 0.160, -0.015),
        (1.770, 0.210, 0.166, -0.010),
        (1.825, 0.202, 0.163, -0.002),
        (1.875, 0.184, 0.154,  0.006),
        (1.920, 0.153, 0.137,  0.013),
        (1.952, 0.105, 0.105,  0.017),
        (1.970, 0.055, 0.061,  0.020),
    ]
    sides = 48
    verts, faces = [], []
    for z, rx, ry, cy in rings:
        for i in range(sides):
            a = math.tau * i / sides
            sy = math.sin(a)
            # Slight face-plane bias keeps cheeks soft without an egg profile.
            y = cy + ry * sy
            if sy < -0.30:
                y += 0.008 * ((-sy - 0.30) / 0.70)
            verts.append((rx * math.cos(a), y, z))
    for r in range(len(rings)-1):
        a0, b0 = r*sides, (r+1)*sides
        for i in range(sides):
            j = (i+1) % sides
            faces.append((a0+i,a0+j,b0+j,b0+i))
    faces.append(tuple(reversed(range(sides))))
    top = (len(rings)-1)*sides
    faces.append(tuple(top+i for i in range(sides)))
    mesh = bpy.data.meshes.new(name+'Mesh')
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.parent = ROOT
    obj.data.materials.append(mat)
    for p in obj.data.polygons:
        p.use_smooth = True
    bevel = obj.modifiers.new('FaceSoftness','BEVEL')
    bevel.width = 0.006
    bevel.segments = 2
    bpy.context.view_layer.objects.active = obj
    try:
        bpy.ops.object.modifier_apply(modifier=bevel.name)
    except Exception:
        pass
    return obj


def blade_clump(name, sections, material, ring_sides=10):
    verts, faces = [], []
    for x,y,z,w,d in sections:
        for i in range(ring_sides):
            a = math.tau*i/ring_sides
            verts.append((x+math.cos(a)*w, y+math.sin(a)*d, z))
    for r in range(len(sections)-1):
        a0,b0=r*ring_sides,(r+1)*ring_sides
        for i in range(ring_sides):
            j=(i+1)%ring_sides
            faces.append((a0+i,a0+j,b0+j,b0+i))
    faces.append(tuple(reversed(range(ring_sides))))
    end=(len(sections)-1)*ring_sides
    faces.append(tuple(end+i for i in range(ring_sides)))
    mesh=bpy.data.meshes.new(name+'Mesh')
    mesh.from_pydata(verts,[],faces); mesh.update()
    obj=bpy.data.objects.new(name,mesh); bpy.context.collection.objects.link(obj)
    obj.parent=ROOT; obj.data.materials.append(material)
    for p in obj.data.polygons: p.use_smooth=True
    bevel=obj.modifiers.new('SculptedClump','BEVEL'); bevel.width=0.004; bevel.segments=2
    bpy.context.view_layer.objects.active=obj
    try: bpy.ops.object.modifier_apply(modifier=bevel.name)
    except Exception: pass
    return obj


def fuse_meshes(names, new_name, material, voxel=0.004):
    objs=[bpy.data.objects.get(n) for n in names]
    objs=[o for o in objs if o and o.type=='MESH']
    if not objs: return None
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs: o.select_set(True)
    bpy.context.view_layer.objects.active=objs[0]
    bpy.ops.object.join(); obj=objs[0]; obj.name=new_name
    obj.data.materials.clear(); obj.data.materials.append(material)
    for p in obj.data.polygons: p.use_smooth=True
    try:
        obj.data.remesh_voxel_size=voxel; obj.data.remesh_voxel_adaptivity=0.0
        bpy.context.view_layer.objects.active=obj; obj.select_set(True)
        bpy.ops.object.voxel_remesh()
        for p in obj.data.polygons: p.use_smooth=True
    except Exception as exc:
        print('V5.7 fuse fallback:',exc)
    return obj


# -----------------------------------------------------------------------------
# HEAD — reset cumulative V5 tweaks to one clean target silhouette.
# -----------------------------------------------------------------------------
remove_many(['HeadV5'])
rounded_head('HeadV57', SKIN)

# Features tuned to the new shorter/wider head.
for side in (-1,1):
    s=float(side)
    for prefix in ['EyeWhite','Iris','Pupil','EyeGlint']:
        obj=bpy.data.objects.get(f'{prefix}_{side}')
        if obj:
            obj.location.x = abs(obj.location.x)*s*0.97
            obj.location.z += 0.002
    eye=bpy.data.objects.get(f'EyeWhite_{side}')
    iris=bpy.data.objects.get(f'Iris_{side}')
    pupil=bpy.data.objects.get(f'Pupil_{side}')
    if eye:
        eye.scale.x *= 1.03; eye.scale.z *= 1.035
    if iris:
        iris.scale.x *= 1.08; iris.scale.z *= 1.08
    if pupil:
        pupil.scale.x *= 1.04; pupil.scale.z *= 1.04

# Smaller rounder ears integrated closer to the head.
for side in (-1,1):
    ear=bpy.data.objects.get(f'Ear_{side}')
    if ear:
        ear.scale *= 0.88
        ear.location.x *= 0.94
        ear.location.z += 0.006

# Curved dark eyebrows, tiny nose, soft smile.
for name in ['BrowL','BrowR']:
    obj=bpy.data.objects.get(name)
    if obj and hasattr(obj.data,'bevel_depth'):
        obj.data.bevel_depth *= 1.12
nose=bpy.data.objects.get('Nose')
if nose:
    nose.scale *= 0.82
    nose.location.z += 0.004
remove_many(['Smile'])
curve('Smile',[(-0.044,-0.164,1.640),(-0.022,-0.168,1.632),(0,-0.169,1.631),
               (0.023,-0.168,1.634),(0.046,-0.163,1.643)],MOUTH,0.0027)

# -----------------------------------------------------------------------------
# HAIR — strong diagonal sweep like concept, not evenly spaced vertical bangs.
# -----------------------------------------------------------------------------
remove_many([
    'V56HairCap','V56HairBack','V56BangOuterL','V56BangHero','V56BangCenter',
    'V56BangMidR','V56BangRight','V56SideL','V56SideR',
    'V56CrownL','V56CrownM','V56CrownR'
])
recolor(HAIR,(0.045,0.014,0.006)); recolor(HAIR_WARM,(0.085,0.026,0.010))
uv('V57HairCap',(0.0,0.050,1.865),(0.215,0.166,0.168),HAIR,52,30)
uv('V57HairBack',(0.0,0.125,1.805),(0.205,0.156,0.148),HAIR,46,26)

# Large leftward sweep mass — roots begin around center/right crown, tips fan left.
blade_clump('V57SweepBack',[
    (0.045,-0.020,2.035,0.070,0.031),
    (-0.020,-0.060,2.020,0.076,0.032),
    (-0.090,-0.100,1.990,0.072,0.030),
    (-0.155,-0.130,1.945,0.052,0.025),
    (-0.205,-0.148,1.905,0.012,0.009),
],HAIR)
blade_clump('V57SweepHero',[
    (0.075,-0.030,2.025,0.066,0.030),
    (0.030,-0.080,1.995,0.067,0.030),
    (-0.020,-0.120,1.950,0.058,0.026),
    (-0.055,-0.150,1.895,0.040,0.020),
    (-0.070,-0.168,1.840,0.010,0.008),
],HAIR_WARM)
blade_clump('V57CenterBang',[
    (0.105,-0.025,2.010,0.052,0.027),
    (0.082,-0.080,1.980,0.051,0.025),
    (0.052,-0.125,1.935,0.043,0.021),
    (0.030,-0.155,1.885,0.029,0.016),
    (0.020,-0.171,1.835,0.008,0.007),
],HAIR)
# Smaller right fringe/temple balances the sweep.
blade_clump('V57RightBang',[
    (0.145,-0.010,1.990,0.044,0.024),
    (0.172,-0.052,1.955,0.039,0.021),
    (0.190,-0.092,1.915,0.030,0.018),
    (0.198,-0.120,1.870,0.018,0.012),
    (0.194,-0.135,1.835,0.006,0.006),
],HAIR_WARM)
blade_clump('V57LeftTemple',[
    (-0.185,-0.020,1.930,0.043,0.025),
    (-0.205,-0.060,1.885,0.036,0.021),
    (-0.215,-0.095,1.835,0.027,0.017),
    (-0.208,-0.120,1.785,0.010,0.008),
],HAIR)
blade_clump('V57RightTemple',[
    (0.185,0.000,1.930,0.038,0.023),
    (0.207,-0.035,1.890,0.032,0.019),
    (0.215,-0.070,1.845,0.022,0.015),
    (0.210,-0.092,1.808,0.008,0.007),
],HAIR)

# Few small crown accents, swept backward/right rather than standing up.
blade_clump('V57CrownA',[
    (-0.060,0.015,2.005,0.040,0.020),
    (-0.035,0.008,2.040,0.030,0.016),
    (-0.005,0.002,2.060,0.013,0.009),
    (0.020,-0.002,2.058,0.004,0.004),
],HAIR_WARM)
blade_clump('V57CrownB',[
    (0.025,0.020,2.008,0.037,0.019),
    (0.060,0.012,2.040,0.028,0.015),
    (0.095,0.004,2.052,0.012,0.008),
    (0.120,0.000,2.045,0.004,0.004),
],HAIR)
blade_clump('V57CrownC',[
    (0.095,0.018,1.998,0.033,0.018),
    (0.130,0.010,2.025,0.025,0.014),
    (0.160,0.004,2.032,0.010,0.007),
    (0.180,0.000,2.022,0.004,0.004),
],HAIR_WARM)

# -----------------------------------------------------------------------------
# HANDS — soft closed neutral fists, matching the front turnaround better.
# -----------------------------------------------------------------------------
for side in (-1,1):
    s=float(side)
    remove_many([f'HandV55_{side}'])
    cx,cy,cz=0.220*s,-0.104,0.805
    uv(f'V57Palm_{side}',(cx,cy,cz),(0.041,0.031,0.052),SKIN,28,18)
    parts=[f'V57Palm_{side}']
    # Four knuckle lobes sit across the front/lower palm, deeply overlapping.
    for idx,(off,zoff) in enumerate([(-0.026,-0.033),(-0.009,-0.040),(0.010,-0.040),(0.027,-0.032)]):
        nm=f'V57Knuckle_{side}_{idx}'
        uv(nm,(cx+off*s,cy-0.013,cz+zoff),(0.014,0.013,0.018),SKIN,18,12)
        parts.append(nm)
    th=f'V57Thumb_{side}'
    uv(th,(cx+0.035*s,cy-0.018,cz+0.002),(0.018,0.015,0.030),SKIN,20,12,
       rot=(0,math.radians(8*s),math.radians(28*s)))
    parts.append(th)
    hand=fuse_meshes(parts,f'HandV57_{side}',SKIN,0.0038)
    if hand:
        hand.rotation_euler.z=math.radians(-4*s)
        hand.scale.x*=1.02

# Keep slim trousers and refine taper slightly toward the ankle.
for side in (-1,1):
    tr=bpy.data.objects.get(f'Trouser_{side}')
    if tr:
        tr.scale.x*=0.97
        tr.scale.y*=0.985

# Export candidate only.
bpy.ops.object.select_all(action='DESELECT')
ROOT.select_set(True)
for obj in ROOT.children_recursive: obj.select_set(True)
bpy.context.view_layer.objects.active=ROOT
bpy.ops.export_scene.gltf(filepath=OUT_PATH,export_format='GLB',use_selection=True,export_apply=True,export_yup=True)
print(f'Exported Lembah Sari Character V5.7 concept-turnaround candidate to {OUT_PATH}')
