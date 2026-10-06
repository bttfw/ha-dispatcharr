"""Render the shipped card with clearly labelled synthetic, offline-only data.

Requires Playwright and its Chromium browser. No server, login or IPTV is used.
"""

from datetime import UTC, datetime
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs/screenshots"
DEMO_TIME = datetime(2026, 10, 6, 16, tzinfo=UTC)
DEMO = r"""async () => {
  const fixture = cardFixture, now = Date.now()/1000;
  fixture.attributes.viewers[0].connected_at = now - 160;
  Object.assign(fixture.attributes.viewers[1], {
    username:null, user_id:null, device_description:'Dispatcharr-DVR/recording-31',
    connected_at:now - 1800
  });
  fixture.media = {
    media_sources: ['jellyfin','emby','plex'].map(kind => ({
      id:kind,type:kind,name:{jellyfin:'Jellyfin',emby:'Emby',plex:'Plex'}[kind],
      connected:true,session_count:1,last_success:new Date().toISOString(),
      control_enabled:kind === 'jellyfin'
    })),
    sessions: [
      {source_id:'jellyfin',source_type:'jellyfin',source_name:'Jellyfin',
       username:'Sam',user_id:'demo-user-1',device_id:'demo-tv',device_name:'Living room TV',
       client:'Jellyfin',title:'The Long Way Home',media_type:'Movie',playback_status:'playing',
       position_seconds:1680,duration_seconds:6300,source_resolution:'3840x2160',source_fps:24,
       source_bitrate_kbps:18000,video_codec:'hevc',audio_codec:'aac',play_method:'DirectPlay',
       can_stop:true},
      {source_id:'emby',source_type:'emby',source_name:'Emby',
       username:'Taylor',user_id:'demo-user-2',device_id:'demo-tablet',device_name:'Tablet',
       client:'Emby',title:'Beyond the Blue',media_type:'Movie',playback_status:'paused',
       position_seconds:720,duration_seconds:5400,source_resolution:'1920x1080',source_fps:24,
       source_bitrate_kbps:6200,video_codec:'h264',audio_codec:'aac',play_method:'DirectPlay',
       can_stop:true},
      {source_id:'plex',source_type:'plex',source_name:'Plex',
       username:'Jamie',user_id:'demo-user-3',device_id:'demo-browser',device_name:'Browser',
       client:'Plex Web',title:'A New Beginning',series_title:'City Stories',season:1,episode:3,
       media_type:'episode',playback_status:'playing',position_seconds:990,duration_seconds:2700,
       source_resolution:'1920x1080',source_fps:24,source_bitrate_kbps:8000,
       video_codec:'h264',audio_codec:'aac',play_method:'directplay',can_stop:false}
    ].map((row,i)=>({...row,session_id:`demo-session-${i}`,item_id:`demo-item-${i}`,
      observed_at:now,image_key:row.source_id}))
  };
  fixture.images = {};
  for (const [key,colors,label] of [
    ['jellyfin',['#081e40','#449aa3'],'HOME'],
    ['emby',['#0a234a','#547bf4'],'BLUE'],
    ['plex',['#392b50','#db9550'],'CITY']
  ]) {
    const canvas=document.createElement('canvas');canvas.width=128;canvas.height=180;
    const ctx=canvas.getContext('2d'), gradient=ctx.createLinearGradient(0,0,128,180);
    gradient.addColorStop(0,colors[0]);gradient.addColorStop(1,colors[1]);
    ctx.fillStyle=gradient;ctx.fillRect(0,0,128,180);
    ctx.fillStyle='#ffffff32';ctx.beginPath();ctx.arc(96,42,38,0,Math.PI*2);ctx.fill();
    ctx.fillStyle='#ffffff22';ctx.beginPath();ctx.moveTo(0,125);ctx.lineTo(62,57);
    ctx.lineTo(128,125);ctx.fill();ctx.fillStyle='#fff';ctx.textAlign='center';
    ctx.font='bold 20px Arial';ctx.fillText(label,64,144);ctx.font='9px Arial';
    ctx.fillText('FICTIONAL DEMO',64,163);
    fixture.images[key]=await new Promise(resolve=>canvas.toBlob(resolve));
  }
  fixture.update({}, {language:'en',title:'Dispatcharr · Demo'});
}"""


