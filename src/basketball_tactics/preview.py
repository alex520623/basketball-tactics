"""Loopback-only viewer for an existing export; never serve the project root."""

import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import re
import shutil
import sys
from urllib.parse import urlsplit


def create_server(data_dir: Path | str, port: int = 8000) -> ThreadingHTTPServer:
    root = Path(data_dir).resolve(strict=True)
    if not root.is_dir():
        raise ValueError("data-dir must be an existing Backend export directory")
    manifest_path = root / "manifest.json"
    if manifest_path.is_symlink():
        raise ValueError("Manifest must be a regular file within data-dir")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("schema_version") != "0.2.0" or not isinstance(manifest.get("clips"), list) or not manifest["clips"]:
        raise ValueError("Export must have a nonempty JSON 0.2.0 manifest")
    assets = Path(__file__).resolve().parents[2] / "frontend"
    routes = {"/": (assets / "index.html", "text/html; charset=utf-8"),
              "/styles.css": (assets / "styles.css", "text/css; charset=utf-8"),
              "/app.mjs": (assets / "app.mjs", "text/javascript; charset=utf-8"),
              "/model.mjs": (assets / "model.mjs", "text/javascript; charset=utf-8"),
              "/data/manifest.json": (manifest_path, "application/json; charset=utf-8")}
    ids, paths = set(), set()
    for entry in manifest["clips"]:
        cid, relative = entry.get("clip_id"), entry.get("path")
        if (not isinstance(cid, str) or not re.fullmatch(r"[A-Za-z0-9_-]+", cid) or cid in ids
                or not isinstance(relative, str) or not re.fullmatch(r"clips/[A-Za-z0-9_-]+\.json", relative)
                or relative in paths):
            raise ValueError("Manifest contains duplicate IDs or unsafe clip paths")
        ids.add(cid)
        paths.add(relative)
        path = (root / relative).resolve(strict=True)
        if not path.is_relative_to(root):
            raise ValueError("Clip resolves outside data-dir")
        routes["/data/" + relative] = path, "application/json; charset=utf-8"
    for path, _ in routes.values():
        if not path.is_file() or path.stat().st_size > 10 * 1024 * 1024:
            raise ValueError(f"Preview file missing or exceeds the 10 MiB limit: {path.name}")

    class Handler(BaseHTTPRequestHandler):
        def do_HEAD(self):
            self._respond(head_only=True)

        def do_GET(self):
            self._respond(head_only=False)

        def _respond(self, head_only):
            allowed_hosts = {f"127.0.0.1:{self.server.server_port}", f"localhost:{self.server.server_port}"}
            if self.headers.get("Host") not in allowed_hosts:
                self.send_error(403, "Loopback host required")
                return
            route = urlsplit(self.path).path
            if route == "/favicon.ico":
                self.send_response(204)
                self.end_headers()
                return
            if route not in routes:
                self.send_error(404, "Preview resource not found")
                return
            path, content_type = routes[route]
            try:
                # Re-resolve on each request so a changed symlink cannot expose another folder.
                resolved = path.resolve(strict=True)
                boundary = root if route.startswith("/data/") else assets.resolve()
                if not resolved.is_relative_to(boundary):
                    self.send_error(403, "Resource outside preview directory")
                    return
                with resolved.open("rb") as stream:
                    self.send_response(200)
                    self.send_header("Content-Type", content_type)
                    self.send_header("Content-Length", str(resolved.stat().st_size))
                    self.send_header("Cache-Control", "no-store")
                    self.send_header("X-Content-Type-Options", "nosniff")
                    self.end_headers()
                    if not head_only:
                        shutil.copyfileobj(stream, self.wfile, length=64 * 1024)
            except FileNotFoundError:
                self.send_error(404, "Preview resource missing")
            except (BrokenPipeError, ConnectionResetError):
                pass

    return ThreadingHTTPServer(("127.0.0.1", port), Handler)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Open an existing S1 export in a local browser viewer")
    parser.add_argument("--data-dir", type=Path, default=Path("outputs/s1-event-2"))
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args(argv)
    try:
        with create_server(args.data_dir, args.port) as server:
            print(f"Local preview: http://127.0.0.1:{server.server_port}/", flush=True)
            print("Only viewer assets and this export are served. Press Ctrl+C to stop.", flush=True)
            server.serve_forever()
    except KeyboardInterrupt:
        return 0
    except (OSError, ValueError, TypeError, KeyError) as exc:
        print(f"Preview failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
