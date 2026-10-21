/**
 * Magic Fill — Intelligent Personal Memory & Autofill Engine
 * Minimalist Modern Light-Theme SaaS Workspace (Production Grade)
 * Handles Knowledge Ingestion, Document Studio, Memory Vault,
 * Intelligent Form Autofill, and Consent-Based Manual Form Learning.
 */

document.addEventListener("DOMContentLoaded", () => {
  // Elements - Header & Metrics
  const backendBadge = document.getElementById("backendBadge");
  const backendStatusText = document.getElementById("backendStatusText");
  const metricUserName = document.getElementById("metricUserName");
  const metricUserSub = document.getElementById("metricUserSub");
  const metricDocCount = document.getElementById("metricDocCount");
  const metricCustomCount = document.getElementById("metricCustomCount");
  const metricExperienceCount = document.getElementById("metricExperienceCount");
  const docBadgeCount = document.getElementById("docBadgeCount");
  const vaultBadgeCount = document.getElementById("vaultBadgeCount");
  const btnExportVaultJson = document.getElementById("btnExportVaultJson");

  // Tab 1: Ingestion Elements
  const rawTextInput = document.getElementById("rawTextInput");
  const charCountLabel = document.getElementById("charCountLabel");
  const fileInput = document.getElementById("fileInput");
  const dropZone = document.getElementById("dropZone");
  const selectedFileName = document.getElementById("selectedFileName");
  const btnProcessAI = document.getElementById("btnProcessAI");
  const btnProcessText = document.getElementById("btnProcessText");
  const btnClearInput = document.getElementById("btnClearInput");

  // Presets Tab 1
  const chipFullBio = document.getElementById("chipFullBio");
  const chipGenderBio = document.getElementById("chipGenderBio");
  const chipFriendName = document.getElementById("chipFriendName");
  const chipUpdateEmail = document.getElementById("chipUpdateEmail");
  const chipEmergency = document.getElementById("chipEmergency");

  // Inspector Elements
  const extractionPlaceholder = document.getElementById("extractionPlaceholder");
  const extractionResultBox = document.getElementById("extractionResultBox");
  const extractionStatusBadge = document.getElementById("extractionStatusBadge");
  const identityNotice = document.getElementById("identityNotice");
  const protectionTitle = document.getElementById("protectionTitle");
  const protectionDesc = document.getElementById("protectionDesc");
  const extractionSummaryGrid = document.getElementById("extractionSummaryGrid");
  const jsonPreviewBox = document.getElementById("jsonPreviewBox");
  const btnCopyJson = document.getElementById("btnCopyJson");

  // Tab 2: Document Studio Elements
  const docDropZone = document.getElementById("docDropZone");
  const docFileInput = document.getElementById("docFileInput");
  const docFileSelectedName = document.getElementById("docFileSelectedName");
  const docLivePreviewBox = document.getElementById("docLivePreviewBox");
  const docLivePreviewImg = document.getElementById("docLivePreviewImg");
  const docLivePreviewName = document.getElementById("docLivePreviewName");
  const docLivePreviewSize = document.getElementById("docLivePreviewSize");
  const docAutoDetectedTag = document.getElementById("docAutoDetectedTag");
  const btnRemoveDocFile = document.getElementById("btnRemoveDocFile");
  const docDescriptionInput = document.getElementById("docDescriptionInput");
  const btnSaveDocument = document.getElementById("btnSaveDocument");
  const documentsGalleryList = document.getElementById("documentsGalleryList");
  const docGalleryCountBadge = document.getElementById("docGalleryCountBadge");
  const docGallerySearch = document.getElementById("docGallerySearch");

  // Document Preset Chips
  const chipDescCnicFront = document.getElementById("chipDescCnicFront");
  const chipDescCnicBack = document.getElementById("chipDescCnicBack");
  const chipDescProfile = document.getElementById("chipDescProfile");
  const chipDescPassport = document.getElementById("chipDescPassport");
  const chipDescDegree = document.getElementById("chipDescDegree");

  // Tab 3: Vault Elements
  const memoryVaultContent = document.getElementById("memoryVaultContent");
  const btnClearMemory = document.getElementById("btnClearMemory");
  const btnToggleAddCustom = document.getElementById("btnToggleAddCustom");
  const addCustomFieldBar = document.getElementById("addCustomFieldBar");
  const btnSaveCustomField = document.getElementById("btnSaveCustomField");
  const btnCancelAddCustom = document.getElementById("btnCancelAddCustom");
  const newFieldKey = document.getElementById("newFieldKey");
  const newFieldLabel = document.getElementById("newFieldLabel");
  const newFieldValue = document.getElementById("newFieldValue");
  const newFieldCategory = document.getElementById("newFieldCategory");
  const vaultSearchInput = document.getElementById("vaultSearchInput");

  // Tab 4: Playground Elements
  const btnSimulateAutofill = document.getElementById("btnSimulateAutofill");
  const btnClearForm = document.getElementById("btnClearForm");
  const btnToggleExtensionGuide = document.getElementById("btnToggleExtensionGuide");
  const extensionGuideBox = document.getElementById("extensionGuideBox");
  const autofillSummaryBar = document.getElementById("autofillSummaryBar");
  const autofillStatsText = document.getElementById("autofillStatsText");

  // Lightbox Modal Elements
  const imageLightboxModal = document.getElementById("imageLightboxModal");
  const lightboxTitle = document.getElementById("lightboxTitle");
  const lightboxImg = document.getElementById("lightboxImg");
  const lightboxCloseBtn = document.getElementById("lightboxCloseBtn");

  // Toast Container
  const toastContainer = document.getElementById("toastContainer");

  // State Management
  let currentUploadedFile = null;
  let currentDocFile = null;
  let currentDocDataUri = null;
  let activeProfileCache = null;
  let savedDocumentsList = [];
  let currentDocFilter = "all";
  let currentVaultFilter = "all";

  // -------------------------------------------------------------------------
  // Auth Elements & State Management
  // -------------------------------------------------------------------------
  const TOKEN_STORAGE_KEY = "magic_fill_token";
  let currentAuthToken = localStorage.getItem(TOKEN_STORAGE_KEY) || null;
  let currentAuthUser = null;

  const navAuthLoggedOut = document.getElementById("navAuthLoggedOut");
  const navAuthLoggedIn = document.getElementById("navAuthLoggedIn");
  const btnNavLogin = document.getElementById("btnNavLogin");
  const btnNavRegister = document.getElementById("btnNavRegister");
  const navUserAvatar = document.getElementById("navUserAvatar");
  const navUserEmail = document.getElementById("navUserEmail");
  const btnNavConnectExt = document.getElementById("btnNavConnectExt");
  const btnNavLogout = document.getElementById("btnNavLogout");

  const authModal = document.getElementById("authModal");
  const authModalClose = document.getElementById("authModalClose");
  const authTabBtnLogin = document.getElementById("authTabBtnLogin");
  const authTabBtnRegister = document.getElementById("authTabBtnRegister");
  const loginForm = document.getElementById("loginForm");
  const loginEmail = document.getElementById("loginEmail");
  const loginPassword = document.getElementById("loginPassword");
  const loginErrorBox = document.getElementById("loginErrorBox");
  const btnLoginSubmit = document.getElementById("btnLoginSubmit");
  const linkSwitchToRegister = document.getElementById("linkSwitchToRegister");

  const registerForm = document.getElementById("registerForm");
  const regFullName = document.getElementById("regFullName");
  const regEmail = document.getElementById("regEmail");
  const regPassword = document.getElementById("regPassword");
  const regPasswordConfirm = document.getElementById("regPasswordConfirm");
  const registerErrorBox = document.getElementById("registerErrorBox");
  const btnRegisterSubmit = document.getElementById("btnRegisterSubmit");
  const linkSwitchToLogin = document.getElementById("linkSwitchToLogin");

  const onboardingModal = document.getElementById("onboardingModal");
  const onboardingUserName = document.getElementById("onboardingUserName");
  const btnOnboardingConnect = document.getElementById("btnOnboardingConnect");
  const btnOnboardingContinue = document.getElementById("btnOnboardingContinue");

  const websiteAuthGateway = document.getElementById("websiteAuthGateway");
  const privateWorkstation = document.getElementById("privateWorkstation");
  const mainNavTabs = document.getElementById("mainNavTabs");

  // Simplify.jobs Exact Landing Page Controls
  const simplifyQuickAuthDrawer = document.getElementById("simplifyQuickAuthDrawer");
  const btnQuickAuthClose = document.getElementById("btnQuickAuthClose");
  const heroBtnGetStarted = document.getElementById("heroBtnGetStarted");
  const btnBottomGetStarted = document.getElementById("btnBottomGetStarted");
  const btnToggleStudio = document.getElementById("btnToggleStudio");

  const gatewayTabBtnLogin = document.getElementById("gatewayTabBtnLogin");
  const gatewayTabBtnRegister = document.getElementById("gatewayTabBtnRegister");
  const gatewayLoginForm = document.getElementById("gatewayLoginForm");
  const gatewayLoginEmail = document.getElementById("gatewayLoginEmail");
  const gatewayLoginPassword = document.getElementById("gatewayLoginPassword");
  const gatewayLoginErrorBox = document.getElementById("gatewayLoginErrorBox");
  const btnGatewayLoginSubmit = document.getElementById("btnGatewayLoginSubmit");
  const linkGatewayToRegister = document.getElementById("linkGatewayToRegister");

  const gatewayRegisterForm = document.getElementById("gatewayRegisterForm");
  const gatewayRegFullName = document.getElementById("gatewayRegFullName");
  const gatewayRegEmail = document.getElementById("gatewayRegEmail");
  const gatewayRegPassword = document.getElementById("gatewayRegPassword");
  const gatewayRegPasswordConfirm = document.getElementById("gatewayRegPasswordConfirm");
  const gatewayRegisterErrorBox = document.getElementById("gatewayRegisterErrorBox");
  const btnGatewayRegisterSubmit = document.getElementById("btnGatewayRegisterSubmit");
  const linkGatewayToLogin = document.getElementById("linkGatewayToLogin");

  const extensionAuthModal = document.getElementById("extensionAuthModal");
  const extAuthModalClose = document.getElementById("extAuthModalClose");
  const extAuthUserEmail = document.getElementById("extAuthUserEmail");
  const displayAuthCode = document.getElementById("displayAuthCode");
  const btnCopyAuthCode = document.getElementById("btnCopyAuthCode");
  const btnExtAuthDone = document.getElementById("btnExtAuthDone");

  function openQuickAuth(mode = "login") {
    if (currentAuthToken && currentAuthUser) {
      if (privateWorkstation && privateWorkstation.classList.contains("hidden")) {
        privateWorkstation.classList.remove("hidden");
        if (websiteAuthGateway) websiteAuthGateway.classList.add("hidden");
        if (btnToggleStudio) btnToggleStudio.innerHTML = "<span>&larr; View Showcase</span>";
      }
      window.scrollTo({ top: 0, behavior: "smooth" });
      return;
    }
    if (simplifyQuickAuthDrawer) {
      simplifyQuickAuthDrawer.classList.remove("hidden");
      switchGatewayAuthTab(mode);
      const targetInput = mode === "register" ? gatewayRegFullName : gatewayLoginEmail;
      if (targetInput) setTimeout(() => targetInput.focus(), 250);
      setTimeout(() => {
        if (typeof renderGoogleButtons === "function") renderGoogleButtons();
      }, 50);
    } else {
      openAuthModal(mode);
    }
  }

  function closeQuickAuth() {
    if (simplifyQuickAuthDrawer) {
      simplifyQuickAuthDrawer.classList.add("hidden");
    }
  }

  async function authFetch(url, options = {}) {
    const headers = options.headers ? { ...options.headers } : {};
    if (currentAuthToken) {
      headers["Authorization"] = `Bearer ${currentAuthToken}`;
    }
    const mergedOptions = { ...options, headers };
    const res = await fetch(url, mergedOptions);
    if (res.status === 401 && currentAuthToken) {
      handleLogout(false, "Session expired. Please sign in again.");
    }
    return res;
  }

  function updateAuthUI(isLoggedIn, user = null) {
    closeQuickAuth();
    if (isLoggedIn && user) {
      currentAuthUser = user;
      if (websiteAuthGateway) websiteAuthGateway.classList.add("hidden");
      if (privateWorkstation) privateWorkstation.classList.remove("hidden");
      if (mainNavTabs) mainNavTabs.classList.remove("hidden");
      if (btnExportVaultJson) btnExportVaultJson.classList.remove("hidden");
      if (btnToggleStudio) btnToggleStudio.innerHTML = "<span>&larr; View Showcase</span>";

      if (navAuthLoggedOut) navAuthLoggedOut.classList.add("hidden");
      if (navAuthLoggedIn) navAuthLoggedIn.classList.remove("hidden");
      if (navUserEmail) navUserEmail.textContent = user.email || "user@example.com";
      if (navUserAvatar) {

        if (user.avatar_url) {
          navUserAvatar.innerHTML = `<img src="${escapeHtml(user.avatar_url)}" alt="Avatar" referrerpolicy="no-referrer" style="width:100%;height:100%;border-radius:50%;object-fit:cover;">`;
        } else {
          const initial = (user.full_name || user.email || "U").charAt(0).toUpperCase();
          navUserAvatar.textContent = initial;
        }
      }
      if (metricUserSub) metricUserSub.textContent = `Account: ${user.email}`;

    } else {
      currentAuthUser = null;
      if (websiteAuthGateway) websiteAuthGateway.classList.remove("hidden");
      if (privateWorkstation) privateWorkstation.classList.add("hidden");
      if (mainNavTabs) mainNavTabs.classList.add("hidden");
      if (btnExportVaultJson) btnExportVaultJson.classList.add("hidden");
      if (btnToggleStudio) btnToggleStudio.innerHTML = "<span>Memory Studio &rarr;</span>";

      if (navAuthLoggedOut) navAuthLoggedOut.classList.remove("hidden");
      if (navAuthLoggedIn) navAuthLoggedIn.classList.add("hidden");
      if (metricUserName) metricUserName.textContent = "—";
      if (metricDocCount) metricDocCount.textContent = "0";
      if (metricCustomCount) metricCustomCount.textContent = "0";
      if (metricExperienceCount) metricExperienceCount.textContent = "0";
      if (metricUserSub) metricUserSub.textContent = "Personal Knowledge Base & Autofill Profile";
      ensureGatewayVideosPlay();
    }
  }

  function ensureGatewayVideosPlay() {
    const videos = document.querySelectorAll(".gateway-showcase-video, .gateway-bg-video, .hero-showcase-video");
    videos.forEach((v) => {
      v.muted = true;
      v.loop = true;
      const playPromise = v.play();
      if (playPromise !== undefined) {
        playPromise.catch(() => {
          const onFirstInteraction = () => {
            v.play().catch(() => {});
          };
          window.addEventListener("click", onFirstInteraction, { once: true });
          window.addEventListener("scroll", onFirstInteraction, { once: true });
          window.addEventListener("keydown", onFirstInteraction, { once: true });
        });
      }
    });
  }

  function openAuthModal(mode = "login") {
    if (!authModal) return;
    authModal.classList.remove("hidden");
    if (loginErrorBox) loginErrorBox.classList.add("hidden");
    if (registerErrorBox) registerErrorBox.classList.add("hidden");
    if (mode === "register") {
      switchAuthTab("register");
    } else {
      switchAuthTab("login");
    }
  }

  function closeAuthModal() {
    if (authModal) authModal.classList.add("hidden");
  }

  function switchAuthTab(tab) {
    if (tab === "register") {
      if (authTabBtnRegister) {
        authTabBtnRegister.classList.add("active");
        authTabBtnRegister.setAttribute("aria-selected", "true");
      }
      if (authTabBtnLogin) {
        authTabBtnLogin.classList.remove("active");
        authTabBtnLogin.setAttribute("aria-selected", "false");
      }
      if (registerForm) registerForm.classList.remove("hidden");
      if (loginForm) loginForm.classList.add("hidden");
      if (regFullName) regFullName.focus();
    } else {
      if (authTabBtnLogin) {
        authTabBtnLogin.classList.add("active");
        authTabBtnLogin.setAttribute("aria-selected", "true");
      }
      if (authTabBtnRegister) {
        authTabBtnRegister.classList.remove("active");
        authTabBtnRegister.setAttribute("aria-selected", "false");
      }
      if (loginForm) loginForm.classList.remove("hidden");
      if (registerForm) registerForm.classList.add("hidden");
      if (loginEmail) loginEmail.focus();
    }
  }

  async function generateExtensionAuthCode() {
    if (!currentAuthToken) {
      showToast("Please sign in first to connect the extension", "error");
      openAuthModal("login");
      return;
    }
    if (extensionAuthModal) extensionAuthModal.classList.remove("hidden");
    if (extAuthUserEmail) extAuthUserEmail.textContent = currentAuthUser ? currentAuthUser.email : "user@example.com";
    if (displayAuthCode) displayAuthCode.value = "Generating code...";

    try {
      const res = await authFetch("/api/auth/extension/create-code", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ client_id: "chrome-extension" }),
      });
      const data = await res.json();
      if (!res.ok || !data.success) throw new Error(data.message || "Failed to generate code");
      const authCode = (data.data && data.data.code) ? data.data.code : data.code;
      if (displayAuthCode) displayAuthCode.value = authCode;
    } catch (err) {
      if (displayAuthCode) displayAuthCode.value = "Error generating code";
      showToast(`Failed to generate extension code: ${err.message}`, "error");
    }
  }

  function handleLogout(notify = true, customMsg = null) {
    localStorage.removeItem(TOKEN_STORAGE_KEY);
    localStorage.removeItem("magic_fill_access_token");
    localStorage.removeItem("magic_fill_auth_token");
    localStorage.removeItem("magic_fill_user");
    currentAuthToken = null;
    currentAuthUser = null;
    activeProfileCache = null;
    savedDocumentsList = [];
    updateAuthUI(false);
    if (notify) {
      showToast(customMsg || "Signed out successfully", "success");
    }
  }

  // Gateway Auth Tabs Switcher
  function switchGatewayAuthTab(tab) {
    if (tab === "register") {
      if (gatewayTabBtnRegister) {
        gatewayTabBtnRegister.classList.add("active");
        gatewayTabBtnRegister.setAttribute("aria-selected", "true");
      }
      if (gatewayTabBtnLogin) {
        gatewayTabBtnLogin.classList.remove("active");
        gatewayTabBtnLogin.setAttribute("aria-selected", "false");
      }
      if (gatewayRegisterForm) gatewayRegisterForm.classList.remove("hidden");
      if (gatewayLoginForm) gatewayLoginForm.classList.add("hidden");
      if (gatewayRegFullName) gatewayRegFullName.focus();
    } else {
      if (gatewayTabBtnLogin) {
        gatewayTabBtnLogin.classList.add("active");
        gatewayTabBtnLogin.setAttribute("aria-selected", "true");
      }
      if (gatewayTabBtnRegister) {
        gatewayTabBtnRegister.classList.remove("active");
        gatewayTabBtnRegister.setAttribute("aria-selected", "false");
      }
      if (gatewayLoginForm) gatewayLoginForm.classList.remove("hidden");
      if (gatewayRegisterForm) gatewayRegisterForm.classList.add("hidden");
      if (gatewayLoginEmail) gatewayLoginEmail.focus();
    }
    setTimeout(() => {
      if (typeof renderGoogleButtons === "function") renderGoogleButtons();
    }, 50);
  }


  if (gatewayTabBtnLogin) gatewayTabBtnLogin.addEventListener("click", () => switchGatewayAuthTab("login"));
  if (gatewayTabBtnRegister) gatewayTabBtnRegister.addEventListener("click", () => switchGatewayAuthTab("register"));
  if (linkGatewayToRegister) {
    linkGatewayToRegister.addEventListener("click", (e) => {
      e.preventDefault();
      switchGatewayAuthTab("register");
    });
  }
  if (linkGatewayToLogin) {
    linkGatewayToLogin.addEventListener("click", (e) => {
      e.preventDefault();
      switchGatewayAuthTab("login");
    });
  }

  // Gateway Login Form Submission
  if (gatewayLoginForm) {
    gatewayLoginForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      if (gatewayLoginErrorBox) gatewayLoginErrorBox.classList.add("hidden");
      const email = gatewayLoginEmail ? gatewayLoginEmail.value.trim() : "";
      const password = gatewayLoginPassword ? gatewayLoginPassword.value : "";

      if (!email || !password) {
        if (gatewayLoginErrorBox) {
          gatewayLoginErrorBox.textContent = "Please enter both email and password.";
          gatewayLoginErrorBox.classList.remove("hidden");
        }
        return;
      }

      if (btnGatewayLoginSubmit) {
        btnGatewayLoginSubmit.disabled = true;
        btnGatewayLoginSubmit.innerHTML = "<span>Signing In...</span>";
      }

      try {
        const res = await fetch("/api/auth/login", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email, password }),
        });
        const data = await res.json();
        if (!res.ok || !data.success) {
          let errMsg = data.message;
          if (data.details && Array.isArray(data.details)) {
            errMsg = data.details.map((d) => d.message || d.msg || `${d.field}: invalid`).join("; ");
          } else if (data.detail) {
            errMsg = Array.isArray(data.detail) ? data.detail.map((d) => d.msg || d).join("; ") : data.detail;
          }
          if (data.error_code === "USE_GOOGLE_SIGN_IN") {
            errMsg = data.message || "This account was registered with Google. Please click 'Continue with Google' to sign in.";
          }
          throw new Error(errMsg || "Invalid email or password");
        }

        const authData = data.data || data;
        currentAuthToken = authData.access_token;
        localStorage.setItem(TOKEN_STORAGE_KEY, currentAuthToken);
        localStorage.setItem("magic_fill_access_token", currentAuthToken);
        localStorage.setItem("magic_fill_auth_token", currentAuthToken);
        if (authData.user) localStorage.setItem("magic_fill_user", JSON.stringify(authData.user));
        updateAuthUI(true, authData.user);
        gatewayLoginForm.reset();
        showToast(`Welcome back, ${authData.user.full_name || authData.user.email}!`, "success");

        const search = new URLSearchParams(window.location.search);
        if (search.get("source") === "extension") {
          generateExtensionAuthCode();
        } else if (search.get("redirect") === "vault" || window.location.hash === "#vault") {
          switchToTab("vault");
        }

        loadStoredMemory();
      } catch (err) {
        if (gatewayLoginErrorBox) {
          gatewayLoginErrorBox.textContent = err.message;
          gatewayLoginErrorBox.classList.remove("hidden");
        }
      } finally {
        if (btnGatewayLoginSubmit) {
          btnGatewayLoginSubmit.disabled = false;
          btnGatewayLoginSubmit.innerHTML = "<span>Sign In to Vault &rarr;</span>";
        }
      }
    });
  }

  // Gateway Register Form Submission
  if (gatewayRegisterForm) {
    gatewayRegisterForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      if (gatewayRegisterErrorBox) gatewayRegisterErrorBox.classList.add("hidden");
      const fullName = gatewayRegFullName ? gatewayRegFullName.value.trim() : "";
      const email = gatewayRegEmail ? gatewayRegEmail.value.trim() : "";
      const password = gatewayRegPassword ? gatewayRegPassword.value : "";
      const confirm = gatewayRegPasswordConfirm ? gatewayRegPasswordConfirm.value : "";

      if (!email || !password) {
        if (gatewayRegisterErrorBox) {
          gatewayRegisterErrorBox.textContent = "Email and password are required.";
          gatewayRegisterErrorBox.classList.remove("hidden");
        }
        return;
      }
      if (password.length < 6) {
        if (gatewayRegisterErrorBox) {
          gatewayRegisterErrorBox.textContent = "Password must be at least 6 characters long.";
          gatewayRegisterErrorBox.classList.remove("hidden");
        }
        return;
      }
      if (password !== confirm) {
        if (gatewayRegisterErrorBox) {
          gatewayRegisterErrorBox.textContent = "Passwords do not match.";
          gatewayRegisterErrorBox.classList.remove("hidden");
        }
        return;
      }

      if (btnGatewayRegisterSubmit) {
        btnGatewayRegisterSubmit.disabled = true;
        btnGatewayRegisterSubmit.innerHTML = "<span>Creating Account...</span>";
      }

      try {
        const res = await fetch("/api/auth/register", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ full_name: fullName || null, email, password }),
        });
        const data = await res.json();
        if (!res.ok || !data.success) {
          let errMsg = data.message;
          if (data.details && Array.isArray(data.details)) {
            errMsg = data.details.map((d) => d.message || d.msg || `${d.field}: invalid`).join("; ");
          } else if (data.detail) {
            errMsg = Array.isArray(data.detail) ? data.detail.map((d) => d.msg || d).join("; ") : data.detail;
          }
          if (data.error_code === "DUPLICATE_EMAIL") {
            errMsg = "An account with this email address already exists. Please sign in instead.";
          }
          throw new Error(errMsg || "Registration failed. Please check your information.");
        }

        const authData = data.data || data;
        currentAuthToken = authData.access_token;
        localStorage.setItem(TOKEN_STORAGE_KEY, currentAuthToken);
        localStorage.setItem("magic_fill_access_token", currentAuthToken);
        localStorage.setItem("magic_fill_auth_token", currentAuthToken);
        if (authData.user) localStorage.setItem("magic_fill_user", JSON.stringify(authData.user));
        updateAuthUI(true, authData.user);
        gatewayRegisterForm.reset();
        showToast("Account created successfully!", "success");

        if (onboardingModal) {
          if (onboardingUserName) onboardingUserName.textContent = authData.user.full_name || authData.user.email;
          onboardingModal.classList.remove("hidden");
        }

        loadStoredMemory();
      } catch (err) {
        if (gatewayRegisterErrorBox) {
          gatewayRegisterErrorBox.textContent = err.message;
          gatewayRegisterErrorBox.classList.remove("hidden");
        }
      } finally {
        if (btnGatewayRegisterSubmit) {
          btnGatewayRegisterSubmit.disabled = false;
          btnGatewayRegisterSubmit.innerHTML = "<span>Create Account &amp; Setup Extension &rarr;</span>";
        }
      }
    });
  }

  // Auth Button Listeners & Simplify Landing Page Actions
  if (btnNavLogin) {
    btnNavLogin.addEventListener("click", (e) => {
      e.preventDefault();
      openQuickAuth("login");
    });
  }

  if (btnNavRegister) {
    btnNavRegister.addEventListener("click", (e) => {
      e.preventDefault();
      openQuickAuth("register");
    });
  }

  if (heroBtnGetStarted) {
    heroBtnGetStarted.addEventListener("click", (e) => {
      e.preventDefault();
      openQuickAuth("register");
    });
  }

  if (btnBottomGetStarted) {
    btnBottomGetStarted.addEventListener("click", (e) => {
      e.preventDefault();
      openQuickAuth("register");
    });
  }

  if (btnQuickAuthClose) {
    btnQuickAuthClose.addEventListener("click", (e) => {
      e.preventDefault();
      closeQuickAuth();
    });
  }

  if (simplifyQuickAuthDrawer) {
    simplifyQuickAuthDrawer.addEventListener("click", (e) => {
      if (e.target === simplifyQuickAuthDrawer) {
        closeQuickAuth();
      }
    });
  }

  if (btnToggleStudio) {
    btnToggleStudio.addEventListener("click", () => {
      if (!currentAuthToken || !currentAuthUser) {
        openQuickAuth("login");
        return;
      }
      if (privateWorkstation && privateWorkstation.classList.contains("hidden")) {
        privateWorkstation.classList.remove("hidden");
        if (websiteAuthGateway) websiteAuthGateway.classList.add("hidden");
        btnToggleStudio.innerHTML = "<span>&larr; View Showcase</span>";
        window.scrollTo({ top: 0, behavior: "smooth" });
      } else if (privateWorkstation) {
        privateWorkstation.classList.add("hidden");
        if (websiteAuthGateway) websiteAuthGateway.classList.remove("hidden");
        btnToggleStudio.innerHTML = "<span>Memory Studio &rarr;</span>";
        window.scrollTo({ top: 0, behavior: "smooth" });
      }
    });
  }

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      closeQuickAuth();
      closeAuthModal();
      if (imageLightboxModal) imageLightboxModal.classList.add("hidden");
    }
  });

  if (authModalClose) authModalClose.addEventListener("click", closeAuthModal);
  if (authTabBtnLogin) authTabBtnLogin.addEventListener("click", () => switchAuthTab("login"));
  if (authTabBtnRegister) authTabBtnRegister.addEventListener("click", () => switchAuthTab("register"));
  if (linkSwitchToRegister) {
    linkSwitchToRegister.addEventListener("click", (e) => {
      e.preventDefault();
      switchAuthTab("register");
    });
  }
  if (linkSwitchToLogin) {
    linkSwitchToLogin.addEventListener("click", (e) => {
      e.preventDefault();
      switchAuthTab("login");
    });
  }
  if (btnNavLogout) btnNavLogout.addEventListener("click", () => handleLogout(true));
  if (btnNavConnectExt) btnNavConnectExt.addEventListener("click", generateExtensionAuthCode);

  // -------------------------------------------------------------------------
  // Google Identity Services (GIS) Integration ("Continue with Google")
  // -------------------------------------------------------------------------
  let googleClientId = "456121937465-pog6ha9pfgl8cjru833rer0o74j44tbe.apps.googleusercontent.com";
  let googleGisInitialized = false;

  async function loadGoogleAuthConfig() {
    try {
      const res = await fetch("/api/auth/config");
      if (res.ok) {
        const json = await res.json();
        if (json.success && json.data && json.data.google_client_id) {
          googleClientId = json.data.google_client_id;
        }
      }
    } catch (err) {
      console.warn("Could not fetch auth config, using configured fallback Google Client ID:", err);
    }
  }

  function renderGoogleButtons() {
    if (!window.google || !window.google.accounts || !window.google.accounts.id) {
      return false;
    }

    try {
      if (!googleGisInitialized) {
        window.google.accounts.id.initialize({
          client_id: googleClientId,
          callback: handleGoogleAuthCallback,
          auto_select: false,
          cancel_on_tap_outside: true,
        });
        googleGisInitialized = true;
      }

      const signinSlot = document.getElementById("googleSignInButton");
      const signupSlot = document.getElementById("googleSignUpButton");
      const sampleSlot = signinSlot || signupSlot;
      const slotWidth = sampleSlot && sampleSlot.clientWidth ? sampleSlot.clientWidth : (window.innerWidth - 64);
      const computedBtnWidth = Math.min(320, Math.max(200, Math.floor(slotWidth)));

      if (signinSlot && (!gatewayLoginForm || !gatewayLoginForm.classList.contains("hidden"))) {
        signinSlot.innerHTML = "";
        window.google.accounts.id.renderButton(signinSlot, {
          type: "standard",
          theme: "outline",
          size: "large",
          text: "continue_with",
          shape: "rectangular",
          logo_alignment: "left",
          width: computedBtnWidth,
        });
      }

      if (signupSlot && (!gatewayRegisterForm || !gatewayRegisterForm.classList.contains("hidden"))) {
        signupSlot.innerHTML = "";
        window.google.accounts.id.renderButton(signupSlot, {
          type: "standard",
          theme: "outline",
          size: "large",
          text: "signup_with",
          shape: "rectangular",
          logo_alignment: "left",
          width: computedBtnWidth,
        });
      }
      return true;
    } catch (err) {
      console.warn("Error rendering Google Identity buttons:", err);
      return false;
    }
  }

  function triggerGooglePrompt() {
    if (window.google && window.google.accounts && window.google.accounts.id) {
      if (!googleGisInitialized) {
        window.google.accounts.id.initialize({
          client_id: googleClientId,
          callback: handleGoogleAuthCallback,
          auto_select: false,
          cancel_on_tap_outside: true,
        });
        googleGisInitialized = true;
      }
      window.google.accounts.id.prompt((notification) => {
        if (notification.isNotDisplayed()) {
          console.warn("GIS prompt not displayed:", notification.getNotDisplayedReason());
          showToast("Google sign-in popup was blocked. Please check your browser popup/cookie settings.", "error");
        }
      });
    } else {
      showToast("Google Identity Services is loading. Please try again in a moment.", "info");
    }
  }

  const fallbackGwSignIn = document.getElementById("fallbackGatewayGoogleSignInBtn");
  const fallbackGwSignUp = document.getElementById("fallbackGatewayGoogleSignUpBtn");
  if (fallbackGwSignIn) fallbackGwSignIn.addEventListener("click", triggerGooglePrompt);
  if (fallbackGwSignUp) fallbackGwSignUp.addEventListener("click", triggerGooglePrompt);

  window.addEventListener("resize", () => {
    if (typeof renderGoogleButtons === "function") {
      renderGoogleButtons();
    }
  });

  async function initGoogleAuth() {
    await loadGoogleAuthConfig();

    // Check if GIS script is already loaded, otherwise poll briefly
    if (!renderGoogleButtons()) {
      let attempts = 0;
      const interval = setInterval(() => {
        attempts++;
        if (renderGoogleButtons() || attempts > 25) {
          clearInterval(interval);
        }
      }, 250);
    }
  }

  async function handleGoogleAuthCallback(response) {
    if (!response || !response.credential) {
      showToast("Google authentication was not completed.", "error");
      return;
    }

    showToast("Verifying Google account with secure backend...", "info");

    try {
      const res = await fetch("/api/auth/google", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ credential: response.credential }),
      });

      const data = await res.json();
      if (!res.ok || !data.success) {
        throw new Error(data.message || "Google authentication failed");
      }

      const authData = data.data || data;
      currentAuthToken = authData.access_token;
      localStorage.setItem(TOKEN_STORAGE_KEY, currentAuthToken);
      localStorage.setItem("magic_fill_access_token", currentAuthToken);
      localStorage.setItem("magic_fill_auth_token", currentAuthToken);
      if (authData.user) localStorage.setItem("magic_fill_user", JSON.stringify(authData.user));

      updateAuthUI(true, authData.user);

      if (gatewayLoginErrorBox) gatewayLoginErrorBox.classList.add("hidden");
      if (gatewayRegisterErrorBox) gatewayRegisterErrorBox.classList.add("hidden");

      if (authData.is_new_user) {
        showToast(`Welcome to Magic Fill, ${authData.user.full_name || authData.user.email}!`, "success");
        if (onboardingModal) {
          if (onboardingUserName) onboardingUserName.textContent = authData.user.full_name || authData.user.email;
          onboardingModal.classList.remove("hidden");
        }
      } else {
        showToast(`Welcome back, ${authData.user.full_name || authData.user.email}!`, "success");
      }

      // Check for deep-link / extension directives
      const search = new URLSearchParams(window.location.search);
      if (search.get("source") === "extension") {
        generateExtensionAuthCode();
      } else if (search.get("redirect") === "vault" || window.location.hash === "#vault") {
        switchToTab("vault");
      }

      loadStoredMemory();
    } catch (err) {
      console.error("Google auth error:", err);
      showToast(`Google authentication failed: ${err.message}`, "error");
      if (gatewayLoginErrorBox) {
        gatewayLoginErrorBox.textContent = `Google Sign In error: ${err.message}`;
        gatewayLoginErrorBox.classList.remove("hidden");
      }
      if (gatewayRegisterErrorBox) {
        gatewayRegisterErrorBox.textContent = `Google Sign Up error: ${err.message}`;
        gatewayRegisterErrorBox.classList.remove("hidden");
      }
    }
  }

  // Close modals on backdrop click
  [authModal, onboardingModal, extensionAuthModal].forEach((m) => {
    if (!m) return;
    m.addEventListener("click", (e) => {
      if (e.target === m) m.classList.add("hidden");
    });
  });

  // Login Form Submission
  if (loginForm) {
    loginForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      if (loginErrorBox) loginErrorBox.classList.add("hidden");
      const email = loginEmail ? loginEmail.value.trim() : "";
      const password = loginPassword ? loginPassword.value : "";

      if (!email || !password) {
        if (loginErrorBox) {
          loginErrorBox.textContent = "Please enter both email and password.";
          loginErrorBox.classList.remove("hidden");
        }
        return;
      }

      if (btnLoginSubmit) {
        btnLoginSubmit.disabled = true;
        btnLoginSubmit.innerHTML = "<span>Signing In...</span>";
      }

      try {
        const res = await fetch("/api/auth/login", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email, password }),
        });
        const data = await res.json();
        if (!res.ok || !data.success) {
          let errMsg = data.message;
          if (data.details && Array.isArray(data.details)) {
            errMsg = data.details.map((d) => d.message || d.msg || `${d.field}: invalid`).join("; ");
          } else if (data.detail) {
            errMsg = Array.isArray(data.detail) ? data.detail.map((d) => d.msg || d).join("; ") : data.detail;
          }
          if (data.error_code === "USE_GOOGLE_SIGN_IN") {
            errMsg = data.message || "This account was registered with Google. Please click 'Continue with Google' to sign in.";
          }
          throw new Error(errMsg || "Invalid email or password");
        }

        const authData = data.data || data;
        currentAuthToken = authData.access_token;
        localStorage.setItem(TOKEN_STORAGE_KEY, currentAuthToken);
        localStorage.setItem("magic_fill_access_token", currentAuthToken);
        localStorage.setItem("magic_fill_auth_token", currentAuthToken);
        if (authData.user) localStorage.setItem("magic_fill_user", JSON.stringify(authData.user));
        updateAuthUI(true, authData.user);
        closeAuthModal();
        loginForm.reset();
        showToast(`Welcome back, ${authData.user.full_name || authData.user.email}!`, "success");

        const search = new URLSearchParams(window.location.search);
        if (search.get("source") === "extension") {
          generateExtensionAuthCode();
        } else if (search.get("redirect") === "vault" || window.location.hash === "#vault") {
          switchToTab("vault");
        }

        loadStoredMemory();
      } catch (err) {
        if (loginErrorBox) {
          loginErrorBox.textContent = err.message;
          loginErrorBox.classList.remove("hidden");
        }
      } finally {
        if (btnLoginSubmit) {
          btnLoginSubmit.disabled = false;
          btnLoginSubmit.innerHTML = "<span>Sign In to Vault</span>";
        }
      }
    });
  }

  // Register Form Submission
  if (registerForm) {
    registerForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      if (registerErrorBox) registerErrorBox.classList.add("hidden");
      const fullName = regFullName ? regFullName.value.trim() : "";
      const email = regEmail ? regEmail.value.trim() : "";
      const password = regPassword ? regPassword.value : "";
      const confirm = regPasswordConfirm ? regPasswordConfirm.value : "";

      if (!email || !password) {
        if (registerErrorBox) {
          registerErrorBox.textContent = "Email and password are required.";
          registerErrorBox.classList.remove("hidden");
        }
        return;
      }
      if (password.length < 6) {
        if (registerErrorBox) {
          registerErrorBox.textContent = "Password must be at least 6 characters long.";
          registerErrorBox.classList.remove("hidden");
        }
        return;
      }
      if (password !== confirm) {
        if (registerErrorBox) {
          registerErrorBox.textContent = "Passwords do not match.";
          registerErrorBox.classList.remove("hidden");
        }
        return;
      }

      if (btnRegisterSubmit) {
        btnRegisterSubmit.disabled = true;
        btnRegisterSubmit.innerHTML = "<span>Creating Account...</span>";
      }

      try {
        const res = await fetch("/api/auth/register", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ full_name: fullName || null, email, password }),
        });
        const data = await res.json();
        if (!res.ok || !data.success) {
          let errMsg = data.message;
          if (data.details && Array.isArray(data.details)) {
            errMsg = data.details.map((d) => d.message || d.msg || `${d.field}: invalid`).join("; ");
          } else if (data.detail) {
            errMsg = Array.isArray(data.detail) ? data.detail.map((d) => d.msg || d).join("; ") : data.detail;
          }
          if (data.error_code === "DUPLICATE_EMAIL") {
            errMsg = "An account with this email address already exists. Please sign in instead.";
          }
          throw new Error(errMsg || "Registration failed. Please check your information.");
        }

        const authData = data.data || data;
        currentAuthToken = authData.access_token;
        localStorage.setItem(TOKEN_STORAGE_KEY, currentAuthToken);
        localStorage.setItem("magic_fill_access_token", currentAuthToken);
        localStorage.setItem("magic_fill_auth_token", currentAuthToken);
        if (authData.user) localStorage.setItem("magic_fill_user", JSON.stringify(authData.user));
        updateAuthUI(true, authData.user);
        closeAuthModal();
        registerForm.reset();
        showToast("Account created successfully!", "success");

        if (onboardingModal) {
          if (onboardingUserName) onboardingUserName.textContent = authData.user.full_name || authData.user.email;
          onboardingModal.classList.remove("hidden");
        }

        loadStoredMemory();
      } catch (err) {
        if (registerErrorBox) {
          registerErrorBox.textContent = err.message;
          registerErrorBox.classList.remove("hidden");
        }
      } finally {
        if (btnRegisterSubmit) {
          btnRegisterSubmit.disabled = false;
          btnRegisterSubmit.innerHTML = "<span>Create Account & Setup Extension</span>";
        }
      }
    });
  }

  // Onboarding Buttons
  if (btnOnboardingConnect) {
    btnOnboardingConnect.addEventListener("click", () => {
      if (onboardingModal) onboardingModal.classList.add("hidden");
      generateExtensionAuthCode();
    });
  }

  if (btnOnboardingContinue) {
    btnOnboardingContinue.addEventListener("click", () => {
      if (onboardingModal) onboardingModal.classList.add("hidden");
      switchToTab("vault");
    });
  }

  if (extAuthModalClose) {
    extAuthModalClose.addEventListener("click", () => {
      if (extensionAuthModal) extensionAuthModal.classList.add("hidden");
    });
  }

  if (btnExtAuthDone) {
    btnExtAuthDone.addEventListener("click", () => {
      if (extensionAuthModal) extensionAuthModal.classList.add("hidden");
      switchToTab("vault");
    });
  }

  if (btnCopyAuthCode) {
    btnCopyAuthCode.addEventListener("click", () => {
      if (!displayAuthCode || !displayAuthCode.value || displayAuthCode.value.startsWith("Generat") || displayAuthCode.value.startsWith("Error")) return;
      navigator.clipboard.writeText(displayAuthCode.value).then(() => {
        showToast("✓ Single-use authorization code copied!", "success");
      }).catch(() => {
        displayAuthCode.select();
        document.execCommand("copy");
        showToast("✓ Code copied!", "success");
      });
    });
  }

  // -------------------------------------------------------------------------
  // 1. Toast Notification System
  // -------------------------------------------------------------------------
  function showToast(message, type = "success") {
    const toast = document.createElement("div");
    toast.className = `toast-card toast-${type}`;
    toast.textContent = message;
    toastContainer.appendChild(toast);
    setTimeout(() => {
      toast.style.opacity = "0";
      toast.style.transform = "translateY(10px)";
      setTimeout(() => toast.remove(), 300);
    }, 3800);
  }

  // -------------------------------------------------------------------------
  // 2. Character & Word Counter
  // -------------------------------------------------------------------------
  if (rawTextInput && charCountLabel) {
    rawTextInput.addEventListener("input", () => {
      const len = rawTextInput.value.length;
      const words = rawTextInput.value.trim() ? rawTextInput.value.trim().split(/\s+/).length : 0;
      charCountLabel.textContent = `${len.toLocaleString()} chars · ${words.toLocaleString()} words`;
    });

    rawTextInput.addEventListener("keydown", (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
        e.preventDefault();
        btnProcessAI.click();
      }
    });
  }

  // -------------------------------------------------------------------------
  // 3. Segmented Navigation Tabs
  // -------------------------------------------------------------------------
  const tabButtons = {
    ingest: document.getElementById("tabBtnIngest"),
    documents: document.getElementById("tabBtnDocuments"),
    vault: document.getElementById("tabBtnVault"),
    playground: document.getElementById("tabBtnPlayground"),
  };

  const tabPanels = {
    ingest: document.getElementById("tabIngest"),
    documents: document.getElementById("tabDocuments"),
    vault: document.getElementById("tabVault"),
    playground: document.getElementById("tabPlayground"),
  };

  function switchToTab(key) {
    if (!currentAuthUser) {
      openQuickAuth("login");
      return;
    }
    if (!tabButtons[key] || !tabPanels[key]) return;
    Object.values(tabButtons).forEach((b) => {
      b.classList.remove("active");
      b.setAttribute("aria-selected", "false");
    });
    Object.values(tabPanels).forEach((p) => p.classList.remove("active"));

    tabButtons[key].classList.add("active");
    tabButtons[key].setAttribute("aria-selected", "true");
    tabPanels[key].classList.add("active");
    if (key === "vault" || key === "documents") {
      loadStoredMemory();
    }
  }

  Object.entries(tabButtons).forEach(([key, btn]) => {
    if (!btn) return;
    btn.addEventListener("click", () => switchToTab(key));
  });

  // -------------------------------------------------------------------------
  // 4. Backend Health Check
  // -------------------------------------------------------------------------
  async function checkHealth() {
    try {
      const res = await fetch("/health");
      if (res.ok) {
        backendBadge.className = "status-indicator status-connected";
        backendStatusText.textContent = "Online";
      } else {
        throw new Error("Degraded");
      }
    } catch {
      backendBadge.className = "status-indicator status-error";
      backendStatusText.textContent = "Offline";
    }
  }
  checkHealth();
  setInterval(checkHealth, 15000);

  // -------------------------------------------------------------------------
  // 5. Ingestion Studio Presets
  // -------------------------------------------------------------------------
  if (chipFullBio) {
    chipFullBio.addEventListener("click", () => {
      rawTextInput.value = `Full Name: Muazam Ali. Father Name: Muhammad Sarwar.
Email: muazam@example.com. Phone: +92 300 1234567.
Date of Birth: 2002-05-15. CNIC: 35202-1234567-1. Gender: Male.
Address: 45 Tech Avenue, Gulberg III. City: Lahore. Country: Pakistan.
University: University of Education, Lahore. Degree: BS Information Technology. Department: Computer Science. Semester: 8th. Roll Number: 21F-IT-042.
Work Experience: Software Engineer at Apex Technologies from 2023-06-01 to Present. Built scalable microservices and FastAPI systems. Skills: Python, FastAPI, SQLite, React, Docker.`;
      rawTextInput.dispatchEvent(new Event("input"));
      showToast("Loaded comprehensive biography preset", "success");
    });
  }

  if (chipGenderBio) {
    chipGenderBio.addEventListener("click", () => {
      rawTextInput.value = `Name: Muazam Ali. Gender: Male. Date of Birth: 2002-05-15.
Contact: +92 300 1234567, email: muazam@example.com.
City: Lahore. Country: Pakistan.
Education: BS Computer Science from University of Education, Lahore in 2024.`;
      rawTextInput.dispatchEvent(new Event("input"));
      showToast("Loaded preset with Gender, DOB & Country", "success");
    });
  }

  if (chipFriendName) {
    chipFriendName.addEventListener("click", () => {
      rawTextInput.value = "Friends Name is Taha";
      rawTextInput.dispatchEvent(new Event("input"));
      showToast("Loaded friend's name preset ('Friends Name is Taha')", "success");
    });
  }

  if (chipUpdateEmail) {
    chipUpdateEmail.addEventListener("click", () => {
      rawTextInput.value = "Personal mail is muazam.personal@gmail.com";
      rawTextInput.dispatchEvent(new Event("input"));
      showToast("Loaded personal mail preset", "success");
    });
  }

  if (chipEmergency) {
    chipEmergency.addEventListener("click", () => {
      rawTextInput.value = "Emergency Contact: Brother Usman, Phone: +92 300 7654321";
      rawTextInput.dispatchEvent(new Event("input"));
      showToast("Loaded emergency contact preset", "success");
    });
  }

  btnClearInput.addEventListener("click", () => {
    rawTextInput.value = "";
    currentUploadedFile = null;
    if (fileInput) fileInput.value = "";
    selectedFileName.textContent = "Attach CV/Resume (PDF, TXT, MD)";
    rawTextInput.dispatchEvent(new Event("input"));
    showToast("Input cleared", "success");
  });

  // -------------------------------------------------------------------------
  // 6. CV/Resume Document Drag & Drop (Tab 1)
  // -------------------------------------------------------------------------
  dropZone.addEventListener("click", () => fileInput.click());
  dropZone.addEventListener("keydown", (e) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      fileInput.click();
    }
  });
  dropZone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropZone.classList.add("dragover");
  });
  dropZone.addEventListener("dragleave", () => {
    dropZone.classList.remove("dragover");
  });
  dropZone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropZone.classList.remove("dragover");
    if (e.dataTransfer.files && e.dataTransfer.files[0]) handleFileSelected(e.dataTransfer.files[0]);
  });
  fileInput.addEventListener("change", (e) => {
    if (e.target.files && e.target.files[0]) handleFileSelected(e.target.files[0]);
  });

  async function handleFileSelected(file) {
    if (!file) return;
    currentUploadedFile = file;
    selectedFileName.textContent = `Scanning: ${file.name}...`;

    const fileNameLower = file.name.toLowerCase();
    if (fileNameLower.endsWith(".txt") || fileNameLower.endsWith(".md")) {
      const reader = new FileReader();
      reader.onload = (e) => {
        const text = e.target.result || "";
        rawTextInput.value = text;
        rawTextInput.dispatchEvent(new Event("input"));
        selectedFileName.textContent = `Attached: ${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
        showToast(`Scanned ${text.length.toLocaleString()} chars from ${file.name}`, "success");
      };
      reader.onerror = () => {
        selectedFileName.textContent = `Attached: ${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
        showToast(`Attached ${file.name}`, "info");
      };
      reader.readAsText(file);
    } else {
      // For PDF or other documents, parse text immediately so characters and words are visible
      try {
        const formData = new FormData();
        formData.append("file", file);
        const res = await authFetch("/api/memory/parse-text", {
          method: "POST",
          body: formData,
        });
        const data = await res.json();
        if (res.ok && data.success && data.data && data.data.raw_text) {
          rawTextInput.value = data.data.raw_text;
          rawTextInput.dispatchEvent(new Event("input"));
          selectedFileName.textContent = `Attached: ${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
          showToast(`Scanned ${data.data.char_count.toLocaleString()} chars from ${file.name}`, "success");
        } else {
          selectedFileName.textContent = `Attached: ${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
          showToast(data.message || "No readable text found in document (it may be a scanned image).", "error");
        }
      } catch (err) {
        selectedFileName.textContent = `Attached: ${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
        showToast(`Attached ${file.name}`, "info");
      }
    }
  }

  // -------------------------------------------------------------------------
  // 7. Grounding & Ingestion Execution
  // -------------------------------------------------------------------------
  btnProcessAI.addEventListener("click", async () => {
    const rawText = rawTextInput.value.trim();
    if (!rawText && !currentUploadedFile) {
      showToast("Please enter unstructured text or attach a document first.", "error");
      return;
    }

    btnProcessAI.disabled = true;
    btnProcessText.textContent = "Processing...";
    extractionStatusBadge.textContent = "Processing...";

    try {
      let res, data;
      const effectiveUserId = currentAuthUser ? currentAuthUser.id : 1;

      // If we have text in the prompt box, send text directly; otherwise send the file
      if (rawText) {
        res = await authFetch("/api/memory/extract-raw", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ raw_text: rawText, user_id: effectiveUserId, auto_save: true }),
        });
      } else if (currentUploadedFile) {
        const formData = new FormData();
        formData.append("file", currentUploadedFile);
        formData.append("user_id", String(effectiveUserId));
        formData.append("auto_save", "true");
        res = await authFetch("/api/memory/upload-document", { method: "POST", body: formData });
      }

      data = await res.json();
      if (!res.ok || !data.success) throw new Error(data.message || "Failed to process text");

      if (data.data && data.data.raw_text && !rawTextInput.value) {
        rawTextInput.value = data.data.raw_text;
        rawTextInput.dispatchEvent(new Event("input"));
      }

      const extracted = data.data.extracted;
      extractionPlaceholder.classList.add("hidden");
      extractionResultBox.classList.remove("hidden");
      extractionStatusBadge.textContent = "Grounded & Saved";

      const customFields = extracted.custom_fields || [];
      const pinfo = extracted.personal_info;
      const experiences = extracted.experiences || [];

      if (customFields.some((c) => c.field_key.includes("friend") || c.field_key.includes("contact"))) {
        protectionTitle.textContent = "Primary Identity Protected";
        protectionDesc.textContent = `Third-party name mapped cleanly as custom attribute '${customFields[0].field_label}: ${customFields[0].field_value}'. Primary user name remained untouched.`;
      } else if (pinfo && pinfo.full_name) {
        protectionTitle.textContent = "Primary Identity Verified";
        protectionDesc.textContent = `User identity stored as '${pinfo.full_name}'.`;
      } else {
        protectionTitle.textContent = "Memory Synchronized";
        protectionDesc.textContent = "Extracted attributes were safely synchronized to the database.";
      }

      extractionSummaryGrid.innerHTML = `
        <div class="ext-metric-pill">
          <span class="ext-metric-key">Identity</span>
          <span class="ext-metric-val">${pinfo && pinfo.full_name ? "1 record" : "Preserved"}</span>
        </div>
        <div class="ext-metric-pill">
          <span class="ext-metric-key">Experiences</span>
          <span class="ext-metric-val">${experiences.length} milestones</span>
        </div>
        <div class="ext-metric-pill">
          <span class="ext-metric-key">Custom Attributes</span>
          <span class="ext-metric-val">${customFields.length} attributes</span>
        </div>
      `;

      jsonPreviewBox.textContent = JSON.stringify(extracted, null, 2);
      showToast("Knowledge processed and stored in personal vault!", "success");
      loadStoredMemory();
    } catch (err) {
      showToast(`Extraction error: ${err.message}`, "error");
      extractionStatusBadge.textContent = "Error";
    } finally {
      btnProcessAI.disabled = false;
      btnProcessText.textContent = "Process";
    }
  });

  btnCopyJson.addEventListener("click", () => {
    if (jsonPreviewBox.textContent) {
      navigator.clipboard.writeText(jsonPreviewBox.textContent);
      showToast("JSON copied to clipboard", "success");
    }
  });

  // -------------------------------------------------------------------------
  // 8. Tab 2: Photos & Documents Studio
  // -------------------------------------------------------------------------
  if (chipDescCnicFront) {
    chipDescCnicFront.addEventListener("click", () => {
      docDescriptionInput.value = "This is my CNIC front";
      updateLiveClassificationTag();
      showToast("Selected description: 'This is my CNIC front'", "success");
    });
  }
  if (chipDescCnicBack) {
    chipDescCnicBack.addEventListener("click", () => {
      docDescriptionInput.value = "This is my CNIC back";
      updateLiveClassificationTag();
      showToast("Selected description: 'This is my CNIC back'", "success");
    });
  }
  if (chipDescProfile) {
    chipDescProfile.addEventListener("click", () => {
      docDescriptionInput.value = "Official Profile Picture";
      updateLiveClassificationTag();
      showToast("Selected description: 'Official Profile Picture'", "success");
    });
  }
  if (chipDescPassport) {
    chipDescPassport.addEventListener("click", () => {
      docDescriptionInput.value = "Passport Document";
      updateLiveClassificationTag();
      showToast("Selected description: 'Passport Document'", "success");
    });
  }
  if (chipDescDegree) {
    chipDescDegree.addEventListener("click", () => {
      docDescriptionInput.value = "Degree Transcript";
      updateLiveClassificationTag();
      showToast("Selected description: 'Degree Transcript'", "success");
    });
  }

  docDescriptionInput.addEventListener("input", updateLiveClassificationTag);

  function updateLiveClassificationTag() {
    const desc = docDescriptionInput.value.toLowerCase().trim();
    if (!desc) {
      docAutoDetectedTag.textContent = "Classification: General Document";
      return;
    }
    if (desc.includes("cnic front") || desc.includes("front")) {
      docAutoDetectedTag.textContent = "Classification: CNIC Front (Identity)";
    } else if (desc.includes("cnic back") || desc.includes("back")) {
      docAutoDetectedTag.textContent = "Classification: CNIC Back (Identity)";
    } else if (desc.includes("photo") || desc.includes("picture") || desc.includes("headshot") || desc.includes("avatar")) {
      docAutoDetectedTag.textContent = "Classification: Profile Photograph (Profile)";
    } else if (desc.includes("passport")) {
      docAutoDetectedTag.textContent = "Classification: Passport Document (Identity)";
    } else if (desc.includes("degree") || desc.includes("transcript")) {
      docAutoDetectedTag.textContent = "Classification: Degree Transcript (Academic)";
    } else {
      docAutoDetectedTag.textContent = "Classification: Custom Document";
    }
  }

  // Document Dropzone
  docDropZone.addEventListener("click", () => docFileInput.click());
  docDropZone.addEventListener("keydown", (e) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      docFileInput.click();
    }
  });
  docDropZone.addEventListener("dragover", (e) => {
    e.preventDefault();
    docDropZone.classList.add("dragover");
  });
  docDropZone.addEventListener("dragleave", () => {
    docDropZone.classList.remove("dragover");
  });
  docDropZone.addEventListener("drop", (e) => {
    e.preventDefault();
    docDropZone.classList.remove("dragover");
    if (e.dataTransfer.files && e.dataTransfer.files[0]) handleDocFileSelected(e.dataTransfer.files[0]);
  });
  docFileInput.addEventListener("change", (e) => {
    if (e.target.files && e.target.files[0]) handleDocFileSelected(e.target.files[0]);
  });

  function handleDocFileSelected(file) {
    currentDocFile = file;
    docLivePreviewName.textContent = file.name;
    docLivePreviewSize.textContent = `${(file.size / 1024).toFixed(1)} KB`;

    const reader = new FileReader();
    reader.onload = (e) => {
      currentDocDataUri = e.target.result;
      if (file.type.startsWith("image/") || file.type.includes("svg")) {
        docLivePreviewImg.src = currentDocDataUri;
      } else {
        docLivePreviewImg.src = "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='64' height='64'><rect width='64' height='64' fill='%23f1f5f9'/><text x='50%25' y='52%25' font-size='11' font-family='sans-serif' fill='%234f46e5' text-anchor='middle' dominant-baseline='middle'>DOC/PDF</text></svg>";
      }
      docLivePreviewBox.classList.remove("hidden");
    };
    reader.readAsDataURL(file);

    if (!docDescriptionInput.value) {
      const fn = file.name.toLowerCase();
      if (fn.includes("front")) docDescriptionInput.value = "This is my CNIC front";
      else if (fn.includes("back")) docDescriptionInput.value = "This is my CNIC back";
      else if (fn.includes("photo") || fn.includes("pic") || fn.includes("headshot")) docDescriptionInput.value = "Official Profile Picture";
      else if (fn.includes("passport")) docDescriptionInput.value = "Passport Document";
      updateLiveClassificationTag();
    }

    showToast(`Loaded document preview: ${file.name}`, "success");
  }

  btnRemoveDocFile.addEventListener("click", () => {
    currentDocFile = null;
    currentDocDataUri = null;
    docFileInput.value = "";
    docLivePreviewBox.classList.add("hidden");
    docFileSelectedName.classList.add("hidden");
    showToast("File selection cleared", "success");
  });

  btnSaveDocument.addEventListener("click", async () => {
    const description = docDescriptionInput.value.trim();
    if (!currentDocDataUri && !currentDocFile) {
      showToast("Please choose or drop an image/document file first.", "error");
      return;
    }
    if (!description) {
      showToast("Please enter a written description of what this document is.", "error");
      docDescriptionInput.focus();
      return;
    }

    btnSaveDocument.disabled = true;
    btnSaveDocument.innerHTML = "<span>Saving Document...</span>";

    try {
      const effectiveUserId = currentAuthUser ? currentAuthUser.id : 1;
      const payload = {
        user_id: effectiveUserId,
        description: description,
        file_name: currentDocFile ? currentDocFile.name : "document.png",
        mime_type: currentDocFile ? currentDocFile.type : "image/png",
        file_data: currentDocDataUri,
        file_size_bytes: currentDocFile ? currentDocFile.size : 0,
      };

      const res = await authFetch("/api/documents", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      const data = await res.json();
      if (!res.ok || !data.success) throw new Error(data.message || "Failed to save document");

      showToast(`✓ Document saved: "${data.data.title}"`, "success");

      btnRemoveDocFile.click();
      docDescriptionInput.value = "";
      updateLiveClassificationTag();

      loadStoredMemory();
    } catch (err) {
      showToast(`Save error: ${err.message}`, "error");
    } finally {
      btnSaveDocument.disabled = false;
      btnSaveDocument.innerHTML = '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"></path><polyline points="17 21 17 13 7 13 7 21"></polyline><polyline points="7 3 7 8 15 8"></polyline></svg> <span>Save Photo / Document to Vault</span>';
    }
  });

  // Gallery Filters & Search
  const filterChips = document.querySelectorAll(".filter-pills-row .filter-pill, .gallery-filter-bar .filter-chip");
  filterChips.forEach((chip) => {
    chip.addEventListener("click", () => {
      filterChips.forEach((c) => c.classList.remove("active"));
      chip.classList.add("active");
      currentDocFilter = chip.getAttribute("data-filter") || "all";
      renderDocumentsGallery(savedDocumentsList);
    });
  });

  if (docGallerySearch) {
    docGallerySearch.addEventListener("input", () => {
      renderDocumentsGallery(savedDocumentsList);
    });
  }

  // -------------------------------------------------------------------------
  // 9. Load Stored Memory & Documents Vault
  // -------------------------------------------------------------------------
  async function loadStoredMemory() {
    if (!currentAuthUser) return;
    try {
      const url = `/api/memory/current?user_id=${currentAuthUser.id}`;
      const res = await authFetch(url);
      const json = await res.json();
      if (!res.ok || !json.success) throw new Error(json.message);

      const profile = json.data;
      activeProfileCache = profile;

      const pinfo = profile.personal_info;
      const experiences = profile.experiences || [];
      const customFields = profile.custom_fields || [];
      const documents = profile.documents || [];
      savedDocumentsList = documents;

      // Update Metrics Ribbon
      metricUserName.textContent = (pinfo && pinfo.full_name) ? pinfo.full_name : (currentAuthUser ? (currentAuthUser.full_name || currentAuthUser.email) : "Not configured");
      metricDocCount.textContent = documents.length;
      metricCustomCount.textContent = customFields.length;
      metricExperienceCount.textContent = experiences.length;
      docBadgeCount.textContent = documents.length;
      docGalleryCountBadge.textContent = `${documents.length} Items`;
      vaultBadgeCount.textContent = (pinfo ? 1 : 0) + experiences.length + customFields.length + documents.length;

      // Render Documents Gallery (Tab 2)
      renderDocumentsGallery(documents);

      // Render Memory Vault (Tab 3)
      renderMemoryVault(profile);
    } catch (err) {
      console.warn("Failed to load memory:", err);
    }
  }

  function renderDocumentsGallery(documents) {
    const q = (docGallerySearch ? docGallerySearch.value : "").toLowerCase().trim();

    let filtered = (documents || []).filter((doc) => {
      if (currentDocFilter === "identity") {
        const k = (doc.doc_key || "").toLowerCase();
        if (!k.includes("cnic") && !k.includes("passport") && !k.includes("id")) return false;
      } else if (currentDocFilter === "photo") {
        const k = (doc.doc_key || "").toLowerCase();
        if (!k.includes("photo") && !k.includes("picture") && !k.includes("avatar")) return false;
      } else if (currentDocFilter === "academic") {
        const k = (doc.doc_key || "").toLowerCase();
        if (!k.includes("degree") && !k.includes("transcript") && !k.includes("certificate")) return false;
      }

      if (q) {
        const haystack = `${doc.title || ""} ${doc.description || ""} ${doc.doc_key || ""} ${doc.file_name || ""}`.toLowerCase();
        if (!haystack.includes(q)) return false;
      }
      return true;
    });

    if (filtered.length === 0) {
      documentsGalleryList.innerHTML = `
        <div class="inspector-empty-state" style="grid-column: 1 / -1;">
          <div class="empty-vector-circle">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
              <circle cx="8.5" cy="8.5" r="1.5"></circle>
              <polyline points="21 15 16 10 5 21"></polyline>
            </svg>
          </div>
          <h4>${documents.length === 0 ? "No Photos or Documents Stored" : "No Matching Documents Found"}</h4>
          <p>${documents.length === 0 ? "Upload your CNIC front, CNIC back, or profile picture above to see them stored here." : "Try adjusting your search query or category filter."}</p>
        </div>
      `;
      return;
    }

    documentsGalleryList.innerHTML = filtered.map((doc) => `
      <div class="doc-card" id="docCard_${doc.id}">
        <div class="doc-card-thumb-wrap" onclick="openLightbox('${escapeJs(doc.title)}', '${escapeJs(doc.file_data)}')">
          <img class="doc-card-thumb" src="${escapeHtml(doc.file_data)}" alt="${escapeHtml(doc.title)}" onerror="this.src='https://images.unsplash.com/photo-1589829545856-d10d557cf95f?auto=format&fit=crop&w=300&q=80'">
          <span class="doc-card-zoom-badge">
            <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
            Zoom
          </span>
        </div>
        <div class="doc-card-body">
          <div class="doc-card-header">
            <span class="doc-card-title">${escapeHtml(doc.title)}</span>
            <span class="doc-card-badge">${escapeHtml(doc.doc_key)}</span>
          </div>
          <div class="doc-card-desc">“${escapeHtml(doc.description || doc.title)}”</div>
          <div class="doc-card-meta">
            <span>${escapeHtml(doc.file_name)}</span>
            <div class="doc-card-actions">
              <button type="button" class="btn-micro-action" onclick="copyDocumentData('${escapeJs(doc.file_data)}')" title="Copy Base64/URI">Copy</button>
              <button type="button" class="doc-card-btn-del" onclick="deleteDocumentRecord(${doc.id})">Delete</button>
            </div>
          </div>
        </div>
      </div>
    `).join("");
  }

  window.copyDocumentData = function (dataUri) {
    navigator.clipboard.writeText(dataUri);
    showToast("Document Data URI copied to clipboard!", "success");
  };

  // -------------------------------------------------------------------------
  // 10. Memory Vault Rendering & Search/Filter
  // -------------------------------------------------------------------------
  const vaultFilterPills = document.querySelectorAll("#vaultFilterPills .vault-pill-btn, #vaultFilterPills .vault-filter-pill");
  vaultFilterPills.forEach((pill) => {
    pill.addEventListener("click", () => {
      vaultFilterPills.forEach((p) => p.classList.remove("active"));
      pill.classList.add("active");
      currentVaultFilter = pill.getAttribute("data-vfilter") || "all";
      if (activeProfileCache) renderMemoryVault(activeProfileCache);
    });
  });

  if (vaultSearchInput) {
    vaultSearchInput.addEventListener("input", () => {
      if (activeProfileCache) renderMemoryVault(activeProfileCache);
    });
  }

  function renderMemoryVault(profile) {
    const pinfo = profile.personal_info;
    const experiences = profile.experiences || [];
    const customFields = profile.custom_fields || [];
    const documents = profile.documents || [];
    const q = (vaultSearchInput ? vaultSearchInput.value : "").toLowerCase().trim();

    if (!pinfo && experiences.length === 0 && customFields.length === 0 && documents.length === 0) {
      memoryVaultContent.innerHTML = `
        <div class="inspector-empty-state" style="grid-column: 1 / -1;">
          <div class="empty-vector-circle">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path></svg>
          </div>
          <h4>Memory Vault is Empty</h4>
          <p>No biographical records, experiences, custom attributes, or documents found. Ingest details on Tab 1 to start.</p>
        </div>
      `;
      return;
    }

    let vaultHtml = "";

    // 1. Biographical Identity Card
    if (pinfo && (currentVaultFilter === "all" || currentVaultFilter === "bio")) {
      const bioRows = [
        { label: "Full Legal Name", val: pinfo.full_name, high: true },
        { label: "Father Name", val: pinfo.father_name },
        { label: "Gender", val: pinfo.gender, high: true },
        { label: "Date of Birth", val: pinfo.date_of_birth },
        { label: "CNIC / ID", val: pinfo.cnic },
        { label: "Profile Photo", val: pinfo.profile_photo ? "Active in Vault" : "—", color: pinfo.profile_photo ? "var(--accent-emerald)" : "" },
      ];

      const filteredBio = bioRows.filter((r) => !q || r.label.toLowerCase().includes(q) || String(r.val || "").toLowerCase().includes(q));

      if (filteredBio.length > 0) {
        vaultHtml += `
          <div class="vault-card">
            <div class="vault-card-header">
              <span class="vault-card-title">
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>
                Biographical Identity
              </span>
            </div>
            ${filteredBio.map((r) => `
              <div class="vault-data-row">
                <span class="vault-data-label">${escapeHtml(r.label)}</span>
                <span class="vault-data-value ${r.high ? "highlight" : ""}" style="${r.color ? "color:" + r.color : ""}">
                  ${escapeHtml(r.val || "—")}
                  ${r.val && r.val !== "—" ? `<button type="button" class="copy-mini-btn" onclick="copyInlineValue('${escapeJs(r.val)}', this)" title="Copy ${escapeHtml(r.label)}"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg></button>` : ""}
                </span>
              </div>
            `).join("")}
          </div>
        `;
      }
    }

    // 2. Contact Channels Card
    if (pinfo && (currentVaultFilter === "all" || currentVaultFilter === "contact")) {
      const contactRows = [
        { label: "Email Address", val: pinfo.email, high: true },
        { label: "Phone Number", val: pinfo.phone },
        { label: "City", val: pinfo.city },
        { label: "Country", val: pinfo.country },
        { label: "Street Address", val: pinfo.address },
      ];

      const filteredContact = contactRows.filter((r) => !q || r.label.toLowerCase().includes(q) || String(r.val || "").toLowerCase().includes(q));

      if (filteredContact.length > 0) {
        vaultHtml += `
          <div class="vault-card">
            <div class="vault-card-header">
              <span class="vault-card-title">
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"></path></svg>
                Contact Channels
              </span>
            </div>
            ${filteredContact.map((r) => `
              <div class="vault-data-row">
                <span class="vault-data-label">${escapeHtml(r.label)}</span>
                <span class="vault-data-value ${r.high ? "highlight" : ""}">
                  ${escapeHtml(r.val || "—")}
                  ${r.val && r.val !== "—" ? `<button type="button" class="copy-mini-btn" onclick="copyInlineValue('${escapeJs(r.val)}', this)" title="Copy"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg></button>` : ""}
                </span>
              </div>
            `).join("")}
          </div>
        `;
      }
    }

    // 3. Academic Credentials Card
    if (pinfo && (currentVaultFilter === "all" || currentVaultFilter === "academic")) {
      const acadRows = [
        { label: "University / Institution", val: pinfo.university, high: true },
        { label: "Degree / Program", val: pinfo.degree },
        { label: "Department", val: pinfo.department },
        { label: "Current Semester", val: pinfo.semester },
        { label: "Roll / Reg Number", val: pinfo.registration_number },
      ];

      const filteredAcad = acadRows.filter((r) => !q || r.label.toLowerCase().includes(q) || String(r.val || "").toLowerCase().includes(q));

      if (filteredAcad.length > 0) {
        vaultHtml += `
          <div class="vault-card">
            <div class="vault-card-header">
              <span class="vault-card-title">
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M22 10v6M2 10l10-5 10 5-10 5z"></path><path d="M6 12v5c3 3 9 3 12 0v-5"></path></svg>
                Academic Credentials
              </span>
            </div>
            ${filteredAcad.map((r) => `
              <div class="vault-data-row">
                <span class="vault-data-label">${escapeHtml(r.label)}</span>
                <span class="vault-data-value ${r.high ? "highlight" : ""}">
                  ${escapeHtml(r.val || "—")}
                  ${r.val && r.val !== "—" ? `<button type="button" class="copy-mini-btn" onclick="copyInlineValue('${escapeJs(r.val)}', this)" title="Copy"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg></button>` : ""}
                </span>
              </div>
            `).join("")}
          </div>
        `;
      }
    }

    // 4. Saved Documents Quick Cards in Vault
    if (documents.length > 0 && (currentVaultFilter === "all" || currentVaultFilter === "docs")) {
      const filteredDocs = documents.filter((d) => !q || `${d.title} ${d.description} ${d.doc_key}`.toLowerCase().includes(q));

      if (filteredDocs.length > 0) {
        let docCards = filteredDocs.map((d) => `
          <div style="background:#ffffff; border:1px solid #e2e8f0; border-radius:8px; padding:10px; display:flex; gap:12px; align-items:center; box-shadow:0 1px 3px rgba(15,23,42,0.04);">
            <img src="${escapeHtml(d.file_data)}" style="width:48px; height:48px; object-fit:cover; border-radius:6px; cursor:pointer; border:1px solid #e2e8f0;" onclick="openLightbox('${escapeJs(d.title)}', '${escapeJs(d.file_data)}')">
            <div style="flex:1; min-width:0;">
              <div style="display:flex; justify-content:space-between; align-items:center;">
                <strong style="color:#0f172a; font-size:13px;">${escapeHtml(d.title)}</strong>
                <span class="doc-card-badge">${escapeHtml(d.doc_key)}</span>
              </div>
              <div style="font-size:11.5px; color:#64748b; font-style:italic; margin-top:2px;">“${escapeHtml(d.description || d.title)}”</div>
            </div>
            <button type="button" class="doc-card-btn-del" onclick="deleteDocumentRecord(${d.id})">Delete</button>
          </div>
        `).join("");

        vaultHtml += `
          <div class="vault-card" style="grid-column: 1 / -1;">
            <div class="vault-card-header">
              <span class="vault-card-title">
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><circle cx="8.5" cy="8.5" r="1.5"></circle><polyline points="21 15 16 10 5 21"></polyline></svg>
                Identity Documents &amp; Media (${filteredDocs.length})
              </span>
            </div>
            <div style="display:grid; grid-template-columns:repeat(auto-fill, minmax(280px, 1fr)); gap:10px; margin-top:6px;">
              ${docCards}
            </div>
          </div>
        `;
      }
    }

    // 5. Dynamic Custom Attributes Table
    if (customFields.length > 0 && (currentVaultFilter === "all" || currentVaultFilter === "custom")) {
      const filteredCustom = customFields.filter((cf) => !q || `${cf.field_label} ${cf.field_key} ${cf.field_value}`.toLowerCase().includes(q));

      if (filteredCustom.length > 0) {
        let rowsHtml = filteredCustom.map((cf) => {
          const categoryClass = cf.category === "contact" ? "tag-badge-contact" : cf.category === "email" ? "tag-badge-email" : "tag-badge-general";
          return `
            <tr>
              <td style="font-weight:600; color:#0f172a;">${escapeHtml(cf.field_label)}</td>
              <td><code style="font-size:11px; color:#4f46e5; background:#f1f5f9; padding:2px 6px; border-radius:4px;">${escapeHtml(cf.field_key)}</code></td>
              <td style="color:#0284c7; font-weight:600;">
                ${escapeHtml(cf.field_value)}
                <button type="button" class="copy-mini-btn" onclick="copyInlineValue('${escapeJs(cf.field_value)}', this)" title="Copy"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg></button>
              </td>
              <td><span class="${categoryClass}">${escapeHtml(cf.category || "general")}</span></td>
              <td style="text-align:right;">
                <button type="button" class="btn-table-edit" onclick="editCustomField(${cf.id}, '${escapeJs(cf.field_value)}')">Edit</button>
                <button type="button" class="btn-table-del" onclick="deleteCustomField(${cf.id})">Delete</button>
              </td>
            </tr>
          `;
        }).join("");

        vaultHtml += `
          <div class="vault-card" style="grid-column: 1 / -1;">
            <div class="vault-card-header">
              <span class="vault-card-title">
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path></svg>
                Dynamic Custom Attributes (${filteredCustom.length})
              </span>
            </div>
            <table class="data-table">
              <thead>
                <tr>
                  <th>Attribute Label</th>
                  <th>Identifier Slug</th>
                  <th>Current Value</th>
                  <th>Category</th>
                  <th style="text-align:right;">Actions</th>
                </tr>
              </thead>
              <tbody>
                ${rowsHtml}
              </tbody>
            </table>
          </div>
        `;
      }
    }

    // 6. Career Experiences
    if (experiences.length > 0 && (currentVaultFilter === "all" || currentVaultFilter === "work")) {
      const filteredExp = experiences.filter((exp) => !q || `${exp.job_title} ${exp.company} ${exp.skills}`.toLowerCase().includes(q));

      if (filteredExp.length > 0) {
        let expRows = filteredExp.map((exp) => `
          <div style="background:#ffffff; border:1px solid #e2e8f0; border-radius:6px; padding:10px 12px; margin-bottom:10px; box-shadow:0 1px 3px rgba(15,23,42,0.03);">
            <div style="display:flex; justify-content:space-between; align-items:baseline;">
              <strong style="color:#0f172a;">${escapeHtml(exp.job_title)}</strong>
              <span style="font-size:11px; color:#64748b;">${escapeHtml(exp.start_date)} &rarr; ${exp.end_date ? escapeHtml(exp.end_date) : "Present"}</span>
            </div>
            <div style="color:#4f46e5; font-size:12.5px; margin-top:2px;">${escapeHtml(exp.company)}</div>
            ${exp.skills ? `<div style="font-size:11px; color:#64748b; margin-top:4px;">Skills: ${escapeHtml(exp.skills)}</div>` : ""}
          </div>
        `).join("");

        vaultHtml += `
          <div class="vault-card" style="grid-column: 1 / -1;">
            <div class="vault-card-header">
              <span class="vault-card-title">
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><rect x="2" y="7" width="20" height="14" rx="2" ry="2"></rect><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"></path></svg>
                Career Experiences (${filteredExp.length})
              </span>
            </div>
            ${expRows}
          </div>
        `;
      }
    }

    if (!vaultHtml) {
      memoryVaultContent.innerHTML = `
        <div class="inspector-empty-state" style="grid-column: 1 / -1;">
          <h4>No Attributes Matching "${escapeHtml(q)}"</h4>
          <p>Try adjusting your search query or switching the category filter to All.</p>
        </div>
      `;
    } else {
      memoryVaultContent.innerHTML = vaultHtml;
    }
  }

  window.copyInlineValue = function (val, btn) {
    navigator.clipboard.writeText(val);
    showToast(`Copied: "${val}"`, "success");
    if (btn) {
      const orig = btn.innerHTML;
      btn.innerHTML = '<span style="color:#059669; font-weight:bold;">&check;</span>';
      setTimeout(() => { btn.innerHTML = orig; }, 1500);
    }
  };

  // -------------------------------------------------------------------------
  // 11. Custom Field CRUD & Backup Export
  // -------------------------------------------------------------------------
  btnToggleAddCustom.addEventListener("click", () => {
    addCustomFieldBar.classList.toggle("hidden");
    if (!addCustomFieldBar.classList.contains("hidden")) newFieldKey.focus();
  });

  btnCancelAddCustom.addEventListener("click", () => {
    addCustomFieldBar.classList.add("hidden");
  });

  newFieldLabel.addEventListener("input", () => {
    if (!newFieldKey.value || newFieldKey.dataset.autoSlug === "true") {
      newFieldKey.value = newFieldLabel.value
        .toLowerCase()
        .replace(/[^a-z0-9]+/g, "_")
        .replace(/^_+|_+$/g, "");
      newFieldKey.dataset.autoSlug = "true";
    }
  });
  newFieldKey.addEventListener("input", () => {
    newFieldKey.dataset.autoSlug = "false";
  });

  btnSaveCustomField.addEventListener("click", async () => {
    const key = newFieldKey.value.trim();
    const label = newFieldLabel.value.trim();
    const val = newFieldValue.value.trim();
    const cat = newFieldCategory.value.trim() || "general";

    if (!key || !label || !val) {
      showToast("Please fill in key, label, and value.", "error");
      return;
    }

    try {
      const effectiveUserId = currentAuthUser ? currentAuthUser.id : 1;
      const res = await authFetch("/api/custom-fields", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: effectiveUserId, field_key: key, field_label: label, field_value: val, category: cat }),
      });
      const data = await res.json();
      if (!res.ok || !data.success) throw new Error(data.message || "Failed to create custom field");

      showToast(`Created custom attribute '${label}'`, "success");
      newFieldKey.value = ""; newFieldLabel.value = ""; newFieldValue.value = ""; newFieldCategory.value = "";
      addCustomFieldBar.classList.add("hidden");
      loadStoredMemory();
    } catch (err) {
      showToast(`Save error: ${err.message}`, "error");
    }
  });

  btnClearMemory.addEventListener("click", async () => {
    if (!confirm("Are you sure you want to clear your entire personal memory vault? This action cannot be undone.")) return;
    try {
      const effectiveUserId = currentAuthUser ? currentAuthUser.id : 1;
      const res = await authFetch(`/api/memory/clear?user_id=${effectiveUserId}`, { method: "DELETE" });
      const data = await res.json();
      if (!res.ok) throw new Error(data.message || "Failed to clear memory");
      showToast("Personal memory vault cleared successfully", "success");
      loadStoredMemory();
    } catch (err) {
      showToast(`Clear error: ${err.message}`, "error");
    }
  });

  window.editCustomField = async function (id, currentVal) {
    const newVal = prompt("Enter new value:", currentVal);
    if (newVal === null || newVal.trim() === "" || newVal === currentVal) return;
    try {
      const res = await authFetch(`/api/custom-fields/${id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ field_value: newVal.trim() }),
      });
      if (!res.ok) throw new Error("Failed to update");
      showToast("Custom attribute updated", "success");
      loadStoredMemory();
    } catch (err) {
      showToast(`Update error: ${err.message}`, "error");
    }
  };

  window.deleteCustomField = async function (id) {
    if (!confirm("Are you sure you want to delete this custom attribute?")) return;
    try {
      const res = await authFetch(`/api/custom-fields/${id}`, { method: "DELETE" });
      if (!res.ok) throw new Error("Failed to delete");
      showToast("Custom attribute deleted", "success");
      loadStoredMemory();
    } catch (err) {
      showToast(`Delete error: ${err.message}`, "error");
    }
  };

  window.deleteDocumentRecord = async function (id) {
    if (!confirm("Are you sure you want to delete this document from your vault?")) return;
    try {
      const res = await authFetch(`/api/documents/${id}`, { method: "DELETE" });
      if (!res.ok) throw new Error("Failed to delete document");
      showToast("Document deleted from vault", "success");
      loadStoredMemory();
    } catch (err) {
      showToast(`Delete failed: ${err.message}`, "error");
    }
  };

  if (btnExportVaultJson) {
    btnExportVaultJson.addEventListener("click", () => {
      if (!activeProfileCache) {
        showToast("No vault data loaded yet.", "error");
        return;
      }
      const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(activeProfileCache, null, 2));
      const downloadAnchor = document.createElement("a");
      downloadAnchor.setAttribute("href", dataStr);
      downloadAnchor.setAttribute("download", `magic_fill_vault_backup_${new Date().toISOString().slice(0, 10)}.json`);
      document.body.appendChild(downloadAnchor);
      downloadAnchor.click();
      downloadAnchor.remove();
      showToast("Vault JSON backup exported successfully!", "success");
    });
  }

  // -------------------------------------------------------------------------
  // 12. Lightbox Modal
  // -------------------------------------------------------------------------
  window.openLightbox = function (title, src) {
    lightboxTitle.textContent = title;
    lightboxImg.src = src;
    imageLightboxModal.classList.remove("hidden");
  };

  lightboxCloseBtn.addEventListener("click", () => {
    imageLightboxModal.classList.add("hidden");
    lightboxImg.src = "";
  });
  imageLightboxModal.addEventListener("click", (e) => {
    if (e.target === imageLightboxModal) {
      imageLightboxModal.classList.add("hidden");
      lightboxImg.src = "";
    }
  });

  // -------------------------------------------------------------------------
  // 13. Form Playground Simulation & Intelligent Autofill
  // -------------------------------------------------------------------------
  // Live update for range slider value display
  const expSlider = document.getElementById("p_exp_slider");
  const expDisplay = document.getElementById("expSliderDisplay");
  if (expSlider && expDisplay) {
    expSlider.addEventListener("input", (e) => {
      expDisplay.textContent = `${e.target.value} years`;
    });
  }

  btnSimulateAutofill.addEventListener("click", async () => {
    btnSimulateAutofill.disabled = true;
    btnSimulateAutofill.innerHTML = '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"></circle></svg> <span>AI reasoning & autofilling form...</span>';

    const formElements = document.querySelectorAll("#playgroundForm input, #playgroundForm select, #playgroundForm textarea");
    const detectedFields = [];
    const processedRadioGroups = new Set();

    formElements.forEach((el) => {
      const type = (el.type || "text").toLowerCase();
      if (type === "submit" || type === "reset" || type === "button") return;

      if (type === "radio") {
        if (processedRadioGroups.has(el.name)) return;
        processedRadioGroups.add(el.name);
        const radios = Array.from(document.querySelectorAll(`#playgroundForm input[type="radio"][name="${CSS.escape(el.name)}"]`));
        const options = radios.map((r) => {
          const parent = r.closest("label");
          return parent ? parent.innerText.trim() : r.value;
        });
        const groupWrap = el.closest(".modern-radio-group");
        const labelEl = groupWrap ? groupWrap.closest(".form-input-group")?.querySelector(".input-label") : null;
        detectedFields.push({
          field_id: el.id,
          name: el.name,
          label: labelEl ? labelEl.innerText.replace(/\s+/g, " ").trim() : el.name,
          placeholder: null,
          input_type: "radio",
          options: options,
        });
        return;
      }

      const labelEl = document.querySelector(`label[for="${el.id}"]`);
      const isSelect = el.tagName.toLowerCase() === "select";
      const isTextarea = el.tagName.toLowerCase() === "textarea";
      const normType = isSelect ? "select-one" : isTextarea ? "textarea" : type;

      detectedFields.push({
        field_id: el.id,
        name: el.name,
        label: labelEl ? labelEl.innerText.replace(/\s+/g, " ").trim() : null,
        placeholder: el.placeholder || null,
        input_type: normType,
        options: isSelect ? Array.from(el.options).map((o) => o.text.trim()) : null,
      });
    });

    try {
      const effectiveUserId = currentAuthUser ? currentAuthUser.id : 1;
      const res = await authFetch("/api/matching/fields", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: effectiveUserId,
          fields: detectedFields,
          form_context: "Job Application & University Portal Form",
        }),
      });

      const data = await res.json();
      if (!res.ok || !data.success) throw new Error(data.message || "Matching failed");

      const mappings = data.data.mappings || [];
      const unresolvedFields = data.data.unresolved_fields || [];

      // -----------------------------------------------------------------------
      // Dynamic Visual Status Highlighting (Green = Matched, Red = Missing)
      // -----------------------------------------------------------------------
      document.querySelectorAll("#playgroundForm [data-magic-fill-status]").forEach((elem) => {
        elem.removeAttribute("data-magic-fill-status");
      });

      const matchedFieldIds = new Set();
      mappings.forEach((m) => {
        matchedFieldIds.add(m.field_id);
        const el = document.getElementById(m.field_id);
        if (el) {
          el.setAttribute("data-magic-fill-status", "matched");
          const wrap = el.closest(".modern-radio-group, .modern-checkbox-wrap, .toggle-switch-wrap, .modern-range-wrap, .portal-file-cell");
          if (wrap) wrap.setAttribute("data-magic-fill-status", "matched");
        }
      });

      unresolvedFields.forEach((u) => {
        if (!matchedFieldIds.has(u.field_id)) {
          const el = document.getElementById(u.field_id);
          if (el) {
            el.setAttribute("data-magic-fill-status", "missing");
            const wrap = el.closest(".modern-radio-group, .modern-checkbox-wrap, .toggle-switch-wrap, .modern-range-wrap, .portal-file-cell");
            if (wrap) wrap.setAttribute("data-magic-fill-status", "missing");
          }
        }
      });

      if (mappings.length === 0) {
        showToast("No matching personal memory records found in database.", "error");
        return;
      }

      let filledCount = 0;
      let matchedSynonym = false;
      let matchedDropdown = false;
      let matchedFile = false;
      let matchedCustom = false;
      let matchedSalary = false;
      let matchedRadio = false;
      let matchedSwitch = false;
      let matchedRange = false;
      let matchedBio = false;
      let llmCount = 0;
      let detCount = 0;

      mappings.forEach((m) => {
        const el = document.getElementById(m.field_id);
        if (!el) return;

        if (m.source === "llm") {
          llmCount++;
        } else {
          detCount++;
        }

        const tag = el.tagName.toLowerCase();
        const type = (el.type || "text").toLowerCase();
        const isSelect = tag === "select";
        const isFile = type === "file";
        const isRadio = type === "radio";
        const isCheckbox = type === "checkbox";
        const isRange = type === "range";
        const isTextarea = tag === "textarea";

        if (isSelect) {
          const targetVal = String(m.value).toLowerCase().trim();
          let matched = false;

          for (let i = 0; i < el.options.length; i++) {
            const optVal = el.options[i].value.toLowerCase().trim();
            const optText = el.options[i].text.toLowerCase().trim();
            if (optVal === targetVal || optText === targetVal) {
              el.selectedIndex = i;
              matched = true;
              break;
            }
          }

          if (!matched && (targetVal === "male" || targetVal === "m")) {
            for (let i = 0; i < el.options.length; i++) {
              const optVal = el.options[i].value.toLowerCase().trim();
              if (optVal === "male" || optVal === "m") { el.selectedIndex = i; matched = true; break; }
            }
          } else if (!matched && (targetVal === "female" || targetVal === "f")) {
            for (let i = 0; i < el.options.length; i++) {
              const optVal = el.options[i].value.toLowerCase().trim();
              if (optVal === "female" || optVal === "f") { el.selectedIndex = i; matched = true; break; }
            }
          }

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

          matchedDropdown = true;
        } else if (isFile) {
          try {
            const rawVal = String(m.value);
            let fileObj = null;
            let previewSrc = rawVal;
            const targetFilename = el.id === "p_profile_photo" ? "profile_photo.png" : el.id === "p_cnic_front" ? "cnic_front.jpg" : el.id === "p_cnic_back" ? "cnic_back.jpg" : "document.pdf";

            if (rawVal.startsWith("data:image")) {
              const arr = rawVal.split(",");
              const mime = (arr[0].match(/:(.*?);/) || [])[1] || "image/png";
              const bstr = atob(arr[1]);
              let n = bstr.length;
              const u8arr = new Uint8Array(n);
              while (n--) u8arr[n] = bstr.charCodeAt(n);
              fileObj = new File([u8arr], targetFilename, { type: mime });
            } else if (rawVal.startsWith("http://") || rawVal.startsWith("https://")) {
              previewSrc = rawVal;
              const blob = new Blob([rawVal], { type: "text/plain" });
              fileObj = new File([blob], targetFilename, { type: "image/jpeg" });
            } else {
              const blob = new Blob([rawVal], { type: "image/svg+xml" });
              fileObj = new File([blob], `${targetFilename}.svg`, { type: "image/svg+xml" });
              previewSrc = "data:image/svg+xml;utf8," + encodeURIComponent(rawVal);
            }

            if (fileObj && window.DataTransfer) {
              const dt = new DataTransfer();
              dt.items.add(fileObj);
              el.files = dt.files;
            }

            updateSimulatorFilePreview(el.id, previewSrc, targetFilename, "✓ Attached via Magic Fill Memory");
            matchedFile = true;
          } catch (err) {
            console.warn("File attachment simulation error:", err);
          }
        } else if (isRadio) {
          const targetVal = String(m.value).toLowerCase().trim();
          const radios = document.querySelectorAll(`#playgroundForm input[type="radio"][name="${CSS.escape(el.name)}"]`);
          radios.forEach((r) => {
            const rVal = r.value.toLowerCase().trim();
            const parentLabel = r.closest("label") ? r.closest("label").innerText.toLowerCase() : "";
            if (rVal === targetVal || parentLabel.includes(targetVal) || (targetVal === "yes" && (rVal.includes("yes") || parentLabel.includes("yes"))) || (targetVal === "no" && (rVal.includes("no") || parentLabel.includes("no")))) {
              r.checked = true;
              r.dispatchEvent(new Event("change", { bubbles: true }));
              matchedRadio = true;
            }
          });
        } else if (isCheckbox) {
          const checkVal = String(m.value).toLowerCase().trim();
          el.checked = checkVal === "yes" || checkVal === "true" || checkVal === "1" || m.value === true;
          matchedSwitch = true;
        } else if (isRange) {
          const numVal = parseInt(String(m.value).replace(/\D/g, ""), 10) || 0;
          el.value = numVal;
          if (expDisplay) expDisplay.textContent = `${numVal} years`;
          matchedRange = true;
        } else if (type === "date") {
          const rawDate = String(m.value || "").trim();
          const isoMatch = rawDate.match(/^(\d{4}-\d{2}-\d{2})/);
          el.value = isoMatch ? isoMatch[1] : rawDate;
        } else if (isTextarea) {
          el.value = m.value;
          matchedBio = true;
        } else {
          el.value = m.value;
        }

        el.setAttribute("data-magic-fill-autofilled", "true");
        el.setAttribute("data-match-source", m.source || "deterministic");
        el.setAttribute("title", m.source === "llm" 
          ? `🧠 Smart Context Mapped: ${m.reason} (${Math.round((m.confidence || 0.85) * 100)}% confidence)`
          : `⚡ Direct Mapped: ${m.reason} (${Math.round((m.confidence || 0.98) * 100)}% confidence)`
        );
        el.classList.remove("autofilled");
        void el.offsetWidth;
        el.classList.add("autofilled");
        el.dispatchEvent(new Event("input", { bubbles: true }));
        el.dispatchEvent(new Event("change", { bubbles: true }));
        filledCount++;

        if (m.field_id === "p_institution") matchedSynonym = true;
        if (m.field_id === "p_monthly_salary" || m.field_id === "p_expected_income") matchedSalary = true;
        if (m.memory_key.startsWith("custom_fields")) matchedCustom = true;
      });

      autofillSummaryBar.classList.remove("hidden");
      let summaryText = `✓ Autofilled ${filledCount} fields (${llmCount > 0 ? `✨ ${llmCount} context-mapped via AI` : ""}${detCount > 0 ? (llmCount > 0 ? `, ${detCount} direct matched` : `${detCount} direct matched`) : ""}).`;
      if (matchedSalary) summaryText += ` Monthly Salary &rarr; stored salary.`;
      if (matchedSynonym) summaryText += ` Institution Name &rarr; university.`;
      if (matchedDropdown) summaryText += ` Dropdown options selected.`;
      if (matchedFile) summaryText += ` CNIC & photo attached with live preview.`;
      if (matchedRadio) summaryText += ` Radio buttons selected.`;
      if (matchedSwitch) summaryText += ` Checkboxes & toggle switches populated.`;
      if (matchedRange) summaryText += ` Slider value set.`;
      if (matchedBio) summaryText += ` Textarea bio populated.`;
      if (matchedCustom) summaryText += ` Custom memory attributes mapped.`;
      autofillStatsText.textContent = summaryText;

      showToast(`Autofilled ${filledCount} fields across all input types! (🟢 Green = Matched, 🔴 Red = Missing)`, "success");
    } catch (err) {
      showToast(`Autofill failed: ${err.message}`, "error");
    } finally {
      btnSimulateAutofill.disabled = false;
      btnSimulateAutofill.innerHTML = '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon></svg> <span>Run Magic Fill Autofill</span>';
    }
  });

  // -------------------------------------------------------------------------
  // Simulator File Preview Management (Manual Selection & Autofill)
  // -------------------------------------------------------------------------
  const simulatorFileConfig = {
    p_profile_photo: {
      wrap: "photoPreviewWrap",
      img: "photoPreviewImg",
      title: "photoPreviewTitle",
      status: "photoPreviewStatus",
      defaultName: "profile_photo.png",
      label: "Profile Photograph"
    },
    p_cnic_front: {
      wrap: "cnicFrontPreviewWrap",
      img: "cnicFrontPreviewImg",
      title: "cnicFrontPreviewTitle",
      status: "cnicFrontPreviewStatus",
      defaultName: "cnic_front.jpg",
      label: "CNIC Front"
    },
    p_cnic_back: {
      wrap: "cnicBackPreviewWrap",
      img: "cnicBackPreviewImg",
      title: "cnicBackPreviewTitle",
      status: "cnicBackPreviewStatus",
      defaultName: "cnic_back.jpg",
      label: "CNIC Back"
    },
    p_passport_doc: {
      wrap: "passportPreviewWrap",
      img: "passportPreviewImg",
      title: "passportPreviewTitle",
      status: "passportPreviewStatus",
      defaultName: "passport.pdf",
      label: "Passport Document"
    }
  };

  function updateSimulatorFilePreview(inputId, fileOrUrl, fileName, statusText = "✓ Attached via Magic Fill Memory") {
    const cfg = simulatorFileConfig[inputId];
    if (!cfg) return;

    const wrapEl = document.getElementById(cfg.wrap);
    const imgEl = document.getElementById(cfg.img);
    const titleEl = document.getElementById(cfg.title);
    const statusEl = document.getElementById(cfg.status);

    if (!wrapEl || !imgEl) return;

    if (!fileOrUrl) {
      wrapEl.classList.add("hidden");
      imgEl.src = "";
      if (titleEl) titleEl.textContent = cfg.defaultName;
      return;
    }

    const displayName = fileName || cfg.defaultName;
    if (titleEl) titleEl.textContent = displayName;
    if (statusEl) statusEl.textContent = statusText;

    if (typeof fileOrUrl === "string") {
      imgEl.src = fileOrUrl;
      wrapEl.classList.remove("hidden");
    } else if (fileOrUrl instanceof Blob || fileOrUrl instanceof File) {
      const isImg = fileOrUrl.type.startsWith("image/");
      const isPdf = fileOrUrl.type === "application/pdf" || fileOrUrl.name.toLowerCase().endsWith(".pdf");

      if (isImg) {
        const reader = new FileReader();
        reader.onload = (e) => {
          imgEl.src = e.target.result;
          wrapEl.classList.remove("hidden");
        };
        reader.readAsDataURL(fileOrUrl);
      } else if (isPdf) {
        imgEl.src = "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='160' height='160' viewBox='0 0 24 24' fill='none' stroke='%23e11d48' stroke-width='2'><path d='M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z'/><polyline points='14 2 14 8 20 8'/><text x='12' y='18' font-size='5' font-weight='bold' fill='%23e11d48' text-anchor='middle'>PDF</text></svg>";
        wrapEl.classList.remove("hidden");
      } else {
        imgEl.src = "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='160' height='160' viewBox='0 0 24 24' fill='none' stroke='%234f46e5' stroke-width='2'><path d='M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z'/><polyline points='14 2 14 8 20 8'/></svg>";
        wrapEl.classList.remove("hidden");
      }
    }
  }

  // Bind change listeners to simulator file inputs so manual selection gives live image preview
  Object.keys(simulatorFileConfig).forEach((inputId) => {
    const inputEl = document.getElementById(inputId);
    if (!inputEl) return;

    inputEl.addEventListener("change", (e) => {
      const file = e.target.files && e.target.files[0];
      if (file) {
        const sizeKb = (file.size / 1024).toFixed(0);
        updateSimulatorFilePreview(inputId, file, `${file.name} (${sizeKb} KB)`, "✓ Selected from Local Device");
        showToast(`Attached ${file.name} to form`, "success");
      } else {
        updateSimulatorFilePreview(inputId, null);
      }
    });
  });

  // Enable clicking the thumbnail to preview in full-screen Lightbox
  Object.values(simulatorFileConfig).forEach((cfg) => {
    const imgEl = document.getElementById(cfg.img);
    const titleEl = document.getElementById(cfg.title);
    if (!imgEl) return;

    imgEl.addEventListener("click", () => {
      if (imgEl.src && imgEl.src.length > 20) {
        const title = titleEl ? titleEl.textContent : cfg.label;
        if (typeof window.openLightbox === "function") {
          window.openLightbox(title, imgEl.src);
        }
      }
    });
  });

  // Enable remove buttons on attachment previews
  document.querySelectorAll(".btn-clear-attachment").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      const targetId = btn.getAttribute("data-target");
      const targetInput = document.getElementById(targetId);
      if (targetInput) targetInput.value = "";
      updateSimulatorFilePreview(targetId, null);
      showToast("Removed attached document", "success");
    });
  });

  function resetPlaygroundForm() {
    document.querySelectorAll("#playgroundForm input, #playgroundForm select, #playgroundForm textarea").forEach((inp) => {
      const type = (inp.type || "text").toLowerCase();
      if (type === "checkbox" || type === "radio") {
        inp.checked = false;
      } else if (type === "range") {
        inp.value = 0;
        const expDisplay = document.getElementById("expSliderDisplay");
        if (expDisplay) expDisplay.textContent = "0 years";
      } else if (type !== "submit" && type !== "reset" && type !== "button") {
        inp.value = "";
      }
      inp.removeAttribute("data-magic-fill-autofilled");
      inp.removeAttribute("data-magic-fill-status");
      inp.classList.remove("autofilled");
    });
    document.querySelectorAll("#playgroundForm [data-magic-fill-status]").forEach((wrap) => {
      wrap.removeAttribute("data-magic-fill-status");
    });
    Object.keys(simulatorFileConfig).forEach((inputId) => {
      updateSimulatorFilePreview(inputId, null);
    });
    if (autofillSummaryBar) autofillSummaryBar.classList.add("hidden");
    showToast("Testing form inputs cleared", "success");
  }

  if (btnClearForm) btnClearForm.addEventListener("click", resetPlaygroundForm);
  const btnClearFormTop = document.getElementById("btnClearFormTop");
  if (btnClearFormTop) btnClearFormTop.addEventListener("click", resetPlaygroundForm);

  btnToggleExtensionGuide.addEventListener("click", () => {
    extensionGuideBox.classList.toggle("hidden");
  });

  // -------------------------------------------------------------------------
  // 14. In-Page Demo: Manual Entry Learning Consent Banner (Light Theme)
  // -------------------------------------------------------------------------
  const playgroundEvaluatedCache = new Set();
  let manualEntryDebounce = null;

  const playgroundInputs = document.querySelectorAll("#playgroundForm input, #playgroundForm select, #playgroundForm textarea");
  playgroundInputs.forEach((inp) => {
    inp.addEventListener("change", handleManualPlaygroundInput);
    inp.addEventListener("blur", handleManualPlaygroundInput);
  });

  async function handleManualPlaygroundInput(e) {
    if (!currentAuthUser) return;
    const el = e.target;
    if (el.getAttribute("data-magic-fill-autofilled") === "true") return;

    const type = (el.type || "text").toLowerCase();
    if (type === "submit" || type === "reset" || type === "button" || type === "file") return;
    if (el.getAttribute("data-magic-fill-ignore") === "true" || el.getAttribute("data-no-learn") === "true") return;
    if (el.id === "mediaDescriptionInput" || el.name === "media_ai_description" || el.id === "rawTextInput") return;
    if (type === "radio" && !el.checked) return;

    let val = "";
    if (type === "checkbox") {
      val = el.checked ? "Yes" : "No";
    } else if (type === "radio") {
      val = el.value || "Yes";
    } else {
      val = (el.value || "").trim();
    }

    if (!val || (val.length < 2 && !val.match(/^\d+$/))) return;

    let label = "";
    if (type === "radio") {
      const groupWrap = el.closest(".modern-radio-group");
      const labelEl = groupWrap ? groupWrap.closest(".form-input-group")?.querySelector(".input-label") : null;
      label = labelEl ? labelEl.innerText.replace(/\s+/g, " ").trim() : el.name;
    } else {
      const labelEl = document.querySelector(`label[for="${el.id}"]`);
      label = labelEl ? labelEl.innerText.replace(/\s+/g, " ").trim() : (el.name || "Field");
    }

    const cacheKey = `${el.id || el.name || label}_${val.toLowerCase()}`;
    if (playgroundEvaluatedCache.has(cacheKey)) return;

    if (manualEntryDebounce) clearTimeout(manualEntryDebounce);
    manualEntryDebounce = setTimeout(async () => {
      playgroundEvaluatedCache.add(cacheKey);
      try {
        const res = await authFetch("/api/memory/evaluate-field", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            field_name: el.name || el.id,
            label: label,
            value: val,
            input_type: el.type || "text",
            placeholder: el.placeholder || null,
            form_context: "Testing Form Simulator"
          }),
        });
        const json = await res.json();
        if (json.success && json.data && json.data.is_learnable) {
          showManualLearningConsentBanner(el, json.data);
        }
      } catch (err) {
        console.warn("Field evaluation error:", err);
      }
    }, 1000);
  }

  function showManualLearningConsentBanner(el, evalData) {
    const existing = document.getElementById("inPageConsentBanner");
    if (existing) existing.remove();

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
        <button id="bannerDismissBtn" style="background:#ffffff; border:1px solid #cbd5e1; color:#475569; border-radius:9999px; padding:6px 12px; font-size:12px; font-weight:600; cursor:pointer;">Not Now</button>
        <button id="bannerKeepBtn" style="background:#f1f5f9; border:1px solid #cbd5e1; color:#334155; border-radius:9999px; padding:6px 12px; font-size:12px; font-weight:600; cursor:pointer;">Keep Existing</button>
        <button id="bannerSaveBtn" style="background:#0f172a; border:none; color:#ffffff; border-radius:9999px; padding:6px 16px; font-size:12px; font-weight:700; cursor:pointer; box-shadow:0 2px 8px rgba(15,23,42,0.15);">Update Memory</button>
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
        <button id="bannerDismissBtn" style="background:#ffffff; border:1px solid #cbd5e1; color:#475569; border-radius:9999px; padding:6px 14px; font-size:12px; font-weight:600; cursor:pointer;">Not Now</button>
        <button id="bannerSaveBtn" style="background:#0f172a; border:none; color:#ffffff; border-radius:9999px; padding:6px 16px; font-size:12px; font-weight:700; cursor:pointer; box-shadow:0 2px 8px rgba(15,23,42,0.15);">Save to Memory</button>
      `;
    }

    const banner = document.createElement("div");
    banner.id = "inPageConsentBanner";
    banner.style.cssText = "position:fixed; top:24px; right:24px; z-index:9999; animation:toastSlideIn 0.3s cubic-bezier(0.16, 1, 0.3, 1);";
    banner.innerHTML = `
      <div style="background:#ffffff; border:1px solid #cbd5e1; border-radius:14px; box-shadow:0 20px 45px -10px rgba(15,23,42,0.22), 0 2px 4px rgba(15,23,42,0.06); padding:16px 18px; width:350px; color:#0f172a; font-family:inherit;">
        <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:10px;">
          <div style="display:flex; align-items:center; gap:8px;">
            <div style="background:#0f172a; width:26px; height:26px; border-radius:7px; display:flex; align-items:center; justify-content:center; color:#fff;">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon></svg>
            </div>
            <strong style="font-size:13.5px; color:#0f172a;">${titleText}</strong>
          </div>
          <button id="bannerCloseBtn" style="background:none; border:none; color:#94a3b8; font-size:20px; cursor:pointer; line-height:1;">&times;</button>
        </div>
        ${contentHtml}
        <div style="display:flex; gap:8px; justify-content:flex-end;">
          ${buttonsHtml}
        </div>
      </div>
    `;

    document.body.appendChild(banner);

    const close = () => {
      if (banner && banner.parentNode) banner.parentNode.removeChild(banner);
    };

    banner.querySelector("#bannerCloseBtn").addEventListener("click", close);
    const dismissBtn = banner.querySelector("#bannerDismissBtn");
    if (dismissBtn) dismissBtn.addEventListener("click", close);
    const keepBtn = banner.querySelector("#bannerKeepBtn");
    if (keepBtn) keepBtn.addEventListener("click", close);

    const saveBtn = banner.querySelector("#bannerSaveBtn");
    saveBtn.addEventListener("click", async () => {
      saveBtn.disabled = true;
      saveBtn.innerText = isUpdate ? "Updating..." : "Saving...";

      try {
        const res = await authFetch("/api/memory/commit-learning", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            action_type: evalData.action_type,
            canonical_key: evalData.canonical_key,
            field_label: evalData.field_label,
            value: evalData.new_value,
            category: evalData.category === "PROFESSIONAL_INFO" ? "professional" : "personal"
          }),
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.message);

        // Dynamically update field indicator from red (missing) to green (matched)
        el.setAttribute("data-magic-fill-status", "matched");
        const wrap = el.closest(".modern-radio-group, .modern-checkbox-wrap, .toggle-switch-wrap, .modern-range-wrap, .portal-file-cell");
        if (wrap) wrap.setAttribute("data-magic-fill-status", "matched");

        saveBtn.style.background = "#059669";
        saveBtn.innerText = isUpdate ? "✓ Updated Memory!" : "✓ Saved to Memory!";
        showToast(isUpdate ? "Saved information updated in memory!" : "New information learned & saved! (Field indicator updated to Green)", "success");
        loadStoredMemory();
        setTimeout(close, 1800);
      } catch (err) {
        saveBtn.style.background = "#e11d48";
        saveBtn.innerText = "Error saving";
        setTimeout(close, 2200);
      }
    });
  }

  // -------------------------------------------------------------------------
  // 15. Helper Utilities
  // -------------------------------------------------------------------------
  function escapeHtml(str) {
    if (!str) return "";
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  function escapeJs(str) {
    if (!str) return "";
    return String(str).replace(/'/g, "\\'").replace(/"/g, '\\"');
  }

  // -------------------------------------------------------------------------
  // 16. Initialize Application Authentication & Deep-Link Routing
  // -------------------------------------------------------------------------
  async function initAuth() {
    if (currentAuthToken) {
      try {
        const res = await fetch("/api/auth/me", {
          headers: { "Authorization": `Bearer ${currentAuthToken}` },
        });
        if (res.ok) {
          const json = await res.json();
          if (json.success && json.data) {
            updateAuthUI(true, json.data);
          } else {
            handleLogout(false);
          }
        } else {
          handleLogout(false);
        }
      } catch (err) {
        console.warn("Auth initialization check failed:", err);
      }
    } else {
      updateAuthUI(false);
    }

    // Handle Deep-Links and Parameter Directives
    const path = window.location.pathname;
    const search = new URLSearchParams(window.location.search);
    const hash = window.location.hash;

    if (path === "/login" || hash === "#login") {
      if (!currentAuthUser) {
        openQuickAuth("login");
      } else if (search.get("source") === "extension") {
        generateExtensionAuthCode();
      }
    } else if (path === "/register" || hash === "#register") {
      if (!currentAuthUser) {
        openQuickAuth("register");
      }
    } else if (path === "/onboarding" || hash === "#onboarding") {
      if (!currentAuthUser) {
        openQuickAuth("login");
      } else if (onboardingModal) {
        onboardingModal.classList.remove("hidden");
      }
    } else if (hash === "#vault" || search.get("redirect") === "vault" || search.get("action") === "vault") {
      if (!currentAuthUser) {
        openQuickAuth("login");
      } else {
        switchToTab("vault");
      }
    } else if (hash === "#documents") {
      if (!currentAuthUser) {
        openQuickAuth("login");
      } else {
        switchToTab("documents");
      }
    } else if (hash === "#playground") {
      if (!currentAuthUser) {
        openQuickAuth("login");
      } else {
        switchToTab("playground");
      }
    } else if (hash === "#ingest") {
      if (!currentAuthUser) {
        openQuickAuth("login");
      } else {
        switchToTab("ingest");
      }
    }

    // Initialize Google Identity Services buttons
    initGoogleAuth();

    // Load initial memory only if authenticated
    if (currentAuthUser) {
      loadStoredMemory();
    } else {
      ensureGatewayVideosPlay();
    }

    // Initialize Smooth Scroll Animations Engine
    initScrollAnimations();
  }

  // -------------------------------------------------------------------------
  // 17. Scroll-Based Smooth Animation Engine
  // -------------------------------------------------------------------------
  function initScrollAnimations() {
    // 1. Observe Scroll Reveal Elements
    const revealElements = document.querySelectorAll(
      ".scroll-reveal, .scroll-reveal-left, .scroll-reveal-right, .scroll-reveal-scale"
    );

    if ("IntersectionObserver" in window) {
      const revealObserver = new IntersectionObserver(
        (entries, observer) => {
          entries.forEach((entry) => {
            if (entry.isIntersecting) {
              entry.target.classList.add("revealed");
              // If this is or contains the live form counter, trigger smooth count-up
              const counterEl = entry.target.id === "liveFormCounter" 
                ? entry.target 
                : entry.target.querySelector("#liveFormCounter");
              if (counterEl) {
                animateCounter(counterEl, 1480, 1600);
              }
              observer.unobserve(entry.target);
            }
          });
        },
        {
          threshold: 0.12,
          rootMargin: "0px 0px -40px 0px",
        }
      );

      revealElements.forEach((el) => revealObserver.observe(el));
    } else {
      // Fallback for older browsers
      revealElements.forEach((el) => el.classList.add("revealed"));
    }

    // 2. Smooth Number Count-Up Animation
    function animateCounter(counterEl, target, duration) {
      if (!counterEl || counterEl.dataset.animated) return;
      counterEl.dataset.animated = "true";
      let startTimestamp = null;
      const step = (timestamp) => {
        if (!startTimestamp) startTimestamp = timestamp;
        const progress = Math.min((timestamp - startTimestamp) / duration, 1);
        const easeOut = 1 - Math.pow(1 - progress, 3);
        const currentVal = Math.floor(easeOut * target);
        counterEl.textContent = currentVal.toLocaleString() + "+";
        if (progress < 1) {
          window.requestAnimationFrame(step);
        } else {
          counterEl.textContent = target.toLocaleString() + "+";
        }
      };
      window.requestAnimationFrame(step);
    }

    // 3. Parallax Motion & Navbar Scroll State
    const navPill = document.querySelector(".simplify-nav-pill");
    const cyanWavesSvg = document.querySelector(".cyan-wave-svg");
    const floatCards = document.querySelectorAll(".simplify-float-card");
    let isTicking = false;

    window.addEventListener(
      "scroll",
      () => {
        if (!isTicking) {
          window.requestAnimationFrame(() => {
            const scrollY = window.scrollY || window.pageYOffset;

            // Navbar Scrolled Glassmorphism State
            if (navPill) {
              if (scrollY > 30) {
                navPill.classList.add("scrolled");
              } else {
                navPill.classList.remove("scrolled");
              }
            }

            // Subtle Parallax Drift on Hero Cyan Wave
            if (cyanWavesSvg && scrollY < 900) {
              cyanWavesSvg.style.transform = `translateY(${scrollY * 0.08}px) rotate(${scrollY * 0.005}deg)`;
            }

            // Smooth Differential Float on Hero Floating Satellite Badges
            if (floatCards.length > 0 && scrollY < 900) {
              floatCards.forEach((card, idx) => {
                const factor = (idx % 2 === 0 ? 1 : -1) * 0.05 * (idx + 1);
                card.style.transform = `translateY(${scrollY * factor}px)`;
              });
            }

            isTicking = false;
          });
          isTicking = true;
        }
      },
      { passive: true }
    );

    // 4. Trigger video check
    ensureGatewayVideosPlay();
  }

  // Start Application
  initAuth();
});
