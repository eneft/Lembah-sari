# Natural village environment

The playable V5 scene applies `village_environment_detail.gd` after replacing the house. It uses the restored V5 terrain as its layout reference and excludes both the retired house and the traditional V4 house from all material/geometry changes. Player asset, animation, camera and gameplay scripts are unchanged.

Trees have branching trunks and rounded clusters of individually shaped leaves. Shrubs use smaller leaf clusters; palms use curved fronds with paired leaflets. All leaves share one MultiMesh and a subtle wind/vein shader. Low-resolution invisible canopy shapes cast shadows so every leaf is not rendered repeatedly into shadow cascades.

Grass, dirt path, cultivated soil, hills, timber and bamboo use deterministic world-space material variation. River and paddy water use animated small ripples with muted turquoise/green colors. Rounded, irregular river stones and small shoreline pebbles share another MultiMesh. Grass tufts are restricted to peripheral beds, path margins and riverbanks; the bridge approach stays clear.

The pass uses a fixed seed and shared materials/geometry. No new large texture downloads are required. Native Compatibility renderer captures verify shader compilation; existing house and locomotion smoke tests verify replacement and controls. Web export remains subject to the existing 20 MiB game-data budget. Real-device Safari performance remains a separate validation step.
