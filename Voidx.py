#!/usr/bin/env python3
"""voidx — OSINT toolkit."""

import hashlib
import importlib.util
import ipaddress
import os
import random
import re
import socket
import subprocess
import sys
import time
import urllib.parse

RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
WHITE = "\033[97m"
RESET = "\033[0m"

REQUIRED_MODULES = [
    ("requests", "requests"),
    ("bs4", "beautifulsoup4"),
    ("whois", "python-whois"),
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
}

# Search pacing: minimum seconds between outbound search requests.
_MIN_INTERVAL = 2.5
_last_hit = 0.0
BLOCK_MARKERS = ("bots use duckduckgo", "anomaly-modal", "anomaly_modal")


def show_interactive_help():
    clear_screen()
    print(f"{CYAN}======================================================{RESET}")
    print(f"{RED}       VOIDX MANUAL INSTALLATION GUIDE (MAN){RESET}")
    print(f"{CYAN}======================================================{RESET}\n")
    print(f"{WHITE}Welcome to the manual setup guide. Type commands below:{RESET}\n")
    print(f"{YELLOW}--- STAGE 1: Environment Variable Export ---{RESET}")
    print(f"{CYAN}Type:{RESET} export VOIDX_BOOTSTRAP_STATE=UNLOCKED\n")
    print(f"{YELLOW}--- STAGE 2: Root Configuration Staging ---{RESET}")
    print(f"{CYAN}Type:{RESET} mkdir -p ~/.config/voidx && echo 'root_init=true' > ~/.config/voidx/bootstrap.lock && chmod 400 ~/.config/voidx/bootstrap.lock\n")
    print(f"{YELLOW}--- STAGE 3: Python Package Dependencies ---{RESET}")
    print(f"{CYAN}Type:{RESET} pip install requests beautifulsoup4 python-whois\n")
    try:
        input(f"{WHITE}Press [ENTER] to return...{RESET}")
    except (KeyboardInterrupt, EOFError):
        pass
def check_fully_installed():
    if os.environ.get("VOIDX_BOOTSTRAP_STATE") != "UNLOCKED":
        return False
    config_file = os.path.expanduser("~/.config/voidx/bootstrap.lock")
    if not os.path.exists(config_file):
        return False
    try:
        if oct(os.stat(config_file).st_mode)[-3:] != "400":
            return False
    except Exception:
        return False
    for mod_name, _ in REQUIRED_MODULES:
        if importlib.util.find_spec(mod_name) is None:
            return False
    return True


def bootstrapper():
    if check_fully_installed():
        return

    while True:
        clear_screen()
        print(f"{CYAN}======================================================{RESET}")
        print(f"{RED}             VOIDX BOOTSTRAPPER v2.0{RESET}")
        print(f"{CYAN}======================================================{RESET}\n")
        print(f"{WHITE}Tip: Type shell commands here (export, mkdir, pip) or 'help'.{RESET}")
        print(f"{YELLOW}Press [ENTER] with a blank line to run the verification audit.{RESET}")
        
        try:
            choice = input(f"\n{WHITE}boot> {RESET}").strip()
        except (KeyboardInterrupt, EOFError):
            sys.exit(0)
        
        if not choice:
            pass
        elif choice.lower() in ("exit", "0"):
            sys.exit(0)
        elif choice.lower() == "help":
            show_interactive_help()
            continue
        elif choice.startswith("export "):
            try:
                parts = choice[7:].split("=", 1)
                if len(parts) == 2:
                    k, v = parts[0].strip(), parts[1].strip().strip('"\'')
                    os.environ[k] = v
                    print(f"{GREEN}[✔] Exported: {k}={v}{RESET}")
                else:
                    print(f"{RED}[!] Invalid syntax. Use: export KEY=VALUE{RESET}")
            except Exception as e:
                print(f"{RED}[!] Error: {e}{RESET}")
            try:
                input(f"\n{WHITE}Press [ENTER] to continue...{RESET}")
            except (KeyboardInterrupt, EOFError):
                pass
            continue
        else:
            ret = os.system(choice)
            if ret == 0:
                print(f"{GREEN}[✔] Command executed successfully.{RESET}")
            else:
                print(f"{RED}[!] Command returned non-zero exit code.{RESET}")
            try:
                input(f"\n{WHITE}Press [ENTER] to continue...{RESET}")
            except (KeyboardInterrupt, EOFError):
                pass
            continue

        # --- AUDIT SEQUENCE ---
        clear_screen()
        print(f"{CYAN}======================================================{RESET}")
        print(f"{RED} VOIDX SYSTEM AUDIT IN PROGRESS{RESET}")
        print(f"{CYAN}======================================================{RESET}\n")

        print(f"{YELLOW}[STAGE 1/3] Environment Variable Verification...{RESET}")
        if os.environ.get("VOIDX_BOOTSTRAP_STATE") != "UNLOCKED":
            print(f"{RED}[X] FATAL: Environment variable 'VOIDX_BOOTSTRAP_STATE' is not set.{RESET}")
            try:
                input(f"\n{WHITE}Press [ENTER] to return to boot prompt...{RESET}")
            except (KeyboardInterrupt, EOFError):
                pass
            continue
        print(f"{GREEN}[✔] Stage 1 passed.{RESET}\n")
        time.sleep(0.5)

        print(f"{YELLOW}[STAGE 2/3] Root Staging & Permission Audit...{RESET}")
        config_file = os.path.expanduser("~/.config/voidx/bootstrap.lock")
        if not os.path.exists(config_file):
            print(f"{RED}[X] FATAL: Missing boot configuration lock at {config_file}{RESET}")
            try:
                input(f"\n{WHITE}Press [ENTER] to return to boot prompt...{RESET}")
            except (KeyboardInterrupt, EOFError):
                pass
            continue
        
        file_mode = oct(os.stat(config_file).st_mode)[-3:]
        if file_mode != "400":
            try:
                os.chmod(config_file, 0o400)
                print(f"{YELLOW}[!] Fixed lock file permissions to 400.{RESET}")
            except Exception as e:
                print(f"{RED}[X] Could not fix permissions: {e}{RESET}")
                try:
                    input(f"\n{WHITE}Press [ENTER] to return to boot prompt...{RESET}")
                except (KeyboardInterrupt, EOFError):
                    pass
                continue
        print(f"{GREEN}[✔] Stage 2 passed.{RESET}\n")
        time.sleep(0.5)

        print(f"{YELLOW}[STAGE 3/3] Module Dependency Audit...{RESET}")
        missing_pkgs = [pkg for mod, pkg in REQUIRED_MODULES if importlib.util.find_spec(mod) is None]
        if missing_pkgs:
            print(f"{RED}[X] Bootstrap Failed: Missing package(s): {', '.join(missing_pkgs)}{RESET}")
            try:
                input(f"\n{WHITE}Press [ENTER] to return to boot prompt...{RESET}")
            except (KeyboardInterrupt, EOFError):
                pass
            continue
        print(f"{GREEN}[✔] Stage 3 passed.{RESET}\n")

        print(f"{GREEN}[+] All manual bootstrap conditions met. Launching Voidx...{RESET}\n")
        time.sleep(1.5)
        break


