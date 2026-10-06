#!/usr/bin/env python3
"""Author in-place Walk/Run cycles on the adventurous-boy rig.

Requires numpy and scipy. Geometry, skin weights, materials, embedded images,
and the original Idle curves are copied without alteration. Rotations are baked
at 60 Hz so Godot and other glTF players share the same foot contacts.

References (pose principles, not motion-capture data):
https://docs.blender.org/api/htmlI/x8053.html
https://blog.animschool.edu/2024/04/10/the-key-poses-of-a-run-cycle/
"""

import argparse
import copy
import hashlib
import json
import math
import struct
from pathlib import Path

import numpy as np
from scipy.interpolate import CubicHermiteSpline, CubicSpline, PchipInterpolator
from scipy.spatial.transform import Rotation as R


DTYPES = {5120: "i1", 5121: "u1", 5122: "<i2", 5123: "<u2", 5125: "<u4", 5126: "<f4"}
WIDTHS = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}
IDENTITY = R.identity()
GAITS = {
    "Walk": {"duration": 0.82, "stance": 0.62, "span": 0.34, "front": 0.17, "lift": 0.07},
    "Run": {"duration": 0.66, "stance": 0.36, "span": 0.42, "front": 0.20, "lift": 0.145},
}


def read_glb(path):
    data = Path(path).read_bytes()
    magic, version, total = struct.unpack_from("<III", data)
    assert magic == 0x46546C67 and version == 2 and total == len(data)
    length, kind = struct.unpack_from("<II", data, 12)
    assert kind == 0x4E4F534A
    doc = json.loads(data[20:20 + length])
    offset = 20 + length
    length, kind = struct.unpack_from("<II", data, offset)
    assert kind == 0x004E4942
    return doc, data[offset + 8:offset + 8 + length]


def accessor(doc, binary, index):
    a = doc["accessors"][index]
    v = doc["bufferViews"][a["bufferView"]]
    dtype = np.dtype(DTYPES[a["componentType"]])
    width = WIDTHS[a["type"]]
    start = v.get("byteOffset", 0) + a.get("byteOffset", 0)
    return np.ndarray((a["count"], width), dtype=dtype, buffer=binary,
                      offset=start, strides=(v.get("byteStride", width * dtype.itemsize), dtype.itemsize)).copy()


def between(a, b):
    a, b = a / np.linalg.norm(a), b / np.linalg.norm(b)
    q = np.r_[np.cross(a, b), 1.0 + np.dot(a, b)]
    if np.linalg.norm(q) < 1e-8:
        axis = np.cross(a, [1., 0., 0.])
        if np.linalg.norm(axis) < 1e-8:
            axis = np.cross(a, [0., 1., 0.])
        return R.from_rotvec(math.pi * axis / np.linalg.norm(axis))
    return R.from_quat(q / np.linalg.norm(q))


def two_bone(start, target, pole, upper, lower):
    delta = target - start
    distance = np.linalg.norm(delta)
    direction = delta / max(distance, 1e-8)
    l1, l2 = np.linalg.norm(upper), np.linalg.norm(lower)
    distance = np.clip(distance, abs(l1 - l2) + 0.001, l1 + l2 - 0.001)
    along = (l1 * l1 - l2 * l2 + distance * distance) / (2 * distance)
    bend = pole - direction * np.dot(pole, direction)
    bend /= max(np.linalg.norm(bend), 1e-8)
    elbow = start + along * direction + math.sqrt(max(l1 * l1 - along * along, 0.0)) * bend
    end = start + distance * direction
    return between(upper, elbow - start), between(lower, end - elbow)


