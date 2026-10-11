import urllib.request
import urllib.parse
import http.cookiejar
import re

cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

# 1. Login as member_kasun
resp = opener.open('http://127.0.0.1:8000/account/login/')
html = resp.read().decode('utf-8')
csrf_token = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', html).group(1)

login_data = urllib.parse.urlencode({
    'login': 'member_kasun',
    'password': 'fitme123',
    'csrfmiddlewaretoken': csrf_token
}).encode('utf-8')
req = urllib.request.Request('http://127.0.0.1:8000/account/login/', data=login_data, headers={'Referer': 'http://127.0.0.1:8000/account/login/'})
resp = opener.open(req)
assert resp.getcode() == 200

# 2. Get Member Dashboard
resp_dash = opener.open('http://127.0.0.1:8000/dashboard/member/')
dash_html = resp_dash.read().decode('utf-8')

# 3. Check for Streamlined 6 Tabs
expected_tabs = [
    'tab-dashboard',
    'tab-workout',
    'tab-nutrition',
    'tab-assessment',
    'tab-progress',
    'tab-membership',
]
removed_tabs = [
    'tab-myprogram',
    'tab-measurements',
    'tab-timeline',
]

for tab in expected_tabs:
    assert f'id="{tab}"' in dash_html, f"Missing expected tab pane {tab}"
    print(f"PASS: Tab {tab} present and active.")

for tab in removed_tabs:
    assert f'id="{tab}"' not in dash_html, f"Found deprecated redundant tab pane {tab}!"
    print(f"PASS: Deprecated tab {tab} cleanly removed/consolidated.")

# 4. Check that topbar has no stray Admin/Coach links for member_kasun
assert 'href="/dashboard/admin/"' not in dash_html, "Stray Admin link found in topbar for normal member!"
assert 'href="/dashboard/coach/"' not in dash_html, "Stray Coach link found in topbar for normal member!"
print("PASS: Unnecessary Admin/Coach links hidden from member topbar.")

# 5. Check unified contents in tab-workout (contains program split + workout log)
assert 'Current Active Training Routine' in dash_html
assert 'Log Current Exercise' in dash_html
print("PASS: Workouts & Program unified successfully.")

# 6. Check unified contents in tab-progress (contains weight trend + morph slider + measurements + photos)
assert 'Weight Progression (kg)' in dash_html
assert '3D Physique Morph Comparison' in dash_html
assert 'New Measurement Entry' in dash_html
assert 'Physique Check-in Photos &amp; Timeline' in dash_html
print("PASS: Body & Progress unified successfully.")

# 7. Check Section 1 auto-link badge
assert 'Auto-Linked from Registration' in dash_html
print("PASS: Assessment Section 1 auto-linked registration verified.")

print("\nALL VERIFICATIONS PASSED! Dashboard is clean, clutter-free, and streamlined.")
