import math
import os
import struct
import sys
import zlib

import bpy

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

# Build only through the accepted tropical-foliage response gate. Rice is the
# next isolated gate; Flower, Lilypad and Garden Bed must remain untouched.
import build_hero_scene_v5_foliage_response as foliage_gate  # noqa: E402

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
    """Bake a calm green base-to-tip gradient for stylized young rice."""
    tau = math.pi * 2.0
    rows = []
    for py in range(size):
        v = py / float(size - 1)
        row = bytearray()
        for px in range(size):
            u = px / float(size - 1)
            wave = (
                math.sin((u * 2.2 + v * 0.8 + phase) * tau) * 0.050
                + math.sin((u * 5.2 - v * 1.7 + 0.31) * tau) * 0.018
            )
            t = clamp(v * 0.90 + 0.05 + wave)
            if t < 0.58:
                q = t / 0.58
                rgb = tuple(mix(dark[c], mid[c], q) for c in range(3))
            else:
                q = (t - 0.58) / 0.42
                rgb = tuple(mix(mid[c], tip[c], q) for c in range(3))

            # A very small warm lift near some tips keeps the paddy lively without
            # turning young rice into mature yellow wheat.
            upper = clamp((v - 0.68) / 0.32)
            sun_field = clamp(
                (math.sin((u * 3.4 + v * 2.3 + 0.47 + phase) * tau) - 0.66)
                / 0.34
            )
            sun = upper * sun_field * 0.070
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


def rice_height(u, v, phase=0.0):
    tau = math.pi * 2.0
    # Broad vertical blade response only: intentionally low-noise at gameplay scale.
    return (
        math.sin((u * 1.8 + v * 0.55 + phase) * tau) * 0.26
        + math.sin((u * 3.1 - v * 0.80 + 0.23) * tau) * 0.08
    ) * (0.35 + 0.65 * v)


def build_rice_normal(name, phase=0.0, size=192, derivative_strength=2.2):
    rows = []
    step = 1.0 / float(size)
    for py in range(size):
        v = py / float(size - 1)
        row = bytearray()
        for px in range(size):
            u = px / float(size - 1)
            h_l = rice_height((u - step) % 1.0, v, phase)
            h_r = rice_height((u + step) % 1.0, v, phase)
            h_d = rice_height(u, max(0.0, v - step), phase)
            h_u = rice_height(u, min(1.0, v + step), phase)
            dx = (h_r - h_l) * derivative_strength
            dy = (h_u - h_d) * derivative_strength
            nx, ny, nz = -dx, -dy, 1.0
            length = math.sqrt(nx * nx + ny * ny + nz * nz) or 1.0
            nx /= length
            ny /= length
            nz /= length
            row.extend(
                (
                    int(round(clamp(nx * 0.5 + 0.5) * 255.0)),
                    int(round(clamp(ny * 0.5 + 0.5) * 255.0)),
                    int(round(clamp(nz * 0.5 + 0.5) * 255.0)),
                )
            )
        rows.append(row)

    path = os.path.join("/tmp", name.lower().replace(" ", "_") + ".png")
    write_rgb_png(path, size, size, rows)
    if os.path.getsize(path) <= 1024:
        raise RuntimeError("Generated young-rice normal PNG is suspiciously small: %s" % path)
    image = bpy.data.images.load(path, check_existing=False)
    image.name = name
    image.colorspace_settings.name = "Non-Color"
    return image


def blade_uv(mesh):
    if not mesh.vertices:
        raise RuntimeError("Rice mesh has no vertices: %s" % mesh.name)
    layer = mesh.uv_layers.get("V5RiceUV") or mesh.uv_layers.new(name="V5RiceUV")
    min_x = min(vertex.co.x for vertex in mesh.vertices)
    max_x = max(vertex.co.x for vertex in mesh.vertices)
    min_z = min(vertex.co.z for vertex in mesh.vertices)
    max_z = max(vertex.co.z for vertex in mesh.vertices)
    dx = max(max_x - min_x, 1e-6)
    dz = max(max_z - min_z, 1e-6)
    for poly in mesh.polygons:
        for loop_index in poly.loop_indices:
            vertex = mesh.vertices[mesh.loops[loop_index].vertex_index]
            u = ((vertex.co.x - min_x) / dx) * 1.15
            v = (vertex.co.z - min_z) / dz
            layer.data[loop_index].uv = (u, v)


