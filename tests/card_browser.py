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
        page.evaluate("window.originalRows = structuredClone(cardFixture.attributes.viewers)")
        card = page.locator("dispatcharr-card")
        expect(card.locator("article.channel-card")).to_have_count(1)
        expect(card.locator(".client")).to_have_count(2)
        expect(card.locator(".connection-count")).to_have_text("2 Connections")
        expect(card.locator(".stat strong")).to_have_text(["1", "2"])
        expect(card.locator(".programme")).to_have_count(1)
        expect(card.locator(".quality")).to_have_count(1)
        expect(card.get_by_text("Dispatcharr clients", exact=True)).to_be_visible()
        expect(card.get_by_text("Alex", exact=True)).to_be_visible()
        expect(card.get_by_text("Sam", exact=True)).to_be_visible()
        expect(card.locator(".logo img")).to_have_count(1)
        assert card.evaluate("e => e.scrollWidth <= e.clientWidth")

        page.evaluate("cardFixture.language='de';cardFixture.update()")
        expect(card.get_by_text("Dispatcharr-Clients", exact=True)).to_be_visible()
        page.evaluate("cardFixture.update({}, {language:'en'})")
        expect(card.get_by_text("Dispatcharr clients", exact=True)).to_be_visible()
        page.evaluate("cardFixture.language='fr';cardFixture.update({}, {language:'auto'})")
        expect(card.get_by_text("Dispatcharr clients", exact=True)).to_be_visible()
        page.evaluate("cardFixture.update({}, {language:'de'})")
        expect(card.get_by_text("Dispatcharr-Clients", exact=True)).to_be_visible()
        card.locator(".client-details summary").first.click()
        expect(card.get_by_text("Dispatcharr-Benutzer-ID", exact=True).first).to_be_visible()
        expect(card.get_by_text("Unbekannt", exact=True).first).to_be_visible()
        page.evaluate("cardFixture.update()")
        expect(card.locator(".client-details").first).to_have_attribute("open", "")
        page.evaluate("cardFixture.update({}, {language:'en'})")

        card.get_by_role("button", name="End session", exact=True).first.click()
        expect(card.get_by_role("dialog")).to_contain_text("Client ID: client_0")
        card.get_by_role("button", name="Cancel", exact=True).click()
        assert page.evaluate("cardFixture.calls.length") == 0
        expect(card.locator(".client")).to_have_count(2)
        card.get_by_role("button", name="End session", exact=True).first.click()
        card.get_by_role("button", name="Stop", exact=True).click()
        expect(card.locator("article.viewer")).to_have_count(1)
        expect(card.locator(".client")).to_have_count(1)
        expect(card.locator(".stat strong")).to_have_text(["1", "1"])
        expect(card.get_by_text("Sam", exact=True)).to_be_visible()
        call = page.evaluate("cardFixture.calls[0]")
        assert call["service"] == "stop_session"
        assert call["data"]["client_id"] == "client_0"
        assert call["data"]["channel_uuid"] == "11111111-2222-4333-8444-555555555555"
        assert "confirm_all" not in call["data"]
        card.locator(".channel-details summary").click()
        card.get_by_role("button", name="Stop channel for everyone", exact=True).click()
        expect(card.get_by_role("dialog")).to_contain_text("ALL clients, including DVR")
        card.get_by_role("button", name="Stop", exact=True).click()
        expect(card.get_by_text("Nobody is watching", exact=True)).to_be_visible()
        assert page.evaluate("cardFixture.calls[1].data.confirm_all") is True

        # A DVR proxy client shares the channel, but keeps its own ID and control.
        page.evaluate("""cardFixture.update({viewers:[originalRows[0], {
          ...originalRows[1], username:null, user_id:null,
          device_description:'Dispatcharr-DVR/recording-31', connected_at:Date.now()/1000-30,
          output_profile:'Recording profile'
        }], active_channels:1})""")
        expect(card.locator(".channel-card")).to_have_count(1)
        expect(card.locator(".client")).to_have_count(2)
        expect(card.locator(".connection-count")).to_have_text("2 Connections · 1 DVR")
        expect(card.locator(".stat strong")).to_have_text(["1", "2"])
        expect(card.locator(".client [data-since]")).to_have_count(2)
        times = card.locator(".client [data-since]").all_text_contents()
        assert times[0] != times[1]
        recording = card.locator(".client").filter(has_text="DVR recording")
        recording.locator("summary").click()
        expect(recording.get_by_text("Recording profile", exact=True)).to_be_visible()
        expect(recording.get_by_text("Dispatcharr-DVR/recording-31", exact=True)).to_be_visible()
        recording.get_by_role("button", name="End session", exact=True).click()
        expect(card.get_by_role("dialog")).to_contain_text("may interrupt the recording")
        card.get_by_role("button", name="Stop", exact=True).click()
        expect(card.locator(".client")).to_have_count(1)
        expect(card.get_by_text("Alex", exact=True)).to_be_visible()
        assert page.evaluate("cardFixture.calls.at(-1).data.client_id") == "client_1"
        assert page.evaluate("cardFixture.calls.at(-1).service") == "stop_session"

        # Never merge by username/title, including a same-ID client on another channel.
        page.evaluate("""cardFixture.update({viewers:[originalRows[0], {
          ...originalRows[0], channel_uuid:'22222222-2222-4333-8444-555555555555'
        }, {...originalRows[1], username:'Alex'}], active_channels:2})""")
        expect(card.locator(".channel-card")).to_have_count(2)
        expect(card.locator(".client")).to_have_count(3)
        expect(card.locator(".channel-title")).to_have_text(["Example TV", "Example TV"])
        card.locator(".client").first.get_by_role("button", name="End session", exact=True).click()
        card.get_by_role("button", name="Stop", exact=True).click()
        expect(card.locator(".channel-card")).to_have_count(2)
        expect(card.locator(".client")).to_have_count(2)
        assert page.evaluate(
            "cardFixture.attributes.viewers.some(r => r.channel_uuid.startsWith('2222') && r.client_id === 'client_0')"
        )

        # More than ten users remain individually visible in a single channel group.
        page.evaluate("""cardFixture.update({viewers:Array.from({length:15}, (_,i)=>({
          ...originalRows[0], client_id:'many-'+i, username:'Viewer '+i
        })), active_channels:1})""")
        expect(card.locator(".channel-card")).to_have_count(1)
        expect(card.locator(".client")).to_have_count(15)
        expect(card.get_by_text("Viewer 14", exact=True)).to_be_visible()
        page.evaluate(
            "cardFixture.update({viewers:originalRows});cardFixture.admin=false;cardFixture.update()"
        )
        expect(card.locator(".session-stop")).to_have_count(0)
        expect(card.get_by_text("Controls require an HA administrator", exact=True)).to_be_visible()
        page.evaluate("cardFixture.admin=true;cardFixture.update()")

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
        page.evaluate("""() => {
          cardFixture.media = {
            media_sources: ['jellyfin','emby','plex'].map(id => ({id,type:id,name:id,connected:true,session_count:1,control_enabled:true})),
            sessions: ['jellyfin','emby','plex'].map(id => ({source_id:id,source_type:id,source_name:id,session_id:'same-session-id',item_id:'item-one',username:'Same name',title:'Test film',playback_status:'paused',position_seconds:120,duration_seconds:3600,observed_at:Date.now()/1000,can_stop:true,image_key:'demo'}))
          }; cardFixture.update({}, {language:'en'});
        }""")
        expect(card.locator("article.viewer")).to_have_count(5)
        expect(card.locator(".sources .status")).to_have_count(4)
        expect(card.get_by_text("Same name", exact=True)).to_have_count(3)
        expect(card.get_by_text("Media sessions", exact=True)).to_be_visible()
        expect(card.locator(".media-viewer .logo img")).to_have_count(3)
        paused = card.locator(".media-viewer progress").first.evaluate("e => e.value")
        page.evaluate("cardFixture.card._tick()")
        assert card.locator(".media-viewer progress").first.evaluate("e => e.value") == paused
        page.evaluate(
            "cardFixture.offline=true;cardFixture.media.media_sources[1].connected=false;cardFixture.media.media_sources[1].error='invalid_auth';cardFixture.media.sessions=cardFixture.media.sessions.filter(r=>r.source_id!=='emby');cardFixture.update()"
        )
        expect(card.locator("article.viewer")).to_have_count(2)
        expect(card.get_by_text("Partly connected", exact=True)).to_be_visible()
        expect(card.get_by_text("emby: Key rejected", exact=True)).to_be_visible()
        card.locator(".media-viewer").first.get_by_role(
            "button", name="End session", exact=True
        ).click()
        expect(card.get_by_role("dialog")).to_contain_text("Session ID: same-session-id")
        card.get_by_role("button", name="Stop", exact=True).click()
        expect(card.locator(".media-viewer")).to_have_count(1)
        call = page.evaluate("cardFixture.calls.at(-1)")
        assert call["service"] == "stop_media_session"
        assert call["data"] == {
            "config_entry_id": "synthetic-only",
            "source_id": "jellyfin",
            "session_id": "same-session-id",
            "item_id": "item-one",
        }
        assert "plex" in card.locator(".media-viewer").inner_text().lower()
        page.set_viewport_size({"width": 390, "height": 1000})
        assert card.evaluate("e => e.scrollWidth <= e.clientWidth")
        assert not errors, errors
        browser.close()
        print(
            "Card browser checks passed: channel UUID grouping, DVR, 15 clients, exact stops, EN/DE, missing data, isolated sources, outage/recovery, mobile and wide layout"
        )


if __name__ == "__main__":
    main()
