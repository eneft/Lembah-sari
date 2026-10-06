#!/usr/bin/env python3
"""Version the game pack URL and activate exported PWA updates immediately."""
import argparse
import json
import re
from pathlib import Path


def prepare(directory: Path, revision: str) -> None:
    if not re.fullmatch(r"[0-9a-f]{7,40}", revision):
        raise ValueError("revision must be a Git commit SHA")
    html_path = directory / "index.html"
    html = html_path.read_text()
    match = re.search(r"const GODOT_CONFIG = (\{[^\n]+\});", html)
    if match is None:
        raise ValueError("Godot config was not found")
    config = json.loads(match.group(1))
    executable = config["executable"]
    pack = executable + ".pck"
    versioned_pack = pack + "?v=" + revision
    config["mainPack"] = versioned_pack
    sizes = config["fileSizes"]
    sizes[versioned_pack] = sizes.pop(pack)
    html = html[:match.start(1)] + json.dumps(config, separators=(",", ":")) + html[match.end(1):]
    html = html.replace("const engine = new Engine(GODOT_CONFIG);", "const engine = new Engine(GODOT_CONFIG);\n"
        "// Fetch a fresh worker without delaying game startup.\n"
        "if ('serviceWorker' in navigator) {\n"
        " navigator.serviceWorker.getRegistration().then((registration) => {\n"
        "  if (registration) return registration.update();\n"
        " }).catch(() => {});\n"
        "}\n")
    # Show engine script/resource errors, including failures after startGame resolves.
    html = html.replace("const engine = new Engine(GODOT_CONFIG);", """const engine = new Engine(GODOT_CONFIG);
const reportRuntimeError = (...parts) => {
 const message = parts.join(' ');
 console.error(message);
 if (!/SCRIPT ERROR|Parse Error|Failed loading|Error loading|Cannot open|could not load|missing hero/i.test(message)) return;
 let panel = document.getElementById('runtime-error');
 if (!panel) {
  panel = document.createElement('pre'); panel.id = 'runtime-error';
  panel.style.cssText = 'position:fixed;top:12px;left:12px;right:12px;z-index:100;background:#241910;color:#ffe4cb;padding:14px;white-space:pre-wrap;max-height:45vh;overflow:auto;font:14px monospace';
  panel.textContent = 'Game gagal memuat scene. Build: '+""" + json.dumps(revision[:7]) + """+'\\n';
  document.body.appendChild(panel);
 }
 panel.textContent += message+'\\n';
};

""")
    html = html.replace("console.error('Error while registering service worker:', err);", "console.error('Error while registering service worker:', err); displayFailureNotice('Browser belum mendukung fitur Godot: ' + missing.join(', '));")
    html = html.replace("engine.startGame({", "engine.startGame({\n onPrintError: reportRuntimeError,")
    html_path.write_text(html)
    # A new entry point bypasses HTML cached by older installed workers.
    (directory / "play.html").write_text(html)
    worker_path = directory / (executable + ".service.worker.js")
    worker = worker_path.read_text()
    worker = re.sub(r"const CACHE_VERSION = '[^']+';", "const CACHE_VERSION = '" + revision + "';", worker)
    worker = worker.replace('"' + pack + '"', '"' + versioned_pack + '"')
    worker = worker.replace("cache.addAll(CACHED_FILES)", "cache.addAll(CACHED_FILES.map((file) => new Request(new URL(file, self.location.href), {cache: 'reload'}))).then(() => self.skipWaiting())")
    activate_marker = "// Enable navigation preload if available."
    if activate_marker not in worker or "self.skipWaiting()" not in worker:
        raise ValueError("Unexpected exported Godot worker format")
    worker = worker.replace("return ('navigationPreload' in self.registration) ? self.registration.navigationPreload.enable() : Promise.resolve();", "return self.clients.claim().then(() => ('navigationPreload' in self.registration) ? self.registration.navigationPreload.enable() : Promise.resolve());")
    worker_path.write_text(worker)
    (directory / "preview-version.json").write_text(json.dumps({"revision": revision, "pack": versioned_pack}))
    print("VERSIONED_PREVIEW_READY", revision, versioned_pack)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", type=Path)
    parser.add_argument("revision")
    args = parser.parse_args()
    prepare(args.directory, args.revision)
