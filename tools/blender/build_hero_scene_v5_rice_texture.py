import math
import os
import struct
import sys
import zlib

import bpy

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

# Build every accepted gate through the lilypad blossom first. This pass is
# intentionally narrow: it textures only the three V5 young-rice materials.
import build_hero_scene_v5_lilypad_texture  # noqa: F401,E402

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


def build_rice_image(name, dark, mid, tip, warm, phase=0.0, size=192):
    """Bake a calm blade-scale base-to-tip gradient for young rice."""
    tau = math.pi * 2.0
    rows = []
    for py in range(size):
        v = py / float(size - 1)
        row = bytearray()
        for px in range(size):
            u = px / float(size - 1)

            # Keep the base damp/deep and lift the blade tips gradually. Small
            # horizontal variation prevents a single flat green sheet at game scale.
            wave = (
                math.sin((u * 2.2 + v * 0.8 + phase) * tau) * 0.060
                + math.sin((u * 5.2 - v * 1.7 + 0.31) * tau) * 0.024
            )
            t = clamp(v * 0.90 + 0.05 + wave)
            if t < 0.58:
                q = t / 0.58
                rgb = tuple(mix(dark[c], mid[c], q) for c in range(3))
            else:
                q = (t - 0.58) / 0.42
                rgb = tuple(mix(mid[c], tip[c], q) for c in range(3))

            # Sparse warm sun at the upper blade only; young rice stays green,
            # not wheat-yellow.
            upper = clamp((v - 0.64) / 0.36)
            sun_field = clamp(
                (math.sin((u * 3.4 + v * 2.3 + 0.47 + phase) * tau) - 0.60)
                / 0.40
            )
            sun = upper * sun_field * 0.10
            rgb = tuple(mix(rgb[c], warm[c], sun) for c in range(3))

            encoded = tuple(linear_to_srgb(channel) for channel in rgb)
            row.extend(int(round(clamp(channel) * 255.0)) for channel in encoded)
        rows.append(row)

    path = os.path.join("/tmp", name.lower().replace(" ", "_") + ".png")
    write_rgb_png(path, size, size, rows)
    if os.path.getsize(path) <= 1024:
        raise RuntimeError("Generated young-rice PNG is suspiciously small: %s" % path)
    image = bpy.data.images.load(path, check_existing=False)
    image.name = name
    image.colorspace_settings.name = "sRGB"
    return image


def apply_texture(material, image):
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    shader = nodes.get("Principled BSDF") or next(
        (node for node in nodes if node.type == "BSDF_PRINCIPLED"), None
    )
    if shader is None:
        raise RuntimeError("Rice material has no Principled shader: %s" % material.name)

    base_socket = shader.inputs.get("Base Color")
    for link in list(links):
        if link.to_node == shader and link.to_socket == base_socket:
            links.remove(link)
    tex = nodes.new("ShaderNodeTexImage")
    tex.image = image
    tex.interpolation = "Linear"
    tex.extension = "REPEAT"
    links.new(tex.outputs["Color"], base_socket)

    shader.inputs["Roughness"].default_value = 0.95
    if "Specular IOR Level" in shader.inputs:
        shader.inputs["Specular IOR Level"].default_value = 0.08
    elif "Specular" in shader.inputs:
        shader.inputs["Specular"].default_value = 0.08
    if "Metallic" in shader.inputs:
        shader.inputs["Metallic"].default_value = 0.0
    if "Emission Strength" in shader.inputs:
        shader.inputs["Emission Strength"].default_value = 0.0


def blade_uv(mesh):
    if not mesh.vertices:
        raise RuntimeError("Rice mesh has no vertices: %s" % mesh.name)
    layer = mesh.uv_layers.get("UVMap") or mesh.uv_layers.new(name="UVMap")
    min_x = min(vertex.co.x for vertex in mesh.vertices)
    max_x = max(vertex.co.x for vertex in mesh.vertices)
    min_z = min(vertex.co.z for vertex in mesh.vertices)
    max_z = max(vertex.co.z for vertex in mesh.vertices)
    dx = max(max_x - min_x, 1e-6)
    dz = max(max_z - min_z, 1e-6)
    for poly in mesh.polygons:
        for loop_index in poly.loop_indices:
            vertex = mesh.vertices[mesh.loops[loop_index].vertex_index]
            u = ((vertex.co.x - min_x) / dx) * 1.20
            v = (vertex.co.z - min_z) / dz
            layer.data[loop_index].uv = (u, v)


palettes = {
    "V5 Young Rice Deep": (
        (0.030, 0.105, 0.018),
        (0.060, 0.205, 0.030),
        (0.115, 0.315, 0.052),
        (0.205, 0.340, 0.075),
        0.13,
    ),
    "V5 Young Rice": (
        (0.045, 0.145, 0.022),
        (0.090, 0.275, 0.040),
        (0.170, 0.405, 0.068),
        (0.255, 0.420, 0.090),
        0.37,
    ),
    "V5 Young Rice Sun": (
        (0.060, 0.175, 0.025),
        (0.125, 0.325, 0.048),
        (0.225, 0.475, 0.085),
        (0.320, 0.465, 0.110),
        0.61,
    ),
}

matched = {}
for material_name, (dark, mid, tip, warm, phase) in palettes.items():
    material = bpy.data.materials.get(material_name)
    if material is None:
        raise RuntimeError("Expected accepted rice material is missing: %s" % material_name)
    image = build_rice_image(
        "Lembah " + material_name,
        dark=dark,
        mid=mid,
        tip=tip,
        warm=warm,
        phase=phase,
    )
    apply_texture(material, image)
    matched[material_name] = 0

seen_meshes = set()
rice_objects = 0
for obj in bpy.context.scene.objects:
    if obj.type != "MESH":
        continue
    if not (obj.name.startswith("V5Rice_") or obj.name.startswith("V5RiceDense_")):
        continue
    rice_objects += 1
    for material in obj.data.materials:
        if material is not None and material.name in matched:
            matched[material.name] += 1
    mesh_key = obj.data.as_pointer()
    if mesh_key not in seen_meshes:
        blade_uv(obj.data)
        seen_meshes.add(mesh_key)

if rice_objects == 0:
    raise RuntimeError("No V5 rice objects found for young-rice texture gate")
missing = [name for name, count in matched.items() if count == 0]
if missing:
    raise RuntimeError("Rice materials were not referenced by V5 clumps: %s" % ", ".join(missing))

# Geometry, placement, paddy water/bunds and every accepted environment material
# remain untouched. Only the three rice materials and their UVs differ here.
bpy.ops.object.select_all(action="SELECT")
bpy.ops.export_scene.gltf(
    filepath=OUT_PATH,
    export_format="GLB",
    use_selection=True,
    export_apply=True,
    export_yup=True,
)
print(
    "Young rice blade texture gate exported to %s (objects=%d, meshes=%d, materials=%s)"
    % (OUT_PATH, rice_objects, len(seen_meshes), matched)
)
