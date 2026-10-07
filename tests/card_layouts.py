"""Shared layout checks, run by card_browser.py with synthetic data and services."""

from playwright.sync_api import expect


def check_layouts(page, card):
    page.evaluate("""() => {
      window.resetLayoutFixture = (layout) => {
        document.querySelector('#dispatcharr-fixture').remove();
        installDispatcharrFixture();
        cardFixture.offline=false;cardFixture.admin=true;cardFixture.calls=[];
        cardFixture.media={
          media_sources:['jellyfin','emby','plex'].map(id=>({id,type:id,name:id,connected:true,session_count:1,control_enabled:true})),
          sessions:['jellyfin','emby','plex'].map(id=>({source_id:id,source_type:id,source_name:id,session_id:'same-session',item_id:'same-item',username:'Media viewer',title:'Same title',playback_status:'paused',position_seconds:120,duration_seconds:3600,observed_at:Date.now()/1000,can_stop:true}))
        };
        cardFixture.update({active_channels:3,control_enabled:true,viewers:[
          {...originalRows[0]},
          {...originalRows[1],username:null,user_id:null,device_description:'Dispatcharr-DVR/recording-31'},
          {...originalRows[0],channel_uuid:'22222222-2222-4333-8444-555555555555'},
          {...originalRows[0],channel_uuid:'33333333-2222-4333-8444-555555555555'},
        ]}, {layout,columns:'auto',compact:false,show_quality:true,show_progress:true,show_controls:true,language:'en'});
        cardFixture.card.style.maxWidth='1240px';
      };
    }""")

    def columns():
        return card.locator(".list").evaluate(
            'e => getComputedStyle(e).gridTemplateColumns.split(" ").length'
        )

    for layout in ("grid", "list", "tiles"):
        page.evaluate("resetLayoutFixture", layout)
        expect(card.locator(".channel-card")).to_have_count(3)
        expect(card.locator(".client")).to_have_count(4)
        expect(card.locator(".media-viewer")).to_have_count(3)
        expect(card.locator(".stat strong")).to_have_text(["3", "4", "3"])
        # Routine footer text is absent; each source retains its status/time.
        expect(card.locator(".footer")).to_have_count(0)
        server_details = card.locator(".server-details")
        expect(server_details.locator("dd").first).not_to_be_visible()
        server_details.locator("summary").click()
        expect(server_details.locator("dt")).to_have_text(
            ["Dispatcharr", "jellyfin", "emby", "plex"]
        )
        expect(server_details.locator("dd").first).to_contain_text("Connected · Last updated:")
        expect(server_details.locator("dd").nth(1)).to_have_text(
            "Connected · Last updated: Unknown"
        )
        page.evaluate("cardFixture.update()")
        expect(server_details).to_have_attribute("open", "")
        server_details.locator("summary").click()
        page.evaluate("cardFixture.update({warnings:['metadata unavailable']})")
        expect(
            card.get_by_text("Some additional data is currently unavailable.", exact=True)
        ).to_be_visible()
        page.evaluate("cardFixture.update({warnings:[]})")
        if layout != "grid":
            expect(card.locator(".preview-name")).to_have_count(4)
            expect(card.locator(".layout-details[open]")).to_have_count(0)
        for width, expected in ((390, 1), (860, 2), (1320, 3)):
            page.set_viewport_size({"width": width, "height": 1100})
            assert columns() == (1 if layout == "list" else expected)
            assert card.evaluate("e => e.scrollWidth <= e.clientWidth")
            assert card.locator(".viewer").evaluate_all(
                "es => es.every(e => e.scrollWidth <= e.clientWidth)"
            )
        for maximum in ("1", "2", "3"):
            page.evaluate("columns=>cardFixture.update({}, {columns})", maximum)
            assert columns() == (1 if layout == "list" else int(maximum))
        page.evaluate(
            "cardFixture.update({}, {compact:true,show_quality:false,show_progress:false})"
        )
        expect(card.locator(".quality").first).not_to_be_visible()
        expect(card.locator(".programme").first).not_to_be_visible()
        expect(card.locator(".stat strong")).to_have_text(["3", "4", "3"])
        page.evaluate("cardFixture.update({}, {show_quality:true,show_progress:true})")
        expect(card.locator(".quality").first).to_be_visible()
        expect(card.locator(".programme").first).to_be_visible()
        page.evaluate("cardFixture.update({}, {language:'de'})")
        if layout != "grid":
            expect(card.get_by_text("Verbindungen & Details", exact=True)).to_have_count(3)
        page.evaluate("cardFixture.update({}, {language:'en'})")

        # Drawer state survives coordinator updates; every stop keeps its target.
        first_channel = card.locator(".channel-card").first
        if layout != "grid":
            first_channel.locator(".layout-details > summary").click()
        first_channel.locator(".client-details summary").first.click()
        page.evaluate("cardFixture.update()")
        expect(first_channel.locator(".client-details").first).to_have_attribute("open", "")
        if layout != "grid":
            expect(first_channel.locator(".layout-details")).to_have_attribute("open", "")
        recording = first_channel.locator(".client").nth(1)
        recording.get_by_role("button", name="End session", exact=True).click()
        expect(card.get_by_role("dialog")).to_contain_text("Client ID: client_1")
        expect(card.get_by_role("dialog")).to_contain_text("may interrupt the recording")
        card.get_by_role("button", name="Cancel", exact=True).click()
        assert page.evaluate("cardFixture.calls.length") == 0
        recording.get_by_role("button", name="End session", exact=True).click()
        card.get_by_role("button", name="Stop", exact=True).click()
        expect(card.locator(".client")).to_have_count(3)
        call = page.evaluate("cardFixture.calls.at(-1)")
        assert call["service"] == "stop_session"
        assert call["data"]["client_id"] == "client_1"
        assert call["data"]["channel_uuid"] == "11111111-2222-4333-8444-555555555555"
        assert "confirm_all" not in call["data"]
        first_channel.locator(".channel-details > summary").click()
        first_channel.get_by_role("button", name="Stop channel for everyone", exact=True).click()
        expect(card.get_by_role("dialog")).to_contain_text("ALL clients, including DVR")
        card.get_by_role("button", name="Stop", exact=True).click()
        expect(card.locator(".channel-card")).to_have_count(2)
        expect(card.locator(".media-viewer")).to_have_count(3)
        assert page.evaluate("cardFixture.calls.at(-1).data.confirm_all") is True

        media = card.locator(".media-viewer").first
        media.locator(".media-details > summary").click()
        page.evaluate("cardFixture.update()")
        expect(media.locator(".media-details")).to_have_attribute("open", "")
        media.get_by_role("button", name="End session", exact=True).click()
        card.get_by_role("button", name="Stop", exact=True).click()
        expect(card.locator(".media-viewer")).to_have_count(2)
        call = page.evaluate("cardFixture.calls.at(-1)")
        assert call["service"] == "stop_media_session"
        assert call["data"]["source_id"] == "jellyfin"
        assert call["data"]["session_id"] == "same-session"
        assert call["data"]["item_id"] == "same-item"

        page.evaluate("cardFixture.admin=false;cardFixture.update()")
        expect(card.locator(".session-stop")).to_have_count(0)
        page.evaluate("cardFixture.offline=true;cardFixture.update()")
        expect(card.locator(".channel-card")).to_have_count(0)
        expect(card.locator(".media-viewer")).to_have_count(2)
        expect(card.get_by_text("Partly connected", exact=True)).to_be_visible()
        page.evaluate(
            "cardFixture.offline=false;cardFixture.media=null;cardFixture.update({viewers:[{client_id:'unknown'}]})"
        )
        expect(card.get_by_text("No logo", exact=True)).to_be_visible()
        expect(card.get_by_text("No current EPG data", exact=True)).to_be_visible()
        page.evaluate("cardFixture.update({viewers:[],active_channels:0})")
        expect(card.get_by_text("Nobody is watching", exact=True)).to_be_visible()
        page.evaluate("""cardFixture.update({active_channels:1,viewers:Array.from({length:15},(_,i)=>({
          ...originalRows[0],client_id:'many-'+i,username:'Viewer '+i
        }))})""")
        expect(card.locator(".client")).to_have_count(15)
        if layout == "grid":
            expect(card.get_by_text("Viewer 14", exact=True)).to_be_visible()
        else:
            expect(card.locator(".preview-name").last).to_have_text("Viewer 14")
        page.evaluate("""cardFixture.update({viewers:[{...originalRows[0],
          device_alias:'<img src=x onerror=alert(1)>'}]})""")
        assert card.locator(".preview-clients img").count() == 0

    # Backward compatibility and defensive handling of hand-written options.
    page.evaluate("""() => {
      resetLayoutFixture('grid');
      cardFixture.card.setConfig({entity:cardFixture.entity,compact:true});
    }""")
    expect(card.locator(".body")).to_have_attribute("data-layout", "grid")
    expect(card.locator(".quality").first).not_to_be_visible()
    page.evaluate(
        "cardFixture.card.setConfig({entity:cardFixture.entity,compact:true,show_quality:true,layout:'invalid',columns:'999'})"
    )
    expect(card.locator(".body")).to_have_attribute("data-columns", "auto")
    expect(card.locator(".quality").first).to_be_visible()

    # Editor contract uses a stub form here; the actual HA form is checked live.
    page.evaluate("""() => {
      customElements.define('ha-form',class extends HTMLElement {});
      window.layoutEditor=document.createElement('dispatcharr-card-editor');
      layoutEditor.setConfig({entity:cardFixture.entity,compact:true,view_layout:{position:'main'}});
      layoutEditor.hass={...cardFixture.card._hass,language:'de'};
      document.body.append(layoutEditor);
      window.editorResult=null;
      layoutEditor.addEventListener('config-changed',e=>window.editorResult=e.detail.config);
    }""")
    assert page.evaluate("layoutEditor._form.data.show_quality") is False
    assert page.evaluate("layoutEditor._form.computeLabel({name:'layout'})") == "Ansicht"
    page.evaluate(
        "layoutEditor._form.dispatchEvent(new CustomEvent('value-changed',{detail:{value:{layout:'list'}}}))"
    )
    assert page.evaluate("layoutEditor._form.schema.some(s=>s.name==='columns')") is False
    assert page.evaluate("editorResult.view_layout.position") == "main"
    page.evaluate(
        "layoutEditor._form.dispatchEvent(new CustomEvent('value-changed',{detail:{value:{layout:'tiles',columns:'3',show_quality:true}}}))"
    )
    assert page.evaluate("editorResult.layout") == "tiles"
    assert page.evaluate("editorResult.columns") == "3"
    assert page.evaluate("layoutEditor._form.schema.some(s=>s.name==='columns')") is True
    page.evaluate("""() => {
      const restored=document.createElement('dispatcharr-card');
      restored.setConfig(JSON.parse(JSON.stringify(editorResult)));
      restored.hass=cardFixture.card._hass;document.body.append(restored);
      window.restoredLayout=restored.shadowRoot.querySelector('.body').dataset.layout;
      window.restoredColumns=restored.shadowRoot.querySelector('.body').dataset.columns;
      restored.remove();layoutEditor.remove();
    }""")
    assert page.evaluate("restoredLayout") == "tiles"
    assert page.evaluate("restoredColumns") == "3"
