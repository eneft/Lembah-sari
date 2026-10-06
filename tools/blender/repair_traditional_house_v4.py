"""Repair the supplied traditional-house GLB while retaining the house body.

Run with Blender 4.0+:
  blender --background --factory-startup --python tools/blender/repair_traditional_house_v4.py -- \
    --input /path/to/traditional_house.glb --output assets/models/player_house_traditional_v4.glb \
    --texture assets/textures/house_roof_clay_v4.png

Source SHA256: 1ba447288ad06f123395d526339a645960dd984144572c1320d63d9bcfe04174
The original source's front is glTF +Z. Geometry is authored in its normalized
units; the game scales the complete asset uniformly, including the decorations.
"""

import argparse
import json
import math
import random
import sys
from array import array
from pathlib import Path

import bpy
import bmesh
from mathutils import Vector


# Symmetric roof fitted to the supplied house's eaves and gables. Blender Z-up.
CX, CY = -0.034, 0.061
INNER_X, INNER_Y = 0.275, 0.309
OUTER_X, OUTER_Y = 0.455, 0.426
RIDGE, BREAK, EAVE = 0.575, 0.385, 0.315
TILE_WIDTH, COURSE, OVERLAP = 0.030, 0.039, 0.008


def srgb(rgb):
    return tuple(v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4 for v in rgb)


def color(hex_value):
    return (*srgb(tuple(int(hex_value[i:i + 2], 16) / 255 for i in (0, 2, 4))), 1.)


def principled(name, hex_value, roughness=.86):
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    shader = material.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = color(hex_value)
    shader.inputs["Roughness"].default_value = roughness
    shader.inputs["Metallic"].default_value = 0.
    return material


def bake_clay_texture(path):
    """Bake a clay surface shader; tile seams are entirely real geometry."""
    path.parent.mkdir(parents=True, exist_ok=True)
    bake_material = bpy.data.materials.new("ClayAlbedoBake")
    bake_material.use_nodes = True
    nodes, links = bake_material.node_tree.nodes, bake_material.node_tree.links
    nodes.clear()
    coordinates = nodes.new("ShaderNodeTexCoord")
    noise = nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 18.
    noise.inputs["Detail"].default_value = 3.
    noise.inputs["Roughness"].default_value = .72
    links.new(coordinates.outputs["UV"], noise.inputs["Vector"])
    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = .16
    ramp.color_ramp.elements[0].color = color("914322")
    ramp.color_ramp.elements[1].position = .85
    ramp.color_ramp.elements[1].color = color("ae623b")
    links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    emission = nodes.new("ShaderNodeEmission")
    links.new(ramp.outputs["Color"], emission.inputs["Color"])
    output = nodes.new("ShaderNodeOutputMaterial")
    links.new(emission.outputs[0], output.inputs["Surface"])
    image = bpy.data.images.new("HouseRoofClayV4", 512, 512, alpha=False)
    image.colorspace_settings.name = "sRGB"
    target = nodes.new("ShaderNodeTexImage")
    target.image = image
    nodes.active = target
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, -10))
    helper = bpy.context.object
    helper.data.materials.append(bake_material)
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 4
    scene.cycles.use_denoising = False
    for layer in scene.view_layers:
        layer.cycles.use_denoising = False
    bpy.ops.object.bake(type="EMIT")
    image.filepath_raw = str(path)
    image.file_format = "PNG"
    image.save()
    image.pack()
    bpy.data.objects.remove(helper, do_unlink=True)
    material = principled("MatteTerracottaRoof", "ffffff", .88)
    shader = material.node_tree.nodes.get("Principled BSDF")
    texture = material.node_tree.nodes.new("ShaderNodeTexImage")
    texture.image = image
    material.node_tree.links.new(texture.outputs["Color"], shader.inputs["Base Color"])
    return material


def roof_height(x, y):
    dx, dy = abs(x - CX), abs(y - CY)
    if dx <= INNER_X and dy <= INNER_Y:
        return RIDGE + (BREAK - RIDGE) * dx / INNER_X
    side = (dx - INNER_X) / (OUTER_X - INNER_X)
    end = (dy - INNER_Y) / (OUTER_Y - INNER_Y)
    return BREAK + (EAVE - BREAK) * max(0., min(1., max(side, end)))


