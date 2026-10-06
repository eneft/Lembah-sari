# Fixed-camera 2.5D village

The player, house, ground, path, bridge, fences and garden beds retain geometry. Decorative trees, palms, bushes, flowers, bank grasses and seedlings use alpha-tested image cards aligned with the fixed camera. Distant hills use one background card. The area has boundary colliders and trees have simple trunk colliders. Cards use normal depth testing so the player can pass in front and behind them.

## Approved riverside composition

The playable composition is intentionally authored rather than scatter-filled: the house remains the focal point; a clustered orchard and flowering shrubs frame the left side; palms sit behind the roof line; stepped rice paddies occupy the right side; a broad S-curve path connects the porch to a right-side wooden bridge; and a calmer foreground river uses grouped rocks, reeds and lily pads. Legacy V4 decorative scatter is suppressed before the curated V5 foliage is placed.

The traditional playable house keeps its repaired clay roof. At runtime the previously flat front gable is covered by a woven-bamboo infill and a visible timber king-post truss, keeping the front elevation consistent with the approved environment concept without changing player collision or the normalized house footprint.

Source images were generated for this project and encoded as WebP game assets. Vegetation shares an atlas; ground and water retain the existing surface shaders. The camera rig is detached from player translation while preserving camera-relative controls and Idle/Walk/Run.

Run `godot --headless --path . --fixed-fps 60 --script res://tools/tests/verify_hybrid_environment.gd` to verify images, replacement meshes and camera stability during movement. CI also runs this check against the exported pack.

## Riverbank polish

The foreground river keeps the approved route but now uses three visual layers: dry bank, a narrow damp shoreline margin, and calmer water. Bank widths vary along the curve so the shoreline no longer reads as parallel ribbons. Rocks are placed as irregular anchor clusters with smaller companion stones, while reeds concentrate around those clusters and inside quiet bends with open gaps between them. The Web water shader uses broad low-frequency color drift and restrained ripples/specular response to avoid a flat plastic pool look.

## Rice terrace polish

The right-side farm keeps four readable paddies but no longer uses board-like slabs or a stamped planting grid. Each terrace has an earthen shelf that reaches toward the base terrain, a slightly inset shallow-water polygon, and a bund with locally varied width. Elevation increases across the terrace group so the stepped structure reads clearly from the fixed camera. Rice clumps use deterministic position, scale and rotation jitter with sparse gaps, while selected grass clusters soften terrace corners without outlining every field. Runtime paddy water uses a dedicated calm shallow-water shader rather than the river response.

## Foliage distribution and midground polish

Vegetation now uses three readable depth bands rather than a repeated front-row scatter. The playable foreground keeps loose orchard, shrub and flower islands with deliberate gaps around the character route. A discontinuous midground belt of smaller trees, palms and bushes occupies the outer left/right horizon and selected spaces behind the house/farm, while the roof peak and main path remain visually open. Runtime image cards use deterministic horizontal mirroring, subtle per-card tone variation and a mild atmospheric green falloff for `V5Mid*` vegetation, reducing visible copy repetition without adding new texture downloads. The midground belt is counted and validated in CI so later passes cannot accidentally remove the ground-to-backdrop transition.

## House yard and prop polish

The house frontage now has a small packed-earth apron that blends into the existing path instead of ending directly on uniform grass. Practical porch-side props are grouped outside the main player route: a terracotta water jar and basin, a compact timber tool rack with hoe and broom, a small firewood stack, a produce crate, and three side stepping stones. Lightweight grass and flower cards soften selected yard edges. These objects are intentionally visual-only and stay outside the central navigation corridor, so the pass adds domestic detail without introducing new gameplay collision or large texture assets.
