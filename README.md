# File Content Block

<!-- block-metadata:start -->
[![Block version: 0.1.0](https://img.shields.io/badge/block-0.1.0-blue)](model.json)
[![BloxSmith compatibility: 1.0.9](https://img.shields.io/badge/BloxSmith-1.0.9-brightgreen)](compatibility.json)
[![License: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-blue)](LICENSE)

Verified BloxSmith versions: **1.0.9** (bundled-block tests; see [test evidence](compatibility.json)).
<!-- block-metadata:end -->


## Role

`file_content` is a source block that reads a file and emits its content. It uses the shared file-path helpers exposed by the framework and publishes the file body rather than the path.

Use it when the workflow needs the text body itself, for example to feed a prompt, transform JSON, display a document, or pass file content into a Python block.

## Files

- `block.py`: content reading, content-type detection, and runtime emission.
- `model.json`: default path, encoding, and output port declaration.
- `block_modal.html`, `inspector_panel.html`, `assets/`: file-content path editor, browser, modal, and inspector UI.
- `node_card.html`: block-owned canvas card body.

## Ports

- Outputs:
  - `contenu` (`id: 1`): emits `message/*`, `text/plain`, or `application/json`.

The block has no inputs.

## Configuration

- `path`: relative or absolute file path.
- `create_if_missing`: creates an empty file before reading when enabled.
- `encoding`: text encoding used to read the file, defaulting to `utf-8`.

## Runtime Behavior

`execute_runtime()` reads the configured file and emits the content on every output. JSON-looking files or JSON extensions are emitted as `application/json`; other content is emitted as `text/plain`.

## Example

Set `path` to `./input.json` and connect the output to a Python block. At runtime, this block reads the file as UTF-8 and emits the JSON text with content type `application/json`.

## UI Behavior

The block reuses the file inspector pattern with copy tailored to content reading. Inspector values
come only from canonical `node.config`.
It edits the path and creation flag only when the user clicks **Apply**. The **Browse** button
uses the shared `CWPathBrowser` control and calls `/api/blocks/file_content/browse-files` directly
to list files without adding file-content-specific behavior to the shared frontend shell.
The modal mirrors the inspector file controls, including the same browser, so users can pick and
apply a file path from either surface.

## Editor Display

The canvas card is rendered by this block through `node_card.html`. It shows only the file name plus
the encoding to keep the fixed node card compact; the full configured path remains available as the
preview tooltip. The shared editor shell keeps ports, dragging, status, and graph links generic.

## Limits

This block reads the full file into memory. It rejects directories, missing files unless creation is enabled, unreadable encodings, and binary-looking content containing null bytes. Use `file` when downstream blocks only need the path.

## Modal

`block_modal.html` is owned by this block. It keeps generic title/config bindings for shared fields,
and adds the same path, creation flag, and browser controls as the inspector.

## Maintenance Notes

File path resolution is shared through the framework-facing `bloxsmith_app.block_api` helpers; this block no longer imports or inherits another block implementation.

## Compatibility policy

[compatibility.json](compatibility.json) records HackInvent's verified BloxSmith versions and test evidence. Only the versions listed above have been verified, using the block-owned suites in a **bundled-block test installation**. This is not a certification of managed-package installation, every browser/OS, or live provider availability. Other framework versions are unverified, not necessarily incompatible.

The block-version badge follows `model.json`, not a published Git tag. `unversioned` means that no block release version is declared; no number is inferred from the framework version. The framework still uses `model.json` for its runtime/install contract; the tester-owned JSON does not replace it. Official integration tests run in the private `bloxmith-blocs` workspace. Test helpers and the proprietary framework are not bundled in this public block repository.
