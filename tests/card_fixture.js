/* Browser-only synthetic data. No API requests or IPTV playback. */
window.installDispatcharrFixture = () => {
  const now = Date.now() / 1000;
  const entity = "sensor.dispatcharr_demo_viewers";
  const row = {
    client_id: "client_0", channel_uuid: "11111111-2222-4333-8444-555555555555",
    user_id: "42", username: "Alex", channel_name: "Example TV", logo_id: 1,
    connected_at: now - 1234, source_resolution: "1920x1080", source_fps: 50,
    video_codec: "h264", audio_codec: "aac", average_bitrate_kbps: 6500,
    provider: "Demo provider", provider_profile: "Primary", stream_profile: "ffmpeg",
    output_profile: "Default", output_format: "ts", proxy_state: "active", playback_status: null,
    programme: { title: "Nature discoveries", start: now - 900, end: now + 1800 },
  };
  const attributes = { entry_id: "synthetic-only", active_channels: 1, control_enabled: true,
    last_success: new Date().toISOString(), viewers: [row, { ...row, client_id: "client_1", username: "Sam", user_id: "43" }] };
  // A locally drawn demo logo; never a real channel or an external image request.
  const canvas = document.createElement("canvas"); canvas.width = 104; canvas.height = 104;
  const ctx = canvas.getContext("2d"); ctx.fillStyle = "#1378aa"; ctx.fillRect(0, 0, 104, 104);
  ctx.fillStyle = "white"; ctx.font = "bold 30px sans-serif"; ctx.textAlign = "center"; ctx.fillText("TV", 52, 63);
  const logo = new Promise(resolve => canvas.toBlob(resolve));
  const card = document.createElement("dispatcharr-card");
  const appHass = document.querySelector("home-assistant")?.hass || {};
  const fixture = window.cardFixture = { card, calls: [], attributes, language: "en", entity, config: { entity, title: "Dispatcharr · Demo" } };
  fixture.update = (patch = {}, config = {}) => {
    Object.assign(fixture.attributes, patch); Object.assign(fixture.config, config);
    card.setConfig(fixture.config);
    card.hass = {
      ...appHass, language: fixture.language, user: { is_admin: true },
      states: { [entity]: { entity_id: entity, state: fixture.offline ? "unavailable" : String(fixture.attributes.viewers.length), attributes: { ...fixture.attributes } }, ...(fixture.media ? {"sensor.demo_media": {entity_id:"sensor.demo_media", state:String(fixture.media.sessions.length), attributes:{entry_id:attributes.entry_id,viewer_entity_id:entity,...fixture.media}}} : {}) },
      // These stubs cannot send a stop or logo request to a real server.
      fetchWithAuth: async (path) => new Response(await (fixture.images?.[path.split('/').at(-1)] || logo), { headers: { "Content-Type": "image/png" } }),
      callService: async (domain, service, data) => {
        fixture.calls.push({ domain, service, data });
        if (service === "stop_media_session") { fixture.media.sessions = fixture.media.sessions.filter(r => r.source_id !== data.source_id || r.session_id !== data.session_id); fixture.update(); }
        else fixture.update({ viewers: service === "stop_session" ? fixture.attributes.viewers.filter(r => r.client_id !== data.client_id) : [] });
      },
    };
  };
  const host = document.createElement("div"); host.id = "dispatcharr-fixture";
  Object.assign(host.style, { position: "fixed", inset: "0", zIndex: "10000", overflow: "auto", background: "var(--primary-background-color)", padding: "12px" });
  card.style.maxWidth = "860px"; card.style.margin = "0 auto";
  host.append(card); document.body.append(host); fixture.update();
};
