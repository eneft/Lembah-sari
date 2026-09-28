import math
import os
import struct
import sys
import zlib

import bpy

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

# Build the last accepted distant-hill pass first. This gate may only change the
# V5 atmospheric ridges and the final export selection needed to keep them visible.
import build_hero_scene_v5_hill_texture  # noqa: F401,E402

OUT_PATH = os.path.abspath(
    os.environ.get(
        "LEMBAH_HERO_OUT",
        os.path.join(os.getcwd(), "assets", "models", "hero_scene_v5.glb"),
    )
)
os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)

# The old horizon family must not leak into Godot, but BackHillA/B/C are the
# already-accepted Distant Hill gate and MUST remain in the final export.
ACCEPTED_DISTANT_HILLS = ("BackHillA", "BackHillB", "BackHillC")
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
    """Bake broad, low-contrast atmospheric variation only."""
    tau = math.pi * 2.0
    rows = []
    for py in range(size):
        v = py / float(size - 1)
        row = bytearray()
        for px in range(size):
            u = px / float(size - 1)
            broad = (
                math.sin((u * 0.72 + v * 0.38 + phase) * tau) * 0.105
                + math.sin((u * 1.43 - v * 0.68 + 0.31 + phase * 0.4) * tau) * 0.050
                + math.sin((u * 2.25 + v * 1.02 + 0.63) * tau) * 0.018
            )
            vertical = (0.5 - v) * 0.025
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


def ridge_material(name, source, image, emission_strength):
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

    tex = nodes.new("ShaderNodeTexImage")
    tex.image = image
    tex.interpolation = "Linear"
    tex.extension = "REPEAT"

    base_socket = shader.inputs.get("Base Color")
    for link in list(links):
        if link.to_node == shader and link.to_socket == base_socket:
            links.remove(link)
    links.new(tex.outputs["Color"], base_socket)

    emission_socket = shader.inputs.get("Emission Color") or shader.inputs.get("Emission")
    if emission_socket is not None:
        for link in list(links):
            if link.to_node == shader and link.to_socket == emission_socket:
                links.remove(link)
        links.new(tex.outputs["Color"], emission_socket)

    strength_socket = shader.inputs.get("Emission Strength")
    if strength_socket is not None:
        strength_socket.default_value = emission_strength

    shader.inputs["Roughness"].default_value = 1.0
    if "Specular IOR Level" in shader.inputs:
        shader.inputs["Specular IOR Level"].default_value = 0.02
    elif "Specular" in shader.inputs:
        shader.inputs["Specular"].default_value = 0.02
    if "Metallic" in shader.inputs:
        shader.inputs["Metallic"].default_value = 0.0
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


def smooth_profile(
    points,
    subdivisions=6,
    phase=0.0,
    wave_a=0.0,
    wave_b=0.0,
    z_offset=0.0,
    x_shift=0.0,
):
    """Create a calm independent skyline without vertically stacking layers."""
    if len(points) < 3:
        return points
    tau = math.pi * 2.0
    min_x = points[0][0]
    max_x = points[-1][0]
    span_x = max(max_x - min_x, 1e-5)
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
            local_min = min(p0[2], p1[2], p2[2], p3[2]) - 0.04
            local_max = max(p0[2], p1[2], p2[2], p3[2]) + 0.04
            z = clamp(z, local_min, local_max)
            u = (x - min_x) / span_x
            z += math.sin((u + phase) * tau) * wave_a
            z += math.sin((u * 0.52 + phase * 1.73) * tau) * wave_b
            result.append((x + x_shift, p1[1], z + z_offset))

    last = points[-1]
    u = 1.0
    last_z = (
        last[2]
        + math.sin((u + phase) * tau) * wave_a
        + math.sin((u * 0.52 + phase * 1.73) * tau) * wave_b
    )
    result.append((last[0] + x_shift, last[1], last_z + z_offset))
    return result