def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def flush_input():
    try:
        import termios

        termios.tcflush(sys.stdin, termios.TCIN)
    except Exception:
        try:
            import msvcrt

            while msvcrt.kbhit():
                msvcrt.getwch()
        except Exception:
            pass


def print_banner():
    banner = """
                           ED.
                t#,        #Wi
               ;##W.   t   E###G.
              :#L:WE   Ej  E#fD#W;
  t      .DD..KG  ,#D  E#, E#t t##L     :KW,      L
  EK:   ,WK. EE    ;#f E#t E#t  .E#K,    ,#W:   ,KG
  E#t  i#D  f#.     t#iE#t E#t    j#f    ;#W. jWi
  E#t j#f   :#G     GK E#t E#t    :EK:    i#KED.
  E#tL#i     ;#L   LW. E#t E#t   t##L       L#W.
  E#WW,       t#f f#:  E#t E#t .D#W;      .GKj#K.
  E#K:         f#D#;   E#t E#tiW#G.      iWf  i#K.
  ED.           G#t    E#t E#K##i       LK:    t#E
  t              #     E#t E##D.        i       tDj
                        Ej E#t
                           #
"""
    print(f"{RED}{banner}{RESET}")
    print(f"{RED}made by Phoenix:){RESET}")
    print()


def separator(char="=", width=60):
    print(f"\n{WHITE}{char * width}{RESET}")
def get_proxy_settings():
    print(f"\n{CYAN}Connection Options{RESET}")
    print(f"{RED}[+]{RESET} 1. Direct connection  {YELLOW}(recommended for search){RESET}")
    print(f"{RED}[+]{RESET} 2. Proxy")
    print(f"{RED}[+]{RESET} 3. Proxy Chain (single proxy endpoint)")
    print(f"{YELLOW}[!] Datacenter/VPN IPs get rate-limited by search engines.{RESET}")
    flush_input()
    try:
        choice = input(f"{WHITE}Select (1/2/3): {RESET}").strip()
    except (KeyboardInterrupt, EOFError):
        choice = "1"
    proxies = None

    if choice in ("2", "3"):
        try:
            proxy_url = input(
                f"{CYAN}Proxy endpoint (e.g. http://127.0.0.1:8080): {RESET}"
            ).strip()
            if proxy_url:
                proxies = {"http": proxy_url, "https": proxy_url}
        except (KeyboardInterrupt, EOFError):
            pass

    return proxies


def _pace():
    global _last_hit
    wait = _MIN_INTERVAL - (time.time() - _last_hit)
    if wait > 0:
        time.sleep(wait + random.uniform(0, 0.8))
    _last_hit = time.time()


