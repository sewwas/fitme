import urllib.request
import re

url = "http://127.0.0.1:3000"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
try:
    with urllib.request.urlopen(req) as response:
        status = response.status
        html = response.read().decode('utf-8')
        print(f"STATUS: {status}")
        print(f"HTML LENGTH: {len(html)} bytes")
        
        # Check title
        title_match = re.search(r"<title>(.*?)</title>", html)
        if title_match:
            print(f"TITLE: {title_match.group(1)}")
            
        # Check headings
        headings = re.findall(r"<h[1-3][^>]*>(.*?)</h[1-3]>", html, re.DOTALL)
        print(f"FOUND {len(headings)} HEADINGS:")
        for h in headings[:12]:
            clean_h = re.sub(r"<[^>]+>", " ", h).strip()
            print(f" - {clean_h}")
            
        # Check key terms
        checks = [
            "TRANSFORM YOUR JOURNEY",
            "WHY DO FITNESS JOURNEYS STOP?",
            "A BETTER WAY TO TRAIN",
            "YOUR PROGRESS. YOUR JOURNEY.",
            "CHOOSE YOUR PATH",
            "HEAVY IRON. TRUE GUIDANCE.",
            "REAL PEOPLE. REAL PROGRESS.",
            "MEET YOUR COACHES",
            "FIND YOUR FIT",
            "FREQUENTLY ASKED QUESTIONS",
            "YOUR DAY ONE STARTS HERE",
            "070 762 7878",
            "Pitigala"
        ]
        print("\nKEYWORD VERIFICATION:")
        for term in checks:
            present = term.lower() in html.lower()
            print(f" [{'✓' if present else '✗'}] {term}")

except Exception as e:
    print(f"Error checking {url}: {e}")
