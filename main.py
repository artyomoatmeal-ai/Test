import requests
import random
import string
import time
import re
from bs4 import BeautifulSoup

def random_str(length=8):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

def run_test():
    base_url = "https://millymods.duckdns.org"
    session = requests.Session()
    
    username = f"bot_{random_str(6)}"
    password = "password123"
    
    print(f"[*] Registering user: {username}...")
    reg_data = {
        'username': username,
        'password': password
    }
    # Form submission in browser showed no CSRF
    r = session.post(f"{base_url}/register", data=reg_data, allow_redirects=True)
    if r.status_code not in [200, 302]:
        print(f"[!] Registration failed: {r.status_code}")
        return

    print(f"[*] Logging in as {username}...")
    login_data = {
        'username': username,
        'password': password
    }
    r = session.post(f"{base_url}/login", data=login_data, allow_redirects=True)
    if r.status_code not in [200, 302]:
        print(f"[!] Login failed: {r.status_code}")
        return

    print(f"[*] Getting submission form...")
    r = session.get(f"{base_url}/submit")
    if "authorized" in r.text.lower() and "/login" in r.url:
        print("[!] Not authorized. Login failed.")
        return
        
    soup = BeautifulSoup(r.text, 'html.parser')
    
    # Extract captcha text from label
    labels = soup.find_all('label')
    captcha_label = None
    for label in labels:
        if "Captcha:" in label.text:
            captcha_label = label
            break
            
    if not captcha_label:
        print("[!] Captcha not found on submission page.")
        # Print a snippet of the page for debugging
        # print(r.text[:500])
        return
    
    captcha_text = captcha_label.text.split("Captcha:")[1].strip()
    print(f"[*] Captcha found: {captcha_text}")
    
    try:
        # Simple arithmetic solver for "X + Y"
        parts = re.findall(r'\d+', captcha_text)
        if len(parts) == 2:
            answer = int(parts[0]) + int(parts[1])
        else:
            print(f"[!] Unrecognized captcha format: {captcha_text}")
            return
    except Exception as e:
        print(f"[!] Error solving captcha: {e}")
        return

    print(f"[*] Solved captcha: {answer}")
    
    # Post random script
    submit_data = {
        'name': f"Test Script {random_str(4).upper()}",
        'nickname': f"Bot_{username}",
        'description': f"This is an automated security test submission. Random data: {random_str(20)}",
        'captcha': str(answer)
    }
    
    # We need a dummy file too
    files = {
        'file': ('test_file.lua', b'-- This is an automated test script\nprint("Hello from ' + username.encode() + b'")')
    }
    
    r = session.post(f"{base_url}/submit", data=submit_data, files=files, allow_redirects=True)
    if r.status_code == 200:
        print(f"[+] Successfully submitted script!")
    else:
        print(f"[!] Submission failed with status {r.status_code}")

if __name__ == "__main__":
    print("=== MILLEYMODS SECURITY TESTING SCRIPT ===")
    print("Target: https://millymods.duckdns.org")
    print("Mode: Infinite Loop (Testing Account Creation & Submission Protection)")
    print("Press Ctrl+C to stop.")
    
    count = 1
    while True:
        print(f"\n--- Iteration {count:03d} ---")
        try:
            run_test()
        except KeyboardInterrupt:
            print("\n[!] Stopped by user.")
            break
        except Exception as e:
            print(f"[!!] Unexpected error: {e}")
        
        count += 1
        time.sleep(1) # Delay between iterations
