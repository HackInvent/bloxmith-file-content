#!/usr/bin/env python3
# -----------------------------------------------------------------------------
# Role: Verifies file content block inspector panel API behavior.
# File Name: F8.09_file_content_block_inspector_panel_api.py
# Author: Alexandre EL
# Email: alex@hackinvent.com
# Created Date: 2026-05-11
# -----------------------------------------------------------------------------

"""F8.09 - FileContent block modular inspector panel and modal.

The test starts an isolated server, renders the block-owned inspector panel and
modal, verifies declared assets, then applies the structured path update action.
No user workspace data is touched.
"""

# Test cases:
# - FileContent UI - Render the inspector panel through the block API.
# - FileContent UI - Render the modal with the same file path and browser controls as the inspector.
# - FileContent UI - Apply structured path/create-if-missing updates.
# - FileContent UI - Verify inspector assets and node-card HTML are served by the block package.

from __future__ import annotations

from urllib.parse import quote
from urllib.request import urlopen

from ui_smoke_common import expect, http_json, isolated_server
from block_test_packages import install_test_package, release_key, surface_payload


def main() -> None:
    with isolated_server() as server:
        # Surfaces are release assets: a bundled kind serves none of them.
        model = install_test_package(server, "file_content")
        key = quote(release_key(model), safe="")
        served = lambda payload, suffix: next(
            asset["path"] for asset in payload["assets"] if asset["path"].endswith(suffix))
        node = {
            "id": "file-content-1",
            "kind": "file_content",
            "type": "file_content",
            "block_version": model["version"],
            "title": "Fichier Contenu",
            "config": {"path": "exports/source.json", "create_if_missing": True, "encoding": "utf-8"},
        }
        rendered = surface_payload(server, model, node, "inspector_panel")
        html = str(rendered.get("html") or "")
        expect("data-file-inspector-root" in html, "The file_content inspector HTML must come from the block.")
        expect("data-file-path" in html, "The file_content inspector panel must contain the path field.")
        expect("data-file-apply" in html, "The file_content inspector panel must expose the Apply button.")
        expect("data-path-browser" in html, "The file_content inspector panel must use the shared path browser.")
        expect("data-path-browser-panel" in html, "The file_content inspector panel must expose the block-owned file browser.")
        expect("exports/source.json" in html, "The file_content inspector panel must read node.config.path.")
        expect("checked" in html, "The file_content inspector panel must read node.config.create_if_missing.")
        expect("The block reads the file as text" in html, "The file_content inspector panel must show its hint.")
        assets = rendered.get("assets") or []

        for asset_path in ("assets/css/inspector_panel.css", "assets/js/inspector_panel.js"):
            with urlopen(f"{server.base_url}/api/blocks/{key}/assets/{served(rendered, asset_path)}", timeout=5) as response:
                body = response.read().decode("utf-8")
            expect("file" in body.lower(), f"Asset inspecteur file_content non servi: {asset_path}")
            if asset_path.endswith(".js"):
                expect("export function mount" in body, "The file_content JS must also mount the block-owned modal.")

        modal = surface_payload(server, model, node, "modal")
        modal_html = str(modal.get("html") or "")
        expect("data-file-modal-root" in modal_html, "The file_content modal must come from the block.")
        expect("data-block-title-field" in modal_html, "The file_content modal must keep the generic title field.")
        expect("data-file-path" in modal_html, "The file_content modal must expose the same path field as the inspector.")
        expect("data-path-browser" in modal_html, "The file_content modal must use the shared path browser.")
        expect("data-path-browser-panel" in modal_html, "The file_content modal must expose the file browser.")
        expect("data-file-apply" in modal_html, "The file_content modal must expose a file Apply button.")
        expect("exports/source.json" in modal_html, "The file_content modal must read node.config.path.")
        expect("data-block-config-field=\"encoding\"" in modal_html, "The file_content modal must keep the technical attributes.")
        modal_assets = modal.get("assets") or []

        source = server.root_dir / "exports" / "source.json"
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_text("{}", encoding="utf-8")
        browser = http_json(server.base_url, f"/api/blocks/file_content/browse-files?path={quote('exports/source.json')}")
        entries = browser.get("entries") or []
        expect(
            any(entry.get("name") == "source.json" for entry in entries),
            "The file_content file browser must be served by /api/blocks/file_content/browse-files.",
        )

        card = surface_payload(server, model, node, "node_card")
        card_html = str(card.get("html") or "")
        expect("data-file-content-node-card" in card_html, "The file_content card must come from the block.")
        expect("source.json" in card_html, "The file_content card must show only the file name.")
        expect(">exports/source.json<" not in card_html, "The file_content card must not show the full path.")
        expect('title="exports/source.json"' in card_html, "The file_content card must keep the full path as a tooltip.")

        applied = http_json(
            server.base_url,
            "/api/blocks/file_content/ui-action",
            method="POST",
            payload={
                "node": node,
                "action": "inspector_update_file",
                "values": {"path": "exports/updated.json", "create_if_missing": False},
            },
        )
        file_patch = applied.get("node_patch", {}).get("config")
        expect(
            file_patch == {"path": "exports/updated.json", "create_if_missing": False},
            "The file_content update must return the expected file patch.",
        )
        expect(applied.get("rerender_inspector") is False, "Typing in file_content must not force a rerender.")

        modal_applied = http_json(
            server.base_url,
            "/api/blocks/file_content/ui-action",
            method="POST",
            payload={
                "node": node,
                "action": "modal_update_file",
                "values": {"path": "exports/modal.json", "create_if_missing": True},
            },
        )
        modal_file_patch = modal_applied.get("node_patch", {}).get("config")
        expect(
            modal_file_patch == {"path": "exports/modal.json", "create_if_missing": True},
            "The file_content modal update must return the expected file patch.",
        )

        modal_fields = http_json(
            server.base_url,
            "/api/blocks/file_content/ui-action",
            method="POST",
            payload={
                "node": node,
                "action": "modal_update_fields",
                "values": {"node_patch": {"config": {"encoding": "latin-1"}}},
            },
        )
        expect(
            modal_fields.get("node_patch", {}).get("config") == {"encoding": "latin-1"},
            "The file_content modal must keep the generic bindings of its technical attributes.",
        )
    print("[ok] F8.09_file_content_block_inspector_panel_api")


if __name__ == "__main__":
    main()
