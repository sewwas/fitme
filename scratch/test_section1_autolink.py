import urllib.request
import urllib.parse
import http.cookiejar
import json
import re

cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

# 1. Fetch login page to get CSRF
resp = opener.open('http://127.0.0.1:8000/account/login/')
html = resp.read().decode('utf-8')
csrf_match = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', html)
csrf_token = csrf_match.group(1) if csrf_match else None
print('1. CSRF token obtained:', bool(csrf_token))

# 2. Login as member_kasun
login_data = urllib.parse.urlencode({
    'login': 'member_kasun',
    'password': 'fitme123',
    'csrfmiddlewaretoken': csrf_token
}).encode('utf-8')
req = urllib.request.Request('http://127.0.0.1:8000/account/login/', data=login_data, headers={'Referer': 'http://127.0.0.1:8000/account/login/'})
resp = opener.open(req)
print('2. Member logged in URL:', resp.geturl(), 'Status:', resp.getcode())

# Extract session csrf
cookies = {c.name: c.value for c in cj}
member_csrf = cookies.get('csrftoken', csrf_token)

# 3. Query /api/assessments/my/
req_my = urllib.request.Request('http://127.0.0.1:8000/api/assessments/my/', headers={
    'Referer': 'http://127.0.0.1:8000/dashboard/member/',
    'X-CSRFToken': member_csrf
})
resp_my = opener.open(req_my)
my_data = json.loads(resp_my.read().decode('utf-8'))
print('3. Success in fetching /api/assessments/my/!')
print('Profile defaults extracted from registration:')
print(json.dumps(my_data.get('profile_defaults', {}), indent=2))

defs = my_data.get('profile_defaults', {})
assert defs.get('full_name'), "Missing full_name in profile_defaults"
print(f"Registered Full Name: {defs.get('full_name')}")
print(f"Registered Phone: {defs.get('phone')}")
print(f"Registered Emergency Contact: {defs.get('emergency_contact')}")

# 4. Check Member Dashboard HTML for Section 1 auto-linked badge and hidden inputs
resp_dash = opener.open('http://127.0.0.1:8000/dashboard/member/')
dash_html = resp_dash.read().decode('utf-8')
assert 'Auto-Linked from Registration' in dash_html, "Missing 'Auto-Linked from Registration' badge in HTML"
assert 'nut_full_name' in dash_html, "Missing hidden input nut_full_name in HTML"
assert 'wrk_full_name' in dash_html, "Missing hidden input wrk_full_name in HTML"
print("4. Dashboard HTML contains verified Auto-Linked Registration badge & pre-filled inputs!")

# 5. Submit Nutrition Assessment without re-typing any basic info (only assessment biometrics)
nut_payload = json.dumps({
    'height_cm': 177.0,
    'waist_cm': 83.5,
    'occupation': 'Software Architect',
    'current_weight_kg': 76.0,
    'target_weight_kg': 71.0,
    'goal_timeline_weeks': 10,
    'primary_goals': ['fat_loss', 'lean_muscle'],
    'activity_level': 'moderately_active',
}).encode('utf-8')

req_nut = urllib.request.Request('http://127.0.0.1:8000/api/assessments/nutrition/submit/', data=nut_payload, headers={
    'Content-Type': 'application/json',
    'X-CSRFToken': member_csrf,
    'Referer': 'http://127.0.0.1:8000/dashboard/member/'
})
resp_nut = opener.open(req_nut)
nut_res = json.loads(resp_nut.read().decode('utf-8'))
print('5. Nutrition Assessment submitted successfully:', nut_res)

# 6. Verify server auto-populated full_name and email from registration record
resp_my2 = opener.open(req_my)
my_data2 = json.loads(resp_my2.read().decode('utf-8'))
saved_nut = my_data2.get('nutrition_assessment', {})
print("Saved Assessment Full Name:", saved_nut.get('full_name'))
print("Saved Assessment Phone:", saved_nut.get('phone'))
print("Saved Assessment Email:", saved_nut.get('email'))
assert saved_nut.get('full_name') == defs.get('full_name'), "Server fallback did not populate member full_name!"
assert saved_nut.get('email') == defs.get('email'), "Server fallback did not populate member email!"

print("\n=======================================================")
print("ALL TESTS PASSED 100%! ZERO DUPLICATE DATA ENTRY.")
print("Section 1 is fully auto-linked to member registration.")
print("=======================================================")
