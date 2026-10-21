/**
 * Magic Fill - Background Service Worker (Manifest V3)
 * Handles secure communication between popup, content scripts, and the FastAPI backend.
 * Uses chrome.storage.local for token and credential isolation.
 */

const DEFAULT_CONFIG = {
  apiBaseUrl: "http://127.0.0.1:8000/api",
  websiteUrl: "http://127.0.0.1:8000",
};

// Keys in chrome.storage.local
const STORAGE_TOKEN_KEY = "magic_fill_token";
const STORAGE_USER_KEY = "magic_fill_user";

async function getStoredAuth() {
  return new Promise((resolve) => {
    chrome.storage.local.get([STORAGE_TOKEN_KEY, STORAGE_USER_KEY], (items) => {
      resolve({
        token: items[STORAGE_TOKEN_KEY] || null,
        user: items[STORAGE_USER_KEY] || null,
      });
    });
  });
}

async function setStoredAuth(token, user) {
  return new Promise((resolve) => {
    chrome.storage.local.set(
      {
        [STORAGE_TOKEN_KEY]: token,
        [STORAGE_USER_KEY]: user,
      },
      () => resolve()
    );
  });
}

async function clearStoredAuth() {
  return new Promise((resolve) => {
    chrome.storage.local.remove([STORAGE_TOKEN_KEY, STORAGE_USER_KEY], () => {
      resolve();
    });
  });
}

chrome.runtime.onInstalled.addListener(() => {
  console.log("Magic Fill extension installed successfully (Manifest V3).");
});

