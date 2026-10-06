# Traditional player house V4

The playable V5 scene now replaces its embedded house with
`assets/models/player_house_traditional_v4.glb`, repaired from the supplied
`traditional house 3d model.glb` (source SHA256
`1ba447288ad06f123395d526339a645960dd984144572c1320d63d9bcfe04174`).

The source's timber, plaster, stone, porch, plants, and tools retain their
geometry and original UV albedo. The repair removes the uneven main roof,
cleans duplicate and degenerate body geometry, rebuilds six symmetric roof
panels with 876 regularly spaced overlapping clay tiles, and aligns the ridge,
gable, and hip caps. Each tile is a closed curved shell. Two fitted timber
gable panels close the old roof cavity. A baked 512px clay albedo lives at
`assets/textures/house_roof_clay_v4.png` and is embedded in the GLB. Metallic
is zero, clay roughness is 0.88, and the source body normal strength is 0.30.

The house front is glTF +Z. In V5 its local yaw is zero, so the porch faces the
village path. The replacement takes the original `HeroHouseRoot` position
before removing it; the current artifact's position is (-4.25, 0.02, -2.85).
The normalized GLB uses uniform scale 6.6. The player starts farther along the
approach at (3.3, 0.08, 3.1), clear of the new stairs. The older `Main.tscn`
replacement uses the same asset with yaw 180 because that map's entrance
faces the opposite local direction.

Reproduce the asset with Blender 4.0+:

```sh
blender --background --factory-startup --python-exit-code 1 \
  --python tools/blender/repair_traditional_house_v4.py -- \
  --input /path/to/traditional_house.glb \
  --output assets/models/player_house_traditional_v4.glb \
  --texture assets/textures/house_roof_clay_v4.png
```

After Godot imports the project, `tools/tests/verify_player_house.gd` checks
the active replacement, removal of the old house, the porch direction relative
to the path, embedded body/roof textures, all six roof panels, the footprint,
and a clear grounded spawn. The existing locomotion test verifies that
Idle/Walk/Run, movement cadence, collision response, and dialogue locking
still work. Both run in the Web preview build workflow.