def build_variant_material(source, name, palette, normal_image):
    dark, mid, tip, warm, phase = palette
    material = source.copy()
    material.name = name
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    shader = nodes.get("Principled BSDF") or next(
        (node for node in nodes if node.type == "BSDF_PRINCIPLED"), None
    )
    if shader is None:
        raise RuntimeError("Rice source material has no Principled shader: %s" % source.name)

    base_socket = shader.inputs.get("Base Color")
    for link in list(links):
        if link.to_node == shader and link.to_socket == base_socket:
            links.remove(link)

    color_image = build_rice_image(
        "Lembah " + name,
        dark=dark,
        mid=mid,
        tip=tip,
        warm=warm,
        phase=phase,
    )
    color_tex = nodes.new("ShaderNodeTexImage")
    color_tex.name = "V5 Rice Color Texture"
    color_tex.image = color_image
    color_tex.interpolation = "Linear"
    color_tex.extension = "REPEAT"
    links.new(color_tex.outputs["Color"], base_socket)

    normal_tex = nodes.new("ShaderNodeTexImage")
    normal_tex.name = "V5 Rice Normal Texture"
    normal_tex.image = normal_image
    normal_tex.interpolation = "Linear"
    normal_tex.extension = "REPEAT"
    normal = nodes.new("ShaderNodeNormalMap")
    normal.name = "V5 Rice Normal"
    normal.space = "TANGENT"
    normal.inputs["Strength"].default_value = 0.20
    links.new(normal_tex.outputs["Color"], normal.inputs["Color"])
    links.new(normal.outputs["Normal"], shader.inputs["Normal"])

    shader.inputs["Roughness"].default_value = 0.88
    if "Specular IOR Level" in shader.inputs:
        shader.inputs["Specular IOR Level"].default_value = 0.10
    elif "Specular" in shader.inputs:
        shader.inputs["Specular"].default_value = 0.10
    if "Metallic" in shader.inputs:
        shader.inputs["Metallic"].default_value = 0.0
    if "Emission Strength" in shader.inputs:
        shader.inputs["Emission Strength"].default_value = 0.0
    return material


palettes = [
    (
        "V5 Young Rice Deep",
        (
            (0.030, 0.105, 0.018),
            (0.060, 0.205, 0.030),
            (0.115, 0.315, 0.052),
            (0.205, 0.340, 0.075),
            0.13,
        ),
    ),
    (
        "V5 Young Rice",
        (
            (0.045, 0.145, 0.022),
            (0.090, 0.275, 0.040),
            (0.170, 0.405, 0.068),
            (0.255, 0.420, 0.090),
            0.37,
        ),
    ),
    (
        "V5 Young Rice Sun",
        (
            (0.060, 0.175, 0.025),
            (0.125, 0.325, 0.048),
            (0.225, 0.475, 0.085),
            (0.320, 0.465, 0.110),
            0.61,
        ),
    ),
]

rice_objects = sorted(
    [
        obj
        for obj in bpy.context.scene.objects
        if obj.type == "MESH"
        and not obj.hide_render
        and (obj.name.startswith("V5Rice_") or obj.name.startswith("V5RiceDense_"))
    ],
    key=lambda obj: obj.name,
)
if not rice_objects:
    raise RuntimeError("No visible V5 rice objects found for young-rice surface gate")

source_mesh = rice_objects[0].data
source_material = next((material for material in source_mesh.materials if material is not None), None)
if source_material is None:
    raise RuntimeError("V5 rice source mesh has no material")

# The source is the pinned CC0 Wheat template, whose MTL material is Yellow.
# Do not rename/mutate that shared template material because hidden legacy/template
# objects use it too. Build isolated meshes/materials only for visible V5Rice clones.
normal_image = build_rice_normal("Lembah Young Rice Surface Normal")
variant_meshes = []
variant_counts = []
for variant_index, (material_name, palette) in enumerate(palettes):
    material = build_variant_material(source_material, material_name, palette, normal_image)
    mesh = source_mesh.copy()
    mesh.name = "V5 Young Rice Variant %d Mesh" % (variant_index + 1)
    mesh.materials.clear()
    mesh.materials.append(material)
    blade_uv(mesh)
    variant_meshes.append(mesh)
    variant_counts.append(0)

for index, obj in enumerate(rice_objects):
    # Alternate neighboring clumps softly. The distribution is deterministic and
    # changes neither placement nor transform, only the isolated rice mesh/material.
    variant = (index * 7 + index // 5) % len(variant_meshes)
    obj.data = variant_meshes[variant]
    variant_counts[variant] += 1

if any(count == 0 for count in variant_counts):
    raise RuntimeError("Rice palette distribution did not use every variant: %s" % variant_counts)

# Export only the same V5 accepted export set used by the foliage response gate;
# hidden source templates and unrelated scene objects remain excluded.
foliage_gate.ridge_export.select_v5_export_set()
bpy.ops.export_scene.gltf(
    filepath=OUT_PATH,
    export_format="GLB",
    use_selection=True,
    export_apply=True,
    export_yup=True,
)
print(
    "Young rice surface response exported to %s (objects=%d; source=%s; variants=%s)"
    % (OUT_PATH, len(rice_objects), source_material.name, variant_counts)
)
