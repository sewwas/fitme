import urllib.request
import re

html = open('scratch/django_unified.html', encoding='utf-8').read()
scripts = re.findall(r'src="(/_next/[^"]+)"', html)
images = re.findall(r'src="(/images/[^"]+)"', html)

print(f"Testing port 8000 asset resolution:")
print(f"Found {len(scripts)} Next.js bundles, {len(images)} images.")

if scripts:
    url = f"http://127.0.0.1:8000{scripts[0]}"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as resp:
        print(f" [PASS] Bundle {scripts[0]}: Status {resp.status}, Size {len(resp.read())} bytes")

if images:
    url = f"http://127.0.0.1:8000{images[0]}"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as resp:
        print(f" [PASS] Image {images[0]}: Status {resp.status}, Size {len(resp.read())} bytes")

dashboards = ['/dashboard/member/', '/dashboard/coach/', '/dashboard/admin/']
for d in dashboards:
    url = f"http://127.0.0.1:8000{d}"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req) as resp:
            print(f" [PASS] Dashboard {d}: Status {resp.status}")
    except urllib.error.HTTPError as e:
        print(f" [INFO] Dashboard {d}: Status {e.code} ({e.reason})")
