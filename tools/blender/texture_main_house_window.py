import math
import os
import struct
import zlib

import bpy

IN_PATH = os.path.abspath(os.environ.get("LEMBAH_HOUSE_IN", "assets/models/house_main_01.glb"))
OUT_PATH = os.path.abspath(os.environ.get("LEMBAH_HOUSE_OUT", IN_PATH))
os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)

if not os.path.exists(IN_PATH):
    raise RuntimeError("Missing house GLB for window-glass pass: %s" % IN_PATH)

bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=IN_PATH)


def clamp(value, lo=0.0, hi=1.0):
    return max(lo, min(hi, value))


def mix(a, b, t):
    return a + (b - a) * t


def linear_to_srgb(value):
    value = clamp(value)
    if value <= 0.0031308:
        return value * 12.92
    return 1.055 * (value ** (1.0 / 2.4)) - 0.055


def png_chunk(kind, payload):
    return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF)


def write_rgb_png(path, width, height, rows):
    raw = bytearray()
    for row in rows:
        raw.append(0)
        raw.extend(row)
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    data = (
        b"\x89PNG\r\n\x1a\n"
        + png_chunk(b"IHDR", ihdr)
        + png_chunk(b"IDAT", zlib.compress(bytes(raw), 9))
        + png_chunk(b"IEND", b"")
    )
    with open(path, "wb") as handle:
        handle.write(data)


def build_window_image(name, size=256):
    """Bake stylized village glass that remains readable at gameplay scale.

    The pane stays opaque for predictable GLB/Godot rendering. The texture gives
    it cool depth, broad sky variation, subtle age streaking, and darker edges.
    Explicit reflection slashes are added as tiny front-surface details later in
    this pass because the texture-only version still read as a flat cyan card at
    the fixed hero camera distance.
    """
    tau = math.pi * 2.0
    deep = (0.025, 0.115, 0.150)
    mid = (0.065, 0.275, 0.325)
    sky = (0.285, 0.585, 0.630)
    dust = (0.245, 0.300, 0.245)
    rows = []

    for py in range(size):
        v = py / float(size - 1)
        row = bytearray()
        for px in range(size):
            u = px / float(size - 1)

            vertical = clamp(0.16 + (1.0 - v) * 0.50)
            broad = (
                math.sin((u * 0.72 + v * 0.48 + 0.11) * tau) * 0.080
                + math.sin((u * 0.31 - v * 0.83 + 0.47) * tau) * 0.035
            )
            t = clamp(vertical + broad)
            rgb = tuple(mix(deep[c], mid[c], t) for c in range(3))

            # Very broad reflected-sky lift. It is intentionally not a narrow
            # stripe; the geometric reflection accents below supply the crisp cue.
            axis = u * 0.78 + (1.0 - v) * 0.62
            reflected = math.exp(-((axis - 0.80) / 0.24) ** 2) * 0.42
            rgb = tuple(mix(rgb[c], sky[c], reflected) for c in range(3))

            edge_distance = min(u, 1.0 - u, v, 1.0 - v)
            edge_mask = 1.0 - clamp(edge_distance / 0.20)
            rgb = tuple(mix(rgb[c], deep[c], edge_mask * 0.28) for c in range(3))

            streak = (
                math.sin((u * 9.0 + 0.23) * tau) * 0.0045
                + math.sin((u * 15.0 + v * 0.55 + 0.61) * tau) * 0.0030
            )
            rgb = tuple(clamp(channel + streak) for channel in rgb)

            lower = clamp((v - 0.80) / 0.20)
            dust_noise = 0.58 + math.sin((u * 2.1 + 0.17) * tau) * 0.17
            dust_amount = lower * dust_noise * 0.050
            rgb = tuple(mix(rgb[c], dust[c], dust_amount) for c in range(3))

            encoded = tuple(linear_to_srgb(channel) for channel in rgb)
            row.extend(int(round(clamp(channel) * 255.0)) for channel in encoded)
        rows.append(row)

    path = os.path.join("/tmp", name.lower().replace(" ", "_") + ".png")
    write_rgb_png(path, size, size, rows)
    if os.path.getsize(path) <= 1024:
        raise RuntimeError("Generated window PNG is suspiciously small: %s" % path)
    image = bpy.data.images.load(path, check_existing=False)
    image.name = name
    image.colorspace_settings.name = "sRGB"
    return image


def ensure_uv(obj):
    if obj.type != "MESH":
        return
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.cube_project(cube_size=1.25, correct_aspect=True)
    bpy.ops.object.mode_set(mode="OBJECT")
    obj.select_set(False)


