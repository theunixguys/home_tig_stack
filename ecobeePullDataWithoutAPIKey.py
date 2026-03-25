#!/usr/bin/env python3
"""
ecobee_download.py — no API key needed
Uses Playwright to authenticate and harvest the Bearer token,
then downloads the report directly via requests.
"""

import subprocess
import requests
import json
import os
import re
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright

EMAIL = "INSERT_EMAIL"
PASSWORD = "INSERT_PASSWORD"
THERMOSTAT_ID = "1234567890"
OUTPUT_FILE = "/home/ecobee/hvac.csv"
TOKEN_CACHE = os.path.expanduser("~/.ecobee_token_cache.json")


def load_cached_token():
    if os.path.exists(TOKEN_CACHE):
        with open(TOKEN_CACHE) as f:
            data = json.load(f)
        # Check if token expires more than 5 minutes from now
        if data.get("expires_at", 0) > datetime.now().timestamp() + 300:
            return data["access_token"]
    return None


def save_token(token):
    # Decode exp from JWT payload (middle segment, base64)
    import base64
    payload = token.split(".")[1]
    # Pad base64 if needed
    payload += "=" * (4 - len(payload) % 4)
    claims = json.loads(base64.b64decode(payload))
    with open(TOKEN_CACHE, "w") as f:
        json.dump({"access_token": token, "expires_at": claims["exp"]}, f)
    os.chmod(TOKEN_CACHE, 0o600)
    print(f"Token cached, expires at {datetime.fromtimestamp(claims['exp'])}")


def get_token_via_playwright():
    captured = {}

    AUTH_URL = (
        "https://auth.ecobee.com/authorize"
        "?response_type=token"
        "&response_mode=form_post"
        "&client_id=988fORFPlXyz9BbDZwqexHPBQoVjaach"
        "&redirect_uri=https://www.ecobee.com/home/authCallback"
        "&audience=https://prod.ecobee.com/api/v1"
        "&scope=openid%20smartWrite%20piiWrite%20piiRead%20smartRead%20deleteGrants"
    )

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800},
            locale="en-US",
            timezone_id="America/New_York",
        )
        page = context.new_page()

        def handle_request(request):
            auth = request.headers.get("authorization", "")
            if auth.startswith("Bearer ") and "api.ecobee.com" in request.url:
                captured["token"] = auth.removeprefix("Bearer ")
                print(f"Token captured from: {request.url}")

        page.on("request", handle_request)

        # Go directly to Auth0 login — skips needing to click anything
        print("Navigating to Auth0 login...")
        page.goto(AUTH_URL)
        page.wait_for_load_state("networkidle", timeout=30000)
        print(f"URL: {page.url}")
        page.screenshot(path="/tmp/ecobee_auth0.png")

        # Dump inputs so we can see what Auth0 rendered
        inputs = page.query_selector_all("input")
        for i, inp in enumerate(inputs):
            print(f"  Input {i}: type={inp.get_attribute('type')} "
                  f"name={inp.get_attribute('name')} "
                  f"id={inp.get_attribute('id')} "
                  f"placeholder={inp.get_attribute('placeholder')}")

        # Fill email
        print("Filling email...")
        page.wait_for_selector("input[type='email'], input[name='username'], input[id='username']", timeout=15000)
        page.fill("input[type='email'], input[name='username'], input[id='username']", EMAIL)
        page.screenshot(path="/tmp/ecobee_email_filled.png")
        page.keyboard.press("Enter")
        page.wait_for_load_state("networkidle", timeout=15000)
        print(f"After email URL: {page.url}")
        page.screenshot(path="/tmp/ecobee_after_email.png")

        # Fill password
        print("Filling password...")
        page.wait_for_selector("input[type='password']", timeout=15000)
        page.fill("input[type='password']", PASSWORD)
        page.keyboard.press("Enter")

        # Wait for redirect back and API calls to fire
        print("Waiting for post-login redirect and API calls...")
        page.wait_for_load_state("networkidle", timeout=30000)
        print(f"Final URL: {page.url}")
        page.screenshot(path="/tmp/ecobee_post_login.png")

        if not captured.get("token"):
            print("Token not yet seen, waiting a bit longer...")
            page.wait_for_timeout(5000)

        browser.close()

    if not captured.get("token"):
        raise RuntimeError("Failed to capture Bearer token")

    return captured["token"]

def get_token():
    token = load_cached_token()
    if token:
        print("Using cached token")
        return token
    print("Token expired or missing, re-authenticating...")
    token = get_token_via_playwright()
    save_token(token)
    return token


def download_last_7_days(access_token):
    end_date = datetime.today()
    start_date = end_date - timedelta(days=2)

    body = {
        "selection": {
            "selectionType": "thermostats",
            "selectionMatch": THERMOSTAT_ID,
        },
        "startDate": start_date.strftime("%Y-%m-%d"),
        "endDate":   end_date.strftime("%Y-%m-%d"),
    }

    params = {
        "format": "json",
        "body": json.dumps(body, separators=(",", ":")),
        "_timestamp": int(datetime.now().timestamp() * 1000),
    }

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "text/csv",
        "Content-Type": "application/json;charset=UTF-8",
        "Origin": "https://www.ecobee.com",
        "Referer": "https://www.ecobee.com/",
    }

    resp = requests.get(
        "https://api.ecobee.com/1/runtimeReportDownload",
        params=params,
        headers=headers,
    )
    resp.raise_for_status()
    return resp.content


if __name__ == "__main__":
    token = get_token()
    print("Downloading runtime report...")
    data = download_last_7_days(token)

    with open(OUTPUT_FILE, "wb") as f:
        f.write(data)

    print(f"Saved {len(data):,} bytes to {OUTPUT_FILE}")

    # Run hvac.py
    print("Running hvac.py...")
    result = subprocess.run(
        ["python3", "/home/ecobee/hvac.py"],
        capture_output=True,
        text=True
    )
    print(result.stdout)
    if result.returncode != 0:
        print(f"hvac.py exited with error:\n{result.stderr}")
    else:
        print("hvac.py completed successfully")
