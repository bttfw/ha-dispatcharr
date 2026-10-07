"""Behavior checks for per-card filtering and incremental DOM updates."""

from playwright.sync_api import expect


def check_customization(page, card):
    for layout in ("grid", "list", "tiles"):
        page.evaluate("resetLayoutFixture", layout)
        page.evaluate("""cardFixture.update({}, {show_title:false,show_subtitle:false,
          show_sources:false,show_counts:false,max_items:2,sort_by:'channel'})""")
        expect(card.locator("h2")).to_have_count(0)
        expect(card.locator(".heading")).to_have_count(0)
        expect(card.locator(".sources")).to_have_count(0)
        expect(card.locator(".stats")).to_have_count(0)
        expect(card.locator("article.viewer")).to_have_count(2)
        card.get_by_role("button", name="Show more (4)", exact=True).click()
        expect(card.locator("article.viewer")).to_have_count(4)
        page.evaluate("cardFixture.update()")
        expect(card.locator("article.viewer")).to_have_count(4)
        card.get_by_role("button", name="Show less", exact=True).click()
        expect(card.locator("article.viewer")).to_have_count(2)

        # Exact source IDs, including two servers of the same type.
        page.evaluate("""() => {
          cardFixture.media.media_sources.push({id:'jellyfin2',type:'jellyfin',name:'Second Jellyfin',connected:true,session_count:1});
          cardFixture.media.sessions.push({...cardFixture.media.sessions[0],source_id:'jellyfin2',source_name:'Second Jellyfin'});
          cardFixture.update({}, {sources:['jellyfin2'],show_counts:true,max_items:0});
        }""")
        expect(card.locator(".channel-card")).to_have_count(0)
        expect(card.locator(".media-viewer")).to_have_count(1)
        expect(card.locator(".stat strong")).to_have_text(["1"])
        expect(card.locator(".server-details dt")).to_have_text(["Second Jellyfin"])
        page.evaluate("cardFixture.update({}, {sources:['dispatcharr'],dvr_mode:'hide'})")
        expect(card.locator(".client")).to_have_count(3)
        expect(card.locator(".dvr-badge")).to_have_count(0)
        expect(card.locator(".stat strong")).to_have_text(["3", "4"])
        page.evaluate("cardFixture.update({}, {dvr_mode:'only'})")
        expect(card.locator(".client")).to_have_count(1)
        expect(card.locator(".dvr-badge")).to_have_count(1)
        page.evaluate("cardFixture.update({}, {dvr_mode:'separate'})")
        expect(card.locator(".channel-card")).to_have_count(4)
        expect(card.locator(".client")).to_have_count(4)
        expect(card.locator(".list-heading")).to_have_text("Recordings")
        # Show filters cannot remove the warning about whole-channel scope.
        page.evaluate("cardFixture.update({}, {layout:'grid',dvr_mode:'hide'})")
        card.locator(".channel-details summary").first.click()
        card.get_by_role("button", name="Stop channel for everyone", exact=True).first.click()
        expect(card.get_by_role("dialog")).to_contain_text("including recordings")
        card.get_by_role("button", name="Cancel", exact=True).click()
        assert page.evaluate("cardFixture.calls.length") == 0

    page.evaluate("resetLayoutFixture('grid')")
    page.evaluate("""() => {
      cardFixture.media.sessions[0].play_method='Transcode';
      cardFixture.media.sessions[1].play_method='DirectStream';
      cardFixture.media.sessions[2].play_method=null;
      cardFixture.update({}, {sort_by:'duration'});
    }""")
    expect(card.locator(".playback-badges .transcode")).to_have_text("Transcoding")
    expect(
        card.locator(".media-viewer").filter(has_text="emby · emby").locator(".playback-badges")
    ).to_contain_text("Direct Stream")
    expect(card.locator(".media-viewer").nth(2).locator(".playback-badges .chip")).to_have_count(1)
    assert card.locator("article.viewer").first.get_attribute("class") == "viewer channel-card"

    # A focused control and already loaded image keep their DOM identity,
    # even when a channel changes position and its action data changes.
    card.locator(".channel-details summary").first.click()
    card.locator(".client-details summary").first.focus()
    page.evaluate("""() => {
      const root=cardFixture.card.shadowRoot;
      window.savedFocus=root.activeElement;
      window.savedChannel=root.querySelector('.channel-card');
      window.savedImage=root.querySelector('.logo img');
      cardFixture.attributes.viewers=cardFixture.attributes.viewers.map(r=>({...r,
        channel_name:r.channel_uuid.startsWith('111')?'Zulu':'Alpha'}));
      cardFixture.update({}, {sort_by:'channel'});
    }""")
    assert page.evaluate(
        "savedFocus.isConnected && cardFixture.card.shadowRoot.activeElement === savedFocus"
    )
    assert page.evaluate("savedChannel.isConnected && savedImage.isConnected")
    assert page.evaluate("savedChannel.querySelector('.channel-details').open")
    expect(card.locator(".channel-title").last).to_have_text("Zulu")
    page.evaluate("cardFixture.update({}, {sort_by:'user'})")
    assert page.evaluate(
        "savedFocus.isConnected && cardFixture.card.shadowRoot.activeElement === savedFocus"
    )

    # Never call a filtered or unavailable source 'nobody watching'.
    page.evaluate(
        """cardFixture.update({}, {sources:['jellyfin'],dvr_mode:'only',idle_compact:true})"""
    )
    expect(card.get_by_text("No matching playback", exact=True)).to_be_visible()
    expect(card.locator(".idle-line")).to_have_count(0)
    page.evaluate("""() => {
      cardFixture.media.sessions=[];
      cardFixture.media.media_sources.forEach(s=>s.session_count=0);
      cardFixture.update({}, {dvr_mode:'show'});
    }""")
    expect(card.locator(".idle-line")).to_have_text("Dispatcharr · DemoNobody is watching")
    expect(card.locator(".stats")).to_have_count(0)
    assert page.evaluate("cardFixture.card._logos.size") == 0
    page.evaluate("cardFixture.media.media_sources[0].connected=false;cardFixture.update()")
    expect(card.locator(".idle-line")).to_have_count(0)
    expect(card.get_by_text("Connection lost", exact=True).first).to_be_visible()
    page.evaluate("cardFixture.update({}, {sources:['removed-server']})")
    expect(
        card.get_by_text("A selected server is no longer configured.", exact=True)
    ).to_be_visible()
    page.evaluate("resetLayoutFixture('list')")
    page.evaluate("cardFixture.update({}, {language:'de',max_items:1,dvr_mode:'separate'})")
    expect(card.get_by_role("button", name="Weitere anzeigen (6)", exact=True)).to_be_visible()
    # New settings round-trip through the actual editor's public event.
    page.evaluate("""() => {
      window.customEditor=document.createElement('dispatcharr-card-editor');
      customEditor.setConfig(cardFixture.config);customEditor.hass=cardFixture.card._hass;
      document.body.append(customEditor);window.customConfig=null;
      customEditor.addEventListener('config-changed',e=>window.customConfig=e.detail.config);
      customEditor._form.dispatchEvent(new CustomEvent('value-changed',{detail:{value:{
        sources:['jellyfin'],max_items:5,show_title:false,idle_compact:true,dvr_mode:'hide',sort_by:'user'
      }}}));
    }""")
    config = page.evaluate("customConfig")
    assert page.evaluate(
        "customEditor._form.schema.filter(s=>s.type==='expandable').every(s=>s.flatten===true)"
    )
    assert config["sources"] == ["jellyfin"] and config["max_items"] == 5
    assert config["show_title"] is False and config["idle_compact"] is True
    assert config["dvr_mode"] == "hide" and config["sort_by"] == "user"
    page.evaluate("customEditor.remove()")