class Rig:
    def __init__(self, doc, binary):
        self.doc, self.binary = doc, binary
        self.nodes = doc["nodes"]
        self.names = {n.get("name"): i for i, n in enumerate(self.nodes)}
        self.parents = {c: p for p, n in enumerate(self.nodes) for c in n.get("children", [])}
        self.local = np.array([n.get("translation", [0, 0, 0]) for n in self.nodes], dtype=float)
        primitive = doc["meshes"][0]["primitives"][0]
        attrs = primitive["attributes"]
        self.vertices = accessor(doc, binary, attrs["POSITION"])
        self.joints = accessor(doc, binary, attrs["JOINTS_0"])
        self.weights = accessor(doc, binary, attrs["WEIGHTS_0"])
        self.skin = doc["skins"][0]["joints"]
        self.inverse_bind = accessor(doc, binary, doc["skins"][0]["inverseBindMatrices"]).reshape(-1, 4, 4).transpose(0, 2, 1)
        self.soless = {}
        self.rest_pos, _ = self.globals({}, self.local[2])
        for side, sign in [("Left", -1), ("Right", 1)]:
            mask = (self.vertices[:, 1] < 0.028) & (self.vertices[:, 0] * sign > 0.01)
            self.soless[side] = (self.vertices[mask], self.joints[mask], self.weights[mask])

    def globals(self, rotations, hips):
        positions, rotations_world = {}, {}
        for i in range(len(self.nodes)):
            parent = self.parents.get(i)
            r = rotations.get(i, IDENTITY)
            translation = hips if i == 2 else self.local[i]
            if parent is None:
                positions[i], rotations_world[i] = translation.copy(), r
            else:
                positions[i] = positions[parent] + rotations_world[parent].apply(translation)
                rotations_world[i] = rotations_world[parent] * r
        return positions, rotations_world

    def sole(self, side, rotations, hips):
        positions, world = self.globals(rotations, hips)
        matrices = []
        for j, node in enumerate(self.skin):
            matrix = np.eye(4)
            matrix[:3, :3] = world[node].as_matrix()
            matrix[:3, 3] = positions[node]
            matrices.append(matrix @ self.inverse_bind[j])
        vertices, joints, weights = self.soless[side]
        points = np.c_[vertices, np.ones(len(vertices))]
        transformed = np.einsum("nkij,nj->nki", np.array(matrices)[joints], points)
        return np.einsum("nk,nki->ni", weights, transformed)[:, :3]

    def leg(self, side, rotations, hips, target, pitch):
        upper, lower, foot = [self.names[side + n] for n in ("UpperLeg", "LowerLeg", "Foot")]
        positions, world = self.globals(rotations, hips)
        r1, r2 = two_bone(positions[upper], target, np.array([0., -0.1, 1.]),
                          self.local[lower], self.local[foot])
        rotations[upper] = world[2].inv() * r1
        rotations[lower] = r1.inv() * r2
        rotations[foot] = r2.inv() * R.from_euler("x", pitch, degrees=True)
        rotations[self.names[side + "ToeBase"]] = R.from_euler("x", -max(pitch - 8, 0) * 0.65, degrees=True)

    def arms(self, rotations, hips, phase, running=False, standing=False):
        for side, sign, offset in [("Left", -1., 0.), ("Right", 1., 0.5)]:
            upper, lower, wrist, hand = [self.names[side + n] for n in ("UpperArm", "LowerArm", "Wrist", "Hand")]
            swing = 0. if standing else math.cos(2 * math.pi * (phase + offset))
            # This stylized rig has folded arms in its bind pose. Preserve the
            # elbow's authored hinge/twist rather than solving a straight-arm
            # IK chain, which twists the sleeves and wrists on this skin.
            rotations[upper] = R.from_euler("xyz", [(32 if running else 21) * swing, 0, -sign * 5], degrees=True)
            elbow = -18 - 5 * max(-swing, 0.) if running else 23 - 5 * swing
            rotations[lower] = R.from_euler("x", elbow, degrees=True)
            rotations[wrist] = IDENTITY
            rotations[hand] = IDENTITY


RUN_HEIGHT = CubicSpline([0., .14, .4, .68, .86, 1.], [.368, .348, .362, .400, .416, .368], bc_type="periodic")


def foot_path(phase, gait):
    stance, span, front = gait["stance"], gait["span"], gait["front"]
    if phase <= stance:
        z, lift = front - span * phase / stance, 0.
        if stance > 0.5:
            pitch = float(PchipInterpolator([0, .10, .46, stance], [-10, 0, 0, 27])(phase))
        else:
            pitch = float(PchipInterpolator([0, .08, .23, stance], [5, 0, 4, 36])(phase))
    else:
        t = (phase - stance) / (1 - stance)
        slope = -span * (1 - stance) / stance
        z = float(CubicHermiteSpline([0., 1.], [front - span, front], [slope, slope])(t))
        lift = gait["lift"] * math.sin(math.pi * t) ** 1.7
        angles = [27, 7, -6, -10] if stance > 0.5 else [36, 12, -9, 5]
        pitch = float(PchipInterpolator([0., .25, .65, 1.], angles)(t))
    return z, lift, pitch


