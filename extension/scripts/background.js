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
  chrome.storage.local.get(["new_data_detection_enabled"], (items) => {
    if (items.new_data_detection_enabled === undefined) {
      chrome.storage.local.set({ new_data_detection_enabled: true });
    }
  });
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
          // Check if local Ollama or custom provider is configured
          const storedConfig = await new Promise((resolve) => {
            chrome.storage.local.get(["magic_fill_ai_config"], (items) => {
              resolve(items && items.magic_fill_ai_config ? items.magic_fill_ai_config : null);
            });
          });

          if (storedConfig && storedConfig.provider === "ollama") {
            return await executeLocalOllamaMatching(storedConfig, message.fields, message.formContext, auth);
          }

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
          // Check New Data Detection preference toggle
          const storageItems = await new Promise((resolve) => {
            chrome.storage.local.get(["new_data_detection_enabled"], resolve);
          });
          if (storageItems && storageItems.new_data_detection_enabled === false) {
            return { success: false, disabled: true, error: "New data detection is turned off." };
          }

          const tokenToUse = message.token || (auth && auth.token);
          const headers = { "Content-Type": "application/json" };
          if (tokenToUse) {
            headers["Authorization"] = `Bearer ${tokenToUse}`;
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
          const tokenToUse = message.token || (auth && auth.token);
          const headers = { "Content-Type": "application/json" };
          if (tokenToUse) {
            headers["Authorization"] = `Bearer ${tokenToUse}`;
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

      case "SYNC_TOKEN_FROM_PAGE": {
        try {
          const token = message.token;
          if (!token) return { success: false };
          if (auth && auth.token === token && auth.user) {
            return { success: true, user: auth.user };
          }
          const res = await fetch(`${DEFAULT_CONFIG.apiBaseUrl}/users/me`, {
            headers: { "Authorization": `Bearer ${token}` }
          });
          if (res.ok) {
            const data = await res.json();
            const user = data.data || data;
            await setStoredAuth(token, user);
            return { success: true, user: user };
          }
          return { success: false };
        } catch (e) {
          return { success: false, error: e.message };
        }
      }

      case "GET_AI_CONFIG": {
        try {
          const localItem = await new Promise((resolve) => {
            chrome.storage.local.get(["magic_fill_ai_config"], (items) => {
              resolve(items && items.magic_fill_ai_config ? items.magic_fill_ai_config : null);
            });
          });

          if (auth && auth.token) {
            const res = await fetch(`${DEFAULT_CONFIG.apiBaseUrl}/ai/config`, {
              headers: { "Authorization": `Bearer ${auth.token}` },
            });
            if (res.ok) {
              const serverData = await res.json();
              if (serverData && serverData.success && serverData.data) {
                const s = serverData.data;
                if (!localItem || localItem.provider !== "ollama") {
                  return { success: true, data: s };
                }
              }
            }
          }

          return {
            success: true,
            data: localItem || {
              provider: "groq",
              model_name: "llama-3.3-70b-versatile",
              api_base_url: null,
              has_api_key: false,
              masked_api_key: null,
              is_active: false,
            },
          };
        } catch (e) {
          return { success: false, error: e.message };
        }
      }

      case "SAVE_AI_CONFIG": {
        try {
          const cfg = message.config;
          await new Promise((resolve) => {
            chrome.storage.local.set({
              magic_fill_ai_config: {
                provider: cfg.provider,
                model_name: cfg.model_name,
                api_base_url: cfg.api_base_url || null,
                has_api_key: !!cfg.api_key,
                masked_api_key: cfg.api_key ? (cfg.api_key.slice(0, 3) + "..." + cfg.api_key.slice(-4)) : null,
                is_active: cfg.provider !== "groq",
              },
            }, resolve);
          });

          if (auth && auth.token && cfg.provider !== "ollama") {
            await fetch(`${DEFAULT_CONFIG.apiBaseUrl}/ai/config`, {
              method: "POST",
              headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${auth.token}`,
              },
              body: JSON.stringify({
                provider: cfg.provider,
                model_name: cfg.model_name,
                api_base_url: cfg.api_base_url || null,
                api_key: cfg.api_key || null,
              }),
            });
          }

          return { success: true };
        } catch (e) {
          return { success: false, error: e.message };
        }
      }

      case "RESET_AI_CONFIG": {
        try {
          await new Promise((resolve) => {
            chrome.storage.local.set({
              magic_fill_ai_config: {
                provider: "groq",
                model_name: "llama-3.3-70b-versatile",
                api_base_url: null,
                has_api_key: false,
                masked_api_key: null,
                is_active: false,
              },
            }, resolve);
          });

          if (auth && auth.token) {
            await fetch(`${DEFAULT_CONFIG.apiBaseUrl}/ai/config`, {
              method: "DELETE",
              headers: { "Authorization": `Bearer ${auth.token}` },
            });
          }

          return { success: true };
        } catch (e) {
          return { success: false, error: e.message };
        }
      }

      case "TEST_AI_CONFIG": {
        const { provider, model_name, api_base_url, api_key } = message.config || {};
        if (provider === "ollama") {
          const baseUrl = (api_base_url || "http://localhost:11434").replace(/\/v1\/?$/, "");
          const startTime = Date.now();
          try {
            const tagsRes = await fetch(`${baseUrl}/api/tags`, { method: "GET" });
            if (!tagsRes.ok) {
              return { success: false, error: `Ollama replied with HTTP ${tagsRes.status}. Make sure 'ollama serve' is running.` };
            }
            const tagsData = await tagsRes.json();
            const models = (tagsData.models || []).map((m) => m.name || m.model);

            const reqModel = model_name || "llama3.2";
            const modelFound = models.some((m) => m.toLowerCase().includes(reqModel.toLowerCase()));
            if (!modelFound && models.length > 0) {
              return {
                success: false,
                error: `Model '${reqModel}' not found in Ollama. Installed: ${models.join(", ")}. Run: ollama pull ${reqModel}`,
              };
            }

            const chatRes = await fetch(`${baseUrl}/v1/chat/completions`, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                model: reqModel,
                messages: [{ role: "user", content: "Reply with READY." }],
                max_tokens: 5,
                temperature: 0.1,
              }),
            });

            const latency = Date.now() - startTime;
            if (!chatRes.ok) {
              const errBody = await chatRes.text();
              return { success: false, error: `Ollama chat test failed (HTTP ${chatRes.status}): ${errBody}` };
            }

            return {
              success: true,
              message: `Ollama (${reqModel}) connected successfully in ${latency}ms!`,
              latency_ms: latency,
              model: reqModel,
              installed_models: models,
            };
          } catch (e) {
            return {
              success: false,
              error: `Could not reach Ollama on ${baseUrl}. Ensure 'ollama serve' is running. (${e.message})`,
            };
          }
        } else {
          try {
            const tokenToUse = auth && auth.token;
            const headers = { "Content-Type": "application/json" };
            if (tokenToUse) headers["Authorization"] = `Bearer ${tokenToUse}`;

            const res = await fetch(`${DEFAULT_CONFIG.apiBaseUrl}/ai/test-connection`, {
              method: "POST",
              headers: headers,
              body: JSON.stringify({
                provider: provider,
                model_name: model_name || null,
                api_base_url: api_base_url || null,
                api_key: api_key || null,
              }),
            });

            const data = await res.json();
            if (res.ok && data.success) {
              return { success: true, ...data.data };
            } else {
              return { success: false, error: data.message || `HTTP ${res.status}` };
            }
          } catch (e) {
            return { success: false, error: e.message };
          }
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

/**
 * Executes form field semantic matching using user's local Ollama instance.
 * Direct connection from browser service worker ensures remote FastAPI is never asked to call localhost.
 */
async function executeLocalOllamaMatching(config, fields, formContext, auth) {
  const baseUrl = (config.api_base_url || "http://localhost:11434").replace(/\/v1\/?$/, "");
  const model = config.model_name || "llama3.2";

  // 1. Fetch current user memory
  let userMemory = null;
  if (auth && auth.token) {
    try {
      const memRes = await fetch(`${DEFAULT_CONFIG.apiBaseUrl}/memory/current`, {
        headers: { "Authorization": `Bearer ${auth.token}` },
      });
      if (memRes.ok) {
        const memData = await memRes.json();
        userMemory = memData.data || memData;
      }
    } catch (e) {
      console.warn("Could not fetch user memory for Ollama:", e);
    }
  }

  if (!userMemory && auth && auth.user) {
    userMemory = {
      personal_info: auth.user.personal_info || {
        full_name: auth.user.full_name,
        email: auth.user.email,
      },
      experiences: auth.user.experiences || [],
      custom_fields: auth.user.custom_fields || [],
    };
  }

  if (!userMemory) {
    throw new Error("Please sign in to Magic Fill so your memory vault can be used with Ollama.");
  }

  // 2. Prepare prompt
  const systemPrompt = "You are Magic Fill, an AI personal autofill assistant. Match form fields to user records. Output strict JSON with key 'mappings' containing an array of objects with: field_id, memory_key, value, confidence (0.0 to 1.0). Only use verified values from the user's records. Never hallucinate.";

  const userPrompt = `USER VERIFIED RECORDS:\n${JSON.stringify(userMemory, null, 2)}\n\nFORM FIELDS TO FILL:\n${JSON.stringify(fields, null, 2)}${formContext ? `\n\nFORM CONTEXT: ${formContext}` : ""}\n\nReturn strictly valid JSON: {"mappings": [{"field_id": "...", "memory_key": "...", "value": "...", "confidence": 0.95}]}`;

  const res = await fetch(`${baseUrl}/v1/chat/completions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      model: model,
      messages: [
        { role: "system", content: systemPrompt },
        { role: "user", content: userPrompt },
      ],
      temperature: 0.1,
      max_tokens: 1024,
      response_format: { type: "json_object" },
    }),
  });

  if (!res.ok) {
    const errText = await res.text();
    throw new Error(`Ollama error (${res.status}): ${errText}`);
  }

  const json = await res.json();
  const content = json.choices && json.choices[0] && json.choices[0].message ? json.choices[0].message.content : "";

  let parsed = null;
  try {
    parsed = JSON.parse(content);
  } catch (e) {
    const cleaned = content.replace(/```json/gi, "").replace(/```/g, "").trim();
    const match = cleaned.match(/\{[\s\S]*\}/);
    if (match) parsed = JSON.parse(match[0]);
  }

  const rawMappings = (parsed && parsed.mappings) ? parsed.mappings : [];

  // Grounding verification
  const memoryStr = JSON.stringify(userMemory).toLowerCase();
  const groundedMappings = rawMappings.filter((m) => {
    if (!m.value) return false;
    const vStr = String(m.value).toLowerCase();
    return memoryStr.includes(vStr) || vStr === "yes" || vStr === "no" || vStr === "true" || vStr === "false";
  }).map((m) => ({
    ...m,
    source: "llm",
  }));

  return {
    success: true,
    data: {
      mappings: groundedMappings,
      total_detected: fields.length,
      total_matched: groundedMappings.length,
      provider: "ollama",
      model: model,
    },
  };
}
