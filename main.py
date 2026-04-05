import asyncio
import httpx
import random
import string
import re
import time
from datetime import datetime

CAPTCHA_RE = re.compile(r'Captcha:\s*(\d+)\s*\+\s*(\d+)', re.IGNORECASE | re.DOTALL)

def random_str(length: int = 8) -> str:
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))


async def run_single_test(client: httpx.AsyncClient, iteration: int, log_file):
    base_url = "https://millymods.duckdns.org"
    username = f"bot_{random_str(8)}"
    password = "password123"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        # 1. Регистрация
        await client.post(
            f"{base_url}/register",
            data={'username': username, 'password': password},
            follow_redirects=True
        )

        # 2. Логин
        await client.post(
            f"{base_url}/login",
            data={'username': username, 'password': password},
            follow_redirects=True
        )

        # 3. Получаем страницу сабмита
        r = await client.get(f"{base_url}/submit", follow_redirects=True)

        # Исправленная проверка авторизации (защита от AttributeError)
        final_url = str(r.url).lower()
        if "/login" in final_url or r.status_code != 200:
            return False, "auth_failed"

        # 4. Решаем капчу
        match = CAPTCHA_RE.search(r.text)
        if not match:
            return False, "captcha_not_found"

        answer = int(match.group(1)) + int(match.group(2))

        # 5. Сабмит
        submit_data = {
            'name': f"TS{random_str(4).upper()}",
            'nickname': username[:15],
            'description': f"stress_{iteration}",
            'captcha': str(answer)
        }

        files = {
            'file': ('t.lua', b'-- stress test')
        }

        r = await client.post(
            f"{base_url}/submit",
            data=submit_data,
            files=files,
            follow_redirects=True
        )

        success = r.status_code in (200, 302)

        if success:
            log_line = f"[{timestamp}] SUCCESS | Username: {username} | Password: {password}\n"
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(log_line)
            print(f"[+] Создан → {username}")
        else:
            print(f"[-] Сабмит не удался: {username} (status {r.status_code})")

        return success, r.status_code

    except Exception as e:
        print(f"[!] Ошибка с {username}: {type(e).__name__} - {e}")
        return False, "exception"


async def main(max_concurrency: int = 40):
    log_file = "created_accounts.log"
    
    with open(log_file, "w", encoding="utf-8") as f:
        f.write("=== MILLYMODS CREATED ACCOUNTS LOG ===\n")
        f.write(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

    print("=== FIXED ULTRA FAST TESTER + LOGGER ===")
    print(f"Concurrency: {max_concurrency}")
    print(f"Логи → {log_file}")
    print("Ctrl+C для остановки\n")

    limits = httpx.Limits(max_connections=250, max_keepalive_connections=120)
    timeout = httpx.Timeout(15.0, connect=8.0)

    async with httpx.AsyncClient(
        limits=limits,
        timeout=timeout,
        follow_redirects=True,
        http2=False
    ) as client:
        
        iteration = 0
        success_count = 0
        start_time = time.perf_counter()

        while True:
            tasks = [run_single_test(client, iteration + i + 1, log_file) 
                    for i in range(max_concurrency)]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            iteration += max_concurrency
            for res in results:
                if isinstance(res, tuple) and res[0] is True:
                    success_count += 1

            if iteration % 80 == 0:
                elapsed = time.perf_counter() - start_time
                rate = iteration / elapsed if elapsed > 0 else 0
                print(f"\r[STATS] #{iteration:05d} | Успешно: {success_count} | Скорость: {rate:.1f} акк/сек", 
                      end="", flush=True)


if __name__ == "__main__":
    try:
        asyncio.run(main(max_concurrency=40))   # начни с 40, потом поднимай
    except KeyboardInterrupt:
        print("\n\n[!] Остановлено.")
    except Exception as e:
        print(f"\n[!] Критическая ошибка: {e}")
