import bpy
import math
import os
from mathutils import Vector, Matrix

OUT_PATH = os.path.abspath(os.environ.get("LEMBAH_HERO_OUT", "assets/models/hero_scene_01.glb"))
HOUSE_PATH = os.path.abspath(os.environ.get("LEMBAH_HOUSE_IN", "assets/models/house_main_01.glb"))
ASSET_DIR = os.path.abspath(os.environ.get("LEMBAH_CC0_DIR", "/tmp/quaternius"))
os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)


def mat(name, color, roughness=0.85, metallic=0.0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1.0)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    return m


MAT_GRASS = mat("Hero Grass", (0.31, 0.50, 0.22), 0.92)
MAT_GRASS_2 = mat("Hero Grass Light", (0.42, 0.62, 0.28), 0.90)
MAT_SOIL = mat("Hero Soil", (0.37, 0.23, 0.12), 0.94)
MAT_SOIL_LIGHT = mat("Hero Soil Light", (0.53, 0.35, 0.19), 0.93)
MAT_WATER = mat("Hero Water", (0.17, 0.50, 0.58), 0.24)
MAT_WATER_SHALLOW = mat("Paddy Water", (0.36, 0.62, 0.55), 0.32)
MAT_WOOD = mat("Bridge Honey Wood", (0.42, 0.23, 0.11), 0.82)
MAT_WOOD_DARK = mat("Bridge Dark Wood", (0.20, 0.10, 0.05), 0.86)
MAT_BAMBOO = mat("Fence Bamboo", (0.52, 0.46, 0.20), 0.88)
MAT_STONE = mat("River Stone", (0.41, 0.42, 0.37), 0.92)
MAT_STONE_LIGHT = mat("Path Stone", (0.62, 0.60, 0.49), 0.91)
MAT_HILL = mat("Distant Hill", (0.19, 0.36, 0.21), 0.98)
MAT_HILL_LIGHT = mat("Distant Hill Light", (0.27, 0.45, 0.25), 0.98)


def apply_mat(obj, material):
    if obj.type == 'MESH':
        obj.data.materials.clear()
        obj.data.materials.append(material)


def box(name, loc, dims, material, rot=(0, 0, 0), bevel=0.08):
    bpy.ops.mesh.primitive_cube_add(location=loc, rotation=rot)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dims
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    apply_mat(obj, material)
    if bevel > 0:
        mod = obj.modifiers.new("Soft edges", "BEVEL")
        mod.width = bevel
        mod.segments = 2
        mod.limit_method = 'ANGLE'
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=mod.name)
    return obj


def cylinder(name, loc, radius, depth, material, rot=(0, 0, 0), vertices=10, bevel=0.025):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=loc, rotation=rot)
    obj = bpy.context.object
    obj.name = name
    apply_mat(obj, material)
    if bevel > 0:
        mod = obj.modifiers.new("Soft edges", "BEVEL")
        mod.width = bevel
        mod.segments = 2
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=mod.name)
    return obj


def ico(name, loc, scale, material, subdivisions=2):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=subdivisions, radius=1.0, location=loc)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    apply_mat(obj, material)
    return obj


