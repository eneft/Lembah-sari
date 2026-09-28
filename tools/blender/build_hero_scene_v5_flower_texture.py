import math
import os
import struct
import sys
import zlib

import bpy

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

# Build the last visually accepted environment first. This gate changes only the
# Cyan and Yellow material slots carried by Template_Flowers; its Green slot is
# deliberately left on the already-accepted foliage material pass.
import build_hero_scene_v5_bank_texture  # noqa: F401,E402

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


def build_petal_image(name, dark, mid, light, warm=None, phase=0.0, size=192):
    """Bake soft, low-frequency petal color variation that survives game scale."""
    tau = math.pi * 2.0
    rows = []
    for py in range(size):
        v = py / float(size - 1)
        row = bytearray()
        for px in range(size):
            u = px / float(size - 1)

            # Flowers occupy only a few pixels in the hero camera. Keep texture
            # broad and calm so it reads as petal volume rather than speckle noise.
            broad = (
                math.sin((u * 1.30 + v * 0.85 + phase) * tau) * 0.145
                + math.sin((u * 2.55 - v * 1.70 + 0.27) * tau) * 0.070
                + math.sin((u * 4.20 + v * 3.10 + 0.61) * tau) * 0.025
            )
            t = clamp(0.50 + broad)
            if t < 0.50:
                q = t / 0.50
                rgb = tuple(mix(dark[c], mid[c], q) for c in range(3))
            else:
                q = (t - 0.50) / 0.50
                rgb = tuple(mix(mid[c], light[c], q) for c in range(3))

            if warm is not None:
                warm_field = clamp(
                    (math.sin((u * 2.8 + v * 2.1 + 0.37 + phase) * tau) - 0.76)
                    / 0.24
                )
                rgb = tuple(mix(rgb[c], warm[c], warm_field * 0.075) for c in range(3))

            encoded = tuple(linear_to_srgb(channel) for channel in rgb)
            row.extend(int(round(clamp(channel) * 255.0)) for channel in encoded)
        rows.append(row)

    path = os.path.join("/tmp", name.lower().replace(" ", "_") + ".png")
    write_rgb_png(path, size, size, rows)
    if os.path.getsize(path) <= 1024:
        raise RuntimeError("Generated flower-petal PNG is suspiciously small: %s" % path)
    image = bpy.data.images.load(path, check_existing=False)
    image.name = name
    image.colorspace_settings.name = "sRGB"
    return image


def petal_material(source, name, image):
    material = source.copy()
    material.name = name
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    shader = nodes.get("Principled BSDF") or next(
        (node for node in nodes if node.type == "BSDF_PRINCIPLED"), None
    )
    if shader is None:
        raise RuntimeError("Flower source material has no Principled shader: %s" % source.name)

    base_socket = shader.inputs.get("Base Color")
    for link in list(links):
        if link.to_node == shader and link.to_socket == base_socket:
            links.remove(link)
    tex = nodes.new("ShaderNodeTexImage")
    tex.image = image
    tex.interpolation = "Linear"
    tex.extension = "REPEAT"
    links.new(tex.outputs["Color"], base_socket)

    # At hero-camera scale the original glossy cyan slots read as bright pins.
    # Push the petals matte so the authored teal/gold values remain quiet accents.
    shader.inputs["Roughness"].default_value = 0.95
    if "Specular IOR Level" in shader.inputs:
        shader.inputs["Specular IOR Level"].default_value = 0.07
    elif "Specular" in shader.inputs:
        shader.inputs["Specular"].default_value = 0.07
    if "Metallic" in shader.inputs:
        shader.inputs["Metallic"].default_value = 0.0
    if "Emission Strength" in shader.inputs:
        shader.inputs["Emission Strength"].default_value = 0.0
    return material


flower = bpy.data.objects.get("Template_Flowers")
if flower is None or flower.type != "MESH":
    raise RuntimeError("Expected Template_Flowers mesh is missing")
if not flower.data.materials:
    raise RuntimeError("Template_Flowers has no material slots")

# Muted blue-green petals: visibly distinct from foliage, but no longer neon cyan
# pinpoints at game distance.
cyan_image = build_petal_image(
    "Lembah Flower Teal Petal",
    dark=(0.012, 0.065, 0.060),
    mid=(0.028, 0.135, 0.120),
    light=(0.070, 0.230, 0.190),
    warm=(0.095, 0.235, 0.150),
    phase=0.17,
)
# Keep the second petal family warm and readable without drifting into saturated
# lemon yellow that competes with the house and rice-field highlights.
yellow_image = build_petal_image(
    "Lembah Flower Gold Petal",
    dark=(0.165, 0.085, 0.014),
    mid=(0.305, 0.180, 0.035),
    light=(0.505, 0.340, 0.070),
    warm=(0.555, 0.265, 0.045),
    phase=0.49,
)

matched = {"Cyan": 0, "Yellow": 0}
for index, source in enumerate(list(flower.data.materials)):
    if source is None:
        continue
    if source.name.startswith("Cyan"):
        flower.data.materials[index] = petal_material(
            source,
            "V5 Textured Flower Teal Petal",
            cyan_image,
        )
        matched["Cyan"] += 1
    elif source.name.startswith("Yellow"):
        flower.data.materials[index] = petal_material(
            source,
            "V5 Textured Flower Gold Petal",
            yellow_image,
        )
        matched["Yellow"] += 1

missing = [name for name, count in matched.items() if count == 0]
if missing:
    raise RuntimeError(
        "Expected Template_Flowers petal slots were not found: %s; slots=%s"
        % (", ".join(missing), [mat.name if mat else "<None>" for mat in flower.data.materials])
    )

# Do not touch the Green slot or any Lilypad/Wheat material. Placed V5Flower_*
# objects share Template_Flowers mesh data, so these two slot replacements alone
# propagate to every flower instance without leaking into other asset families.
bpy.ops.object.select_all(action="SELECT")
bpy.ops.export_scene.gltf(
    filepath=OUT_PATH,
    export_format="GLB",
    use_selection=True,
    export_apply=True,
    export_yup=True,
)
print(
    "Flower petal texture gate exported to %s (Cyan=%d, Yellow=%d; Green untouched)"
    % (OUT_PATH, matched["Cyan"], matched["Yellow"])
)