def capture_previews(page, card, errors):
    """Capture only the synthetic card, including in an authenticated HA frontend."""
    page.evaluate("""() => {
      const app = document.querySelector('home-assistant');
      if (app) app.style.display = 'none';
      Object.assign(document.querySelector('#dispatcharr-fixture').style,
        {position:'relative',inset:'auto',overflow:'visible'});
    }""")
    expect(card.locator("article.viewer")).to_have_count(4)
    expect(card.locator(".channel-card")).to_have_count(1)
    expect(card.locator(".client")).to_have_count(2)
    expect(card.locator(".dvr-badge")).to_have_count(1)
    expect(card.locator(".logo img")).to_have_count(4)
    expect(card.locator(".sources .status")).to_have_count(4)

    def capture(name):
        page.wait_for_function("""() => [...cardFixture.card.shadowRoot.querySelectorAll('img')]
          .every(image => image.complete && image.naturalWidth > 0)""")
        assert card.evaluate("e => e.scrollWidth <= e.clientWidth")
        assert not errors, errors
        card.screenshot(path=str(OUTPUT / name))

    capture("desktop-en.png")
    page.set_viewport_size({"width": 390, "height": 2200})
    capture("mobile-en.png")
    page.evaluate("cardFixture.update({}, {language:'de'});")
    expect(card.get_by_text("Medien-Sessions", exact=True)).to_be_visible()
    capture("mobile.png")
    page.set_viewport_size({"width": 1000, "height": 1400})
    capture("desktop-de.png")
    page.evaluate("""() => {
      cardFixture.media.sessions=[];
      cardFixture.media.media_sources=[{id:'jellyfin',type:'jellyfin',name:'Jellyfin',
        connected:true,session_count:0}];
      cardFixture.card.style.maxWidth='560px';
      cardFixture.update({control_enabled:false});
    }""")
    expect(card.locator("article.viewer")).to_have_count(1)
    capture("grouped-channel-de.png")
    page.evaluate("cardFixture.update({}, {language:'en'});")
    capture("grouped-channel-en.png")
    page.set_viewport_size({"width": 390, "height": 1200})
    page.evaluate("""() => {
      cardFixture.attributes.viewers=[];
      cardFixture.update({active_channels:0});
    }""")
    expect(card.get_by_text("Nobody is watching", exact=True)).to_be_visible()
    capture("empty.png")
    page.evaluate("""() => {
      cardFixture.media=null;cardFixture.offline=true;cardFixture.update();
    }""")
    capture("offline.png")
    page.evaluate("""() => {
      cardFixture.offline=false;
      cardFixture.update({active_channels:1,viewers:[{client_id:'demo-unknown'}],control_enabled:false});
    }""")
    expect(card.get_by_text("No current EPG data", exact=True)).to_be_visible()
    capture("missing.png")


def capture_layouts(page, card, errors):
    """Render every selectable layout with the same fictional four-source data."""
    page.evaluate(DEMO)
    page.evaluate("cardFixture.card.style.maxWidth='1240px'")
    for language in ("en", "de"):
        for layout in ("grid", "list", "tiles"):
            page.evaluate(
                """args => cardFixture.update({}, {...args,
                columns:args.layout==='tiles'?'3':'2',compact:false,
                show_quality:true,show_progress:true})""",
                {"language": language, "layout": layout},
            )
            expect(card.locator(".channel-card")).to_have_count(1)
            expect(card.locator(".client")).to_have_count(2)
            expect(card.locator(".media-viewer")).to_have_count(3)
            page.wait_for_function("""[...cardFixture.card.shadowRoot.querySelectorAll('img')]
                .every(image => image.complete && image.naturalWidth > 0)""")
            for suffix, width in (("", 1320), ("-mobile", 390)):
                page.set_viewport_size({"width": width, "height": 1400})
                assert card.evaluate("e => e.scrollWidth <= e.clientWidth")
                assert not errors, errors
                card.screenshot(path=str(OUTPUT / f"layout-{layout}{suffix}-{language}.png"))


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(
            viewport={"width": 1000, "height": 1400},
            timezone_id="Europe/Berlin",
            device_scale_factor=1,
        )
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.route("**/*", lambda route: route.abort())
        page.clock.install(time=DEMO_TIME)
        page.clock.pause_at(DEMO_TIME)
        page.set_content("""<style>
          :root{--primary-color:#03a9f4;--primary-text-color:#e8eaed;
          --secondary-text-color:#a1a9b4;--card-background-color:#1c2028;
          --primary-background-color:#101319;--secondary-background-color:#242a34;
          --divider-color:#343c47;--success-color:#58bc84;--error-color:#ef7777;
          --ha-card-border-radius:20px;font-family:Arial,sans-serif}
          ha-card{display:block;border:1px solid var(--divider-color)}
        </style>""")
        page.evaluate("customElements.define('home-assistant',class extends HTMLElement {})")
        page.add_script_tag(
            path=str(ROOT / "custom_components/dispatcharr/www/dispatcharr-card.js"),
            type="module",
        )
        page.wait_for_function("Boolean(customElements.get('dispatcharr-card'))")
        page.add_script_tag(path=str(ROOT / "tests/card_fixture.js"))
        page.evaluate("installDispatcharrFixture()")
        page.evaluate(DEMO)
        card = page.locator("dispatcharr-card")
        capture_layouts(page, card, errors)
        page.evaluate(
            "cardFixture.update({}, {layout:'grid',columns:'auto',language:'en'});cardFixture.card.style.maxWidth='960px'"
        )
        page.set_viewport_size({"width": 1000, "height": 1400})
        capture_previews(page, card, errors)
        browser.close()
        print(
            "Rendered 21 screenshots: layouts, EN/DE, desktop/mobile, grouped, empty, offline, missing data."
        )


if __name__ == "__main__":
    main()