def ribbon(name, points, widths, material, z=0.03, bevel=0.04):
    pts = [Vector((p[0], p[1], z if len(p) < 3 else p[2])) for p in points]
    if not isinstance(widths, (list, tuple)):
        widths = [float(widths)] * len(pts)
    verts = []
    for i, p in enumerate(pts):
        if i == 0:
            tangent = pts[1] - pts[0]
        elif i == len(pts) - 1:
            tangent = pts[-1] - pts[-2]
        else:
            tangent = pts[i + 1] - pts[i - 1]
        tangent.z = 0
        tangent.normalize()
        side = Vector((-tangent.y, tangent.x, 0.0)) * (float(widths[i]) * 0.5)
        verts.append(tuple(p - side))
        verts.append(tuple(p + side))
    faces = []
    for i in range(len(pts) - 1):
        a = i * 2
        faces.append((a, a + 1, a + 3, a + 2))
    mesh = bpy.data.meshes.new(name + "Mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    apply_mat(obj, material)
    solid = obj.modifiers.new("Ribbon thickness", "SOLIDIFY")
    solid.thickness = 0.05
    bev = obj.modifiers.new("Ribbon soft edge", "BEVEL")
    bev.width = bevel
    bev.segments = 2
    return obj


def build_ground():
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=26, y_subdivisions=22, size=2.0, location=(0, 0, -0.22))
    ground = bpy.context.object
    ground.name = "SculptedVillageGround"
    ground.scale = (9.7, 7.8, 1.0)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    for v in ground.data.vertices:
        x, y = v.co.x, v.co.y
        v.co.z += math.sin(x * 0.28) * 0.08 + math.cos(y * 0.33) * 0.07
        v.co.z += max(0.0, abs(x) - 7.0) * 0.05
        v.co.z += max(0.0, y - 5.0) * 0.06
    apply_mat(ground, MAT_GRASS)
    solid = ground.modifiers.new("Ground thickness", "SOLIDIFY")
    solid.thickness = 0.34
    bev = ground.modifiers.new("Ground edge softening", "BEVEL")
    bev.width = 0.14
    bev.segments = 2

    ico("BackHillA", (-7.4, 7.4, 1.5), (5.1, 2.7, 2.4), MAT_HILL, 2)
    ico("BackHillB", (1.0, 8.5, 1.7), (6.0, 3.0, 2.6), MAT_HILL_LIGHT, 2)
    ico("BackHillC", (8.4, 7.7, 1.4), (4.9, 2.4, 2.2), MAT_HILL, 2)


def import_house():
    if not os.path.exists(HOUSE_PATH):
        raise RuntimeError(f"Missing house GLB: {HOUSE_PATH}")
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=HOUSE_PATH)
    imported = [o for o in bpy.data.objects if o not in before]
    root = bpy.data.objects.new("HeroHouseRoot", None)
    bpy.context.collection.objects.link(root)
    tops = [o for o in imported if o.parent is None]
    for o in tops:
        o.parent = root
    root.location = (-3.0, 2.0, 0.0)
    return root


def import_obj_template(asset_name):
    path = os.path.join(ASSET_DIR, asset_name + ".obj")
    if not os.path.exists(path):
        raise RuntimeError(f"Missing CC0 source asset: {path}")
    bpy.ops.object.select_all(action='DESELECT')
    before = set(bpy.data.objects)
    try:
        bpy.ops.wm.obj_import(filepath=path)
    except Exception:
        bpy.ops.import_scene.obj(filepath=path, axis_forward='-Z', axis_up='Y')
    imported = [o for o in bpy.data.objects if o not in before and o.type == 'MESH']
    if not imported:
        raise RuntimeError(f"No meshes imported from {path}")
    bpy.ops.object.select_all(action='DESELECT')
    for o in imported:
        o.select_set(True)
    bpy.context.view_layer.objects.active = imported[0]
    bpy.ops.object.join()
    obj = bpy.context.object
    obj.name = "Template_" + asset_name
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    corners = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
    min_x = min(c.x for c in corners); max_x = max(c.x for c in corners)
    min_y = min(c.y for c in corners); max_y = max(c.y for c in corners)
    min_z = min(c.z for c in corners)
    offset = Vector((-(min_x + max_x) * 0.5, -(min_y + max_y) * 0.5, -min_z))
    obj.data.transform(Matrix.Translation(offset))
    obj.location = (0, 0, -100)
    obj.hide_render = True
    obj.hide_viewport = True
    obj.select_set(False)
    return obj


def place(template, name, loc, scale=1.0, rot_z=0.0):
    obj = template.copy()
    obj.data = template.data
    obj.name = name
    obj.location = loc
    if isinstance(scale, (tuple, list)):
        obj.scale = scale
    else:
        obj.scale = (scale, scale, scale)
    obj.rotation_euler[2] = math.radians(rot_z)
    obj.hide_render = False
    obj.hide_viewport = False
    bpy.context.collection.objects.link(obj)
    return obj