def clean_body(source):
    bpy.ops.object.select_all(action="DESELECT")
    source.select_set(True)
    bpy.context.view_layer.objects.active = source
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    source.name = "TraditionalHouseBodyClean"
    bm = bmesh.new()
    bm.from_mesh(source.data)
    original_faces = len(bm.faces)
    bm.normal_update()
    roofing = []
    for face in bm.faces:
        center = face.calc_center_median()
        limit = roof_height(center.x, center.y)
        inside_roof = abs(center.x - CX) < OUTER_X + .008 and abs(center.y - CY) < OUTER_Y + .008
        if center.z > .300 and (center.z > limit - .018 or
                                (inside_roof and face.normal.z > .45) or
                                (face.normal.z > .38 and center.z > limit - .032)):
            roofing.append(face)
    bmesh.ops.delete(bm, geom=roofing, context="FACES")
    bmesh.ops.remove_doubles(bm, verts=list(bm.verts), dist=.000002)
    bmesh.ops.dissolve_degenerate(bm, edges=list(bm.edges), dist=.0000001)
    loose = [v for v in bm.verts if not v.link_faces]
    if loose:
        bmesh.ops.delete(bm, geom=loose, context="VERTS")
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bm.to_mesh(source.data)
    bm.free()
    source.data.update()
    # Retain the source's wall/timber/stone albedo and UVs. Its packed RM image
    # incorrectly makes some timber and ceramic surfaces look metallic.
    for material in source.data.materials:
        if material is None or not material.use_nodes:
            continue
        material.name = "TraditionalHouseTimberStonePlaster"
        for node in material.node_tree.nodes:
            if node.type == "BSDF_PRINCIPLED":
                for socket, value in (("Metallic", 0.), ("Roughness", .85)):
                    for link in list(node.inputs[socket].links):
                        material.node_tree.links.remove(link)
                    node.inputs[socket].default_value = value
            if node.type == "NORMAL_MAP":
                node.inputs["Strength"].default_value = .30
    print("HOUSE_BODY_CLEAN", original_faces, "->", len(source.data.polygons), "removed_roof_faces", len(roofing), flush=True)
    return source