def _fetch(session, method, url, proxies=None, **kw):
    """Request with 202/anomaly detection, cookie reset and jittered backoff."""
    headers = kw.pop("headers", HEADERS)
    last = None
    for attempt in range(3):
        _pace()
        try:
            response = session.request(
                method,
                url,
                headers=headers,
                proxies=proxies,
                timeout=20,
                allow_redirects=True,
                **kw
            )
        except Exception as e:
            last = e
            time.sleep((2 ** attempt) + random.uniform(0, 1.2))
            continue

        body = response.text[:4000].lower()
        if response.status_code == 202 or any(m in body for m in BLOCK_MARKERS):
            last = RuntimeError("202/anomaly page")
        elif response.status_code in (403, 429):
            last = RuntimeError(f"HTTP {response.status_code}")
        elif response.status_code >= 400:
            last = RuntimeError(f"HTTP {response.status_code}")
        else:
            return response

        session.cookies.clear()
        time.sleep((2 ** attempt) + random.uniform(0, 1.2))
    raise last if last else RuntimeError("request failed")


def _unwrap(href):
    if not href:
        return ""
    if href.startswith("//"):
        href = "https:" + href
    qs = urllib.parse.parse_qs(urllib.parse.urlparse(href).query)
    if "uddg" in qs:
        return urllib.parse.unquote(qs["uddg"][0])
    if "RU" in qs:
        return urllib.parse.unquote(qs["RU"][0])
    return href


def _ddg_html(session, query, proxies):
    from bs4 import BeautifulSoup

    response = _fetch(
        session,
        "POST",
        "https://html.duckduckgo.com/html/",
        proxies=proxies,
        data={"q": query, "kl": "us-en"},
        headers={**HEADERS, "Referer": "https://html.duckduckgo.com/"},
    )
    soup = BeautifulSoup(response.text, "html.parser")
    return [
        (a.get_text(" ", strip=True), _unwrap(a.get("href")))
        for a in soup.select(".result__a")
    ]


def _ddg_lite(session, query, proxies):
    from bs4 import BeautifulSoup

    response = _fetch(
        session,
        "GET",
        "https://lite.duckduckgo.com/lite/",
        proxies=proxies,
        params={"q": query},
    )
    soup = BeautifulSoup(response.text, "html.parser")
    out = []
    for a in soup.select("a.result-link"):
        href = _unwrap(a.get("href"))
        if href.startswith("http"):
            out.append((a.get_text(" ", strip=True), href))
    return out


def _mojeek(session, query, proxies):
    from bs4 import BeautifulSoup

    response = _fetch(
        session,
        "GET",
        "https://www.mojeek.com/search",
        proxies=proxies,
        params={"q": query},
    )
    soup = BeautifulSoup(response.text, "html.parser")
    return [
        (a.get_text(" ", strip=True), _unwrap(a.get("href")))
        for a in soup.select("ul.results-standard a.title")
    ]


def _yahoo(session, query, proxies):
    from bs4 import BeautifulSoup

    response = _fetch(
        session,
        "GET",
        "https://search.yahoo.com/search",
        proxies=proxies,
        params={"p": query},
    )
    soup = BeautifulSoup(response.text, "html.parser")
    return [
        (h.get_text(" ", strip=True), _unwrap(a.get("href")))
        for h in soup.select("div.algo h3")
        for a in h.select("a")
    ]


ENGINES = [
    ("duckduckgo", _ddg_html),
    ("duckduckgo-lite", _ddg_lite),
    ("mojeek", _mojeek),
    ("yahoo", _yahoo),
]


def search_engine(query, proxies=None):
    import requests

    session = requests.Session()
    try:
        session.get(
            "https://duckduckgo.com/", headers=HEADERS, proxies=proxies, timeout=15
        )
    except Exception:
        pass

    for name, engine in ENGINES:
        try:
            raw = engine(session, query, proxies)
        except Exception as e:
            print(f"{YELLOW}[~] {name} unavailable ({e}) — trying next.{RESET}")
            continue

        results = []
        seen_urls = set()
        for title, result_url in raw:
            if not result_url.startswith(("http://", "https://")):
                continue
            if "duckduckgo.com/y.js" in result_url or result_url in seen_urls:
                continue
            seen_urls.add(result_url)
            results.append({"title": title, "url": result_url})
            if len(results) >= 10:
                break

        if results:
            print(f"{GREEN}[+] Engine: {name}{RESET}")
            return results

    return []


def shodan_search(query):
    search_url = "https://www.shodan.io/search?" + urllib.parse.urlencode(
        {"query": query}
    )
    return [{"title": f"Shodan search: {query}", "url": search_url}]


def do_search(proxies):
    while True:
        separator()
        try:
            query = input(
                f"{CYAN}Search / dork query (or 'back'): {RESET}"
            ).strip()
        except (KeyboardInterrupt, EOFError):
            return
        if not query or query.lower() == "back":
            return

        print(f"\n{YELLOW}[*] Query: {query}{RESET}\n")
        results = search_engine(query, proxies)
        if not results:
            print(
                f"{RED}[!] All engines blocked. "
                f"Try a direct connection instead of a proxy.{RESET}"
            )
            continue

        print(f"{GREEN}[+] Showing {len(results)} URL(s), maximum 10:{RESET}\n")
        for i, result in enumerate(results, 1):
            print(f"{GREEN}Result [{i}]:{RESET} {result['title']}")
            print(f"{CYAN}URL:{RESET} {result['url']}")
            print("-" * 50)
def do_shodan_search():
    while True:
        separator()
        try:
            query = input(
                f"{CYAN}Shodan query (or 'back'): {RESET}"
            ).strip()
        except (KeyboardInterrupt, EOFError):
            return
        if not query or query.lower() == "back":
            return

        results = shodan_search(query)
        print(f"\n{GREEN}[+] Shodan search link:{RESET}\n")
        for i, result in enumerate(results, 1):
            print(f"{GREEN}Result [{i}]:{RESET} {result['title']}")
            print(f"{CYAN}Details Link:{RESET} {result['url']}")
            print("-" * 50)


def hibp_password_check(proxies):
    import requests

    separator()
    try:
        password = input(f"{CYAN}Password to check: {RESET}")
    except (KeyboardInterrupt, EOFError):
        return
    if not password:
        return

    sha1 = hashlib.sha1(password.encode()).hexdigest().upper()
    prefix, suffix = sha1[:5], sha1[5:]

    try:
        response = requests.get(
            f"https://api.pwnedpasswords.com/range/{prefix}",
            headers={**HEADERS, "Add-Padding": "true"},
            proxies=proxies,
            timeout=15,
        )
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"{RED}[!] HIBP request failed: {e}{RESET}")
        return

    count = 0
    for line in response.text.splitlines():
        parts = line.split(":")
        if len(parts) == 2 and parts[0].strip() == suffix:
            try:
                count = int(parts[1].strip())
            except ValueError:
                pass
            break

    if count:
        print(f"{RED}[!] PWNED — appeared {count:,} times.{RESET}")
    else:
        print(f"{GREEN}[+] Not found in HIBP corpus.{RESET}")


def breach_portals():
    portals = [
        ("Have I Been Pwned", "https://haveibeenpwned.com/"),
        ("HIBP Pwned Passwords", "https://haveibeenpwned.com/Passwords"),
        ("XposedOrNot", "https://xposedornot.com/"),
        ("DataBreach.com", "https://databreach.com/"),
        ("Cybernews Leak Checker", "https://cybernews.com/personal-data-leak-check/"),
        ("Firefox Monitor", "https://monitor.firefox.com/"),
        ("LeakCheck", "https://leakcheck.io/"),
        ("BreachDirectory", "https://breachdirectory.org/"),
        ("Hudson Rock", "https://www.hudsonrock.com/"),
        ("DeHashed", "https://dehashed.com/"),
        ("OSINT Catalog", "https://osintframework.com"),
    ]

    separator()
    print(f"{YELLOW}[*] Breach-check portals:{RESET}\n")
    for name, url in portals:
        print(f" {GREEN}{name:<30}{RESET} {CYAN}{url}{RESET}")

    try:
        open_all = input(
            f"\n{WHITE}Open all in browser? (y/N): {RESET}"
        ).strip().lower()
    except (KeyboardInterrupt, EOFError):
        open_all = "n"

    if open_all == "y":
        import webbrowser

        for _, url in portals:
            webbrowser.open(url)


def full_email_sweep(proxies):
    import requests

    separator()
    try:
        email = input(f"{CYAN}Email to check: {RESET}").strip()
    except (KeyboardInterrupt, EOFError):
        return
    if not email or "@" not in email:
        print(f"{RED}[!] Enter a valid email.{RESET}")
        return

    try:
        response = requests.get(
            "https://api.xposedornot.com/v1/check-email/"
            f"{urllib.parse.quote(email, safe='')}",
            headers=HEADERS,
            proxies=proxies,
            timeout=15,
        )
        response.raise_for_status()
        data = response.json()
        breaches = data.get("breaches", [])

        if breaches and breaches[0]:
            print(f"{RED}[!] EXPOSED — {len(breaches[0])} breach(es):{RESET}")
            for breach in breaches[0]:
                print(f" {WHITE}• {breach}{RESET}")
        else:
            print(f"{GREEN}[+] Clean in XposedOrNot corpus.{RESET}")
    except requests.RequestException as e:
        print(f"{RED}[!] XposedOrNot request failed: {e}{RESET}")
    except (ValueError, TypeError) as e:
        print(f"{RED}[!] Unexpected XposedOrNot response: {e}{RESET}")

    print(f"\n{WHITE}Manual portals:{RESET}")
    print(" https://haveibeenpwned.com/")
    print(" https://databreach.com/")
    print(" https://cybernews.com/personal-data-leak-check/")


