"""Optional real-HA frontend regression check, run only on a disposable test HA.

Requires Playwright + Chromium and a private browser storage-state file from
logging into that test HA. The dashboard must contain one Dispatcharr card with
two synthetic viewers. This script never calls a Dispatcharr stop endpoint.
"""

import argparse
from pathlib import Path
from urllib.parse import urlsplit

from playwright.sync_api import expect, sync_playwright


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:18123")
    parser.add_argument("--dashboard", default="/dispatcharr-test/synthetic")
    parser.add_argument("--storage-state", required=True, type=Path)
    parser.add_argument("--repeat", type=int, default=12)
    args = parser.parse_args()
    if urlsplit(args.url).hostname not in {"127.0.0.1", "localhost", "::1"}:
        parser.error("Only a local disposable Home Assistant is allowed")

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        for run in range(args.repeat):
            context = browser.new_context(
                storage_state=str(args.storage_state), locale="de-DE", color_scheme="dark"
            )
            page = context.new_page()
            page.goto(args.url.rstrip("/") + args.dashboard, wait_until="networkidle")
            expect(page.locator("dispatcharr-card article.viewer")).to_have_count(2)
            # Opening the editor first must load ha-form without visiting options.
            page.get_by_role("button", name="Dashboard bearbeiten", exact=True).click()
            page.get_by_role("button", name="Bearbeiten", exact=True).click()
            expect(page.get_by_role("textbox", name="Titel", exact=True)).to_be_visible()
            expect(page.get_by_text("Zuschauer-Sensor", exact=False).first).to_be_visible()
            page.get_by_role("button", name="Abbrechen", exact=True).click()
            page.get_by_role("button", name="Fertig", exact=True).click()
            print(f"Fresh browser and visual editor: {run + 1}/{args.repeat} passed")
            context.close()
        browser.close()


if __name__ == "__main__":
    main()