// Primary internal message listener
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  const handleAsyncMessage = async () => {
    const auth = await getStoredAuth();

    switch (message.action) {
      case "CHECK_BACKEND_HEALTH": {
        try {
          const res = await fetch("http://127.0.0.1:8000/health", { cache: "no-store" });
          if (!res.ok) throw new Error(`HTTP ${res.status}`);
          const data = await res.json();
          return { success: true, healthy: data.status === "healthy" };
        } catch (err) {
          return { success: false, error: err.message };
        }
      }

      case "GET_AUTH_STATE": {
        return {
          success: true,
          authenticated: Boolean(auth.token),
          user: auth.user,
        };
      }

      case "EXCHANGE_AUTH_CODE": {
        try {
          const code = (message.code || "").trim();
          if (!code) throw new Error("Authorization code cannot be empty.");

          const res = await fetch(`${DEFAULT_CONFIG.apiBaseUrl}/auth/extension/exchange-code`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              code: code,
              client_id: "chrome-extension",
            }),
          });

          const data = await res.json();
          if (!res.ok || !data.success) {
            throw new Error(data.message || "Failed to exchange authorization code.");
          }

          const authData = data.data || data;
          const token = authData.access_token;
          const user = authData.user;
          await setStoredAuth(token, user);

          return { success: true, user: user };
        } catch (err) {
          return { success: false, error: err.message };
        }
      }

      case "SIGN_OUT": {
        await clearStoredAuth();
        return { success: true };
      }

      case "FETCH_USER_PROFILE": {
        if (!auth.token) {
          return { success: false, error: "Unauthenticated. Please sign in via the website.", unauthenticated: true };
        }

        try {
          const url = `${DEFAULT_CONFIG.apiBaseUrl}/memory/current`;
          const res = await fetch(url, {
            headers: {
              "Authorization": `Bearer ${auth.token}`,
            },
          });

          if (res.status === 401) {
            await clearStoredAuth();
            return { success: false, sessionExpired: true, error: "Session expired. Please sign in again." };
          }

          if (!res.ok) throw new Error(`HTTP ${res.status}`);
          const data = await res.json();
          return { success: true, data: data.data, user: auth.user };
        } catch (err) {
          return { success: false, error: err.message };
        }
      }

      case "MATCH_FORM_FIELDS": {
        try {
          const headers = { "Content-Type": "application/json" };
          if (auth && auth.token) {
            headers["Authorization"] = `Bearer ${auth.token}`;
          }

          const userId = (auth.user && auth.user.id) ? auth.user.id : 1;
          const url = `${DEFAULT_CONFIG.apiBaseUrl}/matching/fields`;
          const payload = {
            user_id: userId,
            fields: message.fields,
            form_context: message.formContext || null,
          };

          const res = await fetch(url, {
            method: "POST",
            headers: headers,
            body: JSON.stringify(payload),
          });

          if (res.status === 401 && auth && auth.token) {
            await clearStoredAuth();
            return { success: false, sessionExpired: true, error: "Session expired. Please sign in again." };
          }

          if (!res.ok) {
            const errData = await res.json().catch(() => ({}));
            throw new Error(errData.message || `HTTP error ${res.status}`);
          }

          const responseData = await res.json();
          return { success: true, data: responseData.data };
        } catch (err) {
          return { success: false, error: err.message };
        }
      }

      case "SAVE_MANUAL_FIELDS_TO_MEMORY": {
        try {
          const headers = { "Content-Type": "application/json" };
          if (auth && auth.token) {
            headers["Authorization"] = `Bearer ${auth.token}`;
          }

          const userId = (auth.user && auth.user.id) ? auth.user.id : 1;
          const url = `${DEFAULT_CONFIG.apiBaseUrl}/memory/extract-raw`;
          const payload = {
            raw_text: message.rawText,
            user_id: userId,
            auto_save: true,
          };

          const res = await fetch(url, {
            method: "POST",
            headers: headers,
            body: JSON.stringify(payload),
          });

          if (res.status === 401 && auth && auth.token) {
            await clearStoredAuth();
            return { success: false, sessionExpired: true, error: "Session expired." };
          }

          if (!res.ok) {
            const errData = await res.json().catch(() => ({}));
            throw new Error(errData.message || `HTTP ${res.status}`);
          }

          const responseData = await res.json();
          return { success: true, data: responseData.data };
        } catch (err) {
          return { success: false, error: err.message };
        }
      }

      case "EVALUATE_FIELD_FOR_LEARNING": {
        try {
          const headers = { "Content-Type": "application/json" };
          if (auth && auth.token) {
            headers["Authorization"] = `Bearer ${auth.token}`;
          }

          const url = `${DEFAULT_CONFIG.apiBaseUrl}/memory/evaluate-field`;
          const res = await fetch(url, {
            method: "POST",
            headers: headers,
            body: JSON.stringify(message.field),
          });

          if (res.status === 401 && auth && auth.token) {
            await clearStoredAuth();
            return { success: false, sessionExpired: true, error: "Session expired." };
          }

          if (!res.ok) {
            const errData = await res.json().catch(() => ({}));
            throw new Error(errData.message || `HTTP ${res.status}`);
          }

          const responseData = await res.json();
          return { success: true, data: responseData.data };
        } catch (err) {
          return { success: false, error: err.message };
        }
      }

      case "COMMIT_LEARNED_FIELD": {
        try {
          const headers = { "Content-Type": "application/json" };
          if (auth && auth.token) {
            headers["Authorization"] = `Bearer ${auth.token}`;
          }

          const url = `${DEFAULT_CONFIG.apiBaseUrl}/memory/commit-learning`;
          const res = await fetch(url, {
            method: "POST",
            headers: headers,
            body: JSON.stringify(message.data),
          });

          if (res.status === 401 && auth && auth.token) {
            await clearStoredAuth();
            return { success: false, sessionExpired: true, error: "Session expired." };
          }

          if (!res.ok) {
            const errData = await res.json().catch(() => ({}));
            throw new Error(errData.message || `HTTP ${res.status}`);
          }

          const responseData = await res.json();
          return { success: true, data: responseData.data };
        } catch (err) {
          return { success: false, error: err.message };
        }
      }

      default:
        return { success: false, error: `Unknown action: ${message.action}` };
    }
  };

  handleAsyncMessage()
    .then(sendResponse)
    .catch((err) => {
      console.error("Magic Fill service worker message error:", err);
      sendResponse({ success: false, error: err.message || String(err) });
    });
  return true;
});

// External message listener (for direct website-to-extension code transmission)
chrome.runtime.onMessageExternal.addListener((message, sender, sendResponse) => {
  if (message.action === "AUTHENTICATE_WITH_CODE" && message.code) {
    (async () => {
      try {
        const res = await fetch(`${DEFAULT_CONFIG.apiBaseUrl}/auth/extension/exchange-code`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            code: message.code,
            client_id: "chrome-extension",
          }),
        });
        const data = await res.json();
        if (res.ok && data.success) {
          const authData = data.data || data;
          await setStoredAuth(authData.access_token, authData.user);
          sendResponse({ success: true, user: authData.user });
        } else {
          sendResponse({ success: false, error: data.message });
        }
      } catch (err) {
        sendResponse({ success: false, error: err.message });
      }
    })();
    return true;
  }
});