def whois_lookup():
    import whois

    separator()
    try:
        raw = input(f"{CYAN}Enter domain (e.g. example.com): {RESET}").strip()
    except (KeyboardInterrupt, EOFError):
        return
    if not raw:
        return

    parsed = urllib.parse.urlparse(raw if "://" in raw else "https://" + raw)
    domain = (parsed.hostname or "").lower().rstrip(".")

    if (
        not domain
        or "." not in domain
        or len(domain) > 253
        or any(
            not label
            or len(label) > 63
            or label.startswith("-")
            or label.endswith("-")
            or not re.fullmatch(r"[a-z0-9-]+", label)
            for label in domain.split(".")
        )
    ):
        print(f"{RED}[!] Enter a valid domain name.{RESET}")
        return

    try:
        print(f"\n{YELLOW}[*] Looking up {domain}...{RESET}\n")
        data = whois.whois(domain)
        fields = [
            ("Domain", "domain_name"),
            ("Registrar", "registrar"),
            ("Creation date", "creation_date"),
            ("Updated date", "updated_date"),
            ("Expiration date", "expiration_date"),
            ("Name servers", "name_servers"),
            ("Status", "status"),
            ("Registrant organization", "org"),
            ("Country", "country"),
            ("Registrant email", "emails"),
        ]

        found = False
        for label, key in fields:
            value = data.get(key) if hasattr(data, "get") else None
            if value:
                if isinstance(value, (list, tuple, set)):
                    value = ", ".join(dict.fromkeys(str(v) for v in value))
                print(f"{GREEN}{label}:{RESET} {value}")
                found = True

        if not found:
            print(f"{YELLOW}[!] No WHOIS fields returned.{RESET}")
        print(f"\n{WHITE}Some registration details may be redacted.{RESET}")
    except Exception as e:
        print(f"{RED}[!] WHOIS lookup failed: {e}{RESET}")


def ip_info_lookup(proxies):
    import requests

    separator()
    try:
        raw_ip = input(f"{CYAN}Enter an IP address: {RESET}").strip()
    except (KeyboardInterrupt, EOFError):
        return

    try:
        ip_obj = ipaddress.ip_address(raw_ip)
    except ValueError:
        print(f"{RED}[!] Invalid IPv4 or IPv6 address.{RESET}")
        return

    if not ip_obj.is_global:
        print(f"{YELLOW}[!] This is not a public global IP address.{RESET}")
        return

    try:
        response = requests.get(
            f"https://ipwho.is/{ip_obj}",
            headers=HEADERS,
            proxies=proxies,
            timeout=15,
        )
        response.raise_for_status()
        data = response.json()

        if not data.get("success", False):
            print(
                f"{RED}[!] Lookup failed: "
                f"{data.get('message', 'Unknown API error')}{RESET}"
            )
            return

        connection = data.get("connection") or {}
        timezone = data.get("timezone") or {}
        fields = [
            ("IP Address", data.get("ip")),
            ("Type", data.get("type")),
            ("Country", data.get("country")),
            ("Country Code", data.get("country_code")),
            ("Region", data.get("region")),
            ("City", data.get("city")),
            ("Postal Code", data.get("postal")),
            ("ISP", connection.get("isp")),
            ("Organization", connection.get("org")),
            ("ASN", connection.get("asn")),
            ("Timezone", timezone.get("id")),
            ("Latitude", data.get("latitude")),
            ("Longitude", data.get("longitude")),
            (
                "Map",
                f"https://www.google.com/maps?q="
                f"{data.get('latitude')},{data.get('longitude')}",
            ),
        ]

        print(f"\n{GREEN}=== IP Information ==={RESET}\n")
        for label, value in fields:
            if value not in (None, "", []):
                print(f"{CYAN}{label}:{RESET} {value}")

        print(f"\n{YELLOW}Note: IP geolocation is approximate.{RESET}")
    except requests.RequestException as e:
        print(f"{RED}[!] IP lookup request failed: {e}{RESET}")
    except (ValueError, TypeError) as e:
        print(f"{RED}[!] Unexpected IP lookup response: {e}{RESET}")
def reverse_dns_lookup():
    separator()
    try:
        raw_ip = input(f"{CYAN}Enter IP for reverse DNS: {RESET}").strip()
    except (KeyboardInterrupt, EOFError):
        return

    try:
        ip_obj = ipaddress.ip_address(raw_ip)
    except ValueError:
        print(f"{RED}[!] Invalid IPv4 or IPv6 address.{RESET}")
        return

    try:
        hostname, aliases, ips = socket.gethostbyaddr(str(ip_obj))
        print(f"\n{GREEN}=== Reverse DNS ==={RESET}\n")
        print(f"{CYAN}IP:{RESET} {ip_obj}")
        print(f"{CYAN}Hostname:{RESET} {hostname}")

        if aliases:
            print(f"{CYAN}Aliases:{RESET} {', '.join(aliases)}")
        if ips:
            print(f"{CYAN}Resolved IPs:{RESET} {', '.join(ips)}")
    except socket.herror:
        print(f"{YELLOW}[!] No PTR record found.{RESET}")
    except OSError as e:
        print(f"{RED}[!] Reverse DNS error: {e}{RESET}")


RECON_MARKERS = (
    "page not found", "user not found", "profile not found", "no such user",
    "doesn't exist", "does not exist", "couldn't find", "could not find",
    "nobody on reddit goes by that name", "this account doesn't exist",
    "sorry, this page isn't available", "not found", "404",
)