class MeshBuilder:
    def __init__(self):
        self.vertices, self.faces, self.uvs, self.shades = [], [], [], []

    def closed_strip(self, top, uv, normal, thickness, shade):
        """A tile/sheet is a closed solid, with no zero-thickness cut edges."""
        start, count = len(self.vertices), len(top)
        self.vertices.extend(tuple(p) for p in top)
        self.vertices.extend(tuple(p - normal * thickness) for p in top)
        self.uvs.extend(uv + uv)
        self.shades.extend([shade] * count * 2)
        # The top perimeter is counter-clockwise relative to its surface normal.
        self.faces.append(tuple(start + i for i in range(count)))
        self.faces.append(tuple(start + count + i for i in reversed(range(count))))
        for i in range(count):
            j = (i + 1) % count
            self.faces.append((start + i, start + count + i, start + count + j, start + j))

    def closed_profile(self, rows, uv_rows, normal, thickness, shade):
        """Close one curved tile as a shell, without internal coplanar walls."""
        points, uvs, lookup = [], [], {}
        row_indices = []
        for row, row_uv in zip(rows, uv_rows):
            indices = []
            for point, uv in zip(row, row_uv):
                key = tuple(round(v, 8) for v in point)
                if key not in lookup:
                    lookup[key] = len(points)
                    points.append(point)
                    uvs.append(uv)
                indices.append(lookup[key])
            row_indices.append(indices)
        faces = []
        for i in range(len(rows[0]) - 1):
            candidate = [row_indices[0][i], row_indices[1][i], row_indices[1][i + 1], row_indices[0][i + 1]]
            face = []
            for index in candidate:
                if not face or index != face[-1]:
                    face.append(index)
            if len(face) > 1 and face[0] == face[-1]:
                face.pop()
            if len(set(face)) < 3:
                continue
            direction = (points[face[1]] - points[face[0]]).cross(points[face[2]] - points[face[0]])
            if direction.length < 1e-10:
                continue
            if direction.dot(normal) < 0:
                face.reverse()
            faces.append(face)
        if not faces:
            return
        start, count = len(self.vertices), len(points)
        self.vertices.extend(tuple(p) for p in points)
        self.vertices.extend(tuple(p - normal * thickness) for p in points)
        self.uvs.extend(uvs + uvs)
        self.shades.extend([shade] * count * 2)
        perimeter = {}
        for face in faces:
            self.faces.append(tuple(start + i for i in face))
            self.faces.append(tuple(start + count + i for i in reversed(face)))
            for a, b in zip(face, face[1:] + face[:1]):
                if (b, a) in perimeter:
                    del perimeter[(b, a)]
                else:
                    perimeter[(a, b)] = True
        for a, b in perimeter:
            self.faces.append((start + a, start + count + a, start + count + b, start + b))

    def make(self, name, material, smooth=False):
        mesh = bpy.data.meshes.new(name)
        mesh.from_pydata(self.vertices, [], self.faces)
        mesh.update()
        obj = bpy.data.objects.new(name, mesh)
        bpy.context.collection.objects.link(obj)
        mesh.materials.append(material)
        mesh.uv_layers.new(name="TileUV")
        mesh.color_attributes.new(name="Color", type="BYTE_COLOR", domain="CORNER")
        # Creating a second CustomData layer can invalidate the first layer's
        # RNA pointer in Blender 4.0. Resolve both after allocation is complete.
        uv_layer = mesh.uv_layers["TileUV"]
        shades = mesh.color_attributes["Color"]
        indices = array("i", [0]) * len(mesh.loops)
        mesh.loops.foreach_get("vertex_index", indices)
        uv_layer.data.foreach_set("uv", array("f", (value for index in indices for value in self.uvs[index])))
        shades.data.foreach_set("color", array("f", (value for index in indices for value in (self.shades[index],) * 3 + (1.,))))
        mesh.polygons.foreach_set("use_smooth", [smooth] * len(mesh.polygons))
        bm = bmesh.new()
        bm.from_mesh(mesh)
        # The strip builder already supplies outward winding. Recalculating
        # every disconnected tile shell is quadratic on some Blender versions.
        bm.normal_update()
        assert not [e for e in bm.edges if not e.is_manifold], name + " is not a closed roof mesh"
        bm.free()
        if hasattr(mesh, "use_auto_smooth"):
            mesh.use_auto_smooth = True
            mesh.auto_smooth_angle = math.radians(55)
        return obj


class Patch:
    def __init__(self, name, axis, sign, upper=False):
        self.name, self.axis, self.sign, self.upper = name, axis, sign, upper
        self.along_center = CY if axis == "x" else CX
        self.half_outer = INNER_Y if upper else OUTER_Y if axis == "x" else OUTER_X
        self.half_inner = INNER_Y if axis == "x" else INNER_X
        self.low_height, self.high_height = (BREAK, RIDGE) if upper else (EAVE, BREAK)
        self.outer = INNER_X if upper else OUTER_X if axis == "x" else OUTER_Y
        self.inner = 0. if upper else INNER_X if axis == "x" else INNER_Y
        self.length = math.hypot(self.outer - self.inner, self.high_height - self.low_height)
        self.normal = (self.point(self.along_center + .01, .5) - self.point(self.along_center, .5)).cross(
            self.point(self.along_center, .6) - self.point(self.along_center, .5)).normalized()
        if self.normal.z < 0:
            self.normal.negate()

    def half_width(self, t):
        return self.half_outer + (self.half_inner - self.half_outer) * t

    def point(self, along, t):
        across = self.outer + (self.inner - self.outer) * t
        z = self.low_height + (self.high_height - self.low_height) * t
        return Vector((CX + self.sign * across, along, z)) if self.axis == "x" else Vector((along, CY + self.sign * across, z))


