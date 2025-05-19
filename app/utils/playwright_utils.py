import json
import os
import time
from typing import Dict, Optional
from playwright.async_api import async_playwright
from curl_cffi import requests
import asyncio

from app.core.config import settings, logger

LOGIN_URL = "https://www.teamblind.com/sign-in"
STATE_FILE = "auth_state.json"

_cookies: Optional[Dict[str, str]] = None

def is_cookie_valid(cookies_data: list) -> bool:
    for cookie in cookies_data:
        if cookie["name"] == "bl_session_v2":
            expires = cookie.get("expires", -1)
            if expires == -1: # Session-only cookie
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
            timezone_id="Asia/Dhaka", # Example timezone
            extra_http_headers={
                "sec-ch-ua": settings.User_Agent.split("Chrome/")[1].split(" ")[0].startswith("1") and f'"Chromium";v="{settings.User_Agent.split("Chrome/")[1].split(".")[0]}", "Not A;Brand";v="99"' or '" Not A;Brand";v="99", "Chromium";v="100"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": '"Linux"' # Example, can be Windows, macOS etc.
            }
        )

        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'languages', {get: () => ['en-US','en']});
            Object.defineProperty(navigator, 'plugins', {get: () => [1,2,3]});
            Object.defineProperty(navigator, 'mimeTypes', {get: () => [1,2,3]});
            """)

        page = await context.new_page()
        logger.info(f"Navigating to login page: {LOGIN_URL}")
        await page.goto(LOGIN_URL, wait_until="domcontentloaded")

        logger.info("Filling login form.")
        await page.fill("input[name=email]", settings.TEAMBLIND_USER_EMAIL)
        await page.fill("input[name=password]", settings.TEAMBLIND_USER_PASS)
        
        submit_button_locator = page.locator("form").get_by_role("button", name="Sign in")
        
        count = await submit_button_locator.count()
        if count == 1:
            logger.info("Found unique 'Sign in' button. Clicking...")
            await submit_button_locator.click()
        elif count == 0:
            logger.error("Login 'Sign in' button not found with the current locator.")
            await browser.close() # Close browser before raising exception
            raise Exception("Login 'Sign in' button not found.")
        else:
            logger.error(f"Login 'Sign in' button locator is not unique. Matched {count} elements.")
            await browser.close() # Close browser before raising exception
            raise Exception(f"Login 'Sign in' button locator is not unique, matched {count} elements.")

        logger.info("Waiting for navigation after login submission...")
        try:
            await page.wait_for_url(
                lambda url: "teamblind.com" in url and "sign-in" not in url and "check-email" not in url, 
                timeout=30_000 # Reduced timeout slightly, adjust if needed
            )
            logger.info(f"Successfully navigated to: {page.url} after login attempt. Assuming login successful.")
        except Exception as e:
            logger.error(f"Timeout or error waiting for navigation after login: {e}. Current URL: {page.url}")
            # Consider taking a screenshot here for debugging if this happens
            # await page.screenshot(path="debug_login_nav_failure.png")
            await browser.close()
            raise Exception(f"Failed to confirm navigation after login attempt: {e}")


        # --- POST-LOGIN VERIFICATION REMOVED ---
        # logger.info("Post-login verification step skipped as per configuration.")
        # --- END OF REMOVAL ---

        logger.info("Saving browser state (including cookies).")
        await context.storage_state(path=STATE_FILE)

        cookies_list = await context.cookies()
        _cookies = {c["name"]: c["value"] for c in cookies_list}
        logger.info("Fetched and stored new cookies in memory.")

        await context.close()
        await browser.close()
        logger.info("Playwright browser closed.")

        return _cookies

# ---- UNIVERSAL FAILSAFE REQUEST WRAPPER ----
# (robust_request function remains the same as the previous full version)
async def robust_request(url: str, method="get", max_retries=10, **kwargs):
    global _cookies
    attempt = 0
    last_exception = None

    while attempt <= max_retries:
        current_cookies = _cookies 
        if current_cookies is None: 
            logger.info(f"No in-memory cookies for {url}, fetching new ones (Attempt {attempt + 1}).")
            try:
                current_cookies = await fetch_cookies()
            except Exception as e:
                logger.error(f"Failed to fetch cookies during robust_request: {e}")
                attempt += 1 
                last_exception = e
                if attempt > max_retries:
                    raise Exception(f"Failed to fetch cookies after {max_retries + 1} attempts. Last error: {last_exception}") from last_exception
                await asyncio.sleep(attempt * 2) 
                continue 

        try:
            logger.debug(f"Attempt {attempt + 1}/{max_retries + 1} to {method.upper()} {url}")
            async with requests.AsyncSession() as async_session: 
                if method.lower() == "get":
                    resp = await async_session.get(url, cookies=current_cookies, timeout=20, **kwargs)
                elif method.lower() == "post":
                    resp = await async_session.post(url, cookies=current_cookies, timeout=20, **kwargs)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")
            
            logger.debug(f"Response status for {url}: {resp.status_code}")

            if resp.status_code in (401, 403):
                logger.warning(f"Auth failed (status {resp.status_code}) for {url}. Invalidating cookies and retrying...")
                _cookies = None 
                attempt += 1
                last_exception = requests.RequestsError(f"HTTP {resp.status_code}") 
                await asyncio.sleep(1 + attempt) 
                continue
            
            resp.raise_for_status() 
            return resp
        
        except requests.RequestsError as ex: 
            logger.error(f"Request error for {url} (Attempt {attempt + 1}): {ex}. Status: {getattr(ex, 'response', None) and getattr(ex.response, 'status_code', 'N/A')}")
            last_exception = ex
            if hasattr(ex, 'response') and ex.response is not None and 400 <= ex.response.status_code < 500 and ex.response.status_code not in (401, 403, 429):
                logger.warning(f"Client error {ex.response.status_code} for {url}. Not clearing cookies, but failing fast.")
                raise 
            
            _cookies = None 
            attempt += 1
            if attempt > max_retries:
                logger.error(f"Failed to fetch {url} after {max_retries+1} attempts due to RequestsError.")
                raise last_exception from last_exception
            await asyncio.sleep(attempt * 2) 
            
        except Exception as ex:
            logger.error(f"Generic error during request for {url} (Attempt {attempt + 1}): {ex}")
            last_exception = ex
            _cookies = None 
            attempt += 1
            if attempt > max_retries:
                logger.error(f"Failed to fetch {url} after {max_retries+1} attempts due to generic error.")
                raise last_exception from last_exception
            await asyncio.sleep(attempt * 2) 

    raise Exception(f"Failed to fetch {url} after {max_retries+1} attempts. Last error: {last_exception}") from last_exception