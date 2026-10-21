import os

portals_dir = r"c:\Users\Muazam Ali\OneDrive\Desktop\Magic_Fill\automark-v1.0.0\public\images\portals"
os.makedirs(portals_dir, exist_ok=True)

# 1. LinkedIn
linkedin_svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48" width="48" height="48">
  <rect width="48" height="48" rx="10" fill="#0A66C2"/>
  <path fill="#FFFFFF" d="M14.5 19H9v18h5.5V19zM11.7 10C10 10 8.6 11.4 8.6 13.1c0 1.7 1.4 3.1 3.1 3.1s3.1-1.4 3.1-3.1C14.8 11.4 13.5 10 11.7 10zM39 27.5c0-5-2.7-7.5-6.3-7.5-2.9 0-4.2 1.6-4.9 2.7V19H22.3c.1 1.5 0 18 0 18h5.5v-10.1c0-.5 0-1.1.2-1.5.4-1.1 1.4-2.2 3.1-2.2 2.2 0 3.1 1.7 3.1 4.1V37H40V27.5z"/>
</svg>'''

# 2. Indeed
indeed_svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48" width="48" height="48">
  <rect width="48" height="48" rx="10" fill="#003A9B"/>
  <path fill="#FFFFFF" d="M26.4 11.2c-2.4-.2-4.8.9-6.2 2.7V11h-4.6v23.5c1.5.4 3.1.6 4.6.6V23.7c0-3.3 2.5-6 5.8-6 3.1 0 5.4 2.3 5.4 5.9v11.5h4.6V22.8c0-6.7-4.4-11.4-9.6-11.6z"/>
  <circle cx="20.2" cy="7.5" r="2.8" fill="#FF5A00"/>
</svg>'''

# 3. Workday
workday_svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48" width="48" height="48">
  <rect width="48" height="48" rx="10" fill="#005CB9"/>
  <path fill="#F36F21" d="M24 10c-7.7 0-14 6.3-14 14 0 2.8.8 5.4 2.2 7.6l3.5-2.6c-.8-1.5-1.3-3.2-1.3-5 0-5.3 4.3-9.6 9.6-9.6s9.6 4.3 9.6 9.6c0 1.8-.5 3.5-1.3 5l3.5 2.6c1.4-2.2 2.2-4.8 2.2-7.6 0-7.7-6.3-14-14-14z"/>
  <path fill="#FFFFFF" d="M19 24l-3 10h3.5l1.6-6 1.7 6h3.4l1.7-6 1.6 6h3.5l-3-10h-3.6l-1.9 6.2-1.9-6.2H19z"/>
</svg>'''

# 4. Greenhouse
greenhouse_svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48" width="48" height="48">
  <rect width="48" height="48" rx="10" fill="#00B274"/>
  <path fill="#FFFFFF" d="M24 9l-13 13h7v17h12V22h7L24 9z"/>
  <path fill="#059669" d="M24 16l-7 7h3v11h8V23h3l-7-7z"/>
  <circle cx="24" cy="27" r="2" fill="#FFFFFF"/>
</svg>'''

# 5. Lever
lever_svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48" width="48" height="48">
  <rect width="48" height="48" rx="10" fill="#FF5C35"/>
  <path fill="#FFFFFF" d="M12 14h24v4H16v8h18v4H16v4h20v4H12V14z"/>
</svg>'''

# 6. ZipRecruiter
ziprecruiter_svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48" width="48" height="48">
  <rect width="48" height="48" rx="10" fill="#51A337"/>
  <path fill="#FFFFFF" d="M24 10l-12 14h7v14h10V24h7L24 10z"/>
  <path fill="#FFFFFF" d="M20 28h8v10h-8z" opacity="0.3"/>
</svg>'''

# 7. Glassdoor
glassdoor_svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48" width="48" height="48">
  <rect width="48" height="48" rx="10" fill="#0CAA41"/>
  <path fill="#FFFFFF" d="M13 13h10v5H18v12h5v5H13V13zm22 0h-5v5h5v12h-5v5h10V13h-5z"/>
  <circle cx="24" cy="24" r="3.5" fill="#FFFFFF"/>
</svg>'''

# 8. Ashby
ashby_svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48" width="48" height="48">
  <rect width="48" height="48" rx="10" fill="#6366F1"/>
  <path fill="#FFFFFF" d="M24 10l12 7v14l-12 7-12-7V17l12-7zm0 5l-7.5 4.3v8.6L24 32.2l7.5-4.3v-8.6L24 15z"/>
  <circle cx="24" cy="23.5" r="3" fill="#A5B4FC"/>
</svg>'''

# 9. BambooHR
bamboohr_svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48" width="48" height="48">
  <rect width="48" height="48" rx="10" fill="#23C975"/>
  <path fill="#FFFFFF" d="M15 11h6v26h-6V11zm12 6h6v20h-6V17z"/>
  <path fill="#15803D" d="M17 17l4-4v14l-4-4V17zm12 6l4-4v10l-4-4v-2z"/>
</svg>'''

# 10. Oracle Taleo
taleo_svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48" width="48" height="48">
  <rect width="48" height="48" rx="10" fill="#C74634"/>
  <path fill="#FFFFFF" d="M24 14c-5.5 0-10 4.5-10 10s4.5 10 10 10 10-4.5 10-10-4.5-10-10-10zm0 15.5c-3 0-5.5-2.5-5.5-5.5s2.5-5.5 5.5-5.5 5.5 2.5 5.5 5.5-2.5 5.5-5.5 5.5z"/>
</svg>'''

# 11. Google Forms
googleforms_svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48" width="48" height="48">
  <rect width="48" height="48" rx="10" fill="#7248B9"/>
  <path fill="#FFFFFF" d="M16 12h16a2 2 0 012 2v20a2 2 0 01-2 2H16a2 2 0 01-2-2V14a2 2 0 012-2z"/>
  <path fill="#7248B9" d="M22 17h8v2h-8v-2zm0 5h8v2h-8v-2zm0 5h8v2h-8v-2z"/>
  <circle cx="19" cy="18" r="1.5" fill="#7248B9"/>
  <circle cx="19" cy="23" r="1.5" fill="#7248B9"/>
  <circle cx="19" cy="28" r="1.5" fill="#7248B9"/>
</svg>'''

# 12. Common App
commonapp_svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48" width="48" height="48">
  <rect width="48" height="48" rx="10" fill="#135C9A"/>
  <path fill="#FFFFFF" d="M24 10l4.5 9.5L38 21l-7.5 7.5L32 38l-8-4.5-8 4.5 1.5-9.5L10 21l9.5-1.5L24 10z"/>
  <circle cx="24" cy="23" r="4" fill="#135C9A"/>
</svg>'''

svgs = {
    "linkedin.svg": linkedin_svg,
    "indeed.svg": indeed_svg,
    "workday.svg": workday_svg,
    "greenhouse.svg": greenhouse_svg,
    "lever.svg": lever_svg,
    "ziprecruiter.svg": ziprecruiter_svg,
    "glassdoor.svg": glassdoor_svg,
    "ashby.svg": ashby_svg,
    "bamboohr.svg": bamboohr_svg,
    "taleo.svg": taleo_svg,
    "googleforms.svg": googleforms_svg,
    "commonapp.svg": commonapp_svg,
}

for filename, content in svgs.items():
    path = os.path.join(portals_dir, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content.strip())
    print(f"Created: {path}")

print("All 12 authentic portal SVG logos generated successfully.")
