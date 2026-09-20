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
        expect("data-file-inspector-root" in html, "Le HTML inspecteur file_content doit venir du bloc.")
        expect("data-file-path" in html, "Le panneau inspecteur file_content doit contenir le champ chemin.")
        expect("data-file-apply" in html, "Le panneau inspecteur file_content doit exposer le bouton Appliquer.")
        expect("data-path-browser" in html, "Le panneau inspecteur file_content doit utiliser le path browser commun.")
        expect("data-path-browser-panel" in html, "Le panneau inspecteur file_content doit exposer le navigateur fichier owned par le bloc.")
        expect("exports/source.json" in html, "The file_content inspector panel must read node.config.path.")
        expect("checked" in html, "The file_content inspector panel must read node.config.create_if_missing.")
        expect("The block reads the file as text" in html, "The file_content inspector panel must show its hint.")
        assets = rendered.get("assets") or []

        for asset_path in ("assets/css/inspector_panel.css", "assets/js/inspector_panel.js"):
            with urlopen(f"{server.base_url}/api/blocks/{key}/assets/{served(rendered, asset_path)}", timeout=5) as response:
                body = response.read().decode("utf-8")
            expect("file" in body.lower(), f"Asset inspecteur file_content non servi: {asset_path}")
            if asset_path.endswith(".js"):
                expect("export function mount" in body, "Le JS file_content doit monter aussi le modal block-owned.")

        modal = surface_payload(server, model, node, "modal")
        modal_html = str(modal.get("html") or "")
        expect("data-file-modal-root" in modal_html, "Le modal file_content doit venir du bloc.")
        expect("data-block-title-field" in modal_html, "Le modal file_content doit conserver le champ titre générique.")
        expect("data-file-path" in modal_html, "Le modal file_content doit exposer le même champ chemin que l'inspector.")
        expect("data-path-browser" in modal_html, "Le modal file_content doit utiliser le path browser commun.")
        expect("data-path-browser-panel" in modal_html, "Le modal file_content doit exposer le navigateur fichier.")
        expect("data-file-apply" in modal_html, "Le modal file_content doit exposer un bouton Appliquer fichier.")
        expect("exports/source.json" in modal_html, "Le modal file_content doit lire node.config.path.")
        expect("data-block-config-field=\"encoding\"" in modal_html, "Le modal file_content doit conserver les attributs techniques.")
        modal_assets = modal.get("assets") or []

        source = server.root_dir / "exports" / "source.json"
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_text("{}", encoding="utf-8")
        browser = http_json(server.base_url, f"/api/blocks/file_content/browse-files?path={quote('exports/source.json')}")
        entries = browser.get("entries") or []
        expect(
            any(entry.get("name") == "source.json" for entry in entries),
            "Le navigateur fichier file_content doit etre servi par /api/blocks/file_content/browse-files.",
        )

        card = surface_payload(server, model, node, "node_card")
        card_html = str(card.get("html") or "")
        expect("data-file-content-node-card" in card_html, "La carte file_content doit venir du bloc.")
        expect("source.json" in card_html, "La carte file_content doit afficher uniquement le nom du fichier.")
        expect(">exports/source.json<" not in card_html, "La carte file_content ne doit pas afficher le chemin complet.")
        expect('title="exports/source.json"' in card_html, "La carte file_content doit conserver le chemin complet en tooltip.")

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
