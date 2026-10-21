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
    const selector = "input, select, textarea, [role='switch'], [role='radio'], [role='checkbox'], button[type='submit'], input[type='submit']";
    const rawElements = document.querySelectorAll(selector);
    const fields = [];
    const processedRadioGroups = new Set();
    let counter = 0;

    rawElements.forEach((el) => {
      const type = (el.type || el.getAttribute("type") || "text").toLowerCase();
      if (SENSITIVE_TYPES.has(type)) return;

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
          const rawVal = String(mapping.value || "");
          if (rawVal.startsWith("data:") || rawVal.length > 50) {
            const mimeMatch = rawVal.match(/^data:([^;]+);base64,/);
            const mime = mimeMatch ? mimeMatch[1] : (rawVal.startsWith("data:image") ? "image/png" : "application/pdf");
            const base64Data = rawVal.includes(",") ? rawVal.split(",")[1] : rawVal;
            const bstr = atob(base64Data);
            let n = bstr.length;
            const u8arr = new Uint8Array(n);
            while (n--) u8arr[n] = bstr.charCodeAt(n);

            let filename = "document.pdf";
            const memKey = (mapping.memory_key || "").toLowerCase();
            if (mime.includes("pdf")) filename = "resume_cv.pdf";
            else if (mime.includes("png")) filename = "photograph.png";
            else if (mime.includes("jpeg") || mime.includes("jpg")) filename = "photograph.jpg";
            else if (mime.includes("word") || mime.includes("officedocument")) filename = "resume_cv.docx";
            else if (memKey.includes("resume") || memKey.includes("cv")) filename = "resume_cv.pdf";
            else if (memKey.includes("photo") || memKey.includes("avatar")) filename = "photograph.jpg";
            else if (memKey.includes("cnic")) filename = "cnic_document.jpg";

            const fileObj = new File([u8arr], filename, { type: mime, lastModified: Date.now() });

            if (window.DataTransfer) {
              const dt = new DataTransfer();
              dt.items.add(fileObj);
              el.files = dt.files;
              el.dispatchEvent(new Event("input", { bubbles: true, composed: true }));
              el.dispatchEvent(new Event("change", { bubbles: true, composed: true }));
            }
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

        try {
          el.setAttribute("data-initial-value", mapping.value);
          el.setAttribute("value", mapping.value);
        } catch (e) {}
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
      el.dispatchEvent(new Event("focus", { bubbles: true, composed: true }));
      el.dispatchEvent(new Event("beforeinput", { bubbles: true, composed: true }));
      el.dispatchEvent(new Event("input", { bubbles: true, composed: true }));
      el.dispatchEvent(new Event("change", { bubbles: true, composed: true }));
      try {
        el.dispatchEvent(new KeyboardEvent("keydown", { bubbles: true, composed: true, key: "Enter" }));
        el.dispatchEvent(new KeyboardEvent("keyup", { bubbles: true, composed: true, key: "Enter" }));
        el.dispatchEvent(new Event("blur", { bubbles: true, composed: true }));
      } catch (e) {}

      // Clean up Google Forms Material container error messages and float label
      const gfContainer = el.closest(".quantumWizTextinputPaperinputEl, .o3G8cc, .nd91id, .geS5n, .Qr7Oae, [role='listitem'], .AgroD");
      if (gfContainer) {
        gfContainer.classList.add("is-filled", "has-value");
        gfContainer.classList.remove("is-invalid", "badInput");
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
  const fieldDebounceTimers = new Map();

  function isExcludedField(el, label, val) {
    if (!el || !val) return true;
    const v = val.trim();
    if (v.length < 2 && !/^\d+$/.test(v)) return true;

    // Exclude if element explicitly opts out of Magic Fill auto-learning
    if (el.getAttribute && (el.getAttribute("data-magic-fill-ignore") === "true" || el.getAttribute("data-no-learn") === "true")) return true;

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

    const type = (el.type || el.getAttribute("type") || "").toLowerCase();
    if (type === "submit" || type === "reset" || SENSITIVE_TYPES.has(type) || type === "search" || type === "color" || type === "file") {
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

  function triggerFieldEvaluation(el, immediate = false, overrideVal = null, overrideLabel = null) {
    if (!el) return;
    const tag = (el.tagName || "").toLowerCase();
    const type = (el.type || el.getAttribute("type") || "text").toLowerCase();
    const role = (el.getAttribute("role") || "").toLowerCase();

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
      } else if (tag === "button" || role === "button") {
        val = el.getAttribute("data-value") || el.innerText?.trim() || "";
      } else {
        val = (el.value || "").trim();
      }
    }

    if (!val || (val.length < 2 && !/^\d+$/.test(val))) return;

    const label = overrideLabel || getElementLabel(el);
    if (isExcludedField(el, label, val)) return;

    const fieldKey = el.name || el.id || label || "field";
    const cacheKey = `${fieldKey}_${val.toLowerCase()}`;
    if (evaluatedFieldsCache.has(cacheKey)) return;

    const doEval = () => {
      evaluateFieldForLearning(el, label, val, cacheKey);
    };

    if (immediate) {
      doEval();
    } else {
      if (fieldDebounceTimers.has(fieldKey)) {
        clearTimeout(fieldDebounceTimers.get(fieldKey));
      }
      fieldDebounceTimers.set(fieldKey, setTimeout(doEval, 550));
    }
  }

  function handleUserInput(e) {
    triggerFieldEvaluation(e.target, false);
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
        if (!res || !res.success || !res.data || !res.data.is_learnable) {
          evaluatedFieldsCache.delete(cacheKey);
          return;
        }
        const evalData = res.data;
        showLearningPrompt(el, evalData, cacheKey);
      }
    );
  }

  // 1. Live keystroke listener (debounced 550ms for typing into inputs & textareas)
  document.addEventListener("input", (e) => {
    triggerFieldEvaluation(e.target, false);
  }, true);

  // 2. Native change event (fired on selects, radios, checkboxes, and inputs on commit)
  document.addEventListener("change", (e) => {
    triggerFieldEvaluation(e.target, true);
  }, true);

  // 3. Blur event for text and textarea
  document.addEventListener("blur", (e) => {
    triggerFieldEvaluation(e.target, true);
  }, true);

  // 4. Click event for custom dropdown options, radios, checkboxes, and choice buttons
  document.addEventListener("click", (e) => {
    const target = e.target;
    if (!target) return;

    // A. Option clicked in custom dropdown (Google Forms listbox, custom select, etc.)
    const option = target.closest('[role="option"], .select-option, [data-value]');
    if (option) {
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
      const radioContainer = customWidget.closest('[role="listitem"], .Qr7Oae, .geS5n, fieldset, .form-group') || customWidget.parentElement;
      const questionLabel = getElementLabel(radioContainer) || getElementLabel(customWidget);
      const valEl = customWidget.querySelector('.aDTYNe, .d7L4fc, label, span') || customWidget;
      const widgetVal = (customWidget.getAttribute("data-value") || valEl.innerText || "").trim();
      if (widgetVal) {
        setTimeout(() => triggerFieldEvaluation(customWidget, true, widgetVal, questionLabel), 120);
      }
      return;
    }

    // C. Choice buttons in button groups
    const choiceBtn = target.closest('button, [role="button"]');
    if (choiceBtn && choiceBtn.type !== "submit" && !choiceBtn.closest("#magic-fill-learning-prompt")) {
      const group = choiceBtn.closest('.btn-group, [role="group"], .button-group, .choices, [role="listitem"], .Qr7Oae');
      if (group) {
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
    const inputs = form.querySelectorAll("input, select, textarea, [role='combobox'], [role='radio']:checked, [role='checkbox'][aria-checked='true']");
    inputs.forEach((input) => {
      triggerFieldEvaluation(input, true);
    });
  }, true);

  function showLearningPrompt(el, evalData, cacheKey) {
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
    const badgeText = isUpdate ? "🔄 Changed Data Detected" : "✨ New Data Detected";
    const badgeClass = isUpdate ? "badge-update" : "badge-new";

    let bodyHtml = "";
    let buttonsHtml = "";

    if (isUpdate) {
      bodyHtml = `
        <div class="desc-text">
          Your saved <strong>${escapeHtml(evalData.field_label)}</strong> is different from what you just entered:
        </div>
        <div class="diff-card">
          <div class="diff-row">
            <span class="diff-tag old-tag">Saved:</span>
            <span class="diff-val old-val">${escapeHtml(evalData.existing_value || "Empty")}</span>
          </div>
          <div class="diff-row">
            <span class="diff-tag new-tag">Entered:</span>
            <span class="diff-val new-val">${escapeHtml(evalData.new_value)}</span>
          </div>
        </div>
      `;
      buttonsHtml = `
        <button id="mf-learn-dismiss" class="btn-secondary">Not Now</button>
        <button id="mf-learn-keep" class="btn-secondary">Keep Saved</button>
        <button id="mf-learn-save" class="btn-primary">Update Memory</button>
      `;
    } else {
      bodyHtml = `
        <div class="desc-text">
          Magic Fill detected a new personal or professional field:
        </div>
        <div class="info-card">
          <div class="field-title">${escapeHtml(evalData.field_label)}</div>
          <div class="field-value">${escapeHtml(evalData.new_value)}</div>
        </div>
        <div class="helper-text">
          Would you like to save this to your memory for automatic form filling?
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
          font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        }
        .prompt-card {
          background: #ffffff;
          border: 1px solid #cbd5e1;
          border-radius: 16px;
          box-shadow: 0 20px 45px -10px rgba(15,23,42,0.28), 0 4px 12px rgba(15,23,42,0.08);
          padding: 16px 18px;
          width: 360px;
          color: #0f172a;
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
          background: #0f172a;
          width: 24px;
          height: 24px;
          border-radius: 6px;
          display: flex;
          align-items: center;
          justify-content: center;
          color: #ffffff;
          flex-shrink: 0;
        }
        .badge {
          font-size: 11px;
          font-weight: 700;
          border-radius: 9999px;
          padding: 2px 8px;
          display: inline-block;
        }
        .badge-update {
          background: #fef3c7;
          color: #92400e;
          border: 1px solid #fde68a;
        }
        .badge-new {
          background: #dcfce7;
          color: #166534;
          border: 1px solid #bbf7d0;
        }
        .close-btn {
          background: none;
          border: none;
          color: #94a3b8;
          font-size: 22px;
          cursor: pointer;
          line-height: 1;
          padding: 0 4px;
        }
        .close-btn:hover {
          color: #0f172a;
        }
        .desc-text {
          font-size: 12.5px;
          color: #475569;
          margin-bottom: 8px;
          line-height: 1.45;
        }
        .diff-card {
          background: #f8fafc;
          border: 1px solid #e2e8f0;
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
        .old-tag { color: #dc2626; }
        .new-tag { color: #0284c7; }
        .old-val {
          color: #991b1b;
          text-decoration: line-through;
          font-family: ui-monospace, SFMono-Regular, monospace;
          word-break: break-all;
        }
        .new-val {
          color: #0369a1;
          font-weight: 700;
          font-family: ui-monospace, SFMono-Regular, monospace;
          word-break: break-all;
        }
        .info-card {
          background: #f8fafc;
          border: 1px solid #e2e8f0;
          border-radius: 8px;
          padding: 8px 10px;
          margin-bottom: 8px;
        }
        .field-title {
          font-weight: 700;
          font-size: 12.5px;
          color: #0f172a;
          margin-bottom: 2px;
        }
        .field-value {
          color: #0284c7;
          font-family: ui-monospace, SFMono-Regular, monospace;
          font-size: 11.5px;
          word-break: break-all;
        }
        .helper-text {
          font-size: 11.5px;
          color: #64748b;
          margin-bottom: 12px;
        }
        .btn-row {
          display: flex;
          gap: 8px;
          justify-content: flex-end;
          align-items: center;
        }
        .btn-secondary {
          background: #ffffff;
          border: 1px solid #cbd5e1;
          color: #475569;
          border-radius: 9999px;
          padding: 6px 12px;
          font-size: 12px;
          font-weight: 600;
          cursor: pointer;
        }
        .btn-secondary:hover {
          background: #f1f5f9;
          color: #0f172a;
        }
        .btn-primary {
          background: #0f172a;
          border: 1px solid #0f172a;
          color: #ffffff;
          border-radius: 9999px;
          padding: 6px 16px;
          font-size: 12px;
          font-weight: 700;
          cursor: pointer;
          box-shadow: 0 2px 8px rgba(15,23,42,0.15);
        }
        .btn-primary:hover {
          background: #1e293b;
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
          <button id="mf-learn-close" class="close-btn" title="Close">&times;</button>
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
            el.setAttribute("data-magic-fill-status", "matched");
            if (el.type === "radio" && el.name) {
              document.querySelectorAll(`input[type="radio"][name="${CSS.escape(el.name)}"]`).forEach((r) => {
                r.setAttribute("data-magic-fill-status", "matched");
              });
            }

            saveBtn.style.background = "#059669";
            saveBtn.style.borderColor = "#059669";
            saveBtn.innerText = isUpdate ? "✓ Updated Memory!" : "✓ Saved to Memory!";
            setTimeout(closePrompt, 1600);
          } else {
            saveBtn.style.background = "#e11d48";
            saveBtn.style.borderColor = "#e11d48";
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
