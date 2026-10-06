# Fixed-camera 2.5D village

The player, house, ground, path, bridge, fences and garden beds retain geometry. Decorative trees, palms, bushes and seedlings use alpha-tested image cards aligned with the fixed camera. Distant hills use one background card. The area has boundary colliders and trees have simple trunk colliders. Cards use normal depth testing so the player can pass in front and behind them.

Source images were generated for this project and encoded as WebP game assets. Vegetation shares an atlas; ground and water retain the existing surface shaders. The camera rig is detached from player translation while preserving camera-relative controls and Idle/Walk/Run.

Run `godot --headless --path . --fixed-fps 60 --script res://tools/tests/verify_hybrid_environment.gd` to verify images, replacement meshes and camera stability during movement. CI also runs this check against the exported pack.
