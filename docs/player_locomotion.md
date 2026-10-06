# Adventurous boy locomotion

The committed player GLB contains Idle, Walk, and Run on the original 22-bone
rig. Mesh data, skin weights, inverse bind matrices, textures, and materials are
unchanged. Idle retains its original breathing curves and includes a relaxed
neutral limb pose for returning from locomotion.

Walk uses contact, compression, passing, and rising poses. Run adds shorter
support and a flight phase, more knee flexion, forward torso lean, bent elbows,
and delayed backpack motion. These are authored cycles, not downloaded mocap.

Pose references:

- [Blender: A Walking Character](https://docs.blender.org/api/htmlI/x8053.html)
- [AnimSchool: The Key Poses of a Run Cycle](https://blog.animschool.edu/2024/04/10/the-key-poses-of-a-run-cycle/)

`tools/animation/refine_player_locomotion.py` bakes the poses at approximately
60 Hz, solves the legs against the actual skinned soles, and checks grounding
and identical loop endpoints. Rebuild with Python 3, NumPy, and SciPy:

```sh
python tools/animation/refine_player_locomotion.py \
  --input /path/to/adventurous_boy_rigged_idle_walk_run.glb \
  --output assets/models/player_character_lembah_sari.glb
```

The original input SHA-256 is
`a37fd7b0419c20c3cbba8e70aee03b63973ba4de3342e2e453ae175a32b50c9b`.
The committed GLB can also serve as the input: the tool replaces the existing
Walk/Run tracks rather than appending another set.

The controller uses actual horizontal displacement to select animation and
set cadence. It preserves cycle phase when switching between Walk and Run and
returns to Idle when blocked by a wall. Walk/run movement is 1.25/3.2 units per
second to fit this short character's stride. One cycle travels 0.34/0.62 model
units for Walk or 0.42/0.36 for Run, multiplied by the Visual scale (1.55).
Keep the controller's cycle-distance constants aligned with the authoring tool.

Runtime validation, also required by the Web build workflow:

```sh
godot --headless --path . --fixed-fps 60 \
  --script res://tools/tests/verify_player_locomotion.gd
```

It checks imported textures and bone tracks, looping clips, walking/running
input, reduced joystick cadence, stopping, wall collision, and dialogue lock.
