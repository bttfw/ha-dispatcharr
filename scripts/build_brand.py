"""Render the original SVG mark to transparent Home Assistant brand PNGs.

Development dependency: Playwright with Chromium. No runtime dependencies.
"""

from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "custom_components/dispatcharr/brand"


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    svg = (ROOT / "docs/brand/icon.svg").read_text(encoding="utf-8")
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        for scale, suffix in [(1, ""), (2, "@2x")]:
            page = browser.new_page(device_scale_factor=scale)
            page.set_content(f"<style>body{{margin:0}}svg{{width:256px;height:256px}}</style>{svg}")
            page.locator("svg").screenshot(
                path=str(OUTPUT / f"icon{suffix}.png"), omit_background=True
            )
            for dark, color in [(False, "#10283f"), (True, "#e5f6ff")]:
                page.set_content(
                    "<style>body{margin:0}.brand{display:flex;width:512px;height:128px;"
                    "align-items:center;gap:18px;font-family:Arial,sans-serif}"
                    "svg{width:112px;height:112px;flex-shrink:0}strong{font-size:46px;"
                    "letter-spacing:-1px}p{font-size:18px;margin:7px 0 0}</style>"
                    f'<div class="brand" style="color:{color}">{svg}'
                    "<div><strong>Dispatcharr</strong><p>for Home Assistant</p></div></div>"
                )
                name = f"{'dark_' if dark else ''}logo{suffix}.png"
                page.locator(".brand").screenshot(path=str(OUTPUT / name), omit_background=True)
            page.close()
        browser.close()
    print("Rendered six original brand PNGs")


if __name__ == "__main__":
    main()
