import math
import os
import struct
import sys
import zlib

import bpy

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

# Build the last visually accepted scene first. That pass leaves the complete
# Blender scene alive after export; this gate changes only the three V5 horizon
# ridges and then re-exports the same scene.
import build_hero_scene_v5_hill_texture  # noqa: F401,E402

OUT_PATH = os.path.abspath(
    os.environ.get(
        "LEMBAH_HERO_OUT",
        os.path.join(os.getcwd(), "assets", "models", "hero_scene_v5.glb"),
    )
)
os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)

# V5's ground rebuild intentionally retires the old sphere/capsule horizon. Those
# objects are marked hide_render by build_hero_scene_v5.py, but Blender's glTF
# exporter does not serialize hide_render as runtime visibility. If selected,
# they therefore survive into Godot and completely occlude the V5 ridge meshes.
# Exclude only that retired horizon family at this gate's final export; every
# other accepted scene object remains untouched.
LEGACY_HORIZON_PREFIXES = ("BackHill", "FarHill", "HazeRidge", "MidRidge")


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


def build_ridge_image(name, dark, mid, light, phase=0.0, size=256):
    """Bake only broad haze-scale variation for a distant terrain ridge."""
    tau = math.pi * 2.0
    rows = []
    for py in range(size):
        v = py / float(size - 1)
        row = bytearray()
        for px in range(size):
            u = px / float(size - 1)
            broad = (
                math.sin((u * 0.72 + v * 0.38 + phase) * tau) * 0.145
                + math.sin((u * 1.48 - v * 0.72 + 0.31 + phase * 0.4) * tau) * 0.070
                + math.sin((u * 2.35 + v * 1.10 + 0.63) * tau) * 0.026
            )
            vertical = (0.5 - v) * 0.045
            t = clamp(0.50 + broad + vertical)
            if t < 0.50:
                q = t / 0.50
                rgb = tuple(mix(dark[c], mid[c], q) for c in range(3))
            else:
                q = (t - 0.50) / 0.50
                rgb = tuple(mix(mid[c], light[c], q) for c in range(3))

            encoded = tuple(linear_to_srgb(channel) for channel in rgb)
            row.extend(int(round(clamp(channel) * 255.0)) for channel in encoded)
        rows.append(row)

    path = os.path.join("/tmp", name.lower().replace(" ", "_") + ".png")
    write_rgb_png(path, size, size, rows)
    if os.path.getsize(path) <= 1024:
        raise RuntimeError("Generated ridge PNG is suspiciously small: %s" % path)
    image = bpy.data.images.load(path, check_existing=False)
    image.name = name
    image.colorspace_settings.name = "sRGB"
    return image


def require_mesh(name):
    obj = bpy.data.objects.get(name)
    if obj is None:
        obj = next((candidate for candidate in bpy.data.objects if candidate.name.startswith(name)), None)
    if obj is None or obj.type != "MESH":
        raise RuntimeError("Expected V5 ridge mesh is missing: %s" % name)
    return obj


def source_material(obj):
    if not obj.data.materials:
        raise RuntimeError("Ridge has no source material: %s" % obj.name)
    return obj.data.materials[0]


def ridge_material(name, source, image):
    material = source.copy()
    material.name = name
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    shader = nodes.get("Principled BSDF") or next(
        (node for node in nodes if node.type == "BSDF_PRINCIPLED"), None
    )
    if shader is None:
        raise RuntimeError("Ridge material has no Principled shader: %s" % material.name)

    base_socket = shader.inputs.get("Base Color")
    for link in list(links):
        if link.to_node == shader and link.to_socket == base_socket:
            links.remove(link)

    tex = nodes.new("ShaderNodeTexImage")
    tex.image = image
    tex.interpolation = "Linear"
    tex.extension = "REPEAT"
    links.new(tex.outputs["Color"], base_socket)

    shader.inputs["Roughness"].default_value = 1.0
    if "Specular IOR Level" in shader.inputs:
        shader.inputs["Specular IOR Level"].default_value = 0.04
    elif "Specular" in shader.inputs:
        shader.inputs["Specular"].default_value = 0.04
    if "Metallic" in shader.inputs:
        shader.inputs["Metallic"].default_value = 0.0
    if "Emission Strength" in shader.inputs:
        shader.inputs["Emission Strength"].default_value = 0.0
    return material


