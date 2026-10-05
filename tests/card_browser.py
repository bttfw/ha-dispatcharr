"""Isolated card regression tests. All services and data are synthetic.

Requires Playwright + Chromium. No Home Assistant login or server is required.
"""

from pathlib import Path

from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parents[1]


def main():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 390, "height": 1100})
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.set_content("""<style>:root{--primary-color:#007fab;--primary-text-color:#202020;
            --secondary-text-color:#555;--card-background-color:#fff;
            --secondary-background-color:#f3f5f7;--divider-color:#ddd}</style>""")
        page.evaluate("customElements.define('home-assistant', class extends HTMLElement {})")
        page.add_script_tag(
            path=str(ROOT / "custom_components/dispatcharr/www/dispatcharr-card.js"),
            type="module",
        )
        page.wait_for_function("Boolean(customElements.get('dispatcharr-card'))")
        page.add_script_tag(path=str(ROOT / "tests/card_fixture.js"))
        page.evaluate("installDispatcharrFixture()")
        card = page.locator("dispatcharr-card")
        expect(card.locator("article.viewer")).to_have_count(2)
        expect(card.get_by_text("Viewers", exact=True)).to_be_visible()
        expect(card.get_by_text("Alex", exact=True)).to_be_visible()
        expect(card.locator(".logo img")).to_have_count(2)
        assert card.evaluate("e => e.scrollWidth <= e.clientWidth")

        page.evaluate("cardFixture.language='de';cardFixture.update()")
        expect(card.get_by_text("Zuschauer", exact=True)).to_be_visible()
        page.evaluate("cardFixture.update({}, {language:'en'})")
        expect(card.get_by_text("Viewers", exact=True)).to_be_visible()
        page.evaluate("cardFixture.language='fr';cardFixture.update({}, {language:'auto'})")
        expect(card.get_by_text("Viewers", exact=True)).to_be_visible()
        page.evaluate("cardFixture.update({}, {language:'de'})")
        expect(card.get_by_text("Zuschauer", exact=True)).to_be_visible()
        card.locator("summary").first.click()
        expect(card.get_by_text("Dispatcharr-Benutzer-ID", exact=True).first).to_be_visible()
        expect(card.get_by_text("Unbekannt", exact=True).first).to_be_visible()
        page.evaluate("cardFixture.update({}, {language:'en'})")

        card.get_by_role("button", name="End session", exact=True).first.click()
        expect(card.get_by_role("dialog")).to_contain_text("Client ID: client_0")
        card.get_by_role("button", name="Cancel", exact=True).click()
        assert page.evaluate("cardFixture.calls.length") == 0
        expect(card.locator("article.viewer")).to_have_count(2)
        card.get_by_role("button", name="End session", exact=True).first.click()
        card.get_by_role("button", name="Stop", exact=True).click()
        expect(card.locator("article.viewer")).to_have_count(1)
        expect(card.get_by_text("Sam", exact=True)).to_be_visible()
        call = page.evaluate("cardFixture.calls[0]")
        assert call["service"] == "stop_session"
        assert call["data"]["client_id"] == "client_0"
        assert "confirm_all" not in call["data"]
        card.locator("summary").click()
        card.get_by_role("button", name="Stop channel for everyone", exact=True).click()
        expect(card.get_by_role("dialog")).to_contain_text("ALL connected viewers")
        card.get_by_role("button", name="Stop", exact=True).click()
        expect(card.get_by_text("Nobody is watching", exact=True)).to_be_visible()
        assert page.evaluate("cardFixture.calls[1].data.confirm_all") is True

        page.evaluate("cardFixture.offline=true;cardFixture.update()")
        expect(card.get_by_text("Connection lost", exact=True).first).to_be_visible()
        expect(card.get_by_text("Last updated", exact=False)).to_be_visible()
        page.evaluate(
            "cardFixture.offline=false;cardFixture.update({viewers:[{client_id:'unknown-client'}],control_enabled:false})"
        )
        expect(card.get_by_text("No current EPG data", exact=True)).to_be_visible()
        expect(card.get_by_text("No logo", exact=True)).to_be_visible()
        expect(card.get_by_text("Controls are disabled", exact=True)).to_be_visible()
        expect(card.get_by_role("button", name="End session", exact=True)).to_have_count(0)
        assert card.evaluate("e => e.scrollWidth <= e.clientWidth")
        page.set_viewport_size({"width": 1000, "height": 1000})
        page.evaluate("cardFixture.update({viewers:[{client_id:'one'}, {client_id:'two'}]})")
        boxes = card.locator("article.viewer").evaluate_all(
            "es => es.map(e => ({x:e.offsetLeft,y:e.offsetTop}))"
        )
        assert boxes[0]["x"] != boxes[1]["x"] and boxes[0]["y"] == boxes[1]["y"]
        assert not errors, errors
        browser.close()
        print(
            "Card browser checks passed: EN/DE/auto, fallback, exact client/channel confirmation, missing data, outage/recovery, mobile and wide layout"
        )


if __name__ == "__main__":
    main()