def make_terrain_curtain(
    obj,
    base_z=-0.54,
    phase=0.0,
    wave_a=0.0,
    wave_b=0.0,
    z_offset=0.0,
    x_shift=0.0,
):
    """Fill each ridge downward; only its skyline should remain visible."""
    old_mesh = obj.data
    original = [tuple(vertex.co) for vertex in old_mesh.vertices]
    if len(original) < 6 or len(original) % 2 != 0:
        raise RuntimeError(
            "Unexpected ridge topology for %s: %d vertices" % (obj.name, len(original))
        )

    count = len(original) // 2
    y_center = sum(vertex[1] for vertex in original) / float(len(original))
    controls = [(vertex[0], y_center, vertex[2]) for vertex in original[:count]]
    top = smooth_profile(
        controls,
        subdivisions=6,
        phase=phase,
        wave_a=wave_a,
        wave_b=wave_b,
        z_offset=z_offset,
        x_shift=x_shift,
    )

    verts = list(top)
    base_start = len(verts)
    verts.extend((x, y_center, base_z) for x, _y, _z in top)
    faces = [
        (i, base_start + i, base_start + i + 1, i + 1)
        for i in range(len(top) - 1)
    ]

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


def is_retired_horizon(obj):
    if any(obj.name.startswith(name) for name in ACCEPTED_DISTANT_HILLS):
        return False
    if obj.name.startswith(("V5NearRidge", "V5MidRidge", "V5FarRidge")):
        return False
    return any(obj.name.startswith(prefix) for prefix in LEGACY_HORIZON_PREFIXES)


def select_v5_export_set():
    bpy.ops.object.select_all(action="DESELECT")
    omitted = []
    selected = 0
    kept_hills = []

    for obj in bpy.context.scene.objects:
        if is_retired_horizon(obj):
            omitted.append(obj.name)
            continue
        obj.select_set(True)
        selected += 1
        if any(obj.name.startswith(name) for name in ACCEPTED_DISTANT_HILLS):
            kept_hills.append(obj.name)

    if selected == 0:
        raise RuntimeError("Atmospheric ridge export selection is empty")
    if len(kept_hills) < 3:
        raise RuntimeError(
            "Accepted distant hills must remain in ridge export; found: %s" % kept_hills
        )
    if not any(
        name.startswith(("HazeRidge", "MidRidge", "FarHill", "BackHill"))
        for name in omitted
    ):
        raise RuntimeError("Expected retired horizon objects were not found")

    print("Atmospheric ridge export excludes retired horizon: %s" % ", ".join(sorted(omitted)))
    print("Atmospheric ridge export preserves accepted hills: %s" % ", ".join(sorted(kept_hills)))
    print("Atmospheric ridge final export keeps %d scene objects" % selected)


near = require_mesh("V5NearRidge")
mid = require_mesh("V5MidRidge")
far = require_mesh("V5FarRidge")

near_source = source_material(near)
mid_source = source_material(mid)
far_source = source_material(far)

# Muted family with a much smaller value jump between layers. Atmospheric depth
# now comes mostly from overlap, not from three bright stacked stripes.
near_img = build_ridge_image(
    "Lembah Ridge Near Haze",
    dark=(0.090, 0.145, 0.075),
    mid=(0.120, 0.185, 0.105),
    light=(0.155, 0.225, 0.135),
    phase=0.11,
)
mid_img = build_ridge_image(
    "Lembah Ridge Mid Haze",
    dark=(0.115, 0.165, 0.100),
    mid=(0.145, 0.205, 0.130),
    light=(0.180, 0.245, 0.160),
    phase=0.39,
)
far_img = build_ridge_image(
    "Lembah Ridge Far Haze",
    dark=(0.145, 0.190, 0.130),
    mid=(0.175, 0.225, 0.155),
    light=(0.210, 0.260, 0.185),
    phase=0.67,
)

near_mat = ridge_material(
    "V5 Textured Ridge Near", near_source, near_img, emission_strength=0.30
)
mid_mat = ridge_material(
    "V5 Textured Ridge Mid", mid_source, mid_img, emission_strength=0.34
)
far_mat = ridge_material(
    "V5 Textured Ridge Far", far_source, far_img, emission_strength=0.38
)

# Critical fix: remove the previous vertical ladder (-0.10 / +0.04 / +0.18).
# All three layers now occupy nearly the same horizon band; depth comes from
# occlusion and different local peaks, so mid/far appear only where they crest.
make_terrain_curtain(
    near,
    base_z=-0.58,
    phase=0.06,
    wave_a=0.075,
    wave_b=0.032,
    z_offset=-0.015,
    x_shift=0.55,
)
make_terrain_curtain(
    mid,
    base_z=-0.58,
    phase=0.34,
    wave_a=0.105,
    wave_b=0.044,
    z_offset=-0.025,
    x_shift=-0.55,
)
make_terrain_curtain(
    far,
    base_z=-0.58,
    phase=0.63,
    wave_a=0.135,
    wave_b=0.055,
    z_offset=-0.035,
    x_shift=0.10,
)

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
