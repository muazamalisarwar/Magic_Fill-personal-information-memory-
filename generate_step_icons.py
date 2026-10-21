import os

proc_dir = r"c:\Users\Muazam Ali\OneDrive\Desktop\Magic_Fill\automark-v1.0.0\public\images\process"
os.makedirs(proc_dir, exist_ok=True)

# Step 1: Vault Icon
step1_svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="64" height="64" fill="none">
  <rect width="64" height="64" rx="16" fill="url(#vault_bg)"/>
  <path d="M32 14L46 20V32C46 41 39.5 48.5 32 51C24.5 48.5 18 41 18 32V20L32 14Z" fill="url(#vault_shield)" stroke="#A78BFA" stroke-width="2"/>
  <path d="M26 31C26 28 28.5 26 32 26C35.5 26 38 28 38 31V33H39C40.1 33 41 33.9 41 35V41C41 42.1 40.1 43 39 43H25C23.9 43 23 42.1 23 41V35C23 33.9 23.9 33 25 33H26V31ZM28 33H36V31C36 29.3 34.3 28 32 28C29.7 28 28 29.3 28 31V33Z" fill="#FFFFFF"/>
  <circle cx="32" cy="37.5" r="1.8" fill="#8450FF"/>
  <defs>
    <linearGradient id="vault_bg" x1="0" y1="0" x2="64" y2="64" gradientUnits="userSpaceOnUse">
      <stop stop-color="#8450FF" stop-opacity="0.25"/>
      <stop offset="1" stop-color="#6366F1" stop-opacity="0.1"/>
    </linearGradient>
    <linearGradient id="vault_shield" x1="18" y1="14" x2="46" y2="51" gradientUnits="userSpaceOnUse">
      <stop stop-color="#8450FF"/>
      <stop offset="1" stop-color="#6366F1"/>
    </linearGradient>
  </defs>
</svg>'''

# Step 2: Extension Icon
step2_svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="64" height="64" fill="none">
  <rect width="64" height="64" rx="16" fill="url(#ext_bg)"/>
  <!-- Browser window frame -->
  <rect x="14" y="16" width="36" height="28" rx="5" fill="#1E1B4B" stroke="#818CF8" stroke-width="2"/>
  <path d="M14 23H50" stroke="#818CF8" stroke-width="1.5"/>
  <circle cx="19" cy="19.5" r="1.5" fill="#F43F5E"/>
  <circle cx="24" cy="19.5" r="1.5" fill="#F59E0B"/>
  <circle cx="29" cy="19.5" r="1.5" fill="#10B981"/>
  <!-- Puzzle / Connector plugin -->
  <path d="M30 28H37C38.1 28 39 28.9 39 30V33C39.8 33 40.5 33.7 40.5 34.5C40.5 35.3 39.8 36 39 36V39C39 40.1 38.1 41 37 41H34C34 40.2 33.3 39.5 32.5 39.5C31.7 39.5 31 40.2 31 41H28C26.9 41 26 40.1 26 39V36C26.8 36 27.5 35.3 27.5 34.5C27.5 33.7 26.8 33 26 33V30C26 28.9 26.9 28 28 28H30Z" fill="url(#ext_accent)"/>
  <!-- Lightning bolt badge -->
  <path d="M43 33L37 42H42L40 50L49 40H44L46 33H43Z" fill="#FACC15" stroke="#CA8A04" stroke-width="1"/>
  <defs>
    <linearGradient id="ext_bg" x1="0" y1="0" x2="64" y2="64" gradientUnits="userSpaceOnUse">
      <stop stop-color="#6366F1" stop-opacity="0.25"/>
      <stop offset="1" stop-color="#38BDF8" stop-opacity="0.1"/>
    </linearGradient>
    <linearGradient id="ext_accent" x1="26" y1="28" x2="41" y2="41" gradientUnits="userSpaceOnUse">
      <stop stop-color="#818CF8"/>
      <stop offset="1" stop-color="#C084FC"/>
    </linearGradient>
  </defs>
</svg>'''

# Step 3: Autofill Icon
step3_svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="64" height="64" fill="none">
  <rect width="64" height="64" rx="16" fill="url(#fill_bg)"/>
  <!-- Form clipboard -->
  <rect x="16" y="15" width="32" height="38" rx="4" fill="#064E3B" stroke="#34D399" stroke-width="2"/>
  <rect x="24" y="12" width="16" height="6" rx="2" fill="#10B981" stroke="#34D399" stroke-width="1.5"/>
  <!-- Lines with checkmarks -->
  <path d="M22 25L26 29L33 21" stroke="#34D399" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
  <path d="M37 25H42" stroke="#A7F3D0" stroke-width="2" stroke-linecap="round"/>
  <path d="M22 34L26 38L33 30" stroke="#34D399" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
  <path d="M37 34H42" stroke="#A7F3D0" stroke-width="2" stroke-linecap="round"/>
  <!-- Magic wand with glowing sparks -->
  <path d="M48 16L34 30" stroke="#FDE047" stroke-width="3" stroke-linecap="round"/>
  <circle cx="49" cy="15" r="2.5" fill="#FEF08A"/>
  <path d="M49 9V12M49 18V21M43 15H46M52 15H55" stroke="#FACC15" stroke-width="1.8" stroke-linecap="round"/>
  <defs>
    <linearGradient id="fill_bg" x1="0" y1="0" x2="64" y2="64" gradientUnits="userSpaceOnUse">
      <stop stop-color="#10B981" stop-opacity="0.25"/>
      <stop offset="1" stop-color="#059669" stop-opacity="0.1"/>
    </linearGradient>
  </defs>
</svg>'''

icons = {
    "step-vault.svg": step1_svg,
    "step-extension.svg": step2_svg,
    "step-autofill.svg": step3_svg,
}

for filename, content in icons.items():
    path = os.path.join(proc_dir, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content.strip())
    print(f"Created: {path}")

print("All 3 step icons created successfully.")
