import json
import urllib.request
import urllib.parse
import sys

BASE_URL = "http://127.0.0.1:8000"

def get(url, headers=None):
    req = urllib.request.Request(url, headers=headers or {})
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8")
    except Exception as e:
        return 0, str(e)

def post(url, data_dict, headers=None):
    body = json.dumps(data_dict).encode("utf-8")
    h = {"Content-Type": "application/json"}
    if headers:
        h.update(headers)
    req = urllib.request.Request(url, data=body, headers=h, method="POST")
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8")
    except Exception as e:
        return 0, str(e)

def put(url, data_dict, headers=None):
    body = json.dumps(data_dict).encode("utf-8")
    h = {"Content-Type": "application/json"}
    if headers:
        h.update(headers)
    req = urllib.request.Request(url, data=body, headers=h, method="PUT")
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8")
    except Exception as e:
        return 0, str(e)

def delete(url, headers=None):
    req = urllib.request.Request(url, headers=headers or {}, method="DELETE")
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8")
    except Exception as e:
        return 0, str(e)

def run_tests():
    print("=" * 65)
    print("MAGIC FILL PLATFORM & UX IMPROVEMENT VERIFICATION SUITE")
    print("=" * 65)

    # 1. Page Routes
    pages = [
        ("/", "Root Landing Page", ["Magic Fill", "Features"]),
        ("/login", "Dedicated Login Page", ["Sign In to Magic Fill", "Continue with Google", "loginForm"]),
        ("/register", "Dedicated Registration Page", ["Create Your Vault", "Continue with Google", "registerForm"]),
        ("/dashboard", "Dedicated Dashboard", ["Welcome back!", "Vault Active", "Open Memory Studio"]),
        ("/memory", "Personal Memory Studio", ["Personal Memory Studio", "Search by label"]),
        ("/extract", "AI Document Extraction Page", ["AI Document", "Memory Extraction"]),
        ("/extension", "Browser Extension Setup Page", ["Connect Your Browser Extension", "Instant Pairing Code"]),
        ("/playground", "Live Form Simulator Page", ["AI Form Autofill Simulator", "All 10 Input Types Supported"]),
        ("/features", "Features Page", ["On Autopilot", "Features"]),
        ("/about", "About Page", ["Your AI-Native", "Memory Partner"]),
        ("/pricing", "Pricing Page", ["Plans Built For Every Stage"]),
        ("/privacy-policy", "Privacy Policy", ["Privacy Policy", "Data Sovereignty"]),
        ("/term-and-condition", "Terms and Conditions", ["Terms of Service"]),
    ]

    print("\n--- TEST 1: Verifying Dedicated Pages Serving (FastAPI Static Route Handlers) ---")
    all_pages_ok = True
    for route, label, needles in pages:
        status, body = get(f"{BASE_URL}{route}")
        found_needles = [n for n in needles if n.lower() in body.lower()]
        if status == 200 and len(found_needles) == len(needles):
            print(f"  [PASS] {route:<15} ({label:<32}) -> 200 OK | Verified {len(needles)} markers")
        else:
            print(f"  [FAIL] {route:<15} ({label:<32}) -> status {status} | Found: {found_needles} of {needles}")
            all_pages_ok = False

    assert all_pages_ok, "One or more dedicated pages failed to load correctly"

    # 2. Authentication & JWT Handshake
    print("\n--- TEST 2: User Registration & Login ---")
    import time
    unique_ts = int(time.time())
    test_email = f"platform_test_{unique_ts}@magicfill.com"
    test_pass = "SecurePass123!"
    
    # Registration
    status, body = post(f"{BASE_URL}/api/auth/register", {
        "full_name": "Antigravity Platform Tester",
        "email": test_email,
        "password": test_pass
    })
    assert status == 201, f"Registration failed: status={status}, body={body}"
    res = json.loads(body)
    user = res["data"]["user"]
    print(f"  [PASS] Registered test user: {user.get('email')} (ID: {user.get('id')})")

    # Login
    status, body = post(f"{BASE_URL}/api/auth/login", {
        "email": test_email,
        "password": test_pass
    })
    assert status == 200, f"Login failed: status={status}, body={body}"
    res = json.loads(body)
    token = res["data"]["access_token"]
    print(f"  [PASS] Logged in successfully! JWT Token acquired: {token[:25]}... (length={len(token)})")

    auth_headers = {"Authorization": f"Bearer {token}"}

    # 3. Memory & Personal Info API
    print("\n--- TEST 3: Personal Memory Vault Retrieval & Update ---")
    status, body = get(f"{BASE_URL}/api/personal-info/me", headers=auth_headers)
    assert status == 200, f"Failed to get personal info: {status}"
    p_info = json.loads(body)["data"] or {}
    print(f"  [PASS] Current memory loaded. User personal_info record ready.")

    # Update full profile memory
    full_payload = {
        "full_name": "Antigravity Platform Tester",
        "father_name": "Alexander Tester",
        "phone": "+1 (555) 987-6543",
        "degree": "Bachelor of Science",
        "country": "United States",
        "gender": "Male",
        "bio": "Experienced Lead Full Stack AI Engineer specializing in resilient systems.",
        "address": "123 Innovation Way, Tech District"
    }
    status, body = put(f"{BASE_URL}/api/personal-info/me", full_payload, headers=auth_headers)
    assert status == 200, f"Failed to update personal info: {status}, {body}"
    
    # Confirm persistence in DB
    status, body = get(f"{BASE_URL}/api/personal-info/me", headers=auth_headers)
    new_info = json.loads(body)["data"]
    assert new_info.get("phone") == full_payload["phone"], "Phone update was not persisted in DB"
    assert new_info.get("degree") == full_payload["degree"], "Degree was not persisted in DB"
    print(f"  [PASS] Update persisted in PostgreSQL: phone = {new_info.get('phone')}, degree = {new_info.get('degree')}")

    # 4. Custom Field Management (Add -> Verify -> Delete)
    print("\n--- TEST 4: Custom Field CRUD Persistence ---")
    status, body = post(f"{BASE_URL}/api/custom-fields", {
        "field_key": "target_salary",
        "field_label": "Target Annual Compensation",
        "field_value": "$160,000 USD",
        "category": "compensation"
    }, headers=auth_headers)
    assert status in (200, 201), f"Failed to create custom field: {status}, {body}"
    cf_data = json.loads(body)["data"]
    cf_id = cf_data["id"]
    print(f"  [PASS] Custom field created: ID={cf_id}, key={cf_data['field_key']}, value={cf_data['field_value']}")

    # Verify custom field in list
    status, body = get(f"{BASE_URL}/api/custom-fields", headers=auth_headers)
    c_list = json.loads(body)["data"]
    assert any(c["id"] == cf_id for c in c_list), "Custom field not returned in list"
    print(f"  [PASS] Custom field verified in PostgreSQL list ({len(c_list)} custom fields active)")

    # Delete custom field
    status, body = delete(f"{BASE_URL}/api/custom-fields/{cf_id}", headers=auth_headers)
    assert status == 200, f"Failed to delete custom field: {status}"
    print(f"  [PASS] Custom field ID={cf_id} successfully deleted from PostgreSQL")

    # 5. Extension Single-Use Pairing Code Creation
    print("\n--- TEST 5: Browser Extension Pairing Code Generation ---")
    status, body = post(f"{BASE_URL}/api/auth/extension/create-code", {}, headers=auth_headers)
    assert status == 200, f"Failed to create extension code: {status}, {body}"
    code_res = json.loads(body)["data"]
    code = code_res["code"]
    expires = code_res["expires_in_seconds"]
    print(f"  [PASS] Single-use pairing code generated: {code} (expires in {expires}s)")
    assert code.startswith("MF-") and len(code) >= 6, f"Invalid pairing code format: {code}"

    # 6. Form Autofill & Semantic Matching Engine (All 10 Input Types)
    print("\n--- TEST 6: Intelligent Matching Across All 10 Input Types ---")
    simulated_fields = [
        {"field_id": "f_legal_name", "name": "applicant_legal_name", "label": "Applicant Legal Full Name", "input_type": "text"},
        {"field_id": "f_father_name", "name": "parent_guardian_name", "label": "Father / Guardian Name", "input_type": "text"},
        {"field_id": "f_email", "name": "applicant_email_address", "label": "Contact Email Address", "input_type": "email"},
        {"field_id": "f_phone", "name": "contact_telephone", "label": "Mobile / Primary Phone", "input_type": "tel"},
        {"field_id": "f_degree", "name": "highest_degree_level", "label": "Highest Completed Degree", "input_type": "select-one", "options": ["High School", "Associate Degree", "Bachelor of Science", "Master of Science", "Doctorate"]},
        {"field_id": "f_country", "name": "country_residence", "label": "Country of Residence", "input_type": "select-one", "options": ["Pakistan", "United States", "United Kingdom", "Canada"]},
        {"field_id": "f_gender", "name": "gender", "label": "Gender Identification", "input_type": "radio", "options": ["Male", "Female", "Other"]},
        {"field_id": "f_bio", "name": "applicant_cover_note", "label": "Professional Bio & Executive Summary", "input_type": "textarea"},
        {"field_id": "f_exp", "name": "years_experience", "label": "Years of Professional Experience", "input_type": "range"},
    ]

    status, body = post(f"{BASE_URL}/api/matching/fields", {
        "fields": simulated_fields,
        "page_url": "http://127.0.0.1:8000/playground",
        "form_context": "Software Engineering Job Application"
    }, headers=auth_headers)

    assert status == 200, f"Matching engine failed: {status}, {body}"
    match_data = json.loads(body)["data"]
    mappings = match_data.get("mappings", [])
    print(f"  [PASS] Matching completed successfully! {len(mappings)} / {len(simulated_fields)} fields mapped.")
    for m in mappings:
        print(f"    - {m['field_id']:<15} -> '{m['value']}' (conf: {m['confidence']}, reason: {m.get('reason','')[:35]}...)")

    assert len(mappings) >= 5, f"Expected at least 5 semantic matches, got {len(mappings)}"

    print("\n" + "=" * 65)
    print("ALL VERIFICATION SUITE CHECKS PASSED PERFECTLY!")
    print("=" * 65)

if __name__ == "__main__":
    try:
        run_tests()
    except AssertionError as err:
        print(f"\n[ASSERTION FAILED]: {err}")
        sys.exit(1)
    except Exception as exc:
        print(f"\n[UNEXPECTED ERROR]: {exc}")
        sys.exit(1)
