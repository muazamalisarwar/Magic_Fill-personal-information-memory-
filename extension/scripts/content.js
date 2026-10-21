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

  const SENSITIVE_TYPES = new Set(["password", "hidden"]);

  // ---------------------------------------------------------------------------
  // 1. Dynamic Visual Status Styling (Green for Matched, Red for Missing)
  // ---------------------------------------------------------------------------
  function ensureStatusStyles() {
    if (document.getElementById("magic-fill-status-styles")) return;
    const style = document.createElement("style");
    style.id = "magic-fill-status-styles";
    style.textContent = `
      [data-magic-fill-status="matched"] {
        border: 2px solid #22c55e !important;
        box-shadow: 0 0 0 3px rgba(34, 197, 94, 0.28) !important;
        background-color: rgba(34, 197, 94, 0.035) !important;
        transition: border-color 0.25s ease, box-shadow 0.25s ease !important;
      }
      [data-magic-fill-status="missing"] {
        border: 2px solid #ef4444 !important;
        box-shadow: 0 0 0 3px rgba(239, 68, 68, 0.28) !important;
        background-color: rgba(239, 68, 68, 0.035) !important;
        transition: border-color 0.25s ease, box-shadow 0.25s ease !important;
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
    // 1. Check aria-labelledby (Handles space-separated IDs used by Google Forms, Microsoft Forms, ARIA)
    const labelledby = el.getAttribute("aria-labelledby");
    if (labelledby) {
      const ids = labelledby.trim().split(/\s+/);
      const textParts = [];
      for (const id of ids) {
        try {
          const target = document.getElementById(id);
          if (target) {
            const raw = cleanLabelText(target.innerText || target.textContent);
            if (raw && !isGenericPlaceholder(raw)) {
              textParts.push(raw);
            }
          }
        } catch (e) {}
      }
      if (textParts.length > 0) {
        return textParts[0]; // The primary question title
      }
    }

    // 2. Google Forms / Job Portals Question Item Container Heading
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
    const selector = "input, select, textarea, [role='switch'], [role='radio'], [role='checkbox'], button[type='submit'], input[type='submit']";
    const rawElements = document.querySelectorAll(selector);
    const fields = [];
    const processedRadioGroups = new Set();
    let counter = 0;

    rawElements.forEach((el) => {
      const type = (el.type || el.getAttribute("type") || "text").toLowerCase();
      if (SENSITIVE_TYPES.has(type)) return;

      // Exclude hidden or non-interactive fields
      const style = window.getComputedStyle(el);
      if (style.display === "none" || style.visibility === "hidden" || el.disabled || el.readOnly) {
        return;
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
  function applyAutofill(mappings) {
    ensureStatusStyles();
    let filledCount = 0;

    mappings.forEach((mapping) => {
      const el = document.querySelector(`[data-magic-fill-id="${CSS.escape(mapping.field_id)}"]`);
      if (!el) return;

      const tag = el.tagName.toLowerCase();
      const type = (el.type || "text").toLowerCase();
      const role = (el.getAttribute("role") || "").toLowerCase();

      if (tag === "select") {
        let matched = false;
        const targetVal = String(mapping.value).toLowerCase().trim();

        // 1. Exact value or text match
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
        // 2. Gender abbreviation fallback (Male <-> M, Female <-> F)
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
        // 3. Country synonyms & abbreviations (USA, UK, PK)
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
        // 4. Substring fallback
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
            try {
              r.click();
            } catch (e) {}
            r.dispatchEvent(new Event("change", { bubbles: true, composed: true }));
          }
        });
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
      } else if (type === "range") {
        const numVal = parseInt(String(mapping.value).replace(/\D/g, ""), 10) || 0;
        el.value = numVal;
      } else if (type === "date") {
        const rawDate = String(mapping.value || "").trim();
        const isoMatch = rawDate.match(/^(\d{4}-\d{2}-\d{2})/);
        el.value = isoMatch ? isoMatch[1] : rawDate;
      } else if (type === "file") {
        try {
          const rawVal = String(mapping.value);
          let fileObj = null;
          if (rawVal.startsWith("data:image")) {
            const arr = rawVal.split(",");
            const mimeMatch = arr[0].match(/:(.*?);/);
            const mime = mimeMatch ? mimeMatch[1] : "image/png";
            const bstr = atob(arr[1]);
            let n = bstr.length;
            const u8arr = new Uint8Array(n);
            while (n--) u8arr[n] = bstr.charCodeAt(n);
            fileObj = new File([u8arr], "photograph.png", { type: mime });
          } else {
            const blob = new Blob([rawVal], { type: "image/svg+xml" });
            fileObj = new File([blob], "document_image.svg", { type: "image/svg+xml" });
          }

          if (fileObj && window.DataTransfer) {
            const dt = new DataTransfer();
            dt.items.add(fileObj);
            el.files = dt.files;
          }
        } catch (e) {
          console.warn("[Magic Fill] Could not populate file input:", e);
        }
      } else if (tag === "textarea" || type === "text" || type === "email" || type === "tel" || type === "url" || type === "number" || !type) {
        // Native property setter for React, Angular, Vue, and Google Closure (Google Forms)
        try {
          el.focus();
        } catch (e) {}

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
      } else {
        el.value = mapping.value;
      }

      // Mark as autofilled so manual entry tracker ignores it
      el.setAttribute("data-magic-fill-autofilled", "true");
      el.setAttribute("data-magic-fill-status", "matched");

      if (el.type === "radio" && el.name) {
        document.querySelectorAll(`input[type="radio"][name="${CSS.escape(el.name)}"]`).forEach((r) => {
          r.setAttribute("data-magic-fill-status", "matched");
        });
      }

      // Dispatch comprehensive event sequence for Google Forms (Google Closure), React, and Angular
      el.dispatchEvent(new Event("input", { bubbles: true, composed: true }));
      el.dispatchEvent(new Event("change", { bubbles: true, composed: true }));
      try {
        el.dispatchEvent(new KeyboardEvent("keydown", { bubbles: true, composed: true, key: "Enter" }));
        el.dispatchEvent(new KeyboardEvent("keyup", { bubbles: true, composed: true, key: "Enter" }));
        el.dispatchEvent(new Event("blur", { bubbles: true, composed: true }));
      } catch (e) {}

      // Clean up Google Forms Material container error messages and float label
      const gfContainer = el.closest(".quantumWizTextinputPaperinputEl, .o3G8cc, .nd91id, .geS5n, .Qr7Oae, [role='listitem']");
      if (gfContainer) {
        gfContainer.classList.add("is-filled");
        gfContainer.classList.remove("is-invalid");
        const errorAlerts = gfContainer.querySelectorAll(".RxsGPe, [role='alert'], .freebirdFormviewerViewItemsItemErrorMessage");
        errorAlerts.forEach((ea) => {
          ea.style.display = "none";
        });
      }

      filledCount++;
    });

    return filledCount;
  }

  // ---------------------------------------------------------------------------
  // 4. Intelligent Form Learning & Memory Updates
  // ---------------------------------------------------------------------------
  const evaluatedFieldsCache = new Set();
  let evaluateDebounceTimer = null;

  function isExcludedField(el, label, val) {
    if (!el || !val) return true;
    const v = val.trim();
    if (v.length < 2 && !/^\d+$/.test(v)) return true;

    // Exclude if element explicitly opts out of Magic Fill auto-learning
    if (el.getAttribute("data-magic-fill-ignore") === "true" || el.getAttribute("data-no-learn") === "true") return true;

    // Exclude Magic Fill's own web app pages on localhost
    const host = window.location.hostname;
    const path = window.location.pathname;
    if ((host === "localhost" || host === "127.0.0.1") && (path.includes("/extract") || path.includes("/memory") || path.includes("/dashboard") || path.includes("/login") || path.includes("/register"))) {
      return true;
    }

    // Exclude document and file description textareas
    if (el.id === "mediaDescriptionInput" || el.name === "media_ai_description" || el.id === "rawTextInput" || el.id === "chatInput") {
      return true;
    }

    const type = (el.type || "text").toLowerCase();
    if (SENSITIVE_TYPES.has(type) || type === "search" || type === "color" || type === "file") {
      return true;
    }

    // Role check
    const role = (el.getAttribute("role") || "").toLowerCase();
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
    if (el.closest('[data-testid*="chat"], [aria-label*="chat"], [role="log"], [role="feed"], form[action*="chat"]')) {
      return true;
    }

    // Multi-line communication text in textareas (unless explicitly address or bio)
    if (el.tagName.toLowerCase() === "textarea" && (v.length > 200 || v.includes("\n"))) {
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

  function handleUserInput(e) {
    const el = e.target;
    if (!el || !el.tagName) return;
    const tag = el.tagName.toLowerCase();
    const type = (el.type || "text").toLowerCase();

    if (tag !== "input" && tag !== "select" && tag !== "textarea") return;
    if (type === "radio" && !el.checked) return;

    // If edited by user, clear the autofill marker
    if (el.getAttribute("data-magic-fill-autofilled") === "true") {
      el.removeAttribute("data-magic-fill-autofilled");
    }

    let val = "";
    if (tag === "select") {
      val = el.options[el.selectedIndex]?.text?.trim() || (el.value || "").trim();
    } else if (type === "checkbox") {
      val = el.checked ? "Yes" : "No";
    } else if (type === "radio") {
      val = el.value || "Yes";
    } else {
      val = (el.value || "").trim();
    }

    const label = getElementLabel(el);
    if (isExcludedField(el, label, val)) return;

    const cacheKey = `${el.name || el.id || label}_${val.toLowerCase()}`;
    if (evaluatedFieldsCache.has(cacheKey)) return;

    if (evaluateDebounceTimer) clearTimeout(evaluateDebounceTimer);
    evaluateDebounceTimer = setTimeout(() => {
      evaluateFieldForLearning(el, label, val, cacheKey);
    }, 1200);
  }

  function evaluateFieldForLearning(el, label, val, cacheKey) {
    evaluatedFieldsCache.add(cacheKey);

    chrome.runtime.sendMessage(
      {
        action: "EVALUATE_FIELD_FOR_LEARNING",
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
        if (!res || !res.success || !res.data) return;
        const evalData = res.data;
        if (!evalData.is_learnable) return;

        showLearningPrompt(el, evalData, cacheKey);
      }
    );
  }

  document.addEventListener("blur", handleUserInput, true);
  document.addEventListener("change", handleUserInput, true);

  function showLearningPrompt(el, evalData, cacheKey) {
    const existing = document.getElementById("magic-fill-learning-prompt");
    if (existing) existing.remove();

    const host = document.createElement("div");
    host.id = "magic-fill-learning-prompt";
    host.style.position = "fixed";
    host.style.bottom = "24px";
    host.style.right = "24px";
    host.style.zIndex = "2147483647";
    host.style.fontFamily = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif";

    const isUpdate = evalData.action_type === "UPDATE_ATTRIBUTE";
    const titleText = isUpdate ? "Update saved information?" : "Save to Magic Fill memory?";

    let contentHtml = "";
    let buttonsHtml = "";

    if (isUpdate) {
      contentHtml = `
        <div style="font-size:12.5px; color:#475569; margin-bottom:12px; line-height:1.45;">
          Your saved <strong>${escapeHtml(evalData.field_label)}</strong> (<em>${escapeHtml(evalData.existing_value || "")}</em>) is different from the value you just entered (<strong>${escapeHtml(evalData.new_value)}</strong>). Would you like to update your Magic Fill memory?
        </div>
      `;
      buttonsHtml = `
        <button id="mf-learn-dismiss" style="background:#ffffff; border:1px solid #cbd5e1; color:#475569; border-radius:9999px; padding:6px 12px; font-size:12px; font-weight:600; cursor:pointer;">Not Now</button>
        <button id="mf-learn-keep" style="background:#f1f5f9; border:1px solid #cbd5e1; color:#334155; border-radius:9999px; padding:6px 12px; font-size:12px; font-weight:600; cursor:pointer;">Keep Existing</button>
        <button id="mf-learn-save" style="background:#0f172a; border:none; color:#ffffff; border-radius:9999px; padding:6px 16px; font-size:12px; font-weight:700; cursor:pointer; box-shadow:0 2px 8px rgba(15,23,42,0.15);">Update Memory</button>
      `;
    } else {
      contentHtml = `
        <div style="font-size:12.5px; color:#475569; margin-bottom:8px; line-height:1.45;">
          Magic Fill detected a new personal information field:
        </div>
        <div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:8px; padding:9px 12px; font-size:12px; color:#1e293b; margin-bottom:12px; line-height:1.5;">
          <div style="font-weight:700; color:#0f172a; margin-bottom:2px;">${escapeHtml(evalData.field_label)}</div>
          <div style="color:#0284c7; word-break:break-all; font-family:monospace; font-size:11.5px;">${escapeHtml(evalData.new_value)}</div>
        </div>
        <div style="font-size:12px; color:#64748b; margin-bottom:12px;">
          Would you like to save it for future autofill?
        </div>
      `;
      buttonsHtml = `
        <button id="mf-learn-dismiss" style="background:#ffffff; border:1px solid #cbd5e1; color:#475569; border-radius:9999px; padding:6px 14px; font-size:12px; font-weight:600; cursor:pointer;">Not Now</button>
        <button id="mf-learn-save" style="background:#0f172a; border:none; color:#ffffff; border-radius:9999px; padding:6px 16px; font-size:12px; font-weight:700; cursor:pointer; box-shadow:0 2px 8px rgba(15,23,42,0.15);">Save to Memory</button>
      `;
    }

    host.innerHTML = `
      <div style="background:#ffffff; border:1px solid #cbd5e1; border-radius:14px; box-shadow:0 20px 45px -10px rgba(15,23,42,0.22), 0 2px 4px rgba(15,23,42,0.06); padding:16px 18px; width:350px; color:#0f172a;">
        <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:10px;">
          <div style="display:flex; align-items:center; gap:8px;">
            <div style="background:#0f172a; width:26px; height:26px; border-radius:7px; display:flex; align-items:center; justify-content:center; color:#fff;">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon></svg>
            </div>
            <strong style="font-size:13.5px; color:#0f172a;">${titleText}</strong>
          </div>
          <button id="mf-learn-close" style="background:none; border:none; color:#94a3b8; font-size:20px; cursor:pointer; line-height:1;">&times;</button>
        </div>
        ${contentHtml}
        <div style="display:flex; gap:8px; justify-content:flex-end;">
          ${buttonsHtml}
        </div>
      </div>
    `;

    document.body.appendChild(host);

    const closePrompt = () => {
      if (host && host.parentNode) host.parentNode.removeChild(host);
    };

    host.querySelector("#mf-learn-close").addEventListener("click", closePrompt);
    const dismissBtn = host.querySelector("#mf-learn-dismiss");
    if (dismissBtn) dismissBtn.addEventListener("click", closePrompt);

    const keepBtn = host.querySelector("#mf-learn-keep");
    if (keepBtn) keepBtn.addEventListener("click", closePrompt);

    const saveBtn = host.querySelector("#mf-learn-save");
    saveBtn.addEventListener("click", () => {
      saveBtn.disabled = true;
      saveBtn.innerText = isUpdate ? "Updating..." : "Saving...";

      chrome.runtime.sendMessage(
        {
          action: "COMMIT_LEARNED_FIELD",
          data: {
            action_type: evalData.action_type,
            canonical_key: evalData.canonical_key,
            field_label: evalData.field_label,
            value: evalData.new_value,
            category: evalData.category === "PROFESSIONAL_INFO" ? "professional" : "personal",
          },
        },
        (res) => {
          if (res && res.success) {
            // Dynamically flip field visual status from red (missing) to green (matched)!
            el.setAttribute("data-magic-fill-status", "matched");
            if (el.type === "radio" && el.name) {
              document.querySelectorAll(`input[type="radio"][name="${CSS.escape(el.name)}"]`).forEach((r) => {
                r.setAttribute("data-magic-fill-status", "matched");
              });
            }

            saveBtn.style.background = "#059669";
            saveBtn.innerText = isUpdate ? "✓ Updated Memory!" : "✓ Saved to Memory!";
            setTimeout(closePrompt, 1800);
          } else {
            saveBtn.style.background = "#e11d48";
            saveBtn.innerText = "Error saving";
            setTimeout(closePrompt, 2200);
          }
        }
      );
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
        break;
      }

      case "AUTOFILL_FIELDS": {
        const filledCount = applyAutofill(message.mappings || []);
        sendResponse({ success: true, filledCount: filledCount });
        break;
      }

      case "UPDATE_VISUAL_STATUS": {
        applyFieldVisualStatus(message.mappings || [], message.unresolvedFields || []);
        sendResponse({ success: true });
        break;
      }

      case "CLEAR_VISUAL_STATUS": {
        document.querySelectorAll("[data-magic-fill-status]").forEach((el) => {
          el.removeAttribute("data-magic-fill-status");
        });
        sendResponse({ success: true });
        break;
      }

      default:
        sendResponse({ success: false, error: "Unknown action" });
    }
    return true;
  });
})();
