# Preview cache updates

Each web export is postprocessed by `tools/web/prepare_versioned_preview.py` with the checked-out commit SHA. The game pack request and its progress-size key both include `?v=<commit>`, preventing an older installed Godot worker from returning an earlier `index.pck` for a new build.

`play.html` is an additional entry point for users whose original `index.html` remains cached. The exported worker installs into a commit-specific cache, activates immediately, claims existing clients, and deletes earlier game caches. Startup asks the browser to check for worker updates. Repeated visits to the same version still reuse the downloaded WASM and game pack.

`tools/tests/verify_preview_updates.cjs` executes the worker with simulated Cache Storage containing an older game pack. It verifies immediate activation, old-cache removal, a fresh versioned pack request, and cache reuse on the second load. The normal pack remains on disk for native runtime smoke tests.

The branch web-build workflow and the main Pages workflow both run this postprocess and regression test after export.