RECON_SITES = [
    # --- Social ---
    ("X / Twitter", "https://x.com/{id}", "Social"),
    ("Facebook", "https://www.facebook.com/{id}", "Social"),
    ("Instagram", "https://www.instagram.com/{id}/", "Social"),
    ("Threads", "https://www.threads.net/@{id}", "Social"),
    ("TikTok", "https://www.tiktok.com/@{id}", "Social"),
    ("Snapchat", "https://www.snapchat.com/add/{id}", "Social"),
    ("Pinterest", "https://www.pinterest.com/{id}/", "Social"),
    ("Tumblr", "https://{id}.tumblr.com", "Social"),
    ("Mastodon", "https://mastodon.social/@{id}", "Social"),
    ("Bluesky", "https://bsky.app/profile/{id}.bsky.social", "Social"),
    ("VK", "https://vk.com/{id}", "Social"),
    ("OK.ru", "https://ok.ru/{id}", "Social"),
    ("Gab", "https://gab.com/{id}", "Social"),
    ("Parler", "https://parler.com/{id}", "Social"),
    ("Rumble", "https://rumble.com/user/{id}", "Social"),
    ("Vero", "https://vero.co/{id}", "Social"),
    ("Clubhouse", "https://www.clubhouse.com/@{id}", "Social"),
    ("Meetup", "https://www.meetup.com/{id}", "Social"),
    ("Flickr", "https://www.flickr.com/people/{id}", "Social"),
    ("VSCO", "https://vsco.co/{id}", "Social"),
    ("Behance", "https://www.behance.net/{id}", "Social"),
    ("Dribbble", "https://dribbble.com/{id}", "Social"),
    ("DeviantArt", "https://www.deviantart.com/{id}", "Social"),
    ("ArtStation", "https://www.artstation.com/{id}", "Social"),
    ("Cara", "https://cara.app/{id}", "Social"),
    ("MeWe", "https://mewe.com/i/{id}", "Social"),
    ("Post.news", "https://post.news/@{id}", "Social"),
    ("Cohost", "https://cohost.org/{id}", "Social"),
    ("LiveJournal", "https://{id}.livejournal.com", "Social"),
    ("Lemmy", "https://lemmy.world/u/{id}", "Social"),
    ("Matrix", "https://matrix.to/#/@{id}:matrix.org", "Social"),
    ("Lens", "https://lenster.xyz/u/{id}", "Social"),
    ("Quora", "https://www.quora.com/profile/{id}", "Social"),
    # --- Dev / Tech ---
    ("GitHub", "https://github.com/{id}", "Dev"),
    ("GitLab", "https://gitlab.com/{id}", "Dev"),
    ("Bitbucket", "https://bitbucket.org/{id}", "Dev"),
    ("Codeberg", "https://codeberg.org/{id}", "Dev"),
    ("SourceForge", "https://sourceforge.net/u/{id}", "Dev"),
    ("CodePen", "https://codepen.io/{id}", "Dev"),
    ("JSFiddle", "https://jsfiddle.net/user/{id}", "Dev"),
    ("Replit", "https://replit.com/@{id}", "Dev"),
    ("Glitch", "https://glitch.com/@{id}", "Dev"),
    ("Hacker News", "https://news.ycombinator.com/user?id={id}", "Dev"),
    ("Lobsters", "https://lobste.rs/~{id}", "Dev"),
    ("Dev.to", "https://dev.to/{id}", "Dev"),
    ("Hashnode", "https://hashnode.com/@{id}", "Dev"),
    ("Medium", "https://medium.com/@{id}", "Dev"),
    ("Substack", "https://{id}.substack.com", "Dev"),
    ("npm", "https://www.npmjs.com/~{id}", "Dev"),
    ("Docker Hub", "https://hub.docker.com/u/{id}", "Dev"),
    ("Hugging Face", "https://huggingface.co/{id}", "Dev"),
    ("LeetCode", "https://leetcode.com/{id}", "Dev"),
    ("Codeforces", "https://codeforces.com/profile/{id}", "Dev"),
]


def _recon_probe(session, name, template, category, handle, proxies):
    import requests

    url = template.format(id=urllib.parse.quote(handle, safe=""))
    try:
        response = session.get(
            url, headers=HEADERS, proxies=proxies, timeout=10, allow_redirects=True
        )

        if response.status_code == 404:
            status = "blocked"
        elif response.status_code == 200:
            body_lower = response.text.lower()
            if any(marker in body_lower for marker in RECON_MARKERS):
                status = "blocked"
            else:
                status = "found"
        elif response.status_code in (403, 429):
            status = "blocked"
        else:
            status = "maybe"

        return (name, url, category, status)
    except requests.RequestException:
        return (name, url, category, "blocked")