def planar_uv(obj):
    mesh = obj.data
    if not mesh.vertices:
        return
    layer = mesh.uv_layers.get("UVMap") or mesh.uv_layers.new(name="UVMap")
    min_x = min(v.co.x for v in mesh.vertices)
    max_x = max(v.co.x for v in mesh.vertices)
    min_y = min(v.co.y for v in mesh.vertices)
    max_y = max(v.co.y for v in mesh.vertices)
    span_x = max(max_x - min_x, 1e-5)
    span_y = max(max_y - min_y, 1e-5)
    for poly in mesh.polygons:
        for loop_index in poly.loop_indices:
            vertex = mesh.vertices[mesh.loops[loop_index].vertex_index]
            layer.data[loop_index].uv = (
                (vertex.co.x - min_x) / span_x,
                (vertex.co.y - min_y) / span_y,
            )


def assign(obj, material):
    planar_uv(obj)
    obj.data.materials.clear()
    obj.data.materials.append(material)


def select_v5_export_set():
    bpy.ops.object.select_all(action="DESELECT")
    omitted = []
    selected = 0
    for obj in bpy.context.scene.objects:
        if any(obj.name.startswith(prefix) for prefix in LEGACY_HORIZON_PREFIXES):
            omitted.append(obj.name)
            continue
        obj.select_set(True)
        selected += 1
    if selected == 0:
        raise RuntimeError("Atmospheric ridge export selection is empty")
    if not all(any(name.startswith(prefix) for name in omitted) for prefix in ("BackHill", "HazeRidge", "MidRidge")):
        raise RuntimeError("Expected retired legacy horizon objects were not found: %s" % omitted)
    print("Atmospheric ridge final export excludes retired horizon: %s" % ", ".join(sorted(omitted)))
    print("Atmospheric ridge final export keeps %d scene objects" % selected)


near = require_mesh("V5NearRidge")
mid = require_mesh("V5MidRidge")
far = require_mesh("V5FarRidge")

# Every farther layer becomes lighter and less saturated. The range stays broad
# enough to avoid a flat vector fill, but never competes with house, water or rice.
near_img = build_ridge_image(
    "Lembah Ridge Near Haze",
    dark=(0.315, 0.415, 0.285),
    mid=(0.385, 0.485, 0.345),
    light=(0.455, 0.550, 0.405),
    phase=0.11,
)
mid_img = build_ridge_image(
    "Lembah Ridge Mid Haze",
    dark=(0.395, 0.485, 0.355),
    mid=(0.465, 0.550, 0.420),
    light=(0.535, 0.615, 0.485),
    phase=0.39,
)
far_img = build_ridge_image(
    "Lembah Ridge Far Haze",
    dark=(0.485, 0.555, 0.445),
    mid=(0.555, 0.620, 0.510),
    light=(0.625, 0.685, 0.575),
    phase=0.67,
)

near_mat = ridge_material("V5 Textured Ridge Near", source_material(near), near_img)
mid_mat = ridge_material("V5 Textured Ridge Mid", source_material(mid), mid_img)
far_mat = ridge_material("V5 Textured Ridge Far", source_material(far), far_img)

assign(near, near_mat)
assign(mid, mid_mat)
assign(far, far_mat)

select_v5_export_set()
bpy.ops.export_scene.gltf(
    filepath=OUT_PATH,
    export_format="GLB",
    use_selection=True,
    export_apply=True,
    export_yup=True,
)
print(
    "Atmospheric ridge texture gate exported to %s (%s -> %s; %s -> %s; %s -> %s)"
    % (
        OUT_PATH,
        near.name,
        near_mat.name,
        mid.name,
        mid_mat.name,
        far.name,
        far_mat.name,
    )
)
