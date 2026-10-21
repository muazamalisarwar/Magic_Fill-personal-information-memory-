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

  // Theme Elements
  const themeToggleBtn = document.getElementById("themeToggleBtn");
  const iconSun = document.getElementById("iconSun");
  const iconMoon = document.getElementById("iconMoon");

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
      } catch (e) {}
      if (chrome.storage && chrome.storage.local) {
        chrome.storage.local.set({ magic_fill_theme: nextTheme });
      }
    });
  }

  function showAlert(message, type = "success") {
    if (!alertBoxEl) return;
    alertBoxEl.className = `alert alert-${type}`;
    alertBoxEl.textContent = message;
    alertBoxEl.classList.remove("hidden");
  }

  function hideAlert() {
    if (alertBoxEl) alertBoxEl.classList.add("hidden");
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

  function setStatus(status, label) {
    if (!backendStatusEl) return;
    backendStatusEl.className = `status-badge status-${status}`;
    const txt = backendStatusEl.querySelector(".status-text");
    if (txt) txt.textContent = label;
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
        ["magic_fill_token", "magic_fill_user", "magic_fill_theme", "cached_profile"],
        (items) => {
          // A. Synchronously apply theme
          const theme = items.magic_fill_theme || "dark";
          applyTheme(theme);

          // B. Instantly render auth view from cached data
          if (items.magic_fill_token && items.magic_fill_user) {
            renderAuthenticatedView(items.magic_fill_user, items.cached_profile);
          } else {
            renderUnauthenticatedView();
          }

          // C. Background non-blocking network checks
          checkHealthNonBlocking();
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
          showAlert("✓ Extension connected successfully!", "success");
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
            showAlert("✓ Automatically synced and linked with website session!", "success");
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

            chrome.tabs.sendMessage(tab.id, {
              action: "UPDATE_VISUAL_STATUS",
              mappings: mappings,
              unresolvedFields: unresolved,
            });

            if (mappings.length === 0) {
              showAlert(`Detected ${matchData.total_detected} fields, but none matched your stored memory.`, "error");
              return;
            }

            chrome.tabs.sendMessage(tab.id, { action: "AUTOFILL_FIELDS", mappings: mappings }, (fillRes) => {
              const filledCount = fillRes && fillRes.success ? fillRes.filledCount : mappings.length;
              showAlert(`✓ Groq AI autofilled ${filledCount} field${filledCount !== 1 ? "s" : ""}!`, "success");
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
