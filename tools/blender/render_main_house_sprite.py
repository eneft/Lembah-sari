import bpy
import math
import os
from mathutils import Vector

IN_PATH = os.path.abspath(os.environ.get("LEMBAH_HOUSE_IN", "assets/models/house_main_01.glb"))
OUT_PATH = os.path.abspath(os.environ.get("LEMBAH_HOUSE_SPRITE_OUT", "assets/2p5d/house_main_render.png"))
os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)

# Fresh scene.
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)

# Import the authored house. This is the only source for the sprite so the
# in-game artwork stays honest to the actual hero asset rather than an AI
# over-paint or a hand-drawn placeholder.
bpy.ops.import_scene.gltf(filepath=IN_PATH)

# Keep the house centered and slightly lifted above the sprite shadow.
for obj in bpy.context.scene.objects:
    if obj.type == "MESH":
        obj.select_set(True)

# Add a soft painted contact shadow that becomes part of the transparent sprite.
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

shadow_mat = make_mat("Soft painted contact shadow", (0.08, 0.055, 0.035), 1.0, 0.18)
bpy.ops.mesh.primitive_uv_sphere_add(segments=64, ring_count=16, location=(0.0, 0.0, 0.12))
shadow = bpy.context.object
shadow.name = "SpriteContactShadow"
shadow.scale = (4.45, 2.25, 0.055)
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
shadow.data.materials.append(shadow_mat)

# Camera: fixed 3/4 orthographic angle matching the intended game view.
def look_at(obj, target):
    direction = Vector(target) - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()

bpy.ops.object.camera_add(location=(10.5, -14.8, 9.3))
camera = bpy.context.object
camera.name = "LembahSari2p5DCamera"
camera.data.type = "ORTHO"
camera.data.ortho_scale = 10.7
camera.data.lens = 50
look_at(camera, (0.0, -0.25, 2.0))
bpy.context.scene.camera = camera

# Warm morning key light with broad soft fill. The lighting is deliberately
# illustrative: enough volume to read the house, but not photoreal PBR drama.
bpy.ops.object.light_add(type="AREA", location=(-4.5, -7.0, 10.5))
key = bpy.context.object
key.name = "WarmMorningKey"
key.data.energy = 920.0
key.data.shape = "DISK"
key.data.size = 8.5
key.data.color = (1.0, 0.78, 0.57)
look_at(key, (0.0, 0.0, 1.8))

bpy.ops.object.light_add(type="AREA", location=(7.5, -2.5, 7.0))
fill = bpy.context.object
fill.name = "SoftSkyFill"
fill.data.energy = 470.0
fill.data.size = 10.0
fill.data.color = (0.70, 0.84, 1.0)
look_at(fill, (0.0, 0.0, 1.6))

bpy.ops.object.light_add(type="AREA", location=(0.0, 6.5, 5.5))
rim = bpy.context.object
rim.name = "WarmRim"
rim.data.energy = 350.0
rim.data.size = 7.0
rim.data.color = (1.0, 0.64, 0.42)
look_at(rim, (0.0, 0.0, 2.1))

# World light is present for shading only; the film stays transparent.
world = bpy.context.scene.world or bpy.data.worlds.new("World")
bpy.context.scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.18, 0.25, 0.20, 1.0)
    bg.inputs["Strength"].default_value = 0.42

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
scene.render.film_transparent = True
scene.render.filepath = OUT_PATH
scene.render.image_settings.color_depth = "8"

# Clean, game-friendly color response.
scene.view_settings.exposure = 0.25
scene.view_settings.gamma = 1.0
try:
    scene.view_settings.view_transform = "Standard"
except Exception:
    pass
try:
    scene.view_settings.look = "Medium High Contrast"
except Exception:
    pass

# Transparent sprite should not carry a horizon, only the hero house and its
# subtle painted contact shadow.
bpy.ops.render.render(write_still=True)
print(f"Rendered 2.5D house sprite: {OUT_PATH}")
