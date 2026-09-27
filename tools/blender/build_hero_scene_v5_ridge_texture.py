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
    material.use_backface_culling = False
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
        shader.inputs["Specular IOR Level"].default_value = 0.03
    elif "Specular" in shader.inputs:
        shader.inputs["Specular"].default_value = 0.03
    if "Metallic" in shader.inputs:
        shader.inputs["Metallic"].default_value = 0.0
    if "Emission Strength" in shader.inputs:
        shader.inputs["Emission Strength"].default_value = 0.0
    return material


def catmull_rom(p0, p1, p2, p3, t):
    t2 = t * t
    t3 = t2 * t
    return 0.5 * (
        2.0 * p1
        + (-p0 + p2) * t
        + (2.0 * p0 - 5.0 * p1 + 4.0 * p2 - p3) * t2
        + (-p0 + 3.0 * p1 - 3.0 * p2 + p3) * t3
    )


def smooth_profile(points, subdivisions=5):
    """Densify the sparse V5 control points into a gentle rolling silhouette."""
    if len(points) < 3:
        return points
    result = []
    for i in range(len(points) - 1):
        p0 = points[max(0, i - 1)]
        p1 = points[i]
        p2 = points[i + 1]
        p3 = points[min(len(points) - 1, i + 2)]
        for step in range(subdivisions):
            t = step / float(subdivisions)
            x = mix(p1[0], p2[0], t)
            z = catmull_rom(p0[2], p1[2], p2[2], p3[2], t)
            # Damp cubic overshoot so the distant ridge never becomes spiky.
            local_min = min(p0[2], p1[2], p2[2], p3[2]) - 0.04
            local_max = max(p0[2], p1[2], p2[2], p3[2]) + 0.04
            z = clamp(z, local_min, local_max)
            result.append((x, p1[1], z))
    result.append(points[-1])
    return result


def make_terrain_curtain(obj, base_z=-0.44):
    """Replace the shallow ribbon with one calm, filled distant-hill curtain."""
    old_mesh = obj.data
    original = [tuple(vertex.co) for vertex in old_mesh.vertices]
    if len(original) < 6 or len(original) % 2 != 0:
        raise RuntimeError("Unexpected ridge topology for %s: %d vertices" % (obj.name, len(original)))

    count = len(original) // 2
    # The first row carries the full V5 contour; average the original two-row Y
    # positions so the replacement remains at the same atmospheric depth.
    y_center = sum(vertex[1] for vertex in original) / float(len(original))
    controls = [(vertex[0], y_center, vertex[2]) for vertex in original[:count]]
    top = smooth_profile(controls, subdivisions=6)

    verts = list(top)
    base_start = len(verts)
    verts.extend((x, y_center, base_z) for x, _y, _z in top)
    faces = []
    for i in range(len(top) - 1):
        faces.append((i, base_start + i, base_start + i + 1, i + 1))

    new_mesh = bpy.data.meshes.new(old_mesh.name + "AtmosphericCurtain")
    new_mesh.from_pydata(verts, [], faces)
    new_mesh.update()
    obj.data = new_mesh
    for modifier in list(obj.modifiers):
        obj.modifiers.remove(modifier)
    if old_mesh.users == 0:
        bpy.data.meshes.remove(old_mesh)
    print(
        "Atmospheric ridge curtain rebuilt: %s (%d controls -> %d profile points, %d faces)"
        % (obj.name, count, len(top), len(faces))
    )


def planar_uv(obj):
    mesh = obj.data
    if not mesh.vertices:
        return
    layer = mesh.uv_layers.get("UVMap") or mesh.uv_layers.new(name="UVMap")
    min_x = min(v.co.x for v in mesh.vertices)
    max_x = max(v.co.x for v in mesh.vertices)
    min_z = min(v.co.z for v in mesh.vertices)
    max_z = max(v.co.z for v in mesh.vertices)
    span_x = max(max_x - min_x, 1e-5)
    span_z = max(max_z - min_z, 1e-5)
    for poly in mesh.polygons:
        for loop_index in poly.loop_indices:
            vertex = mesh.vertices[mesh.loops[loop_index].vertex_index]
            layer.data[loop_index].uv = (
                (vertex.co.x - min_x) / span_x,
                (vertex.co.z - min_z) / span_z,
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

near_source = source_material(near)
mid_source = source_material(mid)
far_source = source_material(far)

# Every farther layer becomes lighter and less saturated. The texture carries
# only broad haze-scale changes so the horizon supports, rather than competes
# with, the playable foreground.
near_img = build_ridge_image(
    "Lembah Ridge Near Haze",
    dark=(0.300, 0.405, 0.285),
    mid=(0.370, 0.470, 0.340),
    light=(0.435, 0.525, 0.395),
    phase=0.11,
)
mid_img = build_ridge_image(
    "Lembah Ridge Mid Haze",
    dark=(0.380, 0.470, 0.355),
    mid=(0.445, 0.530, 0.415),
    light=(0.505, 0.585, 0.470),
    phase=0.39,
)
far_img = build_ridge_image(
    "Lembah Ridge Far Haze",
    dark=(0.465, 0.535, 0.440),
    mid=(0.525, 0.590, 0.500),
    light=(0.585, 0.645, 0.555),
    phase=0.67,
)

near_mat = ridge_material("V5 Textured Ridge Near", near_source, near_img)
mid_mat = ridge_material("V5 Textured Ridge Mid", mid_source, mid_img)
far_mat = ridge_material("V5 Textured Ridge Far", far_source, far_img)

make_terrain_curtain(near, base_z=-0.46)
make_terrain_curtain(mid, base_z=-0.43)
make_terrain_curtain(far, base_z=-0.40)
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
