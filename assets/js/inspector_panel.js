/**
 * Role: Mounts the file content block frontend asset.
 * File Name: inspector_panel.js
 * Author: Alexandre EL
 * Email: alex@hackinvent.com
 * Created Date: 2024-07-19
 */
/**
 * Bind File Content path persistence while the shared CWPathBrowser owns
 * directory browsing and file selection.
 *
 * @param {HTMLElement} root - Mounted modal or inspector root.
 * @param {object} api - Generic block UI API exposing block actions.
 * @param {object} options - Action name and success log for the surface.
 */
function mountFileContentEditor(root, api, { actionName = "inspector_update_file", successMessage = "[file-content] Configuration appliquee." } = {}) {
  const pathInput = root.querySelector("[data-file-path]");
  const createInput = root.querySelector("[data-file-create-if-missing]");
  const applyButton = root.querySelector("[data-file-apply]");
  let dirty = false;

  /**
   * Toggle pending-change state and keep the Apply button in sync.
   *
   * @param {boolean} value - Whether unsaved file-content settings exist.
   */
  const setDirty = (value) => {
    dirty = Boolean(value);
    if (applyButton) {
      applyButton.disabled = !dirty;
    }
  };

  /**
   * Persist the File Content path config for the current UI surface.
   *
   * @returns {Promise<void>} Completes after the block action finishes.
   */
  const apply = async () => {
    if (!pathInput || !dirty) {
      return;
    }
    if (applyButton) {
      applyButton.disabled = true;
    }
    try {
      await api.applyAction(actionName, {
        path: pathInput.value || "",
        create_if_missing: Boolean(createInput?.checked),
      });
      setDirty(false);
      api.log?.(successMessage);
    } catch (error) {
      setDirty(true);
      api.log?.(`[error] Mise à jour Fichier contenu impossible: ${error.message}`);
    }
  };

  /**
   * Mark the path/create option as edited after user input.
   */
  const markEdited = () => setDirty(true);

  pathInput?.addEventListener("input", markEdited);
  pathInput?.addEventListener("change", markEdited);
  pathInput?.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      void apply();
    }
  });
  createInput?.addEventListener("change", markEdited);
  applyButton?.addEventListener("click", () => {
    void apply();
  });
}

/**
 * Mount the File Content inspector panel bindings.
 *
 * @param {HTMLElement} root - Mounted File Content inspector root.
 * @param {object} api - Generic block UI API exposing block actions.
 * @param {object} context - Optional render context from the block UI host.
 */
export function mount(root, api, context = {}) {
  mountFileContentEditor(root, api, {
    actionName: "inspector_update_file",
    successMessage: "[file-content] Configuration appliquee.",
  });
}
registry.file_content = {
  /**
   * Mount the File Content modal bindings using the modal update action.
   *
   * @param {HTMLElement} root - Mounted File Content modal root.
   * @param {object} api - Generic block UI API exposing block actions.
   * @param {object} context - Optional render context from the block UI host.
   */
  mount(root, api, context = {}) {
    mountFileContentEditor(root, api, {
      actionName: "modal_update_file",
      successMessage: "[file-content] Configuration modale appliquee.",
    });
  },
};
