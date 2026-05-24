from __future__ import annotations

import os

import pytest


def _smoke_enabled() -> bool:
    return os.getenv("PLF_PLAYWRIGHT_SMOKE_ENABLED", "").strip().lower() in {"1", "true", "yes", "on"}


pytestmark = pytest.mark.skipif(
    not _smoke_enabled(),
    reason="Set PLF_PLAYWRIGHT_SMOKE_ENABLED=true and PLAYWRIGHT_BASE_URL to run local Playwright smoke tests.",
)


def test_streamlit_root_and_chat_pages_smoke():
    from playwright.sync_api import Error, sync_playwright

    base_url = os.getenv("PLAYWRIGHT_BASE_URL", "http://127.0.0.1:8501").rstrip("/")
    browser_name = os.getenv("PLAYWRIGHT_BROWSER", "chromium").strip() or "chromium"
    headless = os.getenv("PLAYWRIGHT_HEADLESS", "true").strip().lower() not in {"0", "false", "no", "off"}

    with sync_playwright() as playwright:
        browser_type = getattr(playwright, browser_name)
        try:
            browser = browser_type.launch(headless=headless)
        except Error as exc:
            pytest.skip(f"Playwright browser is not installed or cannot launch: {exc}")
        with browser:
            page = browser.new_page()
            page.goto(base_url, wait_until="networkidle")
            page.get_by_text("PLF DB Agent V2").first.wait_for(timeout=10_000)
            page.get_by_text("API ONLY").first.wait_for(timeout=10_000)

            page.goto(f"{base_url}/Chat", wait_until="networkidle")
            page.get_by_role("heading", name="Chat").wait_for(timeout=10_000)
            page.get_by_text("DRAFT").first.wait_for(timeout=10_000)
            page.get_by_text("MANUAL REVIEW REQUIRED").first.wait_for(timeout=10_000)