def _recon_names(session, handle, kind, proxies):
    import requests

    names = {}

    def add(source, value):
        value = (value or "").strip()
        if value and len(value) < 120:
            names.setdefault(source, value)

    if kind == "email":
        digest = hashlib.md5(handle.lower().encode()).hexdigest()
        try:
            response = session.get(
                f"https://gravatar.com/{digest}.json",
                headers=HEADERS,
                proxies=proxies,
                timeout=10,
            )
            if response.status_code == 200:
                entry = (response.json().get("entry") or [{}])[0]
                add("Gravatar display name", entry.get("displayName"))
                full = entry.get("name") or {}
                add(
                    "Gravatar full name",
                    " ".join(
                        part
                        for part in (full.get("givenName"), full.get("familyName"))
                        if part
                    ),
                )
                add("Gravatar profile", entry.get("profileUrl"))
        except (requests.RequestException, ValueError):
            pass

        local = handle.split("@")[0]
        parts = re.split(r"[._\-+]+", local)
        if len(parts) >= 2 and all(p.isalpha() and len(p) > 1 for p in parts[:2]):
            add("Email pattern guess", " ".join(p.capitalize() for p in parts[:2]))

    lookups = [
        ("GitHub", f"https://api.github.com/users/{urllib.parse.quote(handle)}"),
        ("Keybase", f"https://keybase.io/_/api/1.0/user/lookup.json?usernames={urllib.parse.quote(handle)}"),
        ("Dev.to", f"https://dev.to/api/users/by_username?url={urllib.parse.quote(handle)}"),
        ("GitLab", f"https://gitlab.com/api/v4/users?username={urllib.parse.quote(handle)}"),
        ("Hacker News", f"https://hn.algolia.com/api/v1/users/{urllib.parse.quote(handle)}"),
    ]

    for source, url in lookups:
        if kind == "phone" and source in ("GitLab", "Dev.to", "Hacker News"):
            continue
        try:
            response = session.get(
                url, headers=HEADERS, proxies=proxies, timeout=10
            )
            if response.status_code != 200:
                continue
            data = response.json()

            if source == "GitHub":
                add("GitHub name", data.get("name"))
                add("GitHub bio", data.get("bio"))
                add("GitHub location", data.get("location"))
                add("GitHub blog", data.get("blog"))
                add("GitHub company", data.get("company"))
            elif source == "Keybase":
                them = (data.get("them") or [{}])[0]
                profile = them.get("profile") or {}
                add("Keybase full name", profile.get("full_name"))
                add("Keybase location", profile.get("location"))
            elif source == "Dev.to":
                add("Dev.to name", data.get("name"))
            elif source == "GitLab":
                if data:
                    add("GitLab name", data[0].get("name"))
                    add("GitLab bio", data[0].get("bio"))
            elif source == "Hacker News":
                add("Hacker News about", data.get("about"))
        except (requests.RequestException, ValueError, IndexError, TypeError):
            continue

    return names


