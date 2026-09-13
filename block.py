# -----------------------------------------------------------------------------
# Role: Implements the file content block runtime and UI contract.
# File Name: block.py
# Author: Alexandre EL
# Email: alex@hackinvent.com
# Created Date: 2024-08-25
# -----------------------------------------------------------------------------

from __future__ import annotations

from html import escape
from pathlib import Path
from typing import Any

from bloxsmith_app.block_api import (
    BlockDefinition,
    BlockRuntimeContext,
    BlockRuntimeOutput,
    BlockRuntimeResult,
    FileBlockError,
    FilePathBlockMixin,
    render_node_card_template,
)


# Functional behavior:
# FB1 - Use shared file path resolution and emit file contents instead of the path.
# FB2 - Read UTF-8 text files and mark .json files as application/json.
# FB3 - Optionally create a missing file through File behavior before reading.
# FB4 - Reject directories, unreadable encodings, binary/null-byte content, and missing files with explicit failures.
class FileContentBlock(FilePathBlockMixin, BlockDefinition):
    """Autonomous block implementation for `FileContentBlock`."""
    kind = "file_content"

    def ui_assets(self, surface: str = "modal") -> list[dict[str, str]]:
        """Return the file-content UI assets for both modal and inspector surfaces."""

        if surface in {"modal", "inspector_panel"}:
            return [
                {"kind": "css", "path": "assets/css/inspector_panel.css"},
                {"kind": "js", "path": "assets/js/inspector_panel.js"},
            ]
        return []

    def render_node_card(self, *, node: dict[str, Any], payload: dict[str, Any] | None = None) -> dict[str, Any]:
        """Render the File Content canvas card body from the block-owned template.

        Args:
            node: Serialized file-content node whose config contains the source path.
            payload: Optional server/UI rendering payload.

        Returns:
            Block UI payload used by the generic canvas shell.
        """

        config = self._ui_file_config(node)
        raw_config = node.get("config") if isinstance(node.get("config"), dict) else {}
        path = str(config.get("path") or "Aucun chemin")
        display_name = self._file_display_name(path)
        encoding = str(raw_config.get("encoding") or "utf-8")
        return render_node_card_template(
            block=self,
            node=node,
            node_classes=["file-content-node"],
            replacements={
                "title": node.get("title") or self.default_title(),
                "path": path,
                "path_label": display_name,
                "encoding": encoding,
            },
        )

    def _ui_hint(self) -> str:
        """Provide internal FileContentBlock behavior for `_ui_hint`."""
        return (
            "Le bloc lit le fichier comme du texte et émet son contenu complet sur la sortie. "
            "Si l'option est cochée, un fichier manquant est créé vide."
        )

    def render_modal(self, *, node: dict[str, Any], payload: dict[str, Any] | None = None) -> dict[str, Any]:
        """Render the modal with the same file path controls and browser as the inspector panel."""

        config = self._ui_file_config(node)
        template = (self.directory / "block_modal.html").read_text(encoding="utf-8")
        html = self._render_generic_modal_template(
            template=(
                template
                .replace(
                    "{{ path_browser_html }}",
                    self._render_file_path_browser(
                        config,
                        input_id=f"{node.get('id') or 'fileContent'}FileContentModalPathInput",
                    ),
                )
                .replace("{{ checked }}", "checked" if config.get("create_if_missing") else "")
                .replace("{{ hint }}", escape(self._ui_hint()))
                .replace("{{ config_fields_html }}", self._render_modal_technical_config_fields(node))
            ),
            node=node,
            payload=payload or {},
        )
        return {
            "html": html,
            "context": {
                "node_id": str(node.get("id") or ""),
                "node_kind": self.kind,
                "path": str(config.get("path") or ""),
                "create_if_missing": bool(config.get("create_if_missing")),
            },
        }

    def handle_ui_action(
        self,
        *,
        node: dict[str, Any],
        action: str,
        values: dict[str, Any],
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Handle file-content UI actions from the inspector or modal path editor."""

        if action in {"inspector_update_file", "modal_update_file"}:
            return self._apply_file_ui_update(values)
        if action in {"inspector_update_fields", "modal_update_fields"}:
            return self._handle_generic_ui_fields_update(values)
        return super().handle_ui_action(node=node, action=action, values=values, payload=payload)

    def read_content(self, *, root_dir: Path, config: dict[str, Any]) -> dict[str, Any]:
        """Read and return the configured file content for this block.

        Args:
            root_dir: Directory path used by the block runtime.
            config: Raw or normalized block configuration.
        """
        metadata = self.resolve(root_dir=root_dir, config=config)
        if not metadata.get("exists"):
            raise FileBlockError(f"Fichier introuvable: {metadata.get('path') or metadata.get('absolute_path')}")

        target_path = Path(str(metadata.get("absolute_path") or "")).expanduser()
        encoding = str(config.get("encoding") or "utf-8").strip() or "utf-8"
        try:
            content = target_path.read_text(encoding=encoding)
        except UnicodeDecodeError as exc:
            raise FileBlockError(
                f"Le fichier '{metadata.get('path')}' n'est pas lisible en texte avec l'encodage {encoding}."
            ) from exc

        if "\x00" in content:
            raise FileBlockError(f"Le fichier '{metadata.get('path')}' semble binaire.")

        return {
            **metadata,
            "content": content,
            "encoding": encoding,
            "content_type": self._content_type(target_path),
            "characters": len(content),
        }

    def _content_type(self, target_path: Path) -> str:
        """Provide internal FileContentBlock behavior for `_content_type`.

        Args:
            target_path: Filesystem path handled by the block.
        """
        if target_path.suffix.lower() == ".json":
            return "application/json"
        return "text/plain"

    def execute_runtime(self, context: BlockRuntimeContext) -> BlockRuntimeResult:
        """Execute the block through the generic runtime context and return runtime outputs.

        Args:
            context: Generic runtime context injected by the execution engine.
        """
        metadata = self.read_content(root_dir=context.root_dir, config=context.config)
        content = str(metadata.get("content") or "")
        content_type = str(metadata.get("content_type") or "text/plain")
        display_path = str(metadata.get("path") or metadata.get("absolute_path") or "")
        created = bool(metadata.get("created"))
        outputs = [
            BlockRuntimeOutput(
                port_id=int(getattr(port, "id", 0) or 0),
                port_name=str(getattr(port, "name", "") or ""),
                value=content,
                content_type=content_type,
            )
            for port in context.output_ports
        ]
        prefix = "[file-content-created]" if created else "[file-content]"
        return BlockRuntimeResult(
            status="success",
            outputs=outputs,
            logs=[f"{prefix} {context.node_id} -> {len(content)} caractere(s) depuis {display_path}"],
            last_message=content,
            content_type=content_type,
            worker_received=f"{display_path} ({len(content)} caracteres)",
            metadata={"file": {key: value for key, value in metadata.items() if key != "content"}},
        )
