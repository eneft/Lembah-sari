import math
import os
import struct
import sys
import zlib

import bpy

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

# Build the last accepted environment pass first. That module intentionally
# constructs and exports the full scene at import time. The live Blender scene
# remains available afterwards, so this gate can touch only BackHillA/B/C and
# re-export without changing any already-accepted material gate.
import build_hero_scene_v5_bamboo_texture  # noqa: F401,E402

OUT_PATH = os.path.abspath(
    os.environ.get(
        "LEMBAH_HERO_OUT",
        os.path.join(os.getcwd(), "assets", "models", "hero_scene_v5.glb"),
    )
)
os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)


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
    return (
        struct.pack(">I", len(payload))
        + kind
        + payload
        + struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF)
    )


def write_rgb_png(path, width, height, rows):
    raw = bytearray()
    for row in rows:
        raw.append(0)
        raw.extend(row)
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    payload = (
        b"\x89PNG\r\n\x1a\n"
        + png_chunk(b"IHDR", ihdr)
        + png_chunk(b"IDAT", zlib.compress(bytes(raw), 9))
        + png_chunk(b"IEND", b"")
    )
    with open(path, "wb") as handle:
        handle.write(payload)


def build_hill_image(name, dark, mid, light, warm, phase=0.0, size=256):
    """Bake broad atmospheric vegetation masses for distant village hills.

    The hills are background silhouettes, so the texture deliberately avoids
    leaf-scale detail. Only broad slope/canopy value changes survive the fixed
    gameplay camera and keep the background calmer than the playable foreground.
    """
    tau = math.pi * 2.0
    rows = []

    for py in range(size):
        v = py / float(size - 1)
        row = bytearray()
        for px in range(size):
            u = px / float(size - 1)

            broad = (
                math.sin((u * 0.92 + v * 0.64 + phase) * tau) * 0.205
                + math.sin((u * 1.72 - v * 1.08 + 0.31 + phase * 0.45) * tau) * 0.105
                + math.sin((u * 2.85 + v * 1.55 + 0.67) * tau) * 0.040
            )
            vertical = (0.5 - v) * 0.10
            t = clamp(0.50 + broad + vertical)

            if t < 0.50:
                q = t / 0.50
                rgb = tuple(mix(dark[c], mid[c], q) for c in range(3))
            else:
                q = (t - 0.50) / 0.50
                rgb = tuple(mix(mid[c], light[c], q) for c in range(3))

            warm_field = (
                math.sin((u * 1.28 - v * 0.76 + 0.21 + phase) * tau) * 0.72
                + math.sin((u * 2.25 + v * 1.30 + 0.56) * tau) * 0.24
            )
            warm_amount = clamp((warm_field - 0.47) / 0.45) * 0.105
            rgb = tuple(mix(rgb[c], warm[c], warm_amount) for c in range(3))

            encoded = tuple(linear_to_srgb(channel) for channel in rgb)
            row.extend(int(round(clamp(channel) * 255.0)) for channel in encoded)
        rows.append(row)

    path = os.path.join("/tmp", name.lower().replace(" ", "_") + ".png")
    write_rgb_png(path, size, size, rows)
    if os.path.getsize(path) <= 1024:
        raise RuntimeError("Generated distant hill PNG is suspiciously small: %s" % path)

    image = bpy.data.images.load(path, check_existing=False)
    image.name = name
    image.colorspace_settings.name = "sRGB"
    return image


def textured_material(name, source_material, image, roughness=0.98):
    if source_material is None:
        raise RuntimeError("Distant hill source material is missing")

    material = source_material.copy()
    material.name = name
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    shader = nodes.get("Principled BSDF") or next(
        (node for node in nodes if node.type == "BSDF_PRINCIPLED"), None
    )
    if shader is None:
        raise RuntimeError("Distant hill material has no Principled shader: %s" % material.name)

    base_socket = shader.inputs.get("Base Color")
    for link in list(links):
        if link.to_node == shader and link.to_socket == base_socket:
            links.remove(link)

    tex = nodes.new("ShaderNodeTexImage")
    tex.image = image
    tex.interpolation = "Linear"
    tex.extension = "REPEAT"
    links.new(tex.outputs["Color"], base_socket)

    shader.inputs["Roughness"].default_value = roughness
    if "Specular IOR Level" in shader.inputs:
        shader.inputs["Specular IOR Level"].default_value = 0.06
    elif "Specular" in shader.inputs:
        shader.inputs["Specular"].default_value = 0.06
    if "Metallic" in shader.inputs:
        shader.inputs["Metallic"].default_value = 0.0
    if "Emission Strength" in shader.inputs:
        shader.inputs["Emission Strength"].default_value = 0.0
    return material


def require_object(name):
    obj = bpy.data.objects.get(name)
    if obj is None:
        obj = next((candidate for candidate in bpy.data.objects if candidate.name.startswith(name)), None)
    if obj is None or obj.type != "MESH":
        raise RuntimeError("Expected distant hill mesh was not created: %s" % name)
    return obj


def first_material(obj):
    if not obj.data.materials:
        raise RuntimeError("Distant hill mesh has no source material: %s" % obj.name)
    return obj.data.materials[0]


def ensure_uv(obj):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(66.0), island_margin=0.025)
    bpy.ops.object.mode_set(mode="OBJECT")
    obj.select_set(False)


def assign(obj, material):
    ensure_uv(obj)
    obj.data.materials.clear()
    obj.data.materials.append(material)


hill_a = require_object("BackHillA")
hill_b = require_object("BackHillB")
hill_c = require_object("BackHillC")

deep_image = build_hill_image(
    "Lembah Distant Hill Deep",
    dark=(0.055, 0.145, 0.070),
    mid=(0.105, 0.235, 0.105),
    light=(0.175, 0.330, 0.145),
    warm=(0.245, 0.355, 0.135),
    phase=0.13,
)
light_image = build_hill_image(
    "Lembah Distant Hill Sun",
    dark=(0.080, 0.185, 0.080),
    mid=(0.145, 0.285, 0.120),
    light=(0.225, 0.385, 0.165),
    warm=(0.305, 0.405, 0.145),
    phase=0.49,
)

deep_mat = textured_material(
    "V5 Textured Distant Hill",
    first_material(hill_a),
    deep_image,
)
light_mat = textured_material(
    "V5 Textured Distant Hill Light",
    first_material(hill_b),
    light_image,
)

assign(hill_a, deep_mat)
assign(hill_b, light_mat)
assign(hill_c, deep_mat)

bpy.ops.object.select_all(action="SELECT")
bpy.ops.export_scene.gltf(
    filepath=OUT_PATH,
    export_format="GLB",
    use_selection=True,
    export_apply=True,
    export_yup=True,
)
print(
    "Distant hill texture gate exported to %s (%s -> %s; %s -> %s; %s -> %s)"
    % (
        OUT_PATH,
        hill_a.name,
        deep_mat.name,
        hill_b.name,
        light_mat.name,
        hill_c.name,
        deep_mat.name,
    )
)