def build_path_stream_bridge(rock_t, grass_t, lilypad_t):
    path_pts = [(-3.0, -0.6), (-2.7, -1.8), (-2.1, -3.0), (-1.4, -4.2), (-0.8, -5.4), (-0.15, -6.5)]
    ribbon("VillageDirtPath", path_pts, [1.1, 1.25, 1.35, 1.45, 1.35, 1.2], MAT_SOIL_LIGHT, 0.03, 0.10)

    stream_pts = [(-9.4, -5.2), (-6.0, -5.5), (-2.5, -5.3), (1.0, -5.7), (4.5, -5.35), (9.5, -5.8)]
    ribbon("StreamBank", stream_pts, [2.65, 2.8, 2.7, 2.9, 2.65, 2.55], MAT_SOIL, -0.06, 0.12)
    ribbon("StreamWater", stream_pts, [1.72, 1.86, 1.80, 1.96, 1.75, 1.68], MAT_WATER, 0.00, 0.09)

    # timber bridge centered on the path crossing the stream
    center_x = -0.9
    for i in range(9):
        y = -6.32 + i * 0.23
        arch = math.sin(i / 8.0 * math.pi) * 0.14
        box(f"BridgePlank_{i}", (center_x, y, 0.30 + arch), (2.05, 0.27, 0.14), MAT_WOOD, bevel=0.045)
    for x in (center_x - 0.92, center_x + 0.92):
        for y in (-6.25, -5.35, -4.45):
            cylinder("BridgePost", (x, y, 0.82), 0.075, 1.28, MAT_WOOD_DARK, vertices=10, bevel=0.02)
        # rails as slightly tilted segments
        box("BridgeRailA", (x, -5.82, 1.22), (0.10, 0.98, 0.10), MAT_WOOD_DARK, rot=(math.radians(-11), 0, 0), bevel=0.025)
        box("BridgeRailB", (x, -4.92, 1.22), (0.10, 0.98, 0.10), MAT_WOOD_DARK, rot=(math.radians(11), 0, 0), bevel=0.025)

    rock_spots = [(-7.7,-4.7,0.08,0.72,12),(-5.4,-6.2,0.05,0.55,-18),(2.6,-4.8,0.06,0.64,28),(5.5,-6.1,0.04,0.58,-35),(7.5,-5.1,0.05,0.48,5)]
    for idx,(x,y,z,s,r) in enumerate(rock_spots):
        place(rock_t, f"RiverRock_{idx}", (x,y,z), s, r)
    for idx,(x,y) in enumerate([(-8.4,-4.3),(-6.5,-6.5),(-4.1,-4.2),(1.8,-6.6),(3.9,-4.2),(6.7,-6.4),(8.4,-4.5)]):
        place(grass_t, f"BankGrass_{idx}", (x,y,0.05), 0.55 + (idx%3)*0.08, idx*29)
    for idx,(x,y,s) in enumerate([(-5.8,-5.45,0.42),(-3.8,-5.15,0.34),(2.4,-5.55,0.38),(4.4,-5.45,0.30)]):
        place(lilypad_t, f"Lily_{idx}", (x,y,0.08), s, idx*37)


