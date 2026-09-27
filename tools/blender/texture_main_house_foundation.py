import math
import os
import struct
import zlib

import bpy

IN_PATH = os.path.abspath(os.environ.get("LEMBAH_HOUSE_IN", "assets/models/house_main_01.glb"))
OUT_PATH = os.path.abspath(os.environ.get("LEMBAH_HOUSE_OUT", IN_PATH))
os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)

if not os.path.exists(IN_PATH):
    raise RuntimeError("Missing house GLB for foundation stone pass: %s" % IN_PATH)

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


def build_foundation_image(name, size=256):
    """Bake bold-but-broad warm village-stone variation for the low footing.

    The footing is only a thin strip at the gameplay camera, so the previous
    restrained map collapsed into one grey value. This pass deliberately widens
    the value and hue separation at a *large* spatial scale: warm ochre stone,
    muted greige stone, shaded brown stone, and a little damp olive aging. There
    are no brick courses, hard mortar lines, or fine photographic noise.
    """
    tau = math.pi * 2.0
    shadow = (0.160, 0.125, 0.085)
    brown = (0.315, 0.240, 0.145)
    greige = (0.475, 0.410, 0.305)
    light = (0.690, 0.590, 0.410)
    ochre = (0.665, 0.455, 0.225)
    damp = (0.245, 0.315, 0.245)
    rows = []

    for py in range(size):
        v = py / float(size - 1)
        row = bytearray()
        for px in range(size):
            u = px / float(size - 1)

            # Large irregular stone-value masses. These are intentionally much
            # stronger than pass 1 so they survive downsampling to ~10 px high.
            broad = (
                math.sin((u * 0.92 + v * 0.54 + 0.11) * tau) * 0.235
                + math.sin((u * 1.85 - v * 1.20 + 0.39) * tau) * 0.115
                + math.sin((u * 3.20 + v * 1.65 + 0.73) * tau) * 0.050
            )
            t = clamp(0.53 + broad)
            if t < 0.38:
                q = t / 0.38
                rgb = tuple(mix(shadow[c], brown[c], q) for c in range(3))
            elif t < 0.68:
                q = (t - 0.38) / 0.30
                rgb = tuple(mix(brown[c], greige[c], q) for c in range(3))
            else:
                q = (t - 0.68) / 0.32
                rgb = tuple(mix(greige[c], light[c], q) for c in range(3))

            # Broad warm mineral blooms give the base a lived-in tropical stone
            # identity and separate it from the cool ground shadow.
            warm_field = (
                math.sin((u * 1.08 - v * 0.72 + 0.27) * tau) * 0.72
                + math.sin((u * 2.35 + v * 1.10 + 0.58) * tau) * 0.28
            )
            warm_amount = clamp((warm_field - 0.18) / 0.72) * 0.32
            rgb = tuple(mix(rgb[c], ochre[c], warm_amount) for c in range(3))

            # Wider muted damp patches near the lower half. They break the warm
            # mass without becoming green moss or tiny speckled noise.
            lower = clamp((v - 0.42) / 0.58)
            damp_field = (
                math.sin((u * 1.55 + v * 1.85 + 0.66) * tau) * 0.76
                + math.sin((u * 3.15 - v * 0.85 + 0.16) * tau) * 0.18
            )
            damp_amount = lower * clamp((damp_field - 0.34) / 0.58) * 0.22
            rgb = tuple(mix(rgb[c], damp[c], damp_amount) for c in range(3))

            # A soft, broad mineral shadow meanders across the texture. Width is
            # intentionally generous so it reads as stone variation, never a crack.
            mineral_axis = v - (0.46 + 0.15 * math.sin((u * 1.32 + 0.19) * tau))
            mineral = math.exp(-((mineral_axis / 0.085) ** 2)) * 0.15
            rgb = tuple(mix(rgb[c], shadow[c], mineral) for c in range(3))

            encoded = tuple(linear_to_srgb(channel) for channel in rgb)
            row.extend(int(round(clamp(channel) * 255.0)) for channel in encoded)
        rows.append(row)

    path = os.path.join("/tmp", name.lower().replace(" ", "_") + ".png")
    write_rgb_png(path, size, size, rows)
    if os.path.getsize(path) <= 1024:
        raise RuntimeError("Generated foundation stone PNG is suspiciously small: %s" % path)
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
    bpy.ops.uv.cube_project(cube_size=1.55, correct_aspect=True)
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
        raise RuntimeError("Foundation stone material has no Principled shader: %s" % material.name)

    base_socket = shader.inputs.get("Base Color")
    for link in list(links):
        if link.to_node == shader and link.to_socket == base_socket:
            links.remove(link)

    tex = nodes.new("ShaderNodeTexImage")
    tex.image = image
    tex.interpolation = "Linear"
    tex.extension = "REPEAT"
    links.new(tex.outputs["Color"], base_socket)

    shader.inputs["Roughness"].default_value = 0.97
    if "Specular IOR Level" in shader.inputs:
        shader.inputs["Specular IOR Level"].default_value = 0.07
    elif "Specular" in shader.inputs:
        shader.inputs["Specular"].default_value = 0.07
    if "Metallic" in shader.inputs:
        shader.inputs["Metallic"].default_value = 0.0
    if "Emission Strength" in shader.inputs:
        shader.inputs["Emission Strength"].default_value = 0.0


stone_image = build_foundation_image("Lembah Warm Foundation Stone Bold")
matched_materials = []
for material in bpy.data.materials:
    if material.name.startswith("Warm Foundation Stone"):
        texture_material(material, stone_image)
        matched_materials.append(material.name)

if not matched_materials:
    raise RuntimeError("Warm Foundation Stone material not found after house GLB import")

matched_objects = []
for obj in bpy.context.scene.objects:
    if obj.type != "MESH":
        continue
    uses_stone = any(
        slot.material is not None and slot.material.name.startswith("Warm Foundation Stone")
        for slot in obj.material_slots
    )
    if uses_stone:
        ensure_uv(obj)
        matched_objects.append(obj.name)

if not matched_objects:
    raise RuntimeError("No StoneFooting mesh uses the Warm Foundation Stone material")

bpy.ops.object.select_all(action="SELECT")
bpy.ops.export_scene.gltf(
    filepath=OUT_PATH,
    export_format="GLB",
    use_selection=True,
    export_apply=True,
    export_yup=True,
)
print("Textured foundation stone exported to %s (%s)" % (OUT_PATH, ", ".join(matched_objects)))