def tile_roof(patch, material, backing, randomizer):
    tiles, base = MeshBuilder(), MeshBuilder()
    points = [patch.point(patch.along_center - patch.half_width(t), t) for t in (0., 1.)]
    points += [patch.point(patch.along_center + patch.half_width(t), t) for t in (1., 0.)]
    if (points[1] - points[0]).cross(points[2] - points[0]).dot(patch.normal) < 0:
        points.reverse()
    base.closed_strip(points, [(0., 0.), (0., 1.), (1., 1.), (1., 0.)], patch.normal, .004, 1.)
    base_obj = base.make("RoofBacking_" + patch.name, backing)
    rows = math.ceil(patch.length / COURSE)
    count = 0
    columns = math.ceil(patch.half_outer * 2 / TILE_WIDTH) + 2
    for row in range(rows):
        start_t, end_t = row / rows, min(1., (row + 1) / rows + OVERLAP / patch.length)
        for column in range(-columns // 2, columns // 2 + 1):
            u0, u1 = patch.along_center + column * TILE_WIDTH, patch.along_center + (column + 1) * TILE_WIDTH
            shade = randomizer.uniform(.94, 1.04)
            # Seven profile samples form one curved shell per tile. This avoids
            # dark seams caused by internal walls between adjacent strips.
            rows_of_points, rows_of_uv = [], []
            for t in (start_t, end_t):
                top, uv = [], []
                lo, hi = patch.along_center - patch.half_width(t), patch.along_center + patch.half_width(t)
                for segment in range(7):
                    u = max(lo, min(hi, u0 + TILE_WIDTH * segment / 6))
                    fraction = (u - u0) / TILE_WIDTH
                    length_fraction = (t - start_t) / (end_t - start_t)
                    arch = .0040 * math.sin(math.pi * fraction) ** 2
                    lap = .0027 * (1. - length_fraction)
                    top.append(patch.point(u, t) + patch.normal * (.0015 + arch + lap))
                    uv.append((fraction, length_fraction))
                rows_of_points.append(top)
                rows_of_uv.append(uv)
            tiles.closed_profile(rows_of_points, rows_of_uv, patch.normal, .0018, shade)
            if u1 > patch.along_center - patch.half_width(start_t) and u0 < patch.along_center + patch.half_width(start_t):
                count += 1
    tile_obj = tiles.make("RoofTiles_" + patch.name, material, smooth=True)
    print("ROOF_GRID", patch.name, "courses", rows, "tiles", count, flush=True)
    return [base_obj, tile_obj], count


def caps(name, start, end, material, radius=.012, length=.055):
    builder = MeshBuilder()
    direction = (end - start).normalized()
    side = direction.cross(Vector((0., 0., 1.))).normalized()
    up = side.cross(direction).normalized()
    segments = math.ceil((end - start).length / length)
    for segment in range(segments):
        a = start.lerp(end, segment / segments)
        b = start.lerp(end, min(1., (segment + 1) / segments + .003 / (end - start).length))
        profiles = [[end_point + (side * math.cos(j / 8 * math.pi) + up * math.sin(j / 8 * math.pi)) * radius
                     for j in range(9)] for end_point in (a, b)]
        builder.closed_profile(profiles, [[(j / 8, t) for j in range(9)] for t in (0, 1)], up, .0025, 1.)
    return builder.make(name, material, smooth=True)


def beam(name, start, end, material, width=.010):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(start + end) * .5)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = (width, width, (end - start).length)
    obj.rotation_euler = (end - start).to_track_quat("Z", "Y").to_euler()
    obj.data.materials.append(material)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return obj


