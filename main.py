import requests
import random
import string
import time
import re

# Предкомпилированные регулярки и константы
BASE_URL = "https://millymods.duckdns.org"
CAPTCHA_RE = re.compile(r'Captcha:\s*(\d+)\s*\+\s*(\d+)')
RANDOM_CHARS = string.ascii_lowercase + string.digits

SESSION_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

def random_str(length=8):
    return ''.join(random.choices(RANDOM_CHARS, k=length))


def run_test(session):
    username = f"bot_{random_str(6)}"
    password = "password123"

    # === Регистрация ===
    reg_data = {'username': username, 'password': password}
    r = session.post(f"{BASE_URL}/register", data=reg_data, allow_redirects=True, timeout=10)
    if r.status_code not in (200, 302):
        print(f"[!] Reg failed {username}: {r.status_code}")
        return False

    # === Логин ===
    login_data = {'username': username, 'password': password}
    r = session.post(f"{BASE_URL}/login", data=login_data, allow_redirects=True, timeout=10)
    if r.status_code not in (200, 302):
        print(f"[!] Login failed {username}: {r.status_code}")
        return False

    # === Получаем страницу submit (самый критичный момент по скорости) ===
    r = session.get(f"{BASE_URL}/submit", timeout=10)
    if r.status_code != 200 or "/login" in r.url:
        print(f"[!] Not authorized after login: {username}")
        return False

    # Быстрый парсинг капчи без BeautifulSoup
    match = CAPTCHA_RE.search(r.text)
    if not match:
        print(f"[!] Captcha not found for {username}")
        return False

    try:
        x, y = map(int, match.groups())
        answer = x + y
    except Exception:
        print(f"[!] Failed to solve captcha for {username}")
        return False

    # === Отправка скрипта ===
    submit_data = {
        'name': f"Test {random_str(4).upper()}",
        'nickname': f"Bot_{username[-8:]}",        # короче = чуть быстрее
        'description': f"Auto test {random_str(12)}",
        'captcha': str(answer)
    }

    files = {
        'file': ('test.lua', b'-- Auto test\nfrom ' + username.encode() + b'\nprint("Hello")')
    }

    r = session.post(f"{BASE_URL}/submit", data=submit_data, files=files, 
                     allow_redirects=True, timeout=15)

    if r.status_code == 200:
        print(f"[+] Success: {username}")
        return True
    else:
        print(f"[!] Submit failed {username}: {r.status_code}")
        return False


if __name__ == "__main__":
    print("=== MILLYMODS FAST STRESS TEST ===")
    print("Target:", BASE_URL)
    print("Press Ctrl+C to stop.\n")

    count = 0
    session = None

    try:
        while True:
            count += 1
            print(f"\n--- [{count:04d}] ---")

            # Создаём новый Session для каждого теста (чище + меньше памяти со временем)
            session = requests.Session()
            session.headers.update(SESSION_HEADERS)

            start = time.perf_counter()
            success = run_test(session)
            elapsed = time.perf_counter() - start

            print(f"    Time: {elapsed:.3f}s  |  Status: {'OK' if success else 'FAIL'}")

            time.sleep(0.8)  # можно уменьшить до 0.5–0.6, если сервер выдержит

    except KeyboardInterrupt:
        print("\n\n[!] Stopped by user.")
    except Exception as e:
        print(f"\n[!!] Critical error: {e}")
