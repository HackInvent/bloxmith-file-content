#!/usr/bin/env python3
# -----------------------------------------------------------------------------
# Role: Verifies file content block behavior.
# File Name: F5.15_file_content_block.py
# Author: Alexandre EL
# Email: alex@hackinvent.com
# Created Date: 2024-10-01
# -----------------------------------------------------------------------------

"""F5.15 - FileContent block direct runtime behavior.

The test calls FileContentBlock directly against isolated temporary files. It
verifies text/json content emission without depending on user workspace data.
"""

# Test cases:
# - FB1/FB2 - Read a UTF-8 text file and verify text/plain output content.
# - FB1/FB2 - Read a JSON file and verify application/json content type is preserved.
# - FB3 - Create a missing file when configured, then read its empty content.
# - FB4 - Attempt to read a missing file without creation and verify a block failure.

from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace

from ui_smoke_common import expect
from bloxsmith_app.block_api import FileBlockError
from blocs.file_content.block import FileContentBlock
from bloxsmith_app.block_runtime import BlockRuntimeContext


def context(root: Path, config: dict) -> BlockRuntimeContext:
    return BlockRuntimeContext(
        run_id="test-run",
        node_id="file-content-1",
        kind="file_content",
        title="File Content",
        config=config,
        inputs={},
        input_content_types={},
        input_message="",
        input_ports=(),
        output_ports=(SimpleNamespace(id=1, name="contenu"),),
        root_dir=root,
    )


def main() -> None:
    with TemporaryDirectory(prefix="bloxsmith-file-content-test-") as tmp:
        root = Path(tmp)
        text_path = root / "input.txt"
        text_path.write_text("hello file content", encoding="utf-8")
        block = FileContentBlock()

        text_result = block.execute_runtime(context(root, {"path": "input.txt"}))
        expect(text_result.status == "success", "Text file read must succeed.")
        expect(text_result.outputs[0].value == "hello file content", "Text file content mismatch.")
        expect(text_result.outputs[0].content_type == "text/plain", "Text file content type must be text/plain.")

        json_path = root / "input.json"
        json_path.write_text('{"hello": true}', encoding="utf-8")
        json_result = block.execute_runtime(context(root, {"path": "input.json"}))
        expect(json_result.status == "success", "JSON file read must succeed.")
        expect(json_result.outputs[0].content_type == "application/json", "JSON file content type must be application/json.")

        created_result = block.execute_runtime(context(root, {"path": "created.txt", "create_if_missing": True}))
        expect(created_result.status == "success", "Missing file creation must succeed when configured.")
        expect((root / "created.txt").is_file(), "FileContent must create the missing file through File behavior.")
        expect(created_result.outputs[0].value == "", "Newly created FileContent file must emit empty content.")

        try:
            block.execute_runtime(context(root, {"path": "missing.txt", "create_if_missing": False}))
        except FileBlockError as exc:
            expect("introuvable" in str(exc).lower(), "Missing file error must be explicit.")
        else:
            raise AssertionError("Missing file without creation must raise FileBlockError.")
    print("[ok] F5.15_file_content_block")


if __name__ == "__main__":
    main()
