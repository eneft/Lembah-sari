import bpy
import os
from mathutils import Vector

OUT_PATH = os.path.abspath(os.environ.get("LEMBAH_HOUSE_SPRITE_OUT", "assets/2p5d/house_main_render.png"))
os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)

# Build the authored house directly inside this Blender process. The sprite is
# therefore a real render of the game asset, not an AI over-paint.
script_dir = os.path.dirname(os.path.abspath(__file__))
build_script = os.path.join(script_dir, "build_main_house_concept.py")
with open(build_script, "r", encoding="utf-8") as handle:
    build_source = handle.read()
export_marker = "bpy.ops.object.select_all(action='SELECT')\nbpy.ops.export_scene.gltf("
if export_marker not in build_source:
    raise RuntimeError("Could not locate optional GLB export block in house builder")
build_only_source = build_source.split(export_marker, 1)[0]
exec(compile(build_only_source, build_script, "exec"), {"__name__": "__main__", "__file__": build_script})


def set_material_color(material_name, color, roughness=0.92):
    material = bpy.data.materials.get(material_name)
    if not material:
        return
    material.diffuse_color = (*color, 1.0)
    if material.use_nodes:
        bsdf = material.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs["Base Color"].default_value = (*color, 1.0)
            bsdf.inputs["Roughness"].default_value = roughness


# The builder is intentionally conservative for 3D. For the fixed 2.5D camera
# we can push the palette and silhouette harder so the result reads like an
# illustration at mobile size.
set_material_color("Warm timber", (0.50, 0.25, 0.085))
set_material_color("Honey timber", (0.69, 0.39, 0.145))
set_material_color("Deep teak", (0.17, 0.068, 0.024))
set_material_color("Bamboo", (0.65, 0.49, 0.19))
set_material_color("Terracotta", (0.54, 0.105, 0.032), 0.88)
set_material_color("Terracotta highlight", (0.73, 0.22, 0.065), 0.86)
set_material_color("Terracotta shade", (0.31, 0.055, 0.018), 0.91)
set_material_color("Muted teal glass", (0.055, 0.39, 0.42), 0.64)
set_material_color("Foundation", (0.38, 0.37, 0.32), 0.98)
set_material_color("Clay pot", (0.62, 0.20, 0.068), 0.95)
set_material_color("Porch green", (0.22, 0.47, 0.18), 0.94)
set_material_color("Faded coral", (0.71, 0.30, 0.20), 0.97)

# Reduce the giant roof-plane read from the previous render. The house is still
# recognisably the same asset, but its facade/porch now carries more of the
# image like a polished farming-game building.
for obj in bpy.context.scene.objects:
    if obj.name.startswith("RoofFront") or obj.name.startswith("RoofBack"):
        obj.scale.y *= 0.76
    elif obj.name.startswith("RoofTileRib"):
        obj.scale.y *= 0.76
    elif obj.name.startswith("PorchRoof"):
        obj.scale.y *= 0.86
    elif obj.name.startswith("PorchRoofRib"):
        obj.scale.y *= 0.86

# Pull fascia/eave inward to match the shortened roof plane.
for obj in bpy.context.scene.objects:
    if obj.name.startswith("FrontFascia") or obj.name.startswith("RafterTip"):
        obj.location.y += 0.33

