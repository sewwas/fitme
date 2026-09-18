import re
from pathlib import Path

html = Path("scratch/homepage_rendered.html").read_text(encoding="utf-8")

print(f"Total HTML size: {len(html)} bytes")

# Extract Title
title_match = re.search(r"<title>(.*?)</title>", html)
print("Title:", title_match.group(1) if title_match else "Not found")

# Test all critical requirements
tests = [
    # 1. Header
    ("Header Logo", "fitme-official-logo.jpg"),
    ("Header Tagline", "Train with Purpose"),
    ("Nav: The Start", "The Start"),
    ("Nav: The Method", "The Method"),
    ("Nav: Transformation", "Transformation"),
    ("Nav: Programs", "Programs"),
    ("Nav: The Arena", "The Arena"),
    ("Nav: Membership", "Membership"),
    ("Header CTA", "Start Your Transformation"),
    
    # 2. Hero - Chapter 01
    ("Hero Headline", "Transform"),
    ("Hero Subhead", "Journey"),
    ("Hero Supporting Copy", "Train with purpose. Move with confidence."),
    ("Hero Trust Row: COACHING", "COACHING"),
    ("Hero Trust Row: PROGRESS TRACKING", "PROGRESS TRACKING"),
    ("Hero Secondary CTA", "Explore Programs"),
    
    # 3. Chapter 02 - The Resistance
    ("Chapter 02 Headline", "Why Do Fitness"),
    ("Resistance 01", "NO PLAN"),
    ("Resistance 02", "NO ACCOUNTABILITY"),
    ("Resistance 03", "NO MEASURABLE PROGRESS"),
    ("Resistance Statement", "Fitness should not depend on motivation alone."),
    
    # 4. The Fit Me Method
    ("Method Headline", "A Better Way"),
    ("Step 01", "ASSESS"),
    ("Step 02", "PLAN"),
    ("Step 03", "TRAIN"),
    ("Step 04", "FUEL"),
    ("Step 05", "TRACK"),
    
    # 5. Chapter 03 - Transformation
    ("Transformation Headline", "Your Progress."),
    ("Timeline Day 01", "DAY 01"),
    ("Timeline Day 30", "DAY 30"),
    ("Timeline Day 90", "DAY 90"),
    ("Timeline Day 180", "DAY 180"),
    ("Milestone View Progress", "VIEW YOUR PROGRESS"),
    
    # 6. Programs
    ("Programs Headline", "Choose"),
    ("Program STRENGTH", "STRENGTH"),
    ("Program MUSCLE BUILDING", "MUSCLE BUILDING"),
    ("Program FAT LOSS", "FAT LOSS &amp; RECOMP"),
    ("Program ATHLETIC PERFORMANCE", "ATHLETIC PERFORMANCE"),
    ("Program BEGINNER", "BEGINNER FOUNDATIONS"),
    
    # 7. Chapter 04 - The Arena
    ("Arena Headline", "Heavy Iron."),
    ("Card: THE IRON SANCTUARY", "THE IRON SANCTUARY"),
    ("Card: HUMAN ARCHITECTURE", "HUMAN ARCHITECTURE"),
    ("Card: FUEL CALIBRATION", "FUEL CALIBRATION"),
    
    # 8. Real Results
    ("Results Headline", "Real People."),
    ("Testimonial Kasun", "Kasun Ranasinghe"),
    ("Testimonial Dilini", "Dilini Senanayake"),
    
    # 9. Coaches
    ("Coaches Headline", "Meet Your"),
    ("Coach Sewwandi", "Sewwandi Jayawardene"),
    ("Coach Ruchira", "Ruchira Perera"),
    ("Coach Janith", "Janith Silva"),
    
    # 10. Membership
    ("Membership Headline", "Find Your"),
    ("Tier STARTER", "STARTER"),
    ("Tier TRANSFORM", "TRANSFORM"),
    ("Tier ELITE", "ELITE"),
    
    # 11. FAQ
    ("FAQ Headline", "Frequently Asked"),
    ("FAQ 1", "Who is Fit Me for?"),
    ("FAQ 2", "Do I need previous gym experience?"),
    ("FAQ 3", "How does the assessment work?"),
    ("FAQ 4", "How are programs customized?"),
    ("FAQ 5", "Can I change programs?"),
    ("FAQ 6", "Do you provide nutrition guidance?"),
    ("FAQ 7", "How does membership work?"),
    
    # 12. Final CTA
    ("Final CTA Headline", "Your Day One"),
    ("Final CTA Starts Here", "Starts Here"),
    ("Member Login Button", "Member Login"),
    
    # 13. Footer & Contact
    ("Pitigala Address", "New Town, Elpitiya Road, Pitigala, 80420"),
    ("Hotline", "070 762 7878"),
    ("Copyright", "FIT ME PVT LTD"),
]

print("\n--- DETAILED SECTION & REQUIREMENT AUDIT ---")
all_passed = True
for name, needle in tests:
    found = needle.lower() in html.lower()
    if not found:
        all_passed = False
    print(f"[{'PASS' if found else 'FAIL'}] {name} ({needle})")

print("\nALL REQUIREMENTS PASSED:", all_passed)