def personal_recon(proxies):
    import concurrent.futures
    import requests

    separator()
    print(f"{YELLOW}[*] Personal Recon — phone / email / username{RESET}")
    print(
        f"{WHITE}Checks {len(RECON_SITES)} platforms, tries to derive a full name, "
        f"and builds manual links.{RESET}\n"
    )
    try:
        target = input(f"{CYAN}Phone, email or username (or 'back'): {RESET}").strip()
    except (KeyboardInterrupt, EOFError):
        return
    if not target or target.lower() == "back":
        return

    if "@" in target and "." in target.split("@")[-1]:
        kind = "email"
    elif re.fullmatch(r"\+?[0-9][0-9 \-().]{5,}", target):
        kind = "phone"
    else:
        kind = "username"

    handle = target.lstrip("@").strip()

    if kind == "email" and "@" not in handle:
        print(f"{RED}[!] Enter a valid email.{RESET}")
        return
    if kind == "phone":
        digits = re.sub(r"[^0-9]", "", handle)
        if len(digits) < 7:
            print(f"{RED}[!] Enter a valid phone number.{RESET}")
            return
        handle = "+" + digits

    print(f"\n{YELLOW}[*] Type: {kind.upper()} — target: {handle}{RESET}\n")

    session = requests.Session()
    lookup_handle = handle.split("@")[0] if kind == "email" else handle

    print(f"{WHITE}[*] Deriving name candidates...{RESET}")
    names = _recon_names(session, handle, kind, proxies)
    if names:
        for source, value in names.items():
            print(f" {GREEN}{source}:{RESET} {value}")
    else:
        print(f" {YELLOW}No name data returned by APIs.{RESET}")

    print(f"\n{WHITE}[*] Scanning {len(RECON_SITES)} platforms...{RESET}\n")
    hits = {"found": [], "maybe": [], "blocked": []}

    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as pool:
        futures = [
            pool.submit(_recon_probe, session, name, template, category, lookup_handle, proxies)
            for name, template, category in RECON_SITES
        ]
        for future in concurrent.futures.as_completed(futures):
            name, url, category, status = future.result()
            if status in hits:
                hits[status].append((name, url, category))

    def dump(bucket, label, colour):
        if not bucket:
            return
        print(f"\n{colour}[{label}] {len(bucket)} hit(s):{RESET}")
        for name, url, category in sorted(bucket, key=lambda x: (x[2], x[0])):
            print(f" {colour}{category:<13}{RESET} {name:<20} {CYAN}{url}{RESET}")

    dump(hits["found"], "+", GREEN)
    dump(hits["maybe"], "?", YELLOW)
    dump(hits["blocked"], "!", RED)

    if not any(hits.values()):
        print(f"{RED}[!] No profile hits.{RESET}")

    print(
        f"\n{WHITE}[*] Summary: {len(hits['found'])} confirmed, "
        f"{len(hits['maybe'])} uncertain, {len(hits['blocked'])} blocked, "
        f"{len(RECON_SITES)} scanned.{RESET}"
    )

    quoted = urllib.parse.quote_plus(handle)

    separator()
    print(f"{YELLOW}[*] Manual dorks and deep links:{RESET}\n")
    dorks = [
        ("Google — name + handle", f"https://www.google.com/search?q=%22{quoted}%22+name"),
        ("Bing — handle", f"https://www.bing.com/search?q=%22{quoted}%22"),
        ("Yandex — handle", f"https://yandex.com/search/?text=%22{quoted}%22"),
        ("LinkedIn people", f"https://www.linkedin.com/search/results/people/?keywords={quoted}"),
        ("Google — LinkedIn", f"https://www.google.com/search?q=%22{quoted}%22+site%3Alinkedin.com%2Fin"),
        ("Google — PDFs / docs", f"https://www.google.com/search?q=%22{quoted}%22+filetype%3Apdf"),
        ("Google — paste sites", f"https://www.google.com/search?q=%22{quoted}%22+site%3Apastebin.com"),
        ("Have I Been Pwned", "https://haveibeenpwned.com/"),
        ("DeHashed", "https://dehashed.com/"),
        ("Intelligence X", f"https://intelx.io/?s={quoted}"),
        ("Epieos", "https://epieos.com/"),
        ("WhatsMyName", f"https://whatsmyname.app/?q={quoted}"),
        ("Sherlock (web)", f"https://sherlock-project.github.io/?q={quoted}"),
    ]
    if kind == "phone":
        dorks.extend([
            ("Truecaller", f"https://www.truecaller.com/search/global/{quoted}"),
            ("Sync.me", f"https://sync.me/search/?number={quoted}"),
            ("WhatsApp", f"https://wa.me/{quoted}"),
            ("Google — number", f"https://www.google.com/search?q=%22{quoted}%22"),
            ("Numlookup", "https://www.numlookup.com/"),
        ])
    if kind == "email":
        dorks.extend([
            ("Google — email", f"https://www.google.com/search?q=%22{quoted}%22"),
            ("Gravatar", f"https://gravatar.com/{hashlib.md5(handle.lower().encode()).hexdigest()}"),
            ("Firefox Monitor", "https://monitor.firefox.com/"),
        ])

    for label, url in dorks:
        print(f" {GREEN}{label:<24}{RESET} {CYAN}{url}{RESET}")

    try:
        open_all = input(
            f"\n{WHITE}Open manual links in browser? (y/N): {RESET}"
        ).strip().lower()
    except (KeyboardInterrupt, EOFError):
        open_all = "n"

    if open_all == "y":
        import webbrowser

        for _, url in dorks:
            webbrowser.open(url)


def main():
    bootstrapper()
    clear_screen()
    print_banner()
    proxies = get_proxy_settings()

    actions = {
        "1": lambda: do_search(proxies),
        "2": lambda: do_shodan_search(),
        "3": lambda: hibp_password_check(proxies),
        "4": lambda: full_email_sweep(proxies),
        "5": lambda: breach_portals(),
        "6": lambda: whois_lookup(),
        "7": lambda: ip_info_lookup(proxies),
        "8": lambda: reverse_dns_lookup(),
        "9": lambda: personal_recon(proxies),
    }

    while True:
        separator()
        print(f"{WHITE} 1. Search / Dorking{RESET}")
        print(f"{WHITE} 2. Shodan Intelligence Search (link only){RESET}")
        print(f"{WHITE} 3. Check password against HIBP corpus{RESET}")
        print(f"{WHITE} 4. Email check plus manual breach portals{RESET}")
        print(f"{WHITE} 5. List breach-check portals{RESET}")
        print(f"{WHITE} 6. WHOIS Domain Lookup{RESET}")
        print(f"{WHITE} 7. IP Information Lookup{RESET}")
        print(f"{WHITE} 8. Reverse DNS Lookup{RESET}")
        print(f"{WHITE} 9. Personal Reconiscense (phone / email / username){RESET}")
        print(f"{WHITE} 0. Exit{RESET}")

        try:
            flush_input()
            choice = input(f"\n{CYAN}Select> {RESET}").strip()
        except (KeyboardInterrupt, EOFError):
            break

        if choice == "0":
            print(f"\n{GREEN}[+] Exiting voidx.{RESET}\n")
            break
        elif choice in actions:
            actions[choice]()
        else:
            print(f"{RED}[!] Invalid option.{RESET}")


if __name__ == "__main__":
    main()
