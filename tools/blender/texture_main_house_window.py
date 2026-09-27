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
    """Bake a readable stylized glass surface for the fixed hero camera.

    This stays opaque for predictable GLB/Godot rendering. Glass is conveyed by
    cool depth, broad hand-painted sky reflections, darker edge depth, and very
    restrained age streaking. The contrast is intentionally large-scale so the
    material still reads at the actual gameplay camera distance.
    """
    tau = math.pi * 2.0
    deep = (0.030, 0.145, 0.175)
    mid = (0.075, 0.310, 0.345)
    sky = (0.345, 0.650, 0.670)
    sky_bright = (0.560, 0.790, 0.785)
    dust = (0.255, 0.315, 0.255)
    rows = []

    for py in range(size):
        v = py / float(size - 1)
        row = bytearray()
        for px in range(size):
            u = px / float(size - 1)

            # Stronger top-to-bottom depth plus one very broad hand-painted
            # modulation. This gives each pane volume instead of one cyan fill.
            vertical = clamp(0.22 + (1.0 - v) * 0.42)
            broad = math.sin((u * 0.82 + v * 0.54 + 0.13) * tau) * 0.075
            t = clamp(vertical + broad)
            rgb = tuple(mix(deep[c], mid[c], t) for c in range(3))

            # Primary diagonal sky reflection: broad enough to survive the fixed
            # camera, with a brighter core that still avoids a mirror-like pane.
            axis = u * 0.88 + (1.0 - v) * 0.66
            soft_band = math.exp(-((axis - 0.79) / 0.19) ** 2) * 0.66
            core_band = math.exp(-((axis - 0.79) / 0.070) ** 2) * 0.42
            rgb = tuple(mix(rgb[c], sky[c], clamp(soft_band)) for c in range(3))
            rgb = tuple(mix(rgb[c], sky_bright[c], clamp(core_band)) for c in range(3))

            # A secondary faint reflection break prevents the single-band texture
            # from looking like a painted stripe while keeping the design graphic.
            axis_2 = u * 0.52 + v * 0.74
            secondary = math.exp(-((axis_2 - 0.93) / 0.13) ** 2) * 0.18
            rgb = tuple(mix(rgb[c], sky[c], secondary) for c in range(3))

            # Darken the perimeter slightly. Window frames already define the
            # silhouette; this just adds glass depth at the pane edge.
            edge_distance = min(u, 1.0 - u, v, 1.0 - v)
            edge_mask = 1.0 - clamp(edge_distance / 0.18)
            rgb = tuple(mix(rgb[c], deep[c], edge_mask * 0.18) for c in range(3))

            # Very low-contrast age streaks, never dominant over the broad glass
            # read at game scale.
            streak = (
                math.sin((u * 11.0 + 0.23) * tau) * 0.006
                + math.sin((u * 19.0 + v * 0.65 + 0.61) * tau) * 0.004
            )
            rgb = tuple(clamp(channel + streak) for channel in rgb)

            # Slight sill dust warms only the lowest part of the pane.
            lower = clamp((v - 0.78) / 0.22)
            dust_noise = 0.58 + math.sin((u * 2.4 + 0.17) * tau) * 0.18
            dust_amount = lower * dust_noise * 0.055
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

    shader.inputs["Roughness"].default_value = 0.34
    if "Specular IOR Level" in shader.inputs:
        shader.inputs["Specular IOR Level"].default_value = 0.38
    elif "Specular" in shader.inputs:
        shader.inputs["Specular"].default_value = 0.38
    if "Metallic" in shader.inputs:
        shader.inputs["Metallic"].default_value = 0.0
    if "Emission Strength" in shader.inputs:
        shader.inputs["Emission Strength"].default_value = 0.0


window_image = build_window_image("Lembah Weathered Teal Window")
matched_materials = []
for material in bpy.data.materials:
    if material.name.startswith("Muted Teal Window"):
        texture_material(material, window_image)
        matched_materials.append(material.name)

if not matched_materials:
    raise RuntimeError("Muted Teal Window material not found after house GLB import")

matched_objects = []
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

if not matched_objects:
    raise RuntimeError("No WindowGlass mesh uses the expected Muted Teal Window material")

bpy.ops.object.select_all(action="SELECT")
bpy.ops.export_scene.gltf(
    filepath=OUT_PATH,
    export_format="GLB",
    use_selection=True,
    export_apply=True,
    export_yup=True,
)
print("Textured hero-house window glass exported to %s (%s)" % (OUT_PATH, ", ".join(matched_objects)))
