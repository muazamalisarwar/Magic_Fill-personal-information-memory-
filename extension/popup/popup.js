/**
 * Magic Fill - High-Performance Popup Controller
 * Instant-load architecture (< 50ms) via direct chrome.storage.local caching.
 * Non-blocking asynchronous backend health checking and profile sync.
 */

document.addEventListener("DOMContentLoaded", async () => {
  // Common Elements
  const backendStatusEl = document.getElementById("backendStatus");
  const alertBoxEl = document.getElementById("alertBox");

  // Unauthenticated Elements
  const unauthenticatedSection = document.getElementById("unauthenticatedSection");
  const btnSignInWebsite = document.getElementById("btnSignInWebsite");
  const linkCreateAccount = document.getElementById("linkCreateAccount");
  const inputAuthCode = document.getElementById("inputAuthCode");
  const btnExchangeCode = document.getElementById("btnExchangeCode");
  const btnSyncFromTab = document.getElementById("btnSyncFromTab");
  const authErrorBox = document.getElementById("authErrorBox");

  // Authenticated Elements
  const authenticatedSection = document.getElementById("authenticatedSection");
  const userIdBadgeEl = document.getElementById("userIdBadge");
  const profileSummaryEl = document.getElementById("profileSummary");
  const vaultStatsStripEl = document.getElementById("vaultStatsStrip");
  const statDocCountEl = document.getElementById("statDocCount");
  const statCustomCountEl = document.getElementById("statCustomCount");
  const statExpCountEl = document.getElementById("statExpCount");
  const autofillBtn = document.getElementById("autofillBtn");
  const btnManageInfo = document.getElementById("btnManageInfo");
  const btnSignOut = document.getElementById("btnSignOut");
  const scanSummaryEl = document.getElementById("scanSummary");
  const resultsSectionEl = document.getElementById("resultsSection");
  const mappingsListEl = document.getElementById("mappingsList");
  const matchCountBadgeEl = document.getElementById("matchCountBadge");

  // Detection Toggle Elements
  const toggleNewDataDetection = document.getElementById("toggleNewDataDetection");
  const detectionStatusBadge = document.getElementById("detectionStatusBadge");
  const hintNoticeText = document.getElementById("hintNoticeText");

  // Theme Elements
  const themeToggleBtn = document.getElementById("themeToggleBtn");
  const iconSun = document.getElementById("iconSun");
  const iconMoon = document.getElementById("iconMoon");

  // AI Configuration Elements
  const btnToggleAiSettings = document.getElementById("btnToggleAiSettings");
  const aiSettingsBody = document.getElementById("aiSettingsBody");
  const aiChevronIcon = document.getElementById("aiChevronIcon");
  const aiActiveBadge = document.getElementById("aiActiveBadge");
  const aiProviderSelect = document.getElementById("aiProviderSelect");
  const aiBaseUrlGroup = document.getElementById("aiBaseUrlGroup");
  const aiBaseUrlInput = document.getElementById("aiBaseUrlInput");
  const aiBaseUrlHint = document.getElementById("aiBaseUrlHint");
  const aiModelGroup = document.getElementById("aiModelGroup");
  const aiModelInput = document.getElementById("aiModelInput");
  const aiModelHint = document.getElementById("aiModelHint");
  const aiApiKeyGroup = document.getElementById("aiApiKeyGroup");
  const aiApiKeyInput = document.getElementById("aiApiKeyInput");
  const aiKeyHelpLink = document.getElementById("aiKeyHelpLink");
  const btnToggleApiKeyMask = document.getElementById("btnToggleApiKeyMask");
  const iconEye = document.getElementById("iconEye");
  const iconEyeOff = document.getElementById("iconEyeOff");
  const aiKeyStatusHint = document.getElementById("aiKeyStatusHint");
  const aiOllamaHelpCard = document.getElementById("aiOllamaHelpCard");
  const aiTestFeedback = document.getElementById("aiTestFeedback");
  const btnTestAiConnection = document.getElementById("btnTestAiConnection");
  const spinnerTestAi = document.getElementById("spinnerTestAi");
  const textTestAi = document.getElementById("textTestAi");
  const btnSaveAiConfig = document.getElementById("btnSaveAiConfig");
  const btnResetAiConfig = document.getElementById("btnResetAiConfig");

  const AI_METADATA = {
    groq: {
      defaultModel: "llama-3.3-70b-versatile",
      defaultUrl: "",
      needsKey: false,
      needsUrl: false,
      badgeText: "Magic Fill Cloud",
      helpUrl: "https://console.groq.com/keys",
      placeholder: "llama-3.3-70b-versatile",
    },
    openai: {
      defaultModel: "gpt-4o-mini",
      defaultUrl: "https://api.openai.com/v1",
      needsKey: true,
      needsUrl: false,
      badgeText: "OpenAI",
      helpUrl: "https://platform.openai.com/api-keys",
      placeholder: "gpt-4o-mini",
    },
    gemini: {
      defaultModel: "gemini-1.5-flash",
      defaultUrl: "https://generativelanguage.googleapis.com",
      needsKey: true,
      needsUrl: false,
      badgeText: "Gemini",
      helpUrl: "https://aistudio.google.com/app/apikey",
      placeholder: "gemini-1.5-flash",
    },
    openrouter: {
      defaultModel: "meta-llama/llama-3.3-70b-instruct",
      defaultUrl: "https://openrouter.ai/api/v1",
      needsKey: true,
      needsUrl: false,
      badgeText: "OpenRouter",
      helpUrl: "https://openrouter.ai/keys",
      placeholder: "meta-llama/llama-3.3-70b-instruct",
    },
    ollama: {
      defaultModel: "llama3.2",
      defaultUrl: "http://localhost:11434/v1",
      needsKey: false,
      needsUrl: true,
      badgeText: "Ollama (Local)",
      helpUrl: "https://ollama.com",
      placeholder: "llama3.2",
    },
    custom: {
      defaultModel: "custom-model",
      defaultUrl: "http://localhost:8000/v1",
      needsKey: true,
      needsUrl: true,
      badgeText: "Custom AI",
      helpUrl: "",
      placeholder: "model-identifier",
    },
  };

  const WEBSITE_BASE_URL = "http://localhost:4321";

  function applyTheme(theme) {
    if (theme === "light") {
      document.body.classList.remove("dark-theme");
      document.body.classList.add("light-theme");
      document.documentElement.setAttribute("data-theme", "light");
      if (iconSun) iconSun.classList.add("hidden");
      if (iconMoon) iconMoon.classList.remove("hidden");
    } else {
      document.body.classList.remove("light-theme");
      document.body.classList.add("dark-theme");
      document.documentElement.setAttribute("data-theme", "dark");
      if (iconSun) iconSun.classList.remove("hidden");
      if (iconMoon) iconMoon.classList.add("hidden");
    }
  }

  if (themeToggleBtn) {
    themeToggleBtn.addEventListener("click", () => {
      const isLight = document.body.classList.contains("light-theme");
      const nextTheme = isLight ? "dark" : "light";
      applyTheme(nextTheme);
      try {
        localStorage.setItem("magic_fill_theme", nextTheme);
      } catch (e) { }
      if (chrome.storage && chrome.storage.local) {
        chrome.storage.local.set({ magic_fill_theme: nextTheme });
      }
    });
  }

  function updateDetectionToggleUI(enabled) {
    if (toggleNewDataDetection) {
      toggleNewDataDetection.checked = enabled;
    }
    if (detectionStatusBadge) {
      detectionStatusBadge.textContent = enabled ? "ON" : "OFF";
      detectionStatusBadge.className = `detection-badge ${enabled ? "badge-on" : "badge-off"}`;
    }
    if (hintNoticeText) {
      if (enabled) {
        hintNoticeText.textContent = "New details you enter in web forms are automatically detected so you can save them to your vault with 1 click.";
      } else {
        hintNoticeText.textContent = "New data detection is turned OFF. Web forms will not prompt for changes. 1-click autofill remains fully active.";
      }
    }
  }

  if (toggleNewDataDetection) {
    toggleNewDataDetection.addEventListener("change", (e) => {
      const isEnabled = e.target.checked;
      updateDetectionToggleUI(isEnabled);

      // Save preference to chrome.storage.local
      if (chrome.storage && chrome.storage.local) {
        chrome.storage.local.set({ new_data_detection_enabled: isEnabled }, () => {
          // Immediately notify all active browser tabs
          if (chrome.tabs && chrome.tabs.query) {
            chrome.tabs.query({}, (tabs) => {
              tabs.forEach((tab) => {
                if (tab.id) {
                  chrome.tabs.sendMessage(
                    tab.id,
                    { action: "TOGGLE_NEW_DATA_DETECTION", enabled: isEnabled },
                    () => {
                      if (chrome.runtime.lastError) { }
                    }
                  );
                }
              });
            });
          }
        });
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

  function showAlert(message, type = "success") {
    if (!alertBoxEl) return;
    alertBoxEl.className = `alert alert-${type}`;
    const cleanMsg = (message || "").replace(/^[✓✕\s]+/, "");
    const icon = type === "success"
      ? `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" style="flex-shrink:0"><polyline points="20 6 9 17 4 12"/></svg>`
      : `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" style="flex-shrink:0"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>`;
    alertBoxEl.innerHTML = `<div style="display:flex; align-items:center; gap:8px;">${icon}<span>${escapeHtml(cleanMsg)}</span></div>`;
    alertBoxEl.classList.remove("hidden");
  }

  function hideAlert() {
    if (alertBoxEl) alertBoxEl.classList.add("hidden");
  }

  function setStatus(status, label) {
    if (!backendStatusEl) return;
    backendStatusEl.className = `status-badge status-${status}`;
    const txt = backendStatusEl.querySelector(".status-text");
    if (txt) txt.textContent = label;
  }

  function showAuthError(message) {
    if (authErrorBox) {
      authErrorBox.textContent = message;
      authErrorBox.classList.remove("hidden");
    }
  }

  function hideAuthError() {
    if (authErrorBox) {
      authErrorBox.classList.add("hidden");
    }
  }

  // -------------------------------------------------------------------------
  // AI Configuration UI Logic
  // -------------------------------------------------------------------------
  function updateAiSettingsVisibility(provider) {
    const meta = AI_METADATA[provider] || AI_METADATA.groq;

    // Model Group
    if (aiModelInput) {
      aiModelInput.placeholder = meta.placeholder;
      if (!aiModelInput.value || Object.values(AI_METADATA).some((m) => m.defaultModel === aiModelInput.value)) {
        aiModelInput.value = meta.defaultModel;
      }
    }

    // Base URL Group
    if (aiBaseUrlGroup) {
      if (meta.needsUrl) {
        aiBaseUrlGroup.classList.remove("hidden");
        if (aiBaseUrlInput && (!aiBaseUrlInput.value || Object.values(AI_METADATA).some((m) => m.defaultUrl === aiBaseUrlInput.value))) {
          aiBaseUrlInput.value = meta.defaultUrl;
        }
      } else {
        aiBaseUrlGroup.classList.add("hidden");
      }
    }

    // API Key Group
    if (aiApiKeyGroup) {
      if (meta.needsKey) {
        aiApiKeyGroup.classList.remove("hidden");
        if (aiKeyHelpLink) {
          if (meta.helpUrl) {
            aiKeyHelpLink.href = meta.helpUrl;
            aiKeyHelpLink.classList.remove("hidden");
          } else {
            aiKeyHelpLink.classList.add("hidden");
          }
        }
      } else {
        aiApiKeyGroup.classList.add("hidden");
      }
    }

    // Ollama Setup Help Card
    if (aiOllamaHelpCard) {
      if (provider === "ollama") {
        aiOllamaHelpCard.classList.remove("hidden");
      } else {
        aiOllamaHelpCard.classList.add("hidden");
      }
    }

    hideAiTestFeedback();
  }

  function showAiTestFeedback(message, isSuccess = true) {
    if (!aiTestFeedback) return;
    aiTestFeedback.className = `ai-test-feedback ${isSuccess ? "feedback-success" : "feedback-error"}`;
    const cleanMsg = (message || "").replace(/^[✓✕\s]+/, "");
    const icon = isSuccess
      ? `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" style="flex-shrink:0"><polyline points="20 6 9 17 4 12"/></svg>`
      : `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" style="flex-shrink:0"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>`;
    aiTestFeedback.innerHTML = `<div style="display:flex; align-items:center; gap:6px;">${icon}<span>${escapeHtml(cleanMsg)}</span></div>`;
    aiTestFeedback.classList.remove("hidden");
  }

  function hideAiTestFeedback() {
    if (aiTestFeedback) {
      aiTestFeedback.classList.add("hidden");
      aiTestFeedback.textContent = "";
    }
  }

  function updateAiBadge(provider, modelName, isActive = false) {
    if (!aiActiveBadge) return;
    if (!isActive || provider === "groq") {
      aiActiveBadge.textContent = "Default (Groq)";
      aiActiveBadge.className = "ai-provider-badge badge-default";
    } else {
      const meta = AI_METADATA[provider];
      const provName = meta ? meta.badgeText : provider.toUpperCase();
      aiActiveBadge.textContent = `${provName}`;
      aiActiveBadge.className = "ai-provider-badge badge-custom";
    }
  }

  // AI Settings Collapsible Panel Toggle
  if (btnToggleAiSettings && aiSettingsBody) {
    btnToggleAiSettings.addEventListener("click", () => {
      const isExpanded = btnToggleAiSettings.getAttribute("aria-expanded") === "true";
      const nextExpanded = !isExpanded;
      btnToggleAiSettings.setAttribute("aria-expanded", String(nextExpanded));
      if (nextExpanded) {
        aiSettingsBody.classList.remove("hidden");
        if (aiChevronIcon) aiChevronIcon.style.transform = "rotate(180deg)";
      } else {
        aiSettingsBody.classList.add("hidden");
        if (aiChevronIcon) aiChevronIcon.style.transform = "rotate(0deg)";
      }
    });
  }

  // Provider Dropdown Change
  if (aiProviderSelect) {
    aiProviderSelect.addEventListener("change", (e) => {
      const selected = e.target.value;
      updateAiSettingsVisibility(selected);
    });
  }

  // API Key Visibility Eye Toggle
  if (btnToggleApiKeyMask && aiApiKeyInput) {
    btnToggleApiKeyMask.addEventListener("click", () => {
      const isPassword = aiApiKeyInput.type === "password";
      aiApiKeyInput.type = isPassword ? "text" : "password";
      if (iconEye) iconEye.classList.toggle("hidden", isPassword);
      if (iconEyeOff) iconEyeOff.classList.toggle("hidden", !isPassword);
    });
  }

  // Test Connection Action
  if (btnTestAiConnection) {
    btnTestAiConnection.addEventListener("click", async () => {
      const provider = aiProviderSelect ? aiProviderSelect.value : "groq";
      const modelName = (aiModelInput && aiModelInput.value) ? aiModelInput.value.trim() : "";
      const baseUrl = (aiBaseUrlInput && aiBaseUrlInput.value) ? aiBaseUrlInput.value.trim() : "";
      const apiKey = (aiApiKeyInput && aiApiKeyInput.value) ? aiApiKeyInput.value.trim() : "";

      btnTestAiConnection.disabled = true;
      if (spinnerTestAi) spinnerTestAi.classList.remove("hidden");
      if (textTestAi) textTestAi.textContent = "Testing...";
      hideAiTestFeedback();

      chrome.runtime.sendMessage(
        {
          action: "TEST_AI_CONFIG",
          config: {
            provider: provider,
            model_name: modelName,
            api_base_url: baseUrl,
            api_key: apiKey,
          },
        },
        (res) => {
          btnTestAiConnection.disabled = false;
          if (spinnerTestAi) spinnerTestAi.classList.add("hidden");
          if (textTestAi) textTestAi.textContent = "Test Connection";

          if (chrome.runtime.lastError) {
            showAiTestFeedback(`Connection test error: ${chrome.runtime.lastError.message}`, false);
            return;
          }

          if (res && res.success) {
            const lat = res.latency_ms ? ` (${res.latency_ms}ms)` : "";
            showAiTestFeedback(`${res.message || "Connection verified"}${lat}`, true);
          } else {
            showAiTestFeedback(`${res && res.error ? res.error : "Failed to connect to provider"}`, false);
          }
        }
      );
    });
  }

  // Save AI Config Action
  if (btnSaveAiConfig) {
    btnSaveAiConfig.addEventListener("click", () => {
      const provider = aiProviderSelect ? aiProviderSelect.value : "groq";
      const modelName = (aiModelInput && aiModelInput.value) ? aiModelInput.value.trim() : "";
      const baseUrl = (aiBaseUrlInput && aiBaseUrlInput.value) ? aiBaseUrlInput.value.trim() : "";
      const apiKey = (aiApiKeyInput && aiApiKeyInput.value) ? aiApiKeyInput.value.trim() : "";

      btnSaveAiConfig.disabled = true;
      btnSaveAiConfig.textContent = "Saving...";

      chrome.runtime.sendMessage(
        {
          action: "SAVE_AI_CONFIG",
          config: {
            provider: provider,
            model_name: modelName,
            api_base_url: baseUrl,
            api_key: apiKey,
          },
        },
        (res) => {
          btnSaveAiConfig.disabled = false;
          btnSaveAiConfig.textContent = "Save Config";

          if (chrome.runtime.lastError || (res && !res.success)) {
            showAlert(res && res.error ? res.error : "Failed to save AI configuration", "error");
            return;
          }

          updateAiBadge(provider, modelName, provider !== "groq");
          showAlert(`Saved ${provider.toUpperCase()} configuration!`, "success");
        }
      );
    });
  }

  // Reset to Default AI Action
  if (btnResetAiConfig) {
    btnResetAiConfig.addEventListener("click", () => {
      btnResetAiConfig.disabled = true;
      chrome.runtime.sendMessage({ action: "RESET_AI_CONFIG" }, (res) => {
        btnResetAiConfig.disabled = false;
        if (aiProviderSelect) aiProviderSelect.value = "groq";
        if (aiModelInput) aiModelInput.value = AI_METADATA.groq.defaultModel;
        if (aiBaseUrlInput) aiBaseUrlInput.value = "";
        if (aiApiKeyInput) {
          aiApiKeyInput.value = "";
          aiApiKeyInput.placeholder = "Paste your API key here";
        }
        updateAiSettingsVisibility("groq");
        updateAiBadge("groq", AI_METADATA.groq.defaultModel, false);
        showAlert("Reset to Default Magic Fill AI (Groq)", "success");
      });
    });
  }

  function loadAiConfigOnOpen() {
    chrome.runtime.sendMessage({ action: "GET_AI_CONFIG" }, (res) => {
      if (chrome.runtime.lastError || !res || !res.success || !res.data) return;
      const cfg = res.data;
      if (aiProviderSelect) aiProviderSelect.value = cfg.provider || "groq";
      updateAiSettingsVisibility(cfg.provider || "groq");

      if (aiModelInput && cfg.model_name) {
        aiModelInput.value = cfg.model_name;
      }
      if (aiBaseUrlInput && cfg.api_base_url) {
        aiBaseUrlInput.value = cfg.api_base_url;
      }
      if (aiApiKeyInput) {
        if (cfg.masked_api_key) {
          aiApiKeyInput.placeholder = `Saved: ${cfg.masked_api_key}`;
        }
      }

      updateAiBadge(cfg.provider || "groq", cfg.model_name, cfg.is_active || cfg.provider !== "groq");
    });
  }

  // -------------------------------------------------------------------------
  // 1. High-Speed Direct Storage Initialization (< 15ms)
  // -------------------------------------------------------------------------
  function fastInit() {
    hideAlert();
    hideAuthError();

    // Query storage directly without waking background worker first
    if (chrome.storage && chrome.storage.local) {
      chrome.storage.local.get(
        ["magic_fill_token", "magic_fill_user", "magic_fill_theme", "cached_profile", "new_data_detection_enabled"],
        (items) => {
          // A. Synchronously apply theme
          const theme = items.magic_fill_theme || "dark";
          applyTheme(theme);

          // B. Apply New Data Detection toggle state (default: ON / true)
          const isDetectionOn = items.new_data_detection_enabled !== false;
          updateDetectionToggleUI(isDetectionOn);

          // C. Instantly render auth view from cached data
          if (items.magic_fill_token && items.magic_fill_user) {
            renderAuthenticatedView(items.magic_fill_user, items.cached_profile);
          } else {
            renderUnauthenticatedView();
          }

          // D. Background non-blocking network checks
          checkHealthNonBlocking();
          loadAiConfigOnOpen();
          if (items.magic_fill_token) {
            refreshUserProfileNonBlocking();
          }
        }
      );
    } else {
      renderUnauthenticatedView();
    }
  }

  // Non-blocking health check with 1.5s timeout
  function checkHealthNonBlocking() {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 1500);

      fetch("http://127.0.0.1:8000/health", { signal: controller.signal, cache: "no-store" })
        .then((res) => res.json())
        .then((data) => {
          clearTimeout(timeoutId);
          if (data && data.status === "healthy") {
            setStatus("online", "Connected");
          } else {
            setStatus("offline", "Offline");
          }
        })
        .catch(() => {
          clearTimeout(timeoutId);
          setStatus("offline", "Offline");
        });
    } catch {
      setStatus("offline", "Offline");
    }
  }

  // Non-blocking profile refresh
  function refreshUserProfileNonBlocking() {
    try {
      chrome.runtime.sendMessage({ action: "FETCH_USER_PROFILE" }, (profRes) => {
        if (chrome.runtime.lastError) return;
        if (profRes && profRes.sessionExpired) {
          showAlert("Your session has expired. Please sign in again.", "error");
          renderUnauthenticatedView();
          return;
        }

        if (profRes && profRes.success && profRes.data) {
          const profile = profRes.data;
          // Cache in local storage for next instant popup open
          chrome.storage.local.set({ cached_profile: profile });
          updateProfileDOM(profile);
        }
      });
    } catch (e) {
      console.warn("Profile refresh background error:", e);
    }
  }

  function renderUnauthenticatedView() {
    if (unauthenticatedSection) unauthenticatedSection.classList.remove("hidden");
    if (authenticatedSection) authenticatedSection.classList.add("hidden");
    if (autofillBtn) autofillBtn.disabled = true;
  }

  function renderAuthenticatedView(storedUser, cachedProfile) {
    if (unauthenticatedSection) unauthenticatedSection.classList.add("hidden");
    if (authenticatedSection) authenticatedSection.classList.remove("hidden");

    if (userIdBadgeEl && storedUser) {
      userIdBadgeEl.textContent = storedUser.email || "Active User";
    }

    if (autofillBtn) autofillBtn.disabled = false;

    if (cachedProfile) {
      updateProfileDOM(cachedProfile, storedUser);
    } else if (storedUser) {
      if (profileSummaryEl) {
        profileSummaryEl.innerHTML = `
          <div class="profile-name">${escapeHtml(storedUser.full_name || "Memory Vault Active")}</div>
          <div class="profile-meta"><span>${escapeHtml(storedUser.email || "")}</span></div>
        `;
      }
    }
  }

  function updateProfileDOM(profile, storedUser = null) {
    const info = profile.personal_info;
    const exps = profile.experiences || [];
    const customFields = profile.custom_fields || [];
    const docs = profile.documents || [];

    const displayName = (info && info.full_name) || (storedUser && storedUser.full_name) || "Verified Vault User";

    if (profileSummaryEl) {
      profileSummaryEl.innerHTML = `
        <div class="profile-name">${escapeHtml(displayName)}</div>
        <div class="profile-meta">
          ${(info && info.email) ? `<span>${escapeHtml(info.email)}</span>` : ""}
          ${(info && info.phone) ? ` &bull; <span>${escapeHtml(info.phone)}</span>` : ""}
        </div>
      `;
    }

    if (statDocCountEl) statDocCountEl.textContent = docs.length;
    if (statCustomCountEl) statCustomCountEl.textContent = customFields.length;
    if (statExpCountEl) statExpCountEl.textContent = exps.length;
    if (vaultStatsStripEl) vaultStatsStripEl.classList.remove("hidden");
    if (autofillBtn) autofillBtn.disabled = false;
  }

  // -------------------------------------------------------------------------
  // 2. Unauthenticated Actions
  // -------------------------------------------------------------------------
  if (btnSignInWebsite) {
    btnSignInWebsite.addEventListener("click", () => {
      chrome.tabs.create({ url: `${WEBSITE_BASE_URL}/login?source=extension` });
    });
  }

  if (linkCreateAccount) {
    linkCreateAccount.addEventListener("click", (e) => {
      e.preventDefault();
      chrome.tabs.create({ url: `${WEBSITE_BASE_URL}/register` });
    });
  }

  if (btnExchangeCode) {
    btnExchangeCode.addEventListener("click", () => {
      hideAuthError();
      const code = (inputAuthCode ? inputAuthCode.value : "").trim().toUpperCase();
      if (!code) {
        showAuthError("Please enter your single-use authorization code.");
        return;
      }

      btnExchangeCode.disabled = true;
      btnExchangeCode.textContent = "...";

      chrome.runtime.sendMessage({ action: "EXCHANGE_AUTH_CODE", code: code }, (res) => {
        btnExchangeCode.disabled = false;
        btnExchangeCode.textContent = "Link";

        if (res && res.success) {
          showAlert("Extension connected successfully!", "success");
          if (inputAuthCode) inputAuthCode.value = "";
          fastInit();
        } else {
          showAuthError(res ? res.error : "Failed to link extension. Code may have expired.");
        }
      });
    });
  }

  if (btnSyncFromTab) {
    btnSyncFromTab.addEventListener("click", async () => {
      hideAuthError();
      btnSyncFromTab.disabled = true;

      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      if (!tab || !tab.url || (!tab.url.startsWith("http://127.0.0.1:8000") && !tab.url.startsWith("http://localhost:8000") && !tab.url.startsWith("http://localhost:4321"))) {
        showAuthError("Please navigate to the Magic Fill website tab in Chrome or enter your code.");
        btnSyncFromTab.disabled = false;
        return;
      }

      try {
        const injection = await chrome.scripting.executeScript({
          target: { tabId: tab.id },
          func: () => {
            const token = localStorage.getItem("magic_fill_token");
            return { token };
          },
        });

        const tabData = injection && injection[0] ? injection[0].result : null;
        if (!tabData || !tabData.token) {
          showAuthError("You are not signed in on the Magic Fill tab. Please sign in on the website.");
          btnSyncFromTab.disabled = false;
          return;
        }

        const createCodeInjection = await chrome.scripting.executeScript({
          target: { tabId: tab.id },
          func: async () => {
            try {
              const token = localStorage.getItem("magic_fill_token");
              const res = await fetch("http://127.0.0.1:8000/api/auth/extension/create-code", {
                method: "POST",
                headers: {
                  "Content-Type": "application/json",
                  "Authorization": `Bearer ${token}`,
                },
                body: JSON.stringify({ client_id: "chrome-extension" }),
              });
              const json = await res.json();
              return json.success ? json.code : null;
            } catch {
              return null;
            }
          },
        });

        const code = createCodeInjection && createCodeInjection[0] ? createCodeInjection[0].result : null;
        if (!code) {
          showAuthError("Could not retrieve authorization code from website session.");
          btnSyncFromTab.disabled = false;
          return;
        }

        chrome.runtime.sendMessage({ action: "EXCHANGE_AUTH_CODE", code: code }, (res) => {
          btnSyncFromTab.disabled = false;
          if (res && res.success) {
            showAlert("Automatically synced and linked with website session!", "success");
            fastInit();
          } else {
            showAuthError(res ? res.error : "Failed to sync session.");
          }
        });
      } catch (err) {
        showAuthError(`Sync failed: ${err.message}`);
        btnSyncFromTab.disabled = false;
      }
    });
  }

  // -------------------------------------------------------------------------
  // 3. Authenticated Actions
  // -------------------------------------------------------------------------
  if (btnManageInfo) {
    btnManageInfo.addEventListener("click", () => {
      chrome.tabs.create({ url: `${WEBSITE_BASE_URL}/memory` });
    });
  }

  if (btnSignOut) {
    btnSignOut.addEventListener("click", () => {
      chrome.storage.local.remove(["magic_fill_token", "magic_fill_user", "cached_profile"], () => {
        showAlert("Signed out of extension successfully.", "success");
        fastInit();
      });
    });
  }

  // Autofill Action
  if (autofillBtn) {
    autofillBtn.addEventListener("click", async () => {
      hideAlert();
      autofillBtn.disabled = true;
      const originalBtnText = autofillBtn.querySelector(".btn-text").textContent;
      autofillBtn.querySelector(".btn-text").textContent = "Scanning Form...";

      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      if (!tab || !tab.id) {
        showAlert("Cannot access active browser tab.", "error");
        autofillBtn.disabled = false;
        autofillBtn.querySelector(".btn-text").textContent = originalBtnText;
        return;
      }

      chrome.tabs.sendMessage(tab.id, { action: "SCAN_PAGE_FIELDS" }, (scanRes) => {
        if (chrome.runtime.lastError || !scanRes || !scanRes.success) {
          showAlert("No supported form fields detected on this page.", "error");
          autofillBtn.disabled = false;
          autofillBtn.querySelector(".btn-text").textContent = originalBtnText;
          return;
        }

        const detectedFields = scanRes.fields || [];
        if (detectedFields.length === 0) {
          showAlert("No fillable input fields found on this page.", "error");
          autofillBtn.disabled = false;
          autofillBtn.querySelector(".btn-text").textContent = originalBtnText;
          return;
        }

        autofillBtn.querySelector(".btn-text").textContent = `AI matching (${detectedFields.length} fields)...`;

        chrome.runtime.sendMessage(
          {
            action: "MATCH_FORM_FIELDS",
            fields: detectedFields,
            formContext: scanRes.pageTitle || "",
          },
          (matchRes) => {
            autofillBtn.disabled = false;
            autofillBtn.querySelector(".btn-text").textContent = originalBtnText;

            if (matchRes && matchRes.sessionExpired) {
              showAlert("Session expired. Please sign in again.", "error");
              renderUnauthenticatedView();
              return;
            }

            if (!matchRes || !matchRes.success || !matchRes.data) {
              showAlert(matchRes ? matchRes.error : "Failed to communicate with matching engine.", "error");
              return;
            }

            const matchData = matchRes.data;
            const mappings = matchData.mappings || [];
            const unresolved = matchData.unresolved_fields || [];

            chrome.tabs.sendMessage(
              tab.id,
              {
                action: "UPDATE_VISUAL_STATUS",
                mappings: mappings,
                unresolvedFields: unresolved,
              },
              () => {
                if (chrome.runtime.lastError) {
                  // Tab closed or not ready, silently ignore
                }
              }
            );

            if (mappings.length === 0) {
              showAlert(`Detected ${matchData.total_detected} fields, but none matched your stored memory.`, "error");
              return;
            }

            chrome.tabs.sendMessage(tab.id, { action: "AUTOFILL_FIELDS", mappings: mappings }, (fillRes) => {
              if (chrome.runtime.lastError) {
                showAlert("Autofill completed.", "success");
                return;
              }
              const filledCount = fillRes && fillRes.success ? fillRes.filledCount : mappings.length;
              showAlert(`Autofilled ${filledCount} field${filledCount !== 1 ? "s" : ""} from memory!`, "success");
              renderMappingsList(mappings);
            });
          }
        );
      });
    });
  }

  function renderMappingsList(mappings) {
    if (!mappingsListEl) return;
    mappingsListEl.innerHTML = "";
    if (matchCountBadgeEl) matchCountBadgeEl.textContent = mappings.length;

    mappings.forEach((m) => {
      const item = document.createElement("div");
      item.className = "mapping-item";
      const badgeClass = m.source === "llm" ? "badge-llm" : "badge-det";
      const badgeLabel = m.source === "llm" ? "AI Matched" : "Direct Match";

      let displayVal = String(m.value || "");
      if (displayVal.length > 28) displayVal = displayVal.slice(0, 28) + "...";

      item.innerHTML = `
        <div class="mapping-info">
          <span class="mapping-key">${escapeHtml(m.memory_key)}</span>
          <span class="mapping-val">${escapeHtml(displayVal)}</span>
        </div>
        <span class="mapping-badge ${badgeClass}">${badgeLabel}</span>
      `;
      mappingsListEl.appendChild(item);
    });

    if (resultsSectionEl) resultsSectionEl.classList.remove("hidden");
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

  // Execute instant init
  fastInit();
});
