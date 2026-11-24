/**
 * Magic Fill - Content Script
 * Scans web forms, extracts field metadata across all 10 input types,
 * executes browser-compatible autofill, applies dynamic green/red visual field status,
 * and enables consent-based memory learning.
 */

(() => {
  // Prevent duplicate script injection
  if (window.__MAGIC_FILL_INITIALIZED__) return;
  window.__MAGIC_FILL_INITIALIZED__ = true;

  // Seamlessly sync authentication token with extension background worker when on Magic Fill website
  try {
    const localTok = localStorage.getItem("magic_fill_token");
    if (localTok && chrome.runtime && chrome.runtime.id) {
      chrome.runtime.sendMessage({ action: "SYNC_TOKEN_FROM_PAGE", token: localTok });
    }
  } catch (e) {}

  const SENSITIVE_TYPES = new Set(["password", "hidden"]);

  // ---------------------------------------------------------------------------
  // 1. Dynamic Visual Status Styling (Green for Matched, Red for Missing)
  // ---------------------------------------------------------------------------
  function ensureStatusStyles() {
    if (document.getElementById("magic-fill-status-styles")) return;
    const style = document.createElement("style");
    style.id = "magic-fill-status-styles";
    style.textContent = `
      @keyframes magicFillSuccessPop {
        0% { transform: scale(0.985); box-shadow: 0 0 0 0 rgba(37, 99, 235, 0.45); }
        45% { transform: scale(1.012); box-shadow: 0 0 0 6px rgba(37, 99, 235, 0.28), 0 4px 12px rgba(37, 99, 235, 0.16); }
        100% { transform: scale(1); box-shadow: 0 0 0 3.5px rgba(37, 99, 235, 0.22), 0 2px 6px rgba(37, 99, 235, 0.1); }
      }
      @keyframes magicFillMissingPulse {
        0% { transform: scale(0.99); box-shadow: 0 0 0 0 rgba(225, 29, 72, 0.4); }
        50% { transform: scale(1.008); box-shadow: 0 0 0 5px rgba(225, 29, 72, 0.2); }
        100% { transform: scale(1); box-shadow: 0 0 0 3px rgba(225, 29, 72, 0.15); }
      }
      @keyframes magicFillSlideUp {
        from { opacity: 0; transform: translateY(6px); }
        to { opacity: 1; transform: translateY(0); }
      }
      [data-magic-fill-status="matched"] {
        border: 2px solid #2563EB !important;
        box-shadow: 0 0 0 3.5px rgba(37, 99, 235, 0.22), 0 2px 6px rgba(37, 99, 235, 0.1) !important;
        background-color: #EFF6FF !important;
        color: #0F172A !important;
        transition: border-color 0.25s ease, box-shadow 0.25s ease, background-color 0.25s ease !important;
        animation: magicFillSuccessPop 0.45s cubic-bezier(0.16, 1, 0.3, 1) !important;
      }
      [data-magic-fill-status="missing"] {
        border: 2px solid #E11D48 !important;
        box-shadow: 0 0 0 3px rgba(225, 29, 72, 0.18) !important;
        background-color: rgba(225, 29, 72, 0.05) !important;
        transition: border-color 0.35s ease, box-shadow 0.35s ease, background-color 0.35s ease !important;
        animation: magicFillMissingPulse 0.45s cubic-bezier(0.16, 1, 0.3, 1) !important;
      }
      .modern-radio-group[data-magic-fill-status="matched"],
      .modern-checkbox-wrap[data-magic-fill-status="matched"],
      fieldset[data-magic-fill-status="matched"] {
        border: 1px solid #2563EB !important;
        box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.15) !important;
        background-color: rgba(37, 99, 235, 0.04) !important;
      }
      .modern-radio-group[data-magic-fill-status="missing"],
      .modern-checkbox-wrap[data-magic-fill-status="missing"],
      fieldset[data-magic-fill-status="missing"] {
        border: 1px solid #E11D48 !important;
        box-shadow: 0 0 0 2px rgba(225, 29, 72, 0.15) !important;
        background-color: rgba(225, 29, 72, 0.03) !important;
      }
    `;
    (document.head || document.documentElement).appendChild(style);
  }

  /**
   * Applies dynamic green/red visual indicators based on stored data availability.
   */
  function applyFieldVisualStatus(mappings = [], unresolvedFields = []) {
    ensureStatusStyles();

    // Clear existing indicators
    document.querySelectorAll("[data-magic-fill-status]").forEach((el) => {
      el.removeAttribute("data-magic-fill-status");
    });

    const matchedIds = new Set();
    mappings.forEach((m) => {
      matchedIds.add(m.field_id);
      const el = document.querySelector(`[data-magic-fill-id="${CSS.escape(m.field_id)}"]`);
      if (el) {
        el.setAttribute("data-magic-fill-status", "matched");
        const wrap = el.closest(".modern-radio-group, .modern-checkbox-wrap, .toggle-switch-wrap, .modern-range-wrap, .portal-file-cell, fieldset");
        if (wrap) wrap.setAttribute("data-magic-fill-status", "matched");
        if (el.type === "radio" && el.name) {
          document.querySelectorAll(`input[type="radio"][name="${CSS.escape(el.name)}"]`).forEach((r) => {
            r.setAttribute("data-magic-fill-status", "matched");
          });
        }
      }
    });

    unresolvedFields.forEach((u) => {
      if (!matchedIds.has(u.field_id)) {
        const el = document.querySelector(`[data-magic-fill-id="${CSS.escape(u.field_id)}"]`);
        if (el) {
          el.setAttribute("data-magic-fill-status", "missing");
          const wrap = el.closest(".modern-radio-group, .modern-checkbox-wrap, .toggle-switch-wrap, .modern-range-wrap, .portal-file-cell, fieldset");
          if (wrap) wrap.setAttribute("data-magic-fill-status", "missing");
          if (el.type === "radio" && el.name) {
            document.querySelectorAll(`input[type="radio"][name="${CSS.escape(el.name)}"]`).forEach((r) => {
              r.setAttribute("data-magic-fill-status", "missing");
            });
          }
        }
      }
    });
  }

  // ---------------------------------------------------------------------------
  // 2. Comprehensive DOM Scanner (Supports all 10 input types & Google Forms)
  // ---------------------------------------------------------------------------
  function cleanLabelText(str) {
    if (!str) return "";
    return str
      .replace(/\s+/g, " ")
      .replace(/[\*\u204E\u2217\u2731]/g, "") // remove asterisks
      .replace(/\b(this is a required question|required question|required)\b/gi, "")
      .trim();
  }

  function isGenericPlaceholder(text) {
    if (!text) return true;
    const t = text.trim().toLowerCase();
    return /^(your answer|short answer|short answer text|long answer|long answer text|type your answer|enter answer|type here|enter text|write your answer|answer)$/i.test(t);
  }

  function getElementLabel(el) {
    // 1. Google Forms / Enterprise Job Portals Question Item Container Heading (Top priority: direct title)
    const questionContainer = el.closest(
      '[role="listitem"], .Qr7Oae, .geS5n, [jsmodel], .freebirdFormviewerViewNumberedItemContainer, .form-group, .field, .form-field, fieldset'
    );
    if (questionContainer) {
      const titleEl = questionContainer.querySelector(
        '[role="heading"], .M7eMe, .HoDAff, .freebirdFormviewerComponentsQuestionBaseTitle, div[aria-level], legend, label, .quantumWizTextinputPaperinputTitle'
      );
      if (titleEl && !titleEl.contains(el)) {
        const cleaned = cleanLabelText(titleEl.innerText || titleEl.textContent);
        if (cleaned && !isGenericPlaceholder(cleaned)) return cleaned;
      }
    }

    // 2. Check aria-labelledby (Handles space-separated IDs used by Google Forms, Microsoft Forms, ARIA)
    const labelledby = el.getAttribute("aria-labelledby");
    if (labelledby) {
      const ids = labelledby.trim().split(/\s+/);
      for (const id of ids) {
        try {
          const target = document.getElementById(id);
          if (target) {
            const raw = cleanLabelText(target.innerText || target.textContent);
            if (raw && !isGenericPlaceholder(raw)) {
              return raw;
            }
          }
        } catch (e) {}
      }
    }

    // 3. Explicit HTML <label for="id">
    if (el.id) {
      try {
        const labelEl = document.querySelector(`label[for="${CSS.escape(el.id)}"]`);
        if (labelEl) {
          const cleaned = cleanLabelText(labelEl.innerText || labelEl.textContent);
          if (cleaned && !isGenericPlaceholder(cleaned)) return cleaned;
        }
      } catch (e) {}
    }

    // 4. Direct aria-label
    const ariaLabel = el.getAttribute("aria-label");
    if (ariaLabel) {
      const cleaned = cleanLabelText(ariaLabel);
      if (cleaned && !isGenericPlaceholder(cleaned)) return cleaned;
    }

    // 5. Parent <label> element
    const parent = el.closest("label");
    if (parent) {
      const clone = parent.cloneNode(true);
      const child = clone.querySelector("input, select, textarea");
      if (child) child.remove();
      const txt = cleanLabelText(clone.innerText || clone.textContent);
      if (txt && !isGenericPlaceholder(txt)) return txt;
    }

    // 6. Preceding sibling label/span/p
    let prev = el.previousElementSibling;
    while (prev) {
      if (["LABEL", "SPAN", "P", "DIV", "H1", "H2", "H3", "H4", "H5", "H6"].includes(prev.tagName)) {
        const txt = cleanLabelText(prev.innerText || prev.textContent);
        if (txt && !isGenericPlaceholder(txt) && txt.length < 120) return txt;
      }
      prev = prev.previousElementSibling;
    }

    // 7. Check parent container previous element
    const parentContainer = el.parentElement;
    if (parentContainer && parentContainer.previousElementSibling) {
      const prevContainer = parentContainer.previousElementSibling;
      const heading = prevContainer.querySelector ? prevContainer.querySelector("label, span, div, [role='heading']") : null;
      const target = heading || prevContainer;
      const txt = cleanLabelText(target.innerText || target.textContent);
      if (txt && !isGenericPlaceholder(txt) && txt.length < 120) return txt;
    }

    // 8. Placeholder fallback ONLY if meaningful and not generic placeholder
    if (el.placeholder && !isGenericPlaceholder(el.placeholder)) {
      return cleanLabelText(el.placeholder);
    }

    // 9. Name attribute fallback (cleaning entry.123 or form field identifiers)
    if (el.name && !/^entry\.\d+$/i.test(el.name) && !/^input_\d+$/i.test(el.name)) {
      return el.name.replace(/[_\-\.]+/g, " ").trim();
    }

    return "";
  }

  function scanFormFields() {
    const selector = "input:not([type='button']):not([type='submit']):not([type='reset']):not([type='image']), select, textarea, [role='switch'], [role='radio'], [role='checkbox']";
    const rawElements = document.querySelectorAll(selector);
    const fields = [];
    const processedRadioGroups = new Set();
    let counter = 0;

    rawElements.forEach((el) => {
      // Exclude ignore-marked elements or elements inside buttons/nav/modals
      if (el.getAttribute && (el.getAttribute("data-magic-fill-ignore") === "true" || el.getAttribute("data-no-learn") === "true")) return;
      if (el.closest && el.closest("button, [role='button'], nav, header, #magic-fill-learning-prompt, #simPromptModal")) return;

      const type = (el.type || el.getAttribute("type") || "text").toLowerCase();
      if (SENSITIVE_TYPES.has(type) || type === "button" || type === "submit" || type === "reset") return;

      // Exclude hidden or non-interactive fields (allow file inputs which are standardly hidden/styled)
      const style = window.getComputedStyle(el);
      if (type !== "file") {
        if (style.display === "none" || style.visibility === "hidden" || el.disabled || el.readOnly) {
          return;
        }
      } else {
        if (el.disabled) return;
      }

      // Assign or retrieve unique Magic Fill DOM tracking ID
      let fieldId = el.getAttribute("data-magic-fill-id");
      if (!fieldId) {
        fieldId = `mf_${Date.now()}_${counter++}`;
        el.setAttribute("data-magic-fill-id", fieldId);
      }

      const labelText = getElementLabel(el);
      const tag = el.tagName.toLowerCase();

      // Radio Button Group Handling
      if (type === "radio") {
        if (el.name && processedRadioGroups.has(el.name)) return;
        if (el.name) processedRadioGroups.add(el.name);

        const radios = el.name
          ? Array.from(document.querySelectorAll(`input[type="radio"][name="${CSS.escape(el.name)}"]`))
          : [el];

        const options = radios.map((r) => {
          return getElementLabel(r) || r.value || "Option";
        });

        fields.push({
          field_id: fieldId,
          name: el.name || null,
          label: labelText || el.name || "Radio Group",
          placeholder: null,
          aria_label: el.getAttribute("aria-label") || null,
          input_type: "radio",
          tag_name: tag,
          options: options,
          value: el.value || null,
          checked: el.checked || false,
          role: el.getAttribute("role") || null,
        });
        return;
      }

      // Select Dropdown Options
      let options = null;
      if (tag === "select") {
        options = Array.from(el.options).map((opt) => opt.text.trim());
      }

      fields.push({
        field_id: fieldId,
        name: el.name || null,
        label: labelText ? labelText.trim() : null,
        placeholder: el.placeholder || null,
        aria_label: el.getAttribute("aria-label") || null,
        input_type: type,
        tag_name: tag,
        options: options,
        value: el.value || null,
        checked: el.checked || (el.getAttribute("aria-checked") === "true") || false,
        min: el.min || null,
        max: el.max || null,
        step: el.step || null,
        accept: el.accept || null,
        role: el.getAttribute("role") || null,
      });
    });

    return fields;
  }

  // ---------------------------------------------------------------------------
  // 3. Intelligent Autofill Execution across all 10 input types
  // ---------------------------------------------------------------------------
  // ---------------------------------------------------------------------------
  // 3. Intelligent Autofill Execution across all input types & file suggestions
  // ---------------------------------------------------------------------------
  function applyAutofill(mappings = []) {
    ensureStatusStyles();
    let filledCount = 0;
    const matchedFieldIds = new Set();

    mappings.forEach((mapping) => {
      const el = document.querySelector(`[data-magic-fill-id="${CSS.escape(mapping.field_id)}"]`);
      if (!el) return;

      matchedFieldIds.add(mapping.field_id);
      const tag = el.tagName.toLowerCase();
      const type = (el.type || el.getAttribute("type") || "text").toLowerCase();
      const role = (el.getAttribute("role") || "").toLowerCase();

      // 1. Dropdown Select Elements
      if (tag === "select") {
        let matched = false;
        const targetVal = String(mapping.value).toLowerCase().trim();

        for (let i = 0; i < el.options.length; i++) {
          const opt = el.options[i];
          const optVal = opt.value.toLowerCase().trim();
          const optText = opt.text.toLowerCase().trim();
          if (optVal === targetVal || optText === targetVal) {
            el.selectedIndex = i;
            matched = true;
            break;
          }
        }
        // Common gender abbreviations
        if (!matched && (targetVal === "male" || targetVal === "m")) {
          for (let i = 0; i < el.options.length; i++) {
            const optVal = el.options[i].value.toLowerCase().trim();
            const optText = el.options[i].text.toLowerCase().trim();
            if (optVal === "m" || optVal === "male" || optText === "m" || optText === "male") {
              el.selectedIndex = i;
              matched = true;
              break;
            }
          }
        } else if (!matched && (targetVal === "female" || targetVal === "f")) {
          for (let i = 0; i < el.options.length; i++) {
            const optVal = el.options[i].value.toLowerCase().trim();
            const optText = el.options[i].text.toLowerCase().trim();
            if (optVal === "f" || optVal === "female" || optText === "f" || optText === "female") {
              el.selectedIndex = i;
              matched = true;
              break;
            }
          }
        }
        // Common country synonyms
        if (!matched && (targetVal === "united states" || targetVal === "usa" || targetVal === "us")) {
          for (let i = 0; i < el.options.length; i++) {
            const optText = el.options[i].text.toLowerCase().trim();
            if (optText.includes("united states") || optText.includes("usa")) {
              el.selectedIndex = i;
              matched = true;
              break;
            }
          }
        }
        // Substring fallback
        if (!matched) {
          for (let i = 0; i < el.options.length; i++) {
            const optText = el.options[i].text.toLowerCase().trim();
            if (optText && (optText.includes(targetVal) || targetVal.includes(optText))) {
              el.selectedIndex = i;
              matched = true;
              break;
            }
          }
        }
        if (!matched && el.options.length > 0) {
          el.value = mapping.value;
        }
        el.dispatchEvent(new Event("input", { bubbles: true, composed: true }));
        el.dispatchEvent(new Event("change", { bubbles: true, composed: true }));

      // 2. Radio Buttons
      } else if (type === "radio" || role === "radio") {
        const targetVal = String(mapping.value).toLowerCase().trim();
        const container = el.closest('[role="radiogroup"], [role="listitem"], .Qr7Oae, .geS5n, fieldset') || document;
        const radios = el.name
          ? document.querySelectorAll(`input[type="radio"][name="${CSS.escape(el.name)}"]`)
          : Array.from(container.querySelectorAll('[role="radio"], input[type="radio"]'));

        radios.forEach((r) => {
          const rVal = (r.value || r.getAttribute("data-value") || "").toLowerCase().trim();
          const rLabel = (getElementLabel(r) || r.getAttribute("aria-label") || r.innerText || "").toLowerCase().trim();
          if (
            (rVal && (rVal === targetVal || targetVal.includes(rVal))) ||
            (rLabel && (rLabel.includes(targetVal) || targetVal.includes(rLabel))) ||
            (targetVal === "yes" && (rVal.includes("yes") || rLabel.includes("yes") || rVal === "1" || rVal === "true")) ||
            (targetVal === "no" && (rVal.includes("no") || rLabel.includes("no") || rVal === "0" || rVal === "false"))
          ) {
            r.checked = true;
            try { r.click(); } catch (e) {}
            r.dispatchEvent(new Event("change", { bubbles: true, composed: true }));
          }
        });
        const groupWrap = el.closest(".modern-radio-group, fieldset, [role='radiogroup']");
        if (groupWrap) groupWrap.setAttribute("data-magic-fill-status", "matched");

      // 3. Checkboxes & Switches
      } else if (type === "checkbox" || role === "checkbox" || role === "switch") {
        const v = String(mapping.value).toLowerCase().trim();
        const isTrue = v === "yes" || v === "true" || v === "1" || mapping.value === true;
        el.checked = isTrue;
        if (role === "switch" || role === "checkbox") {
          el.setAttribute("aria-checked", isTrue ? "true" : "false");
          if (isTrue && el.getAttribute("aria-checked") !== "true") {
            try { el.click(); } catch (e) {}
          }
        }
        el.dispatchEvent(new Event("input", { bubbles: true, composed: true }));
        el.dispatchEvent(new Event("change", { bubbles: true, composed: true }));
        const checkWrap = el.closest(".modern-checkbox-wrap, .toggle-switch-wrap, label");
        if (checkWrap) checkWrap.setAttribute("data-magic-fill-status", "matched");

      // 4. Range Sliders
      } else if (type === "range") {
        const numVal = parseInt(String(mapping.value).replace(/[^\d.-]/g, ""), 10) || 0;
        el.value = numVal;
        const formWrap = el.closest("form") || document;
        const displayEl = formWrap.querySelector(`#expDisplay, #${CSS.escape(el.id)}Display, output[for="${CSS.escape(el.id)}"]`);
        if (displayEl) {
          displayEl.textContent = `${numVal} Years`;
        }
        el.dispatchEvent(new Event("input", { bubbles: true, composed: true }));
        el.dispatchEvent(new Event("change", { bubbles: true, composed: true }));

      // 5. Date Pickers (Standardized to strict ISO YYYY-MM-DD)
      } else if (type === "date") {
        let rawDate = String(mapping.value || "").trim();
        const isoMatch = rawDate.match(/(\d{4})[-\/.](\d{1,2})[-\/.](\d{1,2})/);
        const usMatch = rawDate.match(/(\d{1,2})[-\/.](\d{1,2})[-\/.](\d{4})/);
        if (isoMatch) {
          el.value = `${isoMatch[1]}-${String(isoMatch[2]).padStart(2, "0")}-${String(isoMatch[3]).padStart(2, "0")}`;
        } else if (usMatch) {
          el.value = `${usMatch[3]}-${String(usMatch[1]).padStart(2, "0")}-${String(usMatch[2]).padStart(2, "0")}`;
        } else {
          try {
            const parsed = new Date(rawDate);
            if (!isNaN(parsed.getTime())) {
              el.value = parsed.toISOString().split("T")[0];
            } else {
              el.value = rawDate;
            }
          } catch (e) {
            el.value = rawDate;
          }
        }
        el.dispatchEvent(new Event("input", { bubbles: true, composed: true }));
        el.dispatchEvent(new Event("change", { bubbles: true, composed: true }));

      // 6. Time Pickers (Standardized to strict HH:MM 24-hour format)
      } else if (type === "time") {
        let rawTime = String(mapping.value || "").trim();
        const match = rawTime.match(/(\d{1,2}):(\d{2})\s*(am|pm)?/i);
        if (match) {
          let hrs = parseInt(match[1], 10);
          const mins = match[2];
          const mer = (match[3] || "").toLowerCase();
          if (mer === "pm" && hrs < 12) hrs += 12;
          if (mer === "am" && hrs === 12) hrs = 0;
          el.value = `${String(hrs).padStart(2, "0")}:${mins}`;
        } else {
          el.value = rawTime;
        }
        el.dispatchEvent(new Event("input", { bubbles: true, composed: true }));
        el.dispatchEvent(new Event("change", { bubbles: true, composed: true }));

      // 7. Datetime-Local Pickers
      } else if (type === "datetime-local") {
        try {
          const parsed = new Date(String(mapping.value).trim());
          if (!isNaN(parsed.getTime())) {
            el.value = parsed.toISOString().slice(0, 16);
          }
        } catch (e) {}
        el.dispatchEvent(new Event("input", { bubbles: true, composed: true }));
        el.dispatchEvent(new Event("change", { bubbles: true, composed: true }));

      // 8. Color Pickers
      } else if (type === "color") {
        const hexMatch = String(mapping.value).match(/^#[0-9a-f]{6}/i);
        if (hexMatch) el.value = hexMatch[0];
        el.dispatchEvent(new Event("input", { bubbles: true, composed: true }));
        el.dispatchEvent(new Event("change", { bubbles: true, composed: true }));

      // 9. Document & Image File Uploads (REQUIREMENT 4: Show suggestion button, do NOT auto-attach)
      } else if (type === "file") {
        showFileAttachmentSuggestion(el, mapping);
        filledCount++;
        return;

      // 10. Text, Textarea, Email, Tel, URL, Number
      } else {
        try { el.focus(); } catch (e) {}
        try {
          const isTextArea = tag === "textarea";
          const proto = isTextArea ? window.HTMLTextAreaElement.prototype : window.HTMLInputElement.prototype;
          const desc = Object.getOwnPropertyDescriptor(proto, "value");
          if (desc && desc.set) {
            desc.set.call(el, mapping.value);
          } else {
            el.value = mapping.value;
          }
        } catch (e) {
          el.value = mapping.value;
        }

        try {
          el.setAttribute("data-initial-value", mapping.value);
          el.setAttribute("value", mapping.value);
        } catch (e) {}
      }

      // Mark as autofilled with green status and smooth animation
      el.setAttribute("data-magic-fill-autofilled", "true");
      el.setAttribute("data-magic-fill-status", "matched");

      if (el.type === "radio" && el.name) {
        document.querySelectorAll(`input[type="radio"][name="${CSS.escape(el.name)}"]`).forEach((r) => {
          r.setAttribute("data-magic-fill-status", "matched");
        });
      }

      // Dispatch comprehensive event sequence
      el.dispatchEvent(new Event("focus", { bubbles: true, composed: true }));
      el.dispatchEvent(new Event("beforeinput", { bubbles: true, composed: true }));
      el.dispatchEvent(new Event("input", { bubbles: true, composed: true }));
      el.dispatchEvent(new Event("change", { bubbles: true, composed: true }));
      try {
        el.dispatchEvent(new KeyboardEvent("keydown", { bubbles: true, composed: true, key: "Enter" }));
        el.dispatchEvent(new KeyboardEvent("keyup", { bubbles: true, composed: true, key: "Enter" }));
        el.dispatchEvent(new Event("blur", { bubbles: true, composed: true }));
      } catch (e) {}

      // Clean up Google Forms Material container error messages
      const gfContainer = el.closest(".quantumWizTextinputPaperinputEl, .o3G8cc, .nd91id, .geS5n, .Qr7Oae, [role='listitem'], .AgroD");
      if (gfContainer) {
        gfContainer.classList.add("is-filled", "has-value");
        gfContainer.classList.remove("is-invalid", "badInput");
        const errorAlerts = gfContainer.querySelectorAll(".RxsGPe, [role='alert'], .freebirdFormviewerViewItemsItemErrorMessage");
        errorAlerts.forEach((ea) => { ea.style.display = "none"; });
      }

      filledCount++;
    });

    // Mark remaining form elements that were NOT matched as missing (RED)
    const allInputs = document.querySelectorAll("input:not([type='submit']):not([type='reset']):not([type='button']), select, textarea");
    allInputs.forEach((input) => {
      const fieldId = input.getAttribute("data-magic-fill-id");
      if (fieldId && !matchedFieldIds.has(fieldId)) {
        input.setAttribute("data-magic-fill-status", "missing");
        const wrap = input.closest(".modern-radio-group, .modern-checkbox-wrap, .toggle-switch-wrap, .modern-range-wrap, .portal-file-cell, fieldset");
        if (wrap) wrap.setAttribute("data-magic-fill-status", "missing");
      }
    });

    return filledCount;
  }

  /**
   * REQUIREMENT 4: Interactive Suggestion Pill for Document & Image Uploads
   * Displays a small suggestion badge asking user for confirmation before attaching files.
   */
  function showFileAttachmentSuggestion(el, mapping) {
    if (!el) return;
    const existing = document.getElementById(`mf-file-sug-${mapping.field_id}`);
    if (existing) existing.remove();

    const label = (getElementLabel(el) || el.name || el.id || "").toLowerCase();
    const memKey = (mapping.memory_key || "").toLowerCase();

    let docType = "Document";
    let promptText = "Matching document found. Do you want to attach it?";
    let iconSvg = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline></svg>`;

    if (label.includes("photo") || label.includes("picture") || label.includes("avatar") || label.includes("image") || label.includes("headshot") || memKey.includes("photo")) {
      docType = "Profile picture";
      promptText = "Profile picture found. Do you want to attach it?";
      iconSvg = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><circle cx="12" cy="8" r="5"/><path d="M20 21a8 8 0 0 0-16 0"/></svg>`;
    } else if (label.includes("resume") || label.includes("cv") || memKey.includes("resume")) {
      docType = "Resume (PDF)";
      promptText = "Resume (PDF) found. Do you want to attach it?";
      iconSvg = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line></svg>`;
    } else if (label.includes("cert") || label.includes("diploma") || memKey.includes("cert")) {
      docType = "Certificate";
      promptText = "Certificate found. Do you want to attach it?";
      iconSvg = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><circle cx="12" cy="8" r="6"/><path d="M15.477 12.89 17 22l-5-3-5 3 1.523-9.11"/></svg>`;
    } else if (label.includes("cnic") || label.includes("identity") || label.includes("id card") || label.includes("passport") || memKey.includes("cnic")) {
      docType = "Identity document";
      promptText = "Identity document found. Do you want to attach it?";
      iconSvg = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><rect width="18" height="18" x="3" y="3" rx="2"/><circle cx="9" cy="9" r="2"/><path d="m21 15-3.086-3.086a2 2 0 0 0-2.828 0L6 21"/></svg>`;
    }

    const suggestion = document.createElement("div");
    suggestion.id = `mf-file-sug-${mapping.field_id}`;
    suggestion.className = "magic-fill-file-suggestion";
    suggestion.style.cssText = `
      display: inline-flex;
      align-items: center;
      gap: 10px;
      padding: 7px 12px;
      background: #FFFFFF;
      border: 1px solid #CBD5E1;
      border-radius: 10px;
      margin-top: 8px;
      font-family: 'Plus Jakarta Sans', -apple-system, sans-serif;
      font-size: 12px;
      color: #0F172A;
      box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
      animation: magicFillSlideUp 0.3s cubic-bezier(0.16, 1, 0.3, 1);
      z-index: 9999;
    `;
    suggestion.innerHTML = `
      <div style="color: #2563EB; display: flex; align-items: center; flex-shrink: 0;">${iconSvg}</div>
      <span style="color: #475569; line-height: 1.3;"><strong style="color: #0F172A;">${escapeHtml(promptText)}</strong></span>
      <div style="display: flex; align-items: center; gap: 6px; margin-left: 4px;">
        <button type="button" class="btn-attach-confirm" style="
          background: #2563EB;
          color: #FFFFFF;
          border: 1px solid #2563EB;
          border-radius: 6px;
          padding: 4px 11px;
          font-size: 11.5px;
          font-weight: 700;
          cursor: pointer;
          box-shadow: 0 1px 3px rgba(37, 99, 235, 0.2);
          transition: all 0.15s ease;
        ">Attach</button>
        <button type="button" class="btn-attach-dismiss" title="Dismiss" style="
          background: none;
          border: none;
          color: #64748B;
          font-size: 16px;
          cursor: pointer;
          line-height: 1;
          padding: 0 4px;
          transition: color 0.15s ease;
        ">&times;</button>
      </div>
    `;

    const confirmBtn = suggestion.querySelector(".btn-attach-confirm");
    const dismissBtn = suggestion.querySelector(".btn-attach-dismiss");

    confirmBtn.addEventListener("click", () => {
      confirmBtn.disabled = true;
      confirmBtn.textContent = "Attaching...";
      try {
        attachFileToInput(el, mapping);
        confirmBtn.style.background = "#2563EB";
        confirmBtn.style.color = "#FFFFFF";
        confirmBtn.textContent = "✓ Attached!";
        el.setAttribute("data-magic-fill-status", "matched");
        const wrap = el.closest(".form-input-group, .portal-file-cell, div");
        if (wrap) wrap.setAttribute("data-magic-fill-status", "matched");
        setTimeout(() => {
          suggestion.style.transition = "opacity 0.3s ease, transform 0.3s ease";
          suggestion.style.opacity = "0";
          suggestion.style.transform = "translateY(4px)";
          setTimeout(() => suggestion.remove(), 300);
        }, 1600);
      } catch (err) {
        confirmBtn.textContent = "Error";
        setTimeout(() => suggestion.remove(), 1200);
      }
    });

    dismissBtn.addEventListener("click", () => {
      suggestion.remove();
      el.setAttribute("data-magic-fill-status", "missing");
    });

    if (el.nextSibling) {
      el.parentNode.insertBefore(suggestion, el.nextSibling);
    } else {
      el.parentNode.appendChild(suggestion);
    }
  }

  function attachFileToInput(el, mapping) {
    const rawVal = String(mapping.value || "");
    if (!rawVal) return;

    let mime = "application/pdf";
    let base64Data = rawVal;
    if (rawVal.startsWith("data:")) {
      const mimeMatch = rawVal.match(/^data:([^;]+);base64,/);
      if (mimeMatch) mime = mimeMatch[1];
      base64Data = rawVal.includes(",") ? rawVal.split(",")[1] : rawVal;
    } else if (rawVal.startsWith("data:image")) {
      mime = "image/png";
    }

    const bstr = atob(base64Data);
    let n = bstr.length;
    const u8arr = new Uint8Array(n);
    while (n--) u8arr[n] = bstr.charCodeAt(n);

    let filename = "document.pdf";
    const label = (getElementLabel(el) || el.name || "").toLowerCase();
    const memKey = (mapping.memory_key || "").toLowerCase();
    if (mime.includes("png")) filename = "profile_picture.png";
    else if (mime.includes("jpeg") || mime.includes("jpg")) filename = "profile_picture.jpg";
    else if (label.includes("photo") || label.includes("picture") || memKey.includes("photo")) filename = "profile_picture.png";
    else if (mime.includes("pdf") || label.includes("resume") || memKey.includes("resume")) filename = "resume_cv.pdf";
    else if (label.includes("cert")) filename = "certificate.pdf";
    else if (label.includes("cnic")) filename = "cnic_document.jpg";

    const fileObj = new File([u8arr], filename, { type: mime, lastModified: Date.now() });
    if (window.DataTransfer) {
      const dt = new DataTransfer();
      dt.items.add(fileObj);
      el.files = dt.files;
      el.dispatchEvent(new Event("input", { bubbles: true, composed: true }));
      el.dispatchEvent(new Event("change", { bubbles: true, composed: true }));
    }

    const isImage = mime.startsWith("image/") || rawVal.startsWith("data:image");
    if (isImage) {
      let previewEl = document.getElementById(`mf-img-prev-${mapping.field_id}`);
      if (!previewEl) {
        previewEl = document.createElement("div");
        previewEl.id = `mf-img-prev-${mapping.field_id}`;
        previewEl.className = "magic-fill-preview-thumbnail";
        previewEl.style.cssText = "display:inline-flex; align-items:center; gap:10px; margin-top:8px; padding:6px 10px; background:#FFFFFF; border:1px solid #CBD5E1; border-radius:10px; font-family:'Plus Jakarta Sans',sans-serif; font-size:11.5px; color:#0F172A; box-shadow:0 2px 8px rgba(0,0,0,0.06);";
        const imgSrc = rawVal.startsWith("data:") ? rawVal : `data:${mime};base64,${base64Data}`;
        previewEl.innerHTML = `
          <img src="${imgSrc}" style="width:40px; height:40px; border-radius:8px; object-fit:cover; border:1px solid #E2E8F0; background:#F8FAFC;" alt="Attached preview" />
          <div>
            <span style="color:#2563EB; font-weight:700; display:block; font-size:11.5px;">✓ Attached from Memory</span>
            <span style="color:#64748B; font-size:11px; font-family:monospace;">${escapeHtml(filename)}</span>
          </div>
        `;
        if (el.nextSibling) {
          el.parentNode.insertBefore(previewEl, el.nextSibling);
        } else {
          el.parentNode.appendChild(previewEl);
        }
      }
    }
  }

  // ---------------------------------------------------------------------------
  // 4. Intelligent Form Learning & Memory Updates
  // ---------------------------------------------------------------------------
  const evaluatedFieldsCache = new Set();
  const fieldDebounceTimers = new Map();
  let isNewDataDetectionEnabled = true;

  // Initialize toggle state from chrome.storage.local
  try {
    if (chrome.storage && chrome.storage.local) {
      chrome.storage.local.get(["new_data_detection_enabled"], (items) => {
        if (items && typeof items.new_data_detection_enabled === "boolean") {
          isNewDataDetectionEnabled = items.new_data_detection_enabled;
        }
      });
    }
  } catch (e) {}

  // React immediately to toggle preference changes across all open tabs
  try {
    if (chrome.storage && chrome.storage.onChanged) {
      chrome.storage.onChanged.addListener((changes, area) => {
        if (area === "local" && changes.new_data_detection_enabled) {
          isNewDataDetectionEnabled = changes.new_data_detection_enabled.newValue !== false;
          if (!isNewDataDetectionEnabled) {
            // Dismiss active prompt immediately if detection was turned off
            const prompt = document.getElementById("magic-fill-learning-prompt");
            if (prompt) prompt.remove();
            // Clear pending debounce evaluation timers
            fieldDebounceTimers.forEach((timer) => clearTimeout(timer));
            fieldDebounceTimers.clear();
          }
        }
      });
    }
  } catch (e) {}

  function isExcludedField(el, label, val) {
    if (!el || !val) return true;
    const v = val.trim();
    if (v.length < 2 && !/^\d+$/.test(v)) return true;

    // Check if element or any ancestor explicitly opts out of Magic Fill auto-learning
    if (el.getAttribute && (el.getAttribute("data-magic-fill-ignore") === "true" || el.getAttribute("data-no-learn") === "true")) return true;
    if (el.closest && el.closest("[data-magic-fill-ignore='true'], [data-no-learn='true']")) return true;

    const tag = (el.tagName || "").toLowerCase();
    const type = (el.type || el.getAttribute("type") || "").toLowerCase();
    const role = (el.getAttribute("role") || "").toLowerCase();
    const id = (el.id || "").toLowerCase();
    const cls = (el.className || "").toString().toLowerCase();

    // Plain buttons, submit, reset, and action controls are NEVER form inputs to learn
    if ((tag === "button" || type === "button" || type === "submit" || type === "reset") && role !== "radio" && role !== "checkbox" && role !== "option") {
      return true;
    }

    // Reject buttons, action controls, submit, reset, simulator controls, and non-form elements
    if ((tag === "button" || type === "button" || type === "submit" || type === "reset") && role !== "radio" && role !== "checkbox" && role !== "option") {
      return true;
    }

    if (id.includes("simulate") || id.includes("clearform") || id.includes("resetform") || cls.includes("simulate") || cls.includes("toolbar") || cls.includes("btn") || id.includes("btn")) {
      if (role !== "radio" && role !== "checkbox" && role !== "option") {
        return true;
      }
    }

    // Any element inside a button, link, navigation bar, footer, or Magic Fill prompt dialogs
    if (el.closest && el.closest("button:not([role='radio']):not([role='checkbox']):not([role='option']), [role='button']:not([role='radio']):not([role='checkbox']):not([role='option']), a, nav, header, footer, #magic-fill-learning-prompt, #simPromptModal")) {
      return true;
    }

    // Reject UI action strings in value
    if (/matching fields|alt\+f|alt\+|simulate autofill|submitting|loading\.\.\./i.test(v)) {
      return true;
    }

    // Exclude document and file description textareas
    if (el.id === "mediaDescriptionInput" || el.name === "media_ai_description" || el.id === "rawTextInput" || el.id === "chatInput") {
      return true;
    }

    if (type === "submit" || type === "reset" || SENSITIVE_TYPES.has(type) || type === "search" || type === "color" || type === "file") {
      return true;
    }

    // Role check
    if (role === "search" || role === "searchbox") return true;

    const combinedDesc = `${el.name || ""} ${el.id || ""} ${label || ""} ${el.placeholder || ""} ${el.className || ""}`.toLowerCase();

    // Sensitive, auth, OTP, card credentials
    if (/(\b(password|passcode|pin|cvv|cvc|otp|2fa|mfa|token|secret|captcha|card_number|cardnumber)\b)/i.test(combinedDesc)) {
      return true;
    }

    // Search bars & query inputs
    if (/(\b(search|query|filter|keyword|find)\b)/i.test(combinedDesc)) {
      return true;
    }

    // Chat, conversation, prompts, comments, replies, reviews, support inquiry
    if (/(\b(chat|prompt|message|comment|reply|discussion|tweet|post_content|review|feedback|support|inquiry)\b)/i.test(combinedDesc)) {
      return true;
    }

    // Chat DOM container heuristic (e.g. ChatGPT, Claude, Discord, Intercom)
    if (el.closest && el.closest('[data-testid*="chat"], [aria-label*="chat"], [role="log"], [role="feed"], form[action*="chat"]')) {
      return true;
    }

    // Multi-line communication text in textareas (unless explicitly address or bio)
    if (el.tagName && el.tagName.toLowerCase() === "textarea" && (v.length > 200 || v.includes("\n"))) {
      if (!/address|street|bio|summary|about/i.test(combinedDesc)) {
        return true;
      }
    }

    // Placeholder text or generic junk
    if (/^(test|n\/a|none|placeholder|undefined|null|asdf)$/i.test(v)) {
      return true;
    }

    return false;
  }

  const TYPING_DEBOUNCE_MS = 1250;
  const fieldLastKeystrokeTime = new Map();

  function triggerFieldEvaluation(el, immediate = false, overrideVal = null, overrideLabel = null, isBlur = false) {
    if (!isNewDataDetectionEnabled) return;
    if (!el) return;
    const tag = (el.tagName || "").toLowerCase();
    const type = (el.type || el.getAttribute("type") || "text").toLowerCase();
    const role = (el.getAttribute("role") || "").toLowerCase();

    // Immediate early-exit for button actions unless specifically acting as an option/radio
    if ((tag === "button" || type === "button" || type === "submit" || type === "reset") && role !== "radio" && role !== "checkbox" && role !== "option") {
      return;
    }
    if (el.closest && el.closest("[data-magic-fill-ignore='true'], [data-no-learn='true']")) {
      return;
    }
    if (el.closest && el.closest("button:not([role='radio']):not([role='checkbox']):not([role='option']), [role='button']:not([role='radio']):not([role='checkbox']):not([role='option']), a, nav, header, footer, #magic-fill-learning-prompt, #simPromptModal")) {
      return;
    }

    // If edited by user, clear the autofill marker
    if (el.getAttribute && el.getAttribute("data-magic-fill-autofilled") === "true") {
      el.removeAttribute("data-magic-fill-autofilled");
    }

    let val = overrideVal !== null ? overrideVal : "";
    if (!val) {
      if (tag === "select") {
        val = el.options && el.selectedIndex >= 0 ? (el.options[el.selectedIndex]?.text?.trim() || el.options[el.selectedIndex]?.value?.trim()) : (el.value || "").trim();
      } else if (type === "checkbox" || role === "checkbox") {
        val = (el.checked || el.getAttribute("aria-checked") === "true") ? "Yes" : "No";
      } else if (type === "radio" || role === "radio") {
        val = el.value || el.getAttribute("data-value") || el.innerText?.trim() || "Yes";
      } else if (role === "option") {
        val = el.getAttribute("data-value") || el.innerText?.trim() || "";
      } else {
        val = (el.value || "").trim();
      }
    }

    const fieldKey = el.getAttribute("data-magic-fill-id") || el.name || el.id || "field";

    // If field is cleared or too short, cancel pending debounce timer and exit
    if (!val || (val.length < 2 && !/^\d+$/.test(val))) {
      if (fieldDebounceTimers.has(fieldKey)) {
        clearTimeout(fieldDebounceTimers.get(fieldKey));
        fieldDebounceTimers.delete(fieldKey);
      }
      return;
    }

    const label = overrideLabel || getElementLabel(el);
    if (isExcludedField(el, label, val)) return;

    const cacheKey = `${fieldKey}_${val.toLowerCase()}`;
    if (!isBlur && evaluatedFieldsCache.has(cacheKey)) return;

    const doEval = () => {
      // Re-verify that user has paused typing
      const lastKeystroke = fieldLastKeystrokeTime.get(fieldKey) || 0;
      if (!isBlur && Date.now() - lastKeystroke < (TYPING_DEBOUNCE_MS - 100)) {
        return;
      }
      evaluateFieldForLearning(el, label, val, cacheKey, isBlur);
    };

    if (immediate || isBlur) {
      if (fieldDebounceTimers.has(fieldKey)) {
        clearTimeout(fieldDebounceTimers.get(fieldKey));
        fieldDebounceTimers.delete(fieldKey);
      }
      doEval();
    } else {
      if (fieldDebounceTimers.has(fieldKey)) {
        clearTimeout(fieldDebounceTimers.get(fieldKey));
      }
      fieldDebounceTimers.set(fieldKey, setTimeout(doEval, TYPING_DEBOUNCE_MS));
    }
  }

  function handleUserInput(e) {
    if (!isNewDataDetectionEnabled) return;
    triggerFieldEvaluation(e.target, false);
  }

  function evaluateFieldForLearning(el, label, val, cacheKey, isBlur = false) {
    if (!isNewDataDetectionEnabled) {
      evaluatedFieldsCache.delete(cacheKey);
      return;
    }
    evaluatedFieldsCache.add(cacheKey);

    try {
      if (!chrome.runtime || !chrome.runtime.id) {
        evaluatedFieldsCache.delete(cacheKey);
        return;
      }

      let localTok = null;
      try {
        localTok = localStorage.getItem("magic_fill_token");
      } catch (e) {}

      chrome.runtime.sendMessage(
        {
          action: "EVALUATE_FIELD_FOR_LEARNING",
          token: localTok || null,
          field: {
            field_name: el.name || el.id || null,
            label: label || null,
            value: val,
            input_type: el.type || "text",
            placeholder: el.placeholder || null,
            page_title: document.title,
          },
        },
        (res) => {
          if (chrome.runtime.lastError) {
            evaluatedFieldsCache.delete(cacheKey);
            return;
          }
          if (!res || !res.success || !res.data || !res.data.is_learnable) {
            evaluatedFieldsCache.delete(cacheKey);
            return;
          }
          const evalData = res.data;

          // Prevent premature suggestions while user is actively typing or entered a prefix
          if (evalData.action_type === "UPDATE_ATTRIBUTE") {
            const savedNorm = (evalData.existing_value || "").trim().toLowerCase();
            const newNorm = (evalData.new_value || val || "").trim().toLowerCase();

            // 1. Equal: no prompt needed
            if (savedNorm === newNorm) {
              evaluatedFieldsCache.delete(cacheKey);
              return;
            }

            // 2. Focused on element and typing a prefix of saved value: suppress prompt
            if (document.activeElement === el && savedNorm.startsWith(newNorm)) {
              evaluatedFieldsCache.delete(cacheKey);
              return;
            }

            // 3. User blurred or paused, but entered value is an incomplete prefix: do not suggest overwriting
            if (savedNorm.startsWith(newNorm) && newNorm.length < savedNorm.length) {
              evaluatedFieldsCache.delete(cacheKey);
              return;
            }
          }

          showLearningPrompt(el, evalData, cacheKey);
        }
      );
    } catch (e) {
      evaluatedFieldsCache.delete(cacheKey);
    }
  }

  // 1. Live keystroke listener (debounced 1250ms per field)
  document.addEventListener("input", (e) => {
    const el = e.target;
    if (!el || !el.tagName) return;
    const tag = el.tagName.toLowerCase();
    const type = (el.type || "").toLowerCase();
    if (tag === "button" || type === "button" || type === "submit" || type === "reset") return;
    if (el.closest && el.closest("button, [role='button'], nav, header, footer, #magic-fill-learning-prompt, #simPromptModal, [data-magic-fill-ignore='true'], [data-no-learn='true']")) return;

    const fieldKey = el.getAttribute("data-magic-fill-id") || el.name || el.id || "field";
    fieldLastKeystrokeTime.set(fieldKey, Date.now());

    triggerFieldEvaluation(el, false, null, null, false);
  }, true);

  // 2. Native change event (fired on selects, radios, checkboxes on commit)
  document.addEventListener("change", (e) => {
    const el = e.target;
    if (!el || !el.tagName) return;
    const tag = el.tagName.toLowerCase();
    const type = (el.type || "").toLowerCase();
    if (tag === "button" || type === "button" || type === "submit" || type === "reset") return;
    if (el.closest && el.closest("button, [role='button'], nav, header, footer, #magic-fill-learning-prompt, #simPromptModal, [data-magic-fill-ignore='true'], [data-no-learn='true']")) return;

    // For standard text inputs, blur handles the final comparison
    if (tag === "input" && (type === "text" || type === "email" || type === "tel" || type === "url" || type === "number" || type === "")) {
      return;
    }
    triggerFieldEvaluation(el, true, null, null, false);
  }, true);

  // 3. Blur event: Field completion check (final comparison when user leaves the field)
  document.addEventListener("blur", (e) => {
    const el = e.target;
    if (!el || !el.tagName) return;
    const tag = el.tagName.toLowerCase();
    const type = (el.type || "").toLowerCase();
    if (tag === "button" || type === "button" || type === "submit" || type === "reset") return;
    if (el.closest && el.closest("button, [role='button'], nav, header, footer, #magic-fill-learning-prompt, #simPromptModal, [data-magic-fill-ignore='true'], [data-no-learn='true']")) return;

    triggerFieldEvaluation(el, true, null, null, true);
  }, true);

  // 4. Click event for custom dropdown options, radios, checkboxes, and choice buttons
  document.addEventListener("click", (e) => {
    const target = e.target;
    if (!target) return;

    // A. Option clicked in custom dropdown (Google Forms listbox, custom select, etc.)
    const option = target.closest('[role="option"], .select-option, [data-value]');
    if (option) {
      if (option.closest && option.closest("[data-magic-fill-ignore='true'], [data-no-learn='true'], nav, header, #magic-fill-learning-prompt, #simPromptModal")) return;
      const optionVal = (option.getAttribute("data-value") || option.innerText || "").trim();
      const container = option.closest('[role="combobox"], [role="listbox"], .form-group, [role="listitem"], .Qr7Oae') || option.parentElement;
      const label = getElementLabel(container) || getElementLabel(option);
      if (optionVal) {
        setTimeout(() => triggerFieldEvaluation(container || option, true, optionVal, label), 120);
      }
      return;
    }

    // B. Custom radio or checkbox widget clicked (Google Forms radio / check)
    const customWidget = target.closest('[role="radio"], [role="checkbox"], [role="switch"], .docssharedwizTogglelabeledContainer');
    if (customWidget) {
      if (customWidget.closest && customWidget.closest("[data-magic-fill-ignore='true'], [data-no-learn='true'], nav, header, #magic-fill-learning-prompt, #simPromptModal")) return;
      const radioContainer = customWidget.closest('[role="listitem"], .Qr7Oae, .geS5n, fieldset, .form-group') || customWidget.parentElement;
      const questionLabel = getElementLabel(radioContainer) || getElementLabel(customWidget);
      const valEl = customWidget.querySelector('.aDTYNe, .d7L4fc, label, span') || customWidget;
      const widgetVal = (customWidget.getAttribute("data-value") || valEl.innerText || "").trim();
      if (widgetVal) {
        setTimeout(() => triggerFieldEvaluation(customWidget, true, widgetVal, questionLabel), 120);
      }
      return;
    }

    // C. Choice buttons in button groups (only if explicitly marked as a choice value)
    const choiceBtn = target.closest('button, [role="button"]');
    if (choiceBtn && choiceBtn.type !== "submit" && !choiceBtn.closest("#magic-fill-learning-prompt") && !choiceBtn.closest("#simPromptModal") && !choiceBtn.closest("[data-magic-fill-ignore='true']")) {
      if (choiceBtn.id === "simulateAutofillBtn" || choiceBtn.id === "clearFormBtn" || choiceBtn.id === "resetFormBtn") return;
      const group = choiceBtn.closest('.btn-group, [role="group"], .button-group, .choices, [role="listitem"], .Qr7Oae');
      if (group && (choiceBtn.hasAttribute("data-value") || choiceBtn.getAttribute("role") === "radio" || choiceBtn.getAttribute("role") === "checkbox")) {
        const btnVal = (choiceBtn.getAttribute("data-value") || choiceBtn.innerText || "").trim();
        const label = getElementLabel(group) || getElementLabel(choiceBtn);
        if (btnVal) {
          setTimeout(() => triggerFieldEvaluation(choiceBtn, true, btnVal, label), 120);
        }
      }
    }
  }, true);

  // 5. Form Submit event: scan and evaluate any remaining filled fields
  document.addEventListener("submit", (e) => {
    const form = e.target;
    if (!form || !form.querySelectorAll) return;
    const inputs = form.querySelectorAll("input:not([type='button']):not([type='submit']):not([type='reset']):not([type='image']):not([type='hidden']), select, textarea, [role='combobox'], [role='radio']:checked, [role='checkbox'][aria-checked='true']");
    inputs.forEach((input) => {
      triggerFieldEvaluation(input, true);
    });
  }, true);

  function showLearningPrompt(el, evalData, cacheKey) {
    // If the current page already has its own in-page simulator prompt modal (#simPromptModal),
    // let the page's native prompt handle the UI to prevent duplicate stacked popups!
    if (document.getElementById("simPromptModal")) {
      return;
    }

    const existing = document.getElementById("magic-fill-learning-prompt");
    if (existing) existing.remove();

    const host = document.createElement("div");
    host.id = "magic-fill-learning-prompt";
    host.style.position = "fixed";
    host.style.bottom = "24px";
    host.style.right = "24px";
    host.style.zIndex = "2147483647";
    host.style.display = "block";
    const shadow = host.attachShadow({ mode: "open" });

    const isUpdate = evalData.action_type === "UPDATE_ATTRIBUTE";
    const badgeText = isUpdate
      ? `<svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" style="display:inline-block; vertical-align:-1px; margin-right:4px;"><path d="M21 12a9 9 0 0 0-9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/><path d="M3 12a9 9 0 0 0 9 9 9.75 9.75 0 0 0 6.74-2.74L21 16"/><path d="M16 21h5v-5"/></svg><span>Changed Data Detected</span>`
      : `<svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" style="display:inline-block; vertical-align:-1px; margin-right:4px;"><path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z"/></svg><span>New Data Detected</span>`;
    const badgeClass = isUpdate ? "badge-update" : "badge-new";

    let bodyHtml = "";
    let buttonsHtml = "";

    if (isUpdate) {
      bodyHtml = `
        <div class="desc-text">
          Your previously saved information is '<strong class="text-old">${escapeHtml(evalData.existing_value || "Empty")}</strong>'. Do you want to update it to '<strong class="text-new">${escapeHtml(evalData.new_value)}</strong>'?
        </div>
        <div class="diff-card">
          <div class="diff-row">
            <span class="diff-tag old-tag">Saved:</span>
            <span class="diff-val old-val">${escapeHtml(evalData.existing_value || "Empty")}</span>
          </div>
          <div class="diff-row">
            <span class="diff-tag new-tag">New:</span>
            <span class="diff-val new-val">${escapeHtml(evalData.new_value)}</span>
          </div>
        </div>
      `;
      buttonsHtml = `
        <button id="mf-learn-dismiss" class="btn-secondary">Not Now</button>
        <button id="mf-learn-save" class="btn-primary">Update Memory</button>
      `;
    } else {
      bodyHtml = `
        <div class="desc-text">
          Magic Fill detected new information for <strong style="color: #FFFFFF;">${escapeHtml(evalData.field_label)}</strong>: '<strong class="text-new">${escapeHtml(evalData.new_value)}</strong>'. Do you want to save it to your memory?
        </div>
        <div class="info-card">
          <div class="field-title">${escapeHtml(evalData.field_label)}</div>
          <div class="field-value">${escapeHtml(evalData.new_value)}</div>
        </div>
      `;
      buttonsHtml = `
        <button id="mf-learn-dismiss" class="btn-secondary">Not Now</button>
        <button id="mf-learn-save" class="btn-primary">Save to Memory</button>
      `;
    }

    shadow.innerHTML = `
      <style>
        * {
          box-sizing: border-box;
          margin: 0;
          padding: 0;
          font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        }
        .prompt-card {
          background: #FFFFFF;
          border: 1px solid #CBD5E1;
          border-radius: 16px;
          box-shadow: 0 12px 32px rgba(0, 0, 0, 0.12), 0 2px 8px rgba(0, 0, 0, 0.05);
          padding: 16px 18px;
          width: 360px;
          color: #0F172A;
          animation: mfSlideIn 0.22s cubic-bezier(0.16, 1, 0.3, 1);
        }
        @keyframes mfSlideIn {
          from { opacity: 0; transform: translateY(14px) scale(0.98); }
          to { opacity: 1; transform: translateY(0) scale(1); }
        }
        .header-row {
          display: flex;
          align-items: center;
          justify-content: space-between;
          margin-bottom: 10px;
        }
        .header-left {
          display: flex;
          align-items: center;
          gap: 8px;
        }
        .logo-icon {
          background: #EFF6FF;
          border: 1px solid #DBEAFE;
          width: 24px;
          height: 24px;
          border-radius: 6px;
          display: flex;
          align-items: center;
          justify-content: center;
          color: #2563EB;
          flex-shrink: 0;
        }
        .badge {
          font-size: 11px;
          font-weight: 700;
          border-radius: 6px;
          padding: 2px 8px;
          display: inline-block;
          font-family: 'JetBrains Mono', ui-monospace, monospace;
        }
        .badge-update {
          background: #EFF6FF;
          color: #2563EB;
          border: 1px solid #DBEAFE;
        }
        .badge-new {
          background: #EFF6FF;
          color: #2563EB;
          border: 1px solid #DBEAFE;
        }
        .text-old {
          color: #E11D48;
          font-weight: 600;
        }
        .text-new {
          color: #16A34A;
          font-weight: 600;
        }
        .close-btn {
          background: transparent;
          border: 1px solid transparent;
          border-radius: 6px;
          color: #64748B;
          width: 24px;
          height: 24px;
          display: flex;
          align-items: center;
          justify-content: center;
          cursor: pointer;
          transition: all 0.15s ease;
        }
        .close-btn:hover {
          color: #0F172A;
          background: #F1F5F9;
          border-color: #E2E8F0;
        }
        .close-btn:active {
          transform: scale(0.92);
        }
        .desc-text {
          font-size: 12.5px;
          color: #475569;
          margin-bottom: 10px;
          line-height: 1.45;
        }
        .diff-card {
          background: #F8FAFC;
          border: 1px solid #E2E8F0;
          border-radius: 8px;
          padding: 8px 10px;
          margin-bottom: 12px;
        }
        .diff-row {
          display: flex;
          align-items: center;
          gap: 6px;
          font-size: 12px;
          margin-bottom: 4px;
        }
        .diff-row:last-child {
          margin-bottom: 0;
        }
        .diff-tag {
          font-weight: 600;
          font-size: 11px;
          width: 48px;
          flex-shrink: 0;
        }
        .old-tag { color: #E11D48; }
        .new-tag { color: #16A34A; }
        .old-val {
          color: #E11D48;
          opacity: 0.8;
          text-decoration: line-through;
          font-family: 'JetBrains Mono', ui-monospace, SFMono-Regular, monospace;
          word-break: break-all;
        }
        .new-val {
          color: #16A34A;
          font-weight: 700;
          font-family: 'JetBrains Mono', ui-monospace, SFMono-Regular, monospace;
          word-break: break-all;
        }
        .info-card {
          background: #F8FAFC;
          border: 1px solid #E2E8F0;
          border-radius: 8px;
          padding: 8px 10px;
          margin-bottom: 12px;
        }
        .field-title {
          font-weight: 700;
          font-size: 12px;
          color: #0F172A;
          margin-bottom: 2px;
        }
        .field-value {
          color: #2563EB;
          font-family: 'JetBrains Mono', ui-monospace, SFMono-Regular, monospace;
          font-size: 11.5px;
          word-break: break-all;
        }
        .helper-text {
          font-size: 11.5px;
          color: #64748B;
          margin-bottom: 12px;
        }
        .btn-row {
          display: flex;
          gap: 8px;
          justify-content: flex-end;
          align-items: center;
        }
        .btn-secondary {
          background: #FFFFFF;
          border: 1px solid #CBD5E1;
          color: #475569;
          border-radius: 8px;
          padding: 7px 14px;
          font-size: 12px;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.15s ease;
        }
        .btn-secondary:hover {
          background: #F1F5F9;
          color: #0F172A;
          border-color: #94A3B8;
        }
        .btn-secondary:active, .btn-primary:active {
          transform: scale(0.98);
        }
        .btn-primary {
          background: #2563EB;
          border: 1px solid #2563EB;
          color: #FFFFFF;
          border-radius: 8px;
          padding: 7px 16px;
          font-size: 12px;
          font-weight: 700;
          cursor: pointer;
          box-shadow: 0 1px 3px rgba(37, 99, 235, 0.25);
          transition: all 0.15s ease;
        }
        .btn-primary:hover {
          background: #1D4ED8;
          border-color: #1D4ED8;
        }
      </style>
      <div class="prompt-card">
        <div class="header-row">
          <div class="header-left">
            <div class="logo-icon">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon></svg>
            </div>
            <span class="badge ${badgeClass}">${badgeText}</span>
          </div>
          <button id="mf-learn-close" class="close-btn" title="Close">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
          </button>
        </div>
        ${bodyHtml}
        <div class="btn-row">
          ${buttonsHtml}
        </div>
      </div>
    `;

    document.body.appendChild(host);

    const closePrompt = () => {
      if (host && host.parentNode) host.parentNode.removeChild(host);
    };

    shadow.querySelector("#mf-learn-close").addEventListener("click", closePrompt);
    const dismissBtn = shadow.querySelector("#mf-learn-dismiss");
    if (dismissBtn) {
      dismissBtn.addEventListener("click", () => {
        evaluatedFieldsCache.delete(cacheKey);
        closePrompt();
      });
    }

    const keepBtn = shadow.querySelector("#mf-learn-keep");
    if (keepBtn) keepBtn.addEventListener("click", closePrompt);

    const saveBtn = shadow.querySelector("#mf-learn-save");
    saveBtn.addEventListener("click", () => {
      saveBtn.disabled = true;
      saveBtn.innerText = isUpdate ? "Updating..." : "Saving...";

      try {
        if (!chrome.runtime || !chrome.runtime.id) {
          saveBtn.innerText = "Error";
          setTimeout(closePrompt, 1500);
          return;
        }

        let localTok = null;
        try {
          localTok = localStorage.getItem("magic_fill_token");
        } catch (e) {}

        chrome.runtime.sendMessage(
          {
            action: "COMMIT_LEARNED_FIELD",
            token: localTok || null,
            data: {
              action_type: evalData.action_type,
              canonical_key: evalData.canonical_key,
              field_label: evalData.field_label,
              value: evalData.new_value,
              category: evalData.category === "PROFESSIONAL_INFO" ? "professional" : "personal",
            },
          },
          (res) => {
            if (chrome.runtime.lastError) {
              saveBtn.style.background = "#f43f5e";
              saveBtn.style.borderColor = "#f43f5e";
              saveBtn.style.color = "#FFFFFF";
              saveBtn.innerText = "Error saving";
              setTimeout(closePrompt, 2200);
              return;
            }

            if (res && res.success) {
              el.setAttribute("data-magic-fill-status", "matched");
              if (el.type === "radio" && el.name) {
                document.querySelectorAll(`input[type="radio"][name="${CSS.escape(el.name)}"]`).forEach((r) => {
                  r.setAttribute("data-magic-fill-status", "matched");
                });
              }

              saveBtn.style.background = "#2563EB";
              saveBtn.style.borderColor = "#2563EB";
              saveBtn.style.color = "#FFFFFF";
              saveBtn.innerText = isUpdate ? "✓ Updated Memory!" : "✓ Saved to Memory!";
              setTimeout(closePrompt, 1600);
            } else {
              saveBtn.style.background = "#f43f5e";
              saveBtn.style.borderColor = "#f43f5e";
              saveBtn.style.color = "#FFFFFF";
              saveBtn.innerText = "Error saving";
              setTimeout(closePrompt, 2200);
            }
          }
        );
      } catch (err) {
        saveBtn.innerText = "Error";
        setTimeout(closePrompt, 1500);
      }
    });
  }

  function escapeHtml(str) {
    if (!str) return "";
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  // ---------------------------------------------------------------------------
  // 5. Chrome Runtime Message Listener
  // ---------------------------------------------------------------------------
  chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    switch (message.action) {
      case "SCAN_PAGE_FIELDS": {
        const detected = scanFormFields();
        sendResponse({
          success: true,
          fields: detected,
          pageTitle: document.title,
          url: window.location.href,
        });
        return false;
      }

      case "AUTOFILL_FIELDS": {
        const filledCount = applyAutofill(message.mappings || []);
        sendResponse({ success: true, filledCount: filledCount });
        return false;
      }

      case "UPDATE_VISUAL_STATUS": {
        applyFieldVisualStatus(message.mappings || [], message.unresolvedFields || []);
        sendResponse({ success: true });
        return false;
      }

      case "CLEAR_VISUAL_STATUS": {
        document.querySelectorAll("[data-magic-fill-status]").forEach((el) => {
          el.removeAttribute("data-magic-fill-status");
        });
        sendResponse({ success: true });
        return false;
      }

      case "TOGGLE_NEW_DATA_DETECTION": {
        isNewDataDetectionEnabled = message.enabled !== false;
        if (!isNewDataDetectionEnabled) {
          const activePrompt = document.getElementById("magic-fill-learning-prompt");
          if (activePrompt) activePrompt.remove();
          fieldDebounceTimers.forEach((timer) => clearTimeout(timer));
          fieldDebounceTimers.clear();
        }
        sendResponse({ success: true, enabled: isNewDataDetectionEnabled });
        return false;
      }

      default:
        sendResponse({ success: false, error: "Unknown action" });
        return false;
    }
  });
})();