# Add a few broad, graphic leaves to replace the "green ball" feeling around
# the veranda. These are part of the house asset rather than an environment.
def make_mat(name, color, roughness=0.9, alpha=1.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (*color, 1.0)
        bsdf.inputs["Roughness"].default_value = roughness
        bsdf.inputs["Alpha"].default_value = alpha
    mat.diffuse_color = (*color, alpha)
    if alpha < 1.0:
        try:
            mat.surface_render_method = "DITHERED"
        except Exception:
            try:
                mat.blend_method = "BLEND"
            except Exception:
                pass
    return mat

LEAF_LIGHT = make_mat("Illustrated leaf light", (0.25, 0.55, 0.22), 0.96)
LEAF_DARK = make_mat("Illustrated leaf dark", (0.11, 0.34, 0.13), 0.97)

for pot_x, pot_y, side in [(-3.22, -2.83, -1.0), (3.12, -2.75, 1.0)]:
    for idx, angle in enumerate((-34.0, -12.0, 14.0, 36.0)):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=20, ring_count=10, location=(pot_x + side * (idx - 1.5) * 0.11, pot_y - 0.03, 1.18 + abs(idx - 1.5) * 0.05))
        leaf = bpy.context.object
        leaf.name = "PorchLeaf"
        leaf.scale = (0.13, 0.055, 0.43)
        leaf.rotation_euler[1] = 0.28 * side
        leaf.rotation_euler[2] = angle * 0.017453292519943295
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        leaf.data.materials.append(LEAF_LIGHT if idx % 2 == 0 else LEAF_DARK)

# Contact shadow baked into transparent sprite.
shadow_mat = make_mat("Soft painted contact shadow", (0.075, 0.050, 0.030), 1.0, 0.13)
bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=16, location=(0.0, 0.0, 0.08))
shadow = bpy.context.object
shadow.name = "SpriteContactShadow"
shadow.scale = (4.25, 2.05, 0.045)
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
shadow.data.materials.append(shadow_mat)


def look_at(obj, target):
    direction = Vector(target) - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()

# Lower, wider 3/4 beauty angle: enough roof to communicate the terracotta
# silhouette, but much more facade/porch than the previous top-heavy pass.
bpy.ops.object.camera_add(location=(11.8, -18.4, 7.9))
camera = bpy.context.object
camera.name = "LembahSari2p5DCamera"
camera.data.type = "ORTHO"
camera.data.ortho_scale = 10.2
look_at(camera, (0.0, -0.55, 2.05))
bpy.context.scene.camera = camera

# Soft illustrative morning light.
bpy.ops.object.light_add(type="AREA", location=(-5.0, -8.0, 10.0))
key = bpy.context.object
key.name = "WarmMorningKey"
key.data.energy = 1080.0
key.data.shape = "DISK"
key.data.size = 9.5
key.data.color = (1.0, 0.79, 0.59)
look_at(key, (0.0, -0.3, 1.9))

bpy.ops.object.light_add(type="AREA", location=(8.0, -1.5, 7.5))
fill = bpy.context.object
fill.name = "SoftSkyFill"
fill.data.energy = 680.0
fill.data.size = 11.0
fill.data.color = (0.74, 0.88, 1.0)
look_at(fill, (0.0, 0.0, 1.7))

bpy.ops.object.light_add(type="AREA", location=(0.0, 7.5, 6.5))
rim = bpy.context.object
rim.name = "WarmRim"
rim.data.energy = 410.0
rim.data.size = 8.0
rim.data.color = (1.0, 0.67, 0.45)
look_at(rim, (0.0, 0.0, 2.2))

world = bpy.context.scene.world or bpy.data.worlds.new("World")
bpy.context.scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.30, 0.40, 0.33, 1.0)
    bg.inputs["Strength"].default_value = 0.58

scene = bpy.context.scene
try:
    scene.render.engine = "BLENDER_EEVEE_NEXT"
except Exception:
    scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 1024
scene.render.resolution_y = 1024
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.image_settings.color_mode = "RGBA"
scene.render.image_settings.color_depth = "8"
scene.render.film_transparent = True
scene.render.filepath = OUT_PATH
scene.view_settings.exposure = 0.58
scene.view_settings.gamma = 1.0
try:
    scene.view_settings.view_transform = "Standard"
except Exception:
    pass
try:
    scene.view_settings.look = "Medium High Contrast"
except Exception:
    pass

bpy.ops.render.render(write_still=True)
print(f"Rendered 2.5D house sprite: {OUT_PATH}")