def build_garden(plant_t, flower_t, grass_t):
    beds = [((1.0, 0.5, 0.05), (3.4, 1.35, 0.18), -8), ((1.6, 2.0, 0.05), (3.0, 1.18, 0.18), 7)]
    for idx,(loc,dims,rot) in enumerate(beds):
        box(f"KitchenGardenBed_{idx}", loc, dims, MAT_SOIL, rot=(0,0,math.radians(rot)), bevel=0.16)
    plants = [
        (0.0,0.1,0.42,0),(0.7,0.0,0.38,20),(1.4,0.1,0.42,-12),(2.1,0.0,0.40,14),
        (0.5,1.7,0.38,-18),(1.2,1.8,0.43,22),(1.9,1.7,0.40,-8),(2.55,1.8,0.36,16)
    ]
    for idx,(x,y,s,r) in enumerate(plants):
        place(plant_t, f"GardenPlant_{idx}", (x,y,0.18), s, r)

    # loose bamboo fence around garden
    fence_pts = [(-0.8,-0.5),(-0.8,0.7),(-0.7,1.9),(-0.6,3.1),(0.6,3.5),(1.9,3.6),(3.2,3.4)]
    for idx,(x,y) in enumerate(fence_pts):
        h = 0.9 + (idx%3)*0.08
        cylinder("BambooFencePost", (x,y,h*0.5), 0.05, h, MAT_BAMBOO, vertices=9, bevel=0.018)
    for idx in range(len(fence_pts)-1):
        x0,y0=fence_pts[idx]; x1,y1=fence_pts[idx+1]
        dx=x1-x0; dy=y1-y0; length=math.sqrt(dx*dx+dy*dy); angle=math.atan2(dy,dx)
        mid=((x0+x1)*0.5,(y0+y1)*0.5,0.60)
        box("BambooFenceRail", mid, (length,0.075,0.075), MAT_BAMBOO, rot=(0,0,angle), bevel=0.02)
    for idx,(x,y) in enumerate([(-0.3,-0.8),(0.35,-0.9),(2.9,0.25),(3.25,1.0),(2.8,2.8)]):
        place(flower_t, f"GardenFlower_{idx}", (x,y,0.05), 0.48 + (idx%2)*0.08, idx*41)
    for idx,(x,y) in enumerate([(-1.25,0.0),(-1.2,2.2),(3.7,0.8),(3.8,2.5)]):
        place(grass_t, f"GardenGrass_{idx}", (x,y,0.04), 0.52, idx*31)


def build_rice_fields(wheat_t, grass_t):
    fields = [((5.0,1.2,0.01),(4.0,3.0,0.12),-4), ((7.2,3.8,0.10),(3.6,2.55,0.12),6)]
    for idx,(loc,dims,rot) in enumerate(fields):
        box(f"PaddyWater_{idx}", loc, dims, MAT_WATER_SHALLOW, rot=(0,0,math.radians(rot)), bevel=0.22)
        # earthen bunds around paddy
        x,y,z=loc; w,h,_=dims
        box("PaddyBund", (x-w*0.5,y,z+0.09),(0.24,h+0.24,0.24),MAT_SOIL_LIGHT,rot=(0,0,math.radians(rot)),bevel=0.08)
        box("PaddyBund", (x+w*0.5,y,z+0.09),(0.24,h+0.24,0.24),MAT_SOIL_LIGHT,rot=(0,0,math.radians(rot)),bevel=0.08)
        box("PaddyBund", (x,y-h*0.5,z+0.09),(w+0.24,0.24,0.24),MAT_SOIL_LIGHT,rot=(0,0,math.radians(rot)),bevel=0.08)
        box("PaddyBund", (x,y+h*0.5,z+0.09),(w+0.24,0.24,0.24),MAT_SOIL_LIGHT,rot=(0,0,math.radians(rot)),bevel=0.08)

    rice_spots=[]
    for row in range(4):
        for col in range(5):
            rice_spots.append((3.45+col*0.72,0.25+row*0.72,0.26, (row*17+col*11)%45))
    for row in range(3):
        for col in range(5):
            rice_spots.append((5.95+col*0.58,3.05+row*0.66,0.34, (row*13+col*19)%50))
    for idx,(x,y,s,r) in enumerate(rice_spots):
        place(wheat_t, f"RiceClump_{idx}", (x,y,0.13), s, r)
    for idx,(x,y) in enumerate([(3.0,-0.2),(7.6,0.0),(8.8,2.2),(5.6,5.0),(8.6,5.2)]):
        place(grass_t, f"PaddyGrass_{idx}", (x,y,0.04), 0.48, idx*37)