def texture_material(material, image):
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    shader = nodes.get("Principled BSDF") or next(
        (node for node in nodes if node.type == "BSDF_PRINCIPLED"), None
    )
    if shader is None:
        raise RuntimeError("Window material has no Principled shader: %s" % material.name)

    base_socket = shader.inputs.get("Base Color")
    for link in list(links):
        if link.to_node == shader and link.to_socket == base_socket:
            links.remove(link)

    tex = nodes.new("ShaderNodeTexImage")
    tex.image = image
    tex.interpolation = "Linear"
    tex.extension = "REPEAT"
    links.new(tex.outputs["Color"], base_socket)

    shader.inputs["Roughness"].default_value = 0.28
    if "Specular IOR Level" in shader.inputs:
        shader.inputs["Specular IOR Level"].default_value = 0.42
    elif "Specular" in shader.inputs:
        shader.inputs["Specular"].default_value = 0.42
    if "Metallic" in shader.inputs:
        shader.inputs["Metallic"].default_value = 0.0
    if "Emission Strength" in shader.inputs:
        shader.inputs["Emission Strength"].default_value = 0.0


def reflection_material():
    material = bpy.data.materials.get("Window Sky Reflection") or bpy.data.materials.new("Window Sky Reflection")
    material.diffuse_color = (0.42, 0.72, 0.73, 1.0)
    material.use_nodes = True
    shader = material.node_tree.nodes.get("Principled BSDF")
    if shader is not None:
        shader.inputs["Base Color"].default_value = (0.42, 0.72, 0.73, 1.0)
        shader.inputs["Roughness"].default_value = 0.24
        if "Specular IOR Level" in shader.inputs:
            shader.inputs["Specular IOR Level"].default_value = 0.46
        elif "Specular" in shader.inputs:
            shader.inputs["Specular"].default_value = 0.46
        if "Metallic" in shader.inputs:
            shader.inputs["Metallic"].default_value = 0.0
        if "Emission Strength" in shader.inputs:
            shader.inputs["Emission Strength"].default_value = 0.0
    return material


def add_reflection_band(glass_obj, suffix, x_offset, z_offset, width, length, angle_deg, material):
    """Add one clipped-looking reflection slash just in front of a pane.

    The generated house windows are axis-aligned facade boxes. The slash is kept
    deliberately short so it remains inside the glass field and underneath the
    existing wooden mullion read, rather than becoming a decorative stripe.
    """
    center = glass_obj.matrix_world.translation
    front_y = center.y - (glass_obj.dimensions.y * 0.5) - 0.004
    bpy.ops.mesh.primitive_cube_add(
        location=(center.x + x_offset, front_y, center.z + z_offset),
        rotation=(0.0, math.radians(angle_deg), 0.0),
    )
    band = bpy.context.object
    band.name = "%s_Reflection_%s" % (glass_obj.name, suffix)
    band.dimensions = (width, 0.008, length)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    band.data.materials.append(material)
    bevel = band.modifiers.new("Soft reflection edge", "BEVEL")
    bevel.width = 0.014
    bevel.segments = 2
    bpy.context.view_layer.objects.active = band
    bpy.ops.object.modifier_apply(modifier=bevel.name)
    return band


window_image = build_window_image("Lembah Weathered Teal Window")
matched_materials = []
for material in bpy.data.materials:
    if material.name.startswith("Muted Teal Window"):
        texture_material(material, window_image)
        matched_materials.append(material.name)

if not matched_materials:
    raise RuntimeError("Muted Teal Window material not found after house GLB import")

matched_objects = []
window_objects = []
for obj in bpy.context.scene.objects:
    if obj.type != "MESH":
        continue
    uses_window = any(
        slot.material is not None and slot.material.name.startswith("Muted Teal Window")
        for slot in obj.material_slots
    )
    if uses_window:
        ensure_uv(obj)
        matched_objects.append(obj.name)
        window_objects.append(obj)

if not matched_objects:
    raise RuntimeError("No WindowGlass mesh uses the expected Muted Teal Window material")

# Texture-only V1 still read as a cyan card in the actual hero render. Two small,
# broad reflection slashes per window make the material identity survive the fixed
# gameplay camera while retaining the stylized low-poly language.
reflection_mat = reflection_material()
reflection_count = 0
for glass in window_objects:
    add_reflection_band(glass, "A", -0.18, 0.17, 0.105, 0.62, -28.0, reflection_mat)
    add_reflection_band(glass, "B", 0.20, -0.12, 0.070, 0.42, -28.0, reflection_mat)
    reflection_count += 2

if reflection_count != len(window_objects) * 2:
    raise RuntimeError("Window reflection overlay count mismatch")

bpy.ops.object.select_all(action="SELECT")
bpy.ops.export_scene.gltf(
    filepath=OUT_PATH,
    export_format="GLB",
    use_selection=True,
    export_apply=True,
    export_yup=True,
)
print(
    "Textured hero-house window glass exported to %s (%s, %d reflection accents)"
    % (OUT_PATH, ", ".join(matched_objects), reflection_count)
)