def gable_boards(sign, material):
    """Close the old reconstructed roof cavity with fitted timber boards."""
    builder = MeshBuilder()
    normal = Vector((0, sign, 0))
    y = CY + sign * (INNER_Y - .005)
    width = .031
    columns = math.ceil(INNER_X * 2 / width)
    for column in range(columns):
        left = -INNER_X + column * INNER_X * 2 / columns
        right = -INNER_X + (column + 1) * INNER_X * 2 / columns
        left_z = RIDGE - .006 + (BREAK - RIDGE) * abs(left) / INNER_X
        right_z = RIDGE - .006 + (BREAK - RIDGE) * abs(right) / INNER_X
        points = [Vector((CX + left, y, BREAK - .008)), Vector((CX + right, y, BREAK - .008)),
                  Vector((CX + right, y, right_z)), Vector((CX + left, y, left_z))]
        # Add a small board groove while retaining a continuous dark backing.
        if column % 2:
            points = [p - normal * .0008 for p in points]
        if (points[1] - points[0]).cross(points[2] - points[0]).dot(normal) < 0:
            points.reverse()
        builder.closed_strip(points, [(0, 0), (1, 0), (1, 1), (0, 1)], normal, .006, .91 + .07 * (column % 3))
    return builder.make("GableTimberBoards_" + str(sign), material)


def main(args):
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    bpy.ops.import_scene.gltf(filepath=str(args.input))
    sources = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    assert len(sources) == 1, "Expected one source-house mesh"
    body = clean_body(sources[0])
    clay = bake_clay_texture(args.texture)
    print("CLAY_TEXTURE_BAKED", flush=True)
    timber = principled("RoofEdgeTimber", "74543b")
    boards = principled("GableTimberBoards", "91613a")
    objects, tile_count = [body], 0
    for patch in [Patch("MainLeft", "x", -1, True), Patch("MainRight", "x", 1, True),
                  Patch("SkirtLeft", "x", -1), Patch("SkirtRight", "x", 1),
                  Patch("SkirtFront", "y", -1), Patch("SkirtBack", "y", 1)]:
        created, count = tile_roof(patch, clay, timber, random.Random(406 + len(objects)))
        objects.extend(created)
        tile_count += count
    objects.append(caps("RoofRidgeCaps", Vector((CX, CY - INNER_Y, RIDGE + .002)), Vector((CX, CY + INNER_Y, RIDGE + .002)), clay, .015))
    for sy in (-1, 1):
        objects.append(gable_boards(sy, boards))
        for sx in (-1, 1):
            ridge = Vector((CX, CY + sy * INNER_Y, RIDGE + .002))
            corner = Vector((CX + sx * INNER_X, CY + sy * INNER_Y, BREAK + .002))
            outer = Vector((CX + sx * OUTER_X, CY + sy * OUTER_Y, EAVE + .002))
            suffix = "%d_%d" % (sx, sy)
            objects.append(caps("RoofBargeCaps_" + suffix, ridge, corner, clay, .010))
            objects.append(caps("RoofHipCaps_" + suffix, corner, outer, clay, .012))
            offset = Vector((0, 0, -.012))
            objects.append(beam("GableFascia_" + suffix, ridge + offset, corner + offset, timber))
    root = bpy.data.objects.new("TraditionalHouseV4", None)
    bpy.context.collection.objects.link(root)
    root["source_sha256"] = "1ba447288ad06f123395d526339a645960dd984144572c1320d63d9bcfe04174"
    root["front_gltf_axis"] = "+Z"
    root["repair"] = "clean body; six parametric roof panels; regular overlapping tiles; aligned ridge and hip caps; matte PBR"
    root["roof_tile_count"] = tile_count
    for obj in objects:
        obj.parent = root
        if obj.type == "MESH":
            assert all(math.isfinite(c) for v in obj.data.vertices for c in v.co), obj.name
            assert len(obj.data.polygons) > 0, obj.name
    args.output.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=str(args.output), export_format="GLB", export_apply=True,
                             export_normals=True, export_texcoords=True, export_extras=True,
                             export_materials="EXPORT")
    print("TRADITIONAL_HOUSE_REPAIRED", json.dumps({"output": str(args.output), "tiles": tile_count,
          "objects": len(objects), "body_faces": len(body.data.polygons), "front": "+Z"}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--texture", required=True, type=Path)
    main(parser.parse_args(sys.argv[sys.argv.index("--") + 1:]))
