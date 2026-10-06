# Fixed-camera 2.5D village

The player, house, ground, path, bridge, fences and garden beds retain geometry. Decorative trees, palms, bushes, flowers, bank grasses and seedlings use alpha-tested image cards aligned with the fixed camera. Distant hills use one background card. The area has boundary colliders and trees have simple trunk colliders. Cards use normal depth testing so the player can pass in front and behind them.

## Approved riverside composition

The playable composition is intentionally authored rather than scatter-filled: the house remains the focal point; a clustered orchard and flowering shrubs frame the left side; palms sit behind the roof line; stepped rice paddies occupy the right side; a broad S-curve path connects the porch to a right-side wooden bridge; and a calmer foreground river uses grouped rocks, reeds and lily pads. Legacy V4 decorative scatter is suppressed before the curated V5 foliage is placed.

The traditional playable house keeps its repaired clay roof. At runtime the previously flat front gable is covered by a woven-bamboo infill and a visible timber king-post truss, keeping the front elevation consistent with the approved environment concept without changing player collision or the normalized house footprint.

Source images were generated for this project and encoded as WebP game assets. Vegetation shares an atlas; ground and water retain the existing surface shaders. The camera rig is detached from player translation while preserving camera-relative controls and Idle/Walk/Run.

Run `godot --headless --path . --fixed-fps 60 --script res://tools/tests/verify_hybrid_environment.gd` to verify images, replacement meshes and camera stability during movement. CI also runs this check against the exported pack.
