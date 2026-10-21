# Magic Fill — Chromium Browser Extension (Manifest V3)

Intelligent web form auto-completion connected to the Magic Fill unified authentication and personal memory database.

---

## 🚀 How to Install and Connect in Chrome / Brave / Edge

### Step 1: Start the FastAPI Backend & Web Application
In PowerShell, navigate to the `backend/` directory and run:
```powershell
cd backend
.\.venv\Scripts\uvicorn.exe app.main:app --host 127.0.0.1 --port 8000 --reload
```
Ensure the backend and web application are accessible at `http://127.0.0.1:8000`.

### Step 2: Create Account / Sign In on the Website
1. Open `http://127.0.0.1:8000` in your Google Chrome browser.
2. Click **Create Account** (or **Sign In** if you already have an account).
3. The website handles all signup and password logins securely. Passwords are never typed into or stored by the browser extension.

### Step 3: Load the Unpacked Extension in Chrome
1. In Google Chrome, navigate to `chrome://extensions/` in your address bar.
2. Enable the **"Developer mode"** toggle in the top-right corner.
3. Click the **"Load unpacked"** button in the top-left corner.
4. Select the `extension/` directory from this project (`.../Magic_Fill/extension`).

### Step 4: Authorize the Extension
1. Click the **Magic Fill** icon in your Chrome toolbar.
2. If not authenticated, click **"Sign In on Website"** or click **"1-Click Sync from Active Web Tab"** if your website tab is open.
3. Alternatively, click **"Connect Extension"** in the website navigation bar to generate a short-lived, single-use authorization code (e.g., `MF-ABC12345`), paste it into the extension popup, and click **Link**.
4. The extension securely exchanges the single-use code for an isolated session token without transmitting passwords or exposing tokens in URLs.
5. Your authenticated memory profile is immediately active!

---

## ⚡ Features & Workflows

1. **Website-Only Authentication**:
   - One unified account and PostgreSQL backend shared by the website and extension.
   - Extension popup never asks for or stores plaintext passwords.
   - Single-use authorization codes with anti-replay and expiration protection.

2. **Manage My Information**:
   - Clicking **Manage My Information** in the popup opens the website directly at your personal memory vault (`/#vault`).
   - Private pages require authentication; after login, redirects to your intended page.
   - Strict cross-user data isolation: you can only view, edit, or delete your own personal records.

3. **Form Detection & Autofill**:
   - Scans DOM elements (`input`, `select`, `textarea`), extracts accessible labels and types.
   - Matches against authenticated user's records via FastAPI matching engine.
   - Never auto-submits forms; fills fields and allows user review before manual submission.

4. **Sign Out**:
   - Clicking **Sign Out** inside the extension popup safely terminates the extension session and clears local credentials without deleting any data on your backend account.