def pose(rig, phase, gait, running):
    phase %= 1.
    wave = math.cos(2 * math.pi * phase)
    hips = np.array([0.004 * math.sin(2 * math.pi * phase), 0., .025])
    hips[1] = float(RUN_HEIGHT((phase % .5) * 2)) if running else .418 - .014 * math.cos(4 * math.pi * phase) - .003 * math.sin(4 * math.pi * phase)
    rotations = {
        2: R.from_euler("xyz", [0, (3.0 if running else 2.3) * wave, .7 * math.sin(2 * math.pi * phase)], degrees=True),
        3: R.from_euler("xyz", [6 if running else 1.5, 0, -.4 * math.sin(2 * math.pi * phase)], degrees=True),
        4: R.from_euler("xyz", [4 if running else 1., -(5 if running else 3.4) * wave, 0], degrees=True),
        5: R.from_euler("x", -5 if running else -.7, degrees=True),
        6: R.from_euler("xyz", [-3 if running else -.6, (1.2 if running else .7) * wave, 0], degrees=True),
        23: R.from_euler("xyz", [(2 if running else .8) * math.sin(4 * math.pi * phase - .7), .6 * math.sin(2 * math.pi * phase - .5), 0], degrees=True),
    }
    targets, paths = {}, {}
    for side, offset in [("Left", 0.), ("Right", .5)]:
        z, lift, pitch = foot_path((phase + offset) % 1., gait)
        ankle = rig.rest_pos[rig.names[side + "Foot"]].copy()
        ankle[1] += lift
        ankle[2] += z
        targets[side] = ankle
        paths[side] = (z, lift, pitch)
    # The two boots have different mesh offsets. Ground their actual skinned
    # soles instead of assuming the ankle markers are the bottom of the shoes.
    for _ in range(10):
        for side in ("Left", "Right"):
            z, lift, pitch = paths[side]
            rig.leg(side, rotations, hips, targets[side], pitch)
            sole = rig.sole(side, rotations, hips)
            rest_vertices = rig.soless[side][0]
            targets[side][1] += lift - float(sole[:, 1].min())
            targets[side][2] += float(rest_vertices[:, 2].mean()) + z - float(sole[:, 2].mean())
    for side in ("Left", "Right"):
        rig.leg(side, rotations, hips, targets[side], paths[side][2])
    rig.arms(rotations, hips, phase, running=running)
    return rotations, hips


class Writer:
    def __init__(self, doc, binary):
        self.doc = copy.deepcopy(doc)
        self.data = bytearray()
        self.doc["bufferViews"], self.doc["accessors"], self.doc["animations"] = [], [], []
        used = set()
        for mesh in doc["meshes"]:
            for primitive in mesh["primitives"]:
                used.update(primitive["attributes"].values())
                used.add(primitive["indices"])
        used.update(s["inverseBindMatrices"] for s in doc["skins"])
        views = {doc["accessors"][a]["bufferView"] for a in used}
        views.update(i["bufferView"] for i in doc["images"])
        view_map, acc_map = {}, {}
        for index in sorted(views):
            v = doc["bufferViews"][index]
            start = v.get("byteOffset", 0)
            view_map[index] = self.view(binary[start:start + v["byteLength"]], v)
        for index in sorted(used):
            a = copy.deepcopy(doc["accessors"][index])
            a["bufferView"] = view_map[a["bufferView"]]
            acc_map[index] = len(self.doc["accessors"])
            self.doc["accessors"].append(a)
        for mesh in self.doc["meshes"]:
            for p in mesh["primitives"]:
                p["attributes"] = {k: acc_map[v] for k, v in p["attributes"].items()}
                p["indices"] = acc_map[p["indices"]]
        for s in self.doc["skins"]:
            s["inverseBindMatrices"] = acc_map[s["inverseBindMatrices"]]
        for i in self.doc["images"]:
            i["bufferView"] = view_map[i["bufferView"]]

    def view(self, data, original=None):
        self.data.extend(b"\0" * (-len(self.data) % 4))
        v = copy.deepcopy(original) if original else {}
        v.update(buffer=0, byteOffset=len(self.data), byteLength=len(data))
        self.data.extend(data)
        index = len(self.doc["bufferViews"])
        self.doc["bufferViews"].append(v)
        return index

    def array(self, values, kind):
        values = np.asarray(values, dtype="<f4")
        a = {"bufferView": self.view(values.tobytes()), "componentType": 5126,
             "count": len(values), "type": kind}
        if kind == "SCALAR":
            a.update(min=[float(values.min())], max=[float(values.max())])
        index = len(self.doc["accessors"])
        self.doc["accessors"].append(a)
        return index

    def track(self, animation, times, values, node, path):
        input_index = self.array(times, "SCALAR")
        output_index = self.array(values, "VEC4" if path == "rotation" else "VEC3")
        animation["channels"].append({"sampler": len(animation["samplers"]), "target": {"node": node, "path": path}})
        animation["samplers"].append({"input": input_index, "output": output_index, "interpolation": "LINEAR"})

    def write(self, path):
        self.doc["buffers"] = [{"byteLength": len(self.data)}]
        body = json.dumps(self.doc, separators=(",", ":"), ensure_ascii=False).encode()
        body += b" " * (-len(body) % 4)
        self.data.extend(b"\0" * (-len(self.data) % 4))
        data = struct.pack("<III", 0x46546C67, 2, 28 + len(body) + len(self.data))
        data += struct.pack("<II", len(body), 0x4E4F534A) + body
        data += struct.pack("<II", len(self.data), 0x004E4942) + self.data
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_bytes(data)