def build_foliage(tree_t, palm_t, bush_t, grass_t, flower_t, rock_t):
    trees=[(-8.3,3.6,1.25,-16),(-7.0,6.0,0.95,22),(8.7,5.9,1.05,-28),(9.0,-0.3,0.88,18),(-8.8,-2.8,0.82,32)]
    for idx,(x,y,s,r) in enumerate(trees):
        place(tree_t,f"HeroTree_{idx}",(x,y,0.0),s,r)
    palms=[(-6.0,4.8,0.95,-20),(7.8,6.2,0.85,34),(8.4,-2.8,0.72,-12)]
    for idx,(x,y,s,r) in enumerate(palms):
        place(palm_t,f"HeroPalm_{idx}",(x,y,0.0),s,r)
    bushes=[(-5.9,0.5,0.7,10),(-5.3,-0.8,0.62,25),(-4.8,4.8,0.62,-15),(4.2,-1.4,0.58,18),(7.2,-2.0,0.66,-22),(8.0,4.8,0.72,5)]
    for idx,(x,y,s,r) in enumerate(bushes):
        place(bush_t,f"HeroBush_{idx}",(x,y,0.0),s,r)
    grass_spots=[(-7.7,0.0),(-6.8,1.5),(-5.5,-2.5),(-4.2,-3.5),(-2.8,4.5),(0.0,4.8),(2.3,4.9),(4.1,5.2),(6.6,-3.2),(8.4,1.6),(7.3,5.2)]
    for idx,(x,y) in enumerate(grass_spots):
        place(grass_t,f"HeroGrass_{idx}",(x,y,0.02),0.55+(idx%3)*0.08,idx*23)
    flower_spots=[(-4.7,-1.8),(-4.0,-2.2),(-2.5,-1.2),(0.0,-2.0),(2.9,-1.5),(4.2,-2.0),(6.5,5.0)]
    for idx,(x,y) in enumerate(flower_spots):
        place(flower_t,f"WildFlowers_{idx}",(x,y,0.03),0.52+(idx%2)*0.06,idx*29)
    rock_spots=[(-5.2,-4.2,0.52,12),(-3.8,-6.3,0.62,-25),(2.1,-6.4,0.48,33),(7.8,-4.4,0.64,-12),(8.4,1.0,0.55,26)]
    for idx,(x,y,s,r) in enumerate(rock_spots):
        place(rock_t,f"HeroRock_{idx}",(x,y,0.02),s,r)


def main():
    build_ground()
    import_house()

    tree_t = import_obj_template("CommonTree_4")
    palm_t = import_obj_template("PalmTree_2")
    bush_t = import_obj_template("Bush_2")
    grass_t = import_obj_template("Grass_Short")
    flower_t = import_obj_template("Flowers")
    rock_t = import_obj_template("Rock_Moss_3")
    wheat_t = import_obj_template("Wheat")
    lilypad_t = import_obj_template("Lilypad")
    plant_t = import_obj_template("Plant_3")

    build_path_stream_bridge(rock_t, grass_t, lilypad_t)
    build_garden(plant_t, flower_t, grass_t)
    build_rice_fields(wheat_t, grass_t)
    build_foliage(tree_t, palm_t, bush_t, grass_t, flower_t, rock_t)

    # Export only visible scene objects, excluding hidden source templates.
    bpy.ops.object.select_all(action='DESELECT')
    for obj in bpy.context.scene.objects:
        if not obj.hide_render and obj.location.z > -50:
            obj.select_set(True)
    bpy.ops.export_scene.gltf(
        filepath=OUT_PATH,
        export_format='GLB',
        use_selection=True,
        export_apply=True,
        export_yup=True,
    )
    print(f"Exported Lembah Sari hero scene to {OUT_PATH}")


if __name__ == "__main__":
    main()
