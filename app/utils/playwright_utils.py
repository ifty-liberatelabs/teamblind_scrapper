import json
import os
import time
from typing import Dict, Optional
from playwright.async_api import async_playwright
from curl_cffi import requests
from app.core.config import settings, logger

LOGIN_URL = "https://www.teamblind.com/sign-in"
STATE_FILE = "auth_state.json"

_cookies: Optional[Dict[str, str]] = None

def is_cookie_valid(cookies_data: list) -> bool:
    for cookie in cookies_data:
        if cookie["name"] == "bl_session_v2":
            expires = cookie.get("expires", -1)
            if expires == -1:
                logger.info("bl_session_v2 is a session-only cookie. Forcing re-login.")
                return False
            if expires > time.time():
                return True
            else:
                logger.warning("bl_session_v2 expired.")
                return False
    logger.warning("bl_session_v2 not found in cookies.")
    return False

async def fetch_cookies() -> Dict[str, str]:
    global _cookies
    if _cookies is not None:
        logger.info("Reusing in-memory cookies.")
        return _cookies

    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f:
                state = json.load(f)
            cookies_data = state.get("cookies", [])
            if is_cookie_valid(cookies_data):
                _cookies = {c["name"]: c["value"] for c in cookies_data}
                logger.info("Reusing valid cookies from auth_state.json.")
                return _cookies
            else:
                logger.warning("Stored cookies are expired or invalid. Will log in again.")
        except Exception as e:
            logger.warning(f"Failed to read or parse auth_state.json: {e}")

    logger.info("Logging in to fetch new cookies.")

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
        context = await browser.new_context(
            user_agent=settings.User_Agent,
            locale="en-US",
            viewport={"width": 1280, "height": 800},
            timezone_id="Asia/Dhaka",
            extra_http_headers={
                "sec-ch-ua": '"Chromium";v="133", " Not A;Brand";v="99"',
                "sec-ch-ua-platform": '"Linux"'
            }
        )

        # Combine all init scripts into one multiline string for clarity
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'languages', {get: () => ['en-US','en']});
            Object.defineProperty(navigator, 'plugins', {get: () => [1,2,3]});
            Object.defineProperty(navigator, 'mimeTypes', {get: () => [1,2,3]});
        """)

        page = await context.new_page()
        await page.goto(LOGIN_URL, wait_until="domcontentloaded")
        await page.fill("input[name=email]", settings.TEAMBLIND_USER_EMAIL)
        await page.fill("input[name=password]", settings.TEAMBLIND_USER_PASS)
        await page.locator("button[type=submit]").click()
        await page.wait_for_url("https://www.teamblind.com/", timeout=60_000)

        await context.storage_state(path=STATE_FILE)

        cookies = await context.cookies()
        _cookies = {c["name"]: c["value"] for c in cookies}
        logger.info("Fetched and stored new cookies.")

        await context.close()
        await browser.close()

        return _cookies

# ---- UNIVERSAL FAILSAFE REQUEST WRAPPER ----

async def robust_request(url: str, method="get", max_retries=10, **kwargs):
    global _cookies
    attempt = 0
    while attempt <= max_retries:
        cookies = await fetch_cookies()
        try:
            req_method = getattr(requests, method.lower())
            resp = req_method(url, cookies=cookies, timeout=20, **kwargs)
            if resp.status_code in (401, 403):
                logger.warning(f"Auth failed (status {resp.status_code}). Relogin and retrying...")
                _cookies = None
                attempt += 1
                continue
            return resp
        except Exception as ex:
            logger.error(f"Request error: {ex}. Relogin and retrying...")
            _cookies = None
            attempt += 1
    raise Exception(f"Failed to fetch {url} after {max_retries+1} attempts.")
