"""Local HTTP integration using the existing real export, never a synthetic game."""

import http.client
import json
import os
from pathlib import Path
import threading

import pytest

from basketball_tactics.preview import create_server

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def export_dir():
    supplied = os.environ.get("SPORTVU_EXPORT")
    root = Path(supplied) if supplied else ROOT / "outputs/s1-event-2"
    if not (root / "manifest.json").is_file():
        if supplied:
            pytest.fail("SPORTVU_EXPORT does not contain manifest.json")
        pytest.skip("Real local export missing; see docs/local-viewer.md")
    return root


@pytest.fixture(scope="module")
def server(export_dir):
    with create_server(export_dir, port=0) as instance:
        thread = threading.Thread(target=instance.serve_forever, daemon=True)
        thread.start()
        yield instance
        instance.shutdown()
        thread.join(timeout=5)


def request(server, path, method="GET", host=None):
    connection = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=5)
    try:
        connection.request(method, path, headers={"Host": host} if host else {})
        response = connection.getresponse()
        return response.status, dict(response.getheaders()), response.read()
    finally:
        connection.close()


def test_real_export_routes_and_head(server):
    assert server.server_address[0] == "127.0.0.1"
    for path in ["/", "/styles.css", "/app.mjs", "/model.mjs"]:
        status, headers, content = request(server, path)
        assert status == 200 and content
        assert headers["Cache-Control"] == "no-store"
        assert headers["X-Content-Type-Options"] == "nosniff"
    status, _, body = request(server, "/data/manifest.json")
    assert status == 200
    manifest = json.loads(body)
    entry = next(c for c in manifest["clips"] if c["clip_id"] == "0021500476-e2-s001")
    status, _, body = request(server, "/data/" + entry["path"])
    clip = json.loads(body)
    assert status == 200 and clip["provenance"]["is_synthetic"] is False
    assert len(clip["frames"]) == 525
    status, headers, body = request(server, "/data/" + entry["path"], method="HEAD")
    assert status == 200 and int(headers["Content-Length"]) > 0 and body == b""


@pytest.mark.parametrize("path", ["/.git/config", "/.env", "/.tools/sportvu-review/0021500476.json",
                                  "/data/../manifest.json", "/data/%2e%2e/.env", "/data/clips/other.json"])
def test_unlisted_resources_not_exposed(server, path):
    assert request(server, path)[0] == 404


def test_untrusted_host_not_allowed(server):
    assert request(server, "/data/manifest.json", host="example.com")[0] == 403


def test_manifest_path_traversal_rejected(export_dir, tmp_path):
    manifest = json.loads((export_dir / "manifest.json").read_text(encoding="utf-8"))
    # Fault injection into real metadata; this directory is never shown as a real game.
    manifest["clips"][0]["path"] = "../private.json"
    (tmp_path / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ValueError, match="unsafe"):
        create_server(tmp_path, port=0)