def author(source, destination):
    doc, binary = read_glb(source)
    rig, writer = Rig(doc, binary), Writer(doc, binary)
    idle = next(a for a in doc["animations"] if a["name"] == "Idle")
    result_idle = {"name": "Idle", "channels": [], "samplers": []}
    tracked = set()
    duration = 0.
    for c in idle["channels"]:
        sampler = idle["samplers"][c["sampler"]]
        times, values = accessor(doc, binary, sampler["input"]), accessor(doc, binary, sampler["output"])
        writer.track(result_idle, times, values, c["target"]["node"], c["target"]["path"])
        tracked.add((c["target"]["node"], c["target"]["path"]))
        duration = max(duration, float(times.max()))
    relaxed = {}
    rig.arms(relaxed, rig.local[2], 0., standing=True)
    # An explicit neutral pose prevents a knee/ankle from keeping its last
    # locomotion rotation when blending back into the original breathing Idle.
    for node in rig.skin:
        if (node, "rotation") not in tracked:
            q = relaxed.get(node, IDENTITY).as_quat()
            writer.track(result_idle, [0., duration], [q, q], node, "rotation")
    writer.doc["animations"].append(result_idle)
    metrics = {}
    for name, gait in GAITS.items():
        times = np.linspace(0., gait["duration"], round(gait["duration"] * 60) + 1)
        frames = [pose(rig, float(t / gait["duration"]), gait, name == "Run") for t in times]
        # Identical endpoints guarantee an exact loop, including all IK results.
        frames[-1] = frames[0]
        animation = {"name": name, "channels": [], "samplers": [], "extras": {
            "stanceFraction": gait["stance"], "cycleDistance": gait["span"] / gait["stance"],
            "authoredBy": "Lembah Sari procedural foot-contact authoring",
        }}
        for node in rig.skin:
            values = np.array([r.get(node, IDENTITY).as_quat() for r, _ in frames])
            for i in range(1, len(values)):
                if np.dot(values[i - 1], values[i]) < 0:
                    values[i] *= -1
            assert np.allclose(values[0], values[-1], atol=1e-6)
            writer.track(animation, times, values, node, "rotation")
        writer.track(animation, times, [h for _, h in frames], 2, "translation")
        writer.doc["animations"].append(animation)
        minimum, planted_errors, clearance = [], [], []
        for time, (rotations, hips) in zip(times, frames):
            phase = (float(time / gait["duration"])) % 1.
            for side, offset in [("Left", 0.), ("Right", .5)]:
                sole = rig.sole(side, rotations, hips)
                p = (phase + offset) % 1.
                minimum.append(float(sole[:, 1].min()))
                if p <= gait["stance"]:
                    planted_errors.append(abs(float(sole[:, 1].min())))
                else:
                    clearance.append(float(sole[:, 1].min()))
        metrics[name] = {"frames": len(times), "tracks": len(animation["channels"]),
                         "duration": gait["duration"], "cycle_distance": gait["span"] / gait["stance"],
                         "min_sole_y": min(minimum), "max_contact_error": max(planted_errors),
                         "max_swing_clearance": max(clearance), "loop_seam": "identical"}
        assert min(minimum) > -0.003, (name, "foot penetrates floor", min(minimum))
        assert max(planted_errors) < .008, (name, "stance foot floats", max(planted_errors))
    writer.write(destination)
    outdoc, outbin = read_glb(destination)
    for a in range(7):
        assert np.array_equal(accessor(doc, binary, a), accessor(outdoc, outbin, a)), "Geometry/skin changed"
    image = doc["bufferViews"][doc["images"][0]["bufferView"]]
    outimage = outdoc["bufferViews"][outdoc["images"][0]["bufferView"]]
    assert binary[image["byteOffset"]:image["byteOffset"] + image["byteLength"]] == outbin[outimage["byteOffset"]:outimage["byteOffset"] + outimage["byteLength"]]
    print(json.dumps({"output": str(destination), "sha256": hashlib.sha256(Path(destination).read_bytes()).hexdigest(), "gaits": metrics}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    author(args.input, args.output)
