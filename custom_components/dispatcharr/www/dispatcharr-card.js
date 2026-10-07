/* Independent Dispatcharr card. No external libraries, playback or credentials. */
// Extra modules can run before HA replaces the native custom-element registry.
// Wait for its application element before extending HTMLElement or registering.
await customElements.whenDefined("home-assistant");

const messages = {
  de: {
    layout: "Ansicht", grid: "Raster", list: "Kompakte Liste", tiles: "Logo-Kacheln", columns: "Maximale Spaltenzahl", automatic: "Automatisch", spacing: "Kompakte Abstände", showQuality: "Quellqualität anzeigen", showProgress: "EPG / Wiedergabefortschritt anzeigen", connectionsDetails: "Verbindungen & Details", layoutHint: "Auf schmalen Karten werden automatisch weniger Spalten angezeigt. Die Liste bleibt einspaltig. Die Gesamtbreite der Karte wird im HA-Dashboard eingestellt.",
    clients: "Verbindungen", oneClient: "Verbindung", dvr: "DVR-Aufnahme", channelDetails: "Senderdetails", clientDetails: "Verbindungsdetails", dvrWarning: "Diese Verbindung gehört laut Dispatcharr zu einer DVR-Aufnahme. Das Beenden kann die Aufnahme unterbrechen.",
    mediaSessions: "Medien-Sessions", proxyClients: "Dispatcharr-Clients", partial: "Teilweise verbunden", source: "Server", sourceUserId: "Server-Benutzer-ID", sessionId: "Session-ID", itemId: "Medien-ID", device: "Gerät", method: "Wiedergabeart", output: "Transkodierte Ausgabe", nominalBitrate: "Gemeldete Bitrate", position: "Wiedergabefortschritt", playing: "Wiedergabe", paused: "Pausiert", buffering: "Puffert", noPoster: "Kein Bild", incomplete: "Die Liste enthält nur erreichbare Quellen. Verbindungen werden getrennt gezählt, nicht als eindeutige Personen.", invalid_auth: "Schlüssel abgewiesen", insufficient_permissions: "Berechtigung fehlt", cannot_connect: "Nicht erreichbar", unsupported_api: "API-Antwort unvollständig", mediaConfirm: "Diese Wiedergabe auf diesem Server beenden?",
    title: "Dispatcharr", viewers: "Zuschauer", channels: "Aktive Kanäle", online: "Verbunden", offline: "Verbindung unterbrochen",
    empty: "Niemand schaut gerade", emptyHint: "Neue Verbindungen erscheinen automatisch.", unknown: "Unbekannt", noEpg: "Keine aktuellen EPG-Daten",
    noLogo: "Kein Logo", last: "Zuletzt aktualisiert", details: "Details", provider: "Provider", providerProfile: "Provider-Profil",
    streamProfile: "Stream-Profil", outputProfile: "Ausgabeprofil", format: "Ausgabeformat", quality: "Quelle", bitrate: "Ø Datenrate",
    stop: "Session beenden", stopAll: "Kanal für alle beenden", confirm: "Beenden", cancel: "Abbrechen", disabled: "Steuerung ist ausgeschaltet",
    singleConfirm: "Nur diese Client-Session beenden?", allConfirm: "Diesen Kanal für ALLE Clients beenden, einschließlich DVR?",
    stopping: "Beenden wird geprüft …", stopped: "Beendet und Status erneut abgefragt.", admin: "Steuerung nur für HA-Administratoren",
    proxy: "Kanal-Proxy", playback: "Wiedergabestatus des Geräts", connected: "Verbunden seit", metadata: "Einige Zusatzdaten sind derzeit nicht verfügbar.",
    entity: "Zuschauer-Sensor", cardTitle: "Titel", compact: "Kompakte Ansicht", controls: "Aktionsschaltflächen anzeigen",
    configure: "Bitte einen Dispatcharr-Zuschauer-Sensor auswählen.", gone: "Die Integration oder der ausgewählte Sensor ist nicht verfügbar.",
    allWarning: "Dies betrifft alle Verbindungen dieses Kanals, einschließlich Aufnahmen und inzwischen hinzugekommener Clients.", connection: "Verbindung",
    language: "Kartensprache", auto: "Home-Assistant-Sprache", now: "Aktuelle Sendung", userId: "Dispatcharr-Benutzer-ID", clientId: "Client-ID",
    resolution: "Auflösung", fps: "Bildrate", video: "Video", audio: "Audio", overview: "Zuschauer im Überblick",
  },
  en: {
    layout: "Layout", grid: "Grid", list: "Compact list", tiles: "Logo tiles", columns: "Maximum columns", automatic: "Automatic", spacing: "Compact spacing", showQuality: "Show source quality", showProgress: "Show EPG / playback progress", connectionsDetails: "Connections & details", layoutHint: "Narrow cards automatically use fewer columns. The list always uses one column. Set the overall card width in the HA dashboard.",
    clients: "Connections", oneClient: "Connection", dvr: "DVR recording", channelDetails: "Channel details", clientDetails: "Connection details", dvrWarning: "Dispatcharr identifies this connection as a DVR recording. Ending it may interrupt the recording.",
    mediaSessions: "Media sessions", proxyClients: "Dispatcharr clients", partial: "Partly connected", source: "Server", sourceUserId: "Server user ID", sessionId: "Session ID", itemId: "Media item ID", device: "Device", method: "Play method", output: "Transcoded output", nominalBitrate: "Reported bitrate", position: "Playback progress", playing: "Playing", paused: "Paused", buffering: "Buffering", noPoster: "No artwork", incomplete: "Only reachable sources are listed. Connections are counted separately, not as unique people.", invalid_auth: "Key rejected", insufficient_permissions: "Permission denied", cannot_connect: "Unreachable", unsupported_api: "Incomplete API response", mediaConfirm: "End this playback on this server?",
    title: "Dispatcharr", viewers: "Viewers", channels: "Active channels", online: "Connected", offline: "Connection lost",
    empty: "Nobody is watching", emptyHint: "New connections appear automatically.", unknown: "Unknown", noEpg: "No current EPG data",
    noLogo: "No logo", last: "Last updated", details: "Details", provider: "Provider", providerProfile: "Provider profile",
    streamProfile: "Stream profile", outputProfile: "Output profile", format: "Output format", quality: "Source", bitrate: "Avg. data rate",
    stop: "End session", stopAll: "Stop channel for everyone", confirm: "Stop", cancel: "Cancel", disabled: "Controls are disabled",
    singleConfirm: "End only this client session?", allConfirm: "Stop this channel for ALL clients, including DVR?",
    stopping: "Checking stop …", stopped: "Stopped and actual status refreshed.", admin: "Controls require an HA administrator",
    proxy: "Channel proxy", playback: "Device playback state", connected: "Connected for", metadata: "Some additional data is currently unavailable.",
    entity: "Viewer sensor", cardTitle: "Title", compact: "Compact view", controls: "Show action buttons",
    configure: "Select a Dispatcharr viewer sensor.", gone: "The integration or selected sensor is unavailable.",
    allWarning: "This affects all connections on this channel, including recordings and clients who connected meanwhile.", connection: "Connection",
    language: "Card language", auto: "Home Assistant language", now: "On now", userId: "Dispatcharr user ID", clientId: "Client ID",
    resolution: "Resolution", fps: "Frame rate", video: "Video", audio: "Audio", overview: "Viewers at a glance",
  },
};
const el = (tag, text, cls) => {
  const node = document.createElement(tag);
  if (text !== undefined && text !== null) node.textContent = String(text);
  if (cls) node.className = cls;
  return node;
};
const language = (hass, preferred) => ["en", "de"].includes(preferred) ? preferred : hass?.language?.startsWith("de") ? "de" : "en";
const icon = (name) => { const node = el("ha-icon"); node.setAttribute("icon", `mdi:${name}`); node.setAttribute("aria-hidden", "true"); return node; };
const candidates = (hass) => Object.values(hass?.states || {}).filter(s => s.entity_id.startsWith("sensor.") && s.attributes.entry_id && Array.isArray(s.attributes.viewers));
const duration = (seconds) => {
  const s = Math.max(0, Math.floor(seconds));
  return s >= 3600 ? `${Math.floor(s / 3600)}h ${Math.floor((s % 3600) / 60)}m` : `${Math.floor(s / 60)}m ${s % 60}s`;
};
// Channel identity is supplied by Dispatcharr. Unknown IDs stay separate;
// names, logos, users and media-server titles are never used to join rows.
const channelGroups = (rows, entry) => {
  const groups = new Map();
  rows.forEach((row, index) => {
    const known = typeof row.channel_uuid === "string" && /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(row.channel_uuid);
    const key = JSON.stringify(known ? ["channel", entry, row.channel_uuid] : ["unknown", entry, index]);
    if (!groups.has(key)) groups.set(key, { key, rows: [], known });
    groups.get(key).rows.push(row);
  });
  return [...groups.values()];
};
// Official v0.31.0 core/utils.py dispatcharr_dvr_user_agent(). This is a
// reported client type, not proof of a person or a recording's saved state.
const isDvr = row => /^Dispatcharr-DVR\/recording-[0-9]+$/.test(row.device_description || "");
const cardConfig = (config = {}) => ({
  title: "Dispatcharr", show_controls: true, language: "auto", ...config,
  layout: ["grid", "list", "tiles"].includes(config.layout) ? config.layout : "grid",
  columns: ["auto", "1", "2", "3"].includes(String(config.columns)) ? String(config.columns) : "auto",
  compact: config.compact === true,
  // Old compact cards hid quality. Preserve that until explicitly changed.
  show_quality: typeof config.show_quality === "boolean" ? config.show_quality : config.compact !== true,
  show_progress: config.show_progress !== false,
});

class DispatcharrCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._logos = new Map();
    this._details = new Set();
    this.shadowRoot.innerHTML = `<style>
      :host{display:block;container-type:inline-size;color:var(--primary-text-color);font-family:var(--paper-font-body1_-_font-family,inherit);--dispatcharr-tint:color-mix(in srgb,var(--primary-color) 8%,transparent)}
      *{box-sizing:border-box}ha-card{overflow:hidden;background:var(--ha-card-background,var(--card-background-color));border-radius:var(--ha-card-border-radius,20px)}
      .body{padding:20px}h2{font-size:21px;font-weight:650;letter-spacing:-.4px;margin:0 0 3px}header{display:flex;gap:14px;justify-content:space-between;align-items:center;flex-wrap:wrap}
      .heading{display:flex;gap:12px;align-items:center;min-width:0}.heading>ha-icon{--mdc-icon-size:26px;background:var(--dispatcharr-tint);color:var(--primary-color);padding:11px;border-radius:15px;width:48px;height:48px}.heading h2{overflow-wrap:anywhere}
      .status,.muted,.time{color:var(--secondary-text-color);font-size:12px}.status{display:flex;align-items:center;gap:7px;padding:6px 9px;background:var(--secondary-background-color);border-radius:20px}.dot{width:7px;height:7px;background:var(--success-color,#43a047);border-radius:50%;flex-shrink:0}
      .offline .dot{background:var(--error-color,#db4437)}.stats{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin:20px 0 16px}.stat{position:relative;padding:13px 15px;background:var(--dispatcharr-tint);border:1px solid color-mix(in srgb,var(--primary-color) 12%,transparent);border-radius:15px;min-width:0}.stat strong{display:block;font-size:30px;line-height:1.2;font-weight:650;letter-spacing:-.8px;margin-bottom:6px}.stat span{font-size:12px;color:var(--secondary-text-color)}.stat ha-icon{position:absolute;right:13px;top:15px;--mdc-icon-size:22px;color:var(--primary-color)}
      .list{display:grid;gap:12px;align-items:start}.viewer{border:1px solid var(--divider-color);border-radius:16px;padding:16px;min-width:0;background:linear-gradient(145deg,var(--dispatcharr-tint),transparent 45%)}.identity{display:flex;gap:13px;align-items:center}.logo{width:62px;height:62px;flex:0 0 62px;background:var(--card-background-color);border:1px solid var(--divider-color);border-radius:14px;display:grid;place-items:center;overflow:hidden;text-align:center;font-size:10px;color:var(--secondary-text-color)}
      .logo img{width:52px;height:52px;object-fit:contain}.who{min-width:0;flex:1}.name{display:flex;align-items:center;gap:5px;font-size:17px;line-height:1.4;font-weight:650}.name ha-icon{--mdc-icon-size:18px;color:var(--secondary-text-color);flex-shrink:0}.name span,.channel{overflow-wrap:anywhere}.channel{display:block;margin-top:2px;font-size:14px}.time{margin-top:5px;font-variant-numeric:tabular-nums}
      .programme{margin-top:16px;padding:13px;border-radius:11px;background:var(--secondary-background-color);font-size:14px;overflow-wrap:anywhere}.eyebrow{display:block;color:var(--secondary-text-color);font-size:10px;letter-spacing:.8px;text-transform:uppercase;margin-bottom:5px}.programme-title{font-weight:550;line-height:1.45}.programme-line{display:flex;justify-content:space-between;gap:8px;margin:9px 0 7px;font-size:11px;color:var(--secondary-text-color);font-variant-numeric:tabular-nums}progress{display:block;width:100%;height:5px;accent-color:var(--primary-color);border:0;border-radius:8px;overflow:hidden}progress::-webkit-progress-bar{background:var(--divider-color)}progress::-webkit-progress-value{background:var(--primary-color)}
      .quality{font-size:11px;color:var(--secondary-text-color);margin-top:14px;line-height:1.7}.chips{display:flex;flex-wrap:wrap;gap:5px}.chip{padding:2px 7px;border:1px solid var(--divider-color);border-radius:6px;color:var(--primary-text-color)}.bitrate{margin-top:5px}.actions{display:flex;gap:8px;flex-wrap:wrap;margin-top:8px}button{display:inline-flex;align-items:center;justify-content:center;gap:7px;font:inherit;font-size:13px;font-weight:500;cursor:pointer;min-height:44px;border:1px solid var(--divider-color);border-radius:10px;padding:8px 12px;background:transparent;color:var(--primary-color)}button ha-icon{--mdc-icon-size:18px}.session-stop{width:100%;background:var(--dispatcharr-tint);border-color:transparent}button:hover{background:var(--secondary-background-color)}button:focus-visible,summary:focus-visible{outline:2px solid var(--primary-color);outline-offset:3px}button:disabled{opacity:.5;cursor:default}.danger{color:var(--error-color,#db4437)}
      details{margin-top:10px;font-size:12px;border-top:1px solid var(--divider-color)}summary{cursor:pointer;color:var(--secondary-text-color);min-height:44px;line-height:44px}dl{display:grid;grid-template-columns:minmax(90px,1fr) minmax(0,1.5fr);gap:9px;margin:0 0 12px}dt{color:var(--secondary-text-color)}dd{margin:0;overflow-wrap:anywhere}
      .empty{grid-column:1/-1;text-align:center;padding:34px 12px;border:1px dashed var(--divider-color);border-radius:16px}.empty ha-icon{--mdc-icon-size:38px;color:var(--primary-color);margin-bottom:14px}.empty strong{display:block;font-weight:550;margin-bottom:8px}.footer{margin-top:16px;font-size:11px;color:var(--secondary-text-color);line-height:1.8}.notice{padding:0 20px 16px;font-size:14px;overflow-wrap:anywhere}.notice:empty{display:none}.notice.error{color:var(--error-color,#db4437)}
      dialog{border:1px solid var(--divider-color);border-radius:16px;color:var(--primary-text-color);background:var(--card-background-color,#fff);padding:24px;max-width:min(440px,calc(100vw - 64px));box-shadow:0 8px 36px #0004}dialog::backdrop{background:#0007}dialog h3{margin-top:0;font-size:18px}dialog p{overflow-wrap:anywhere;line-height:1.5}.dialog-actions{display:flex;justify-content:flex-end;gap:12px;margin-top:20px}
      .sources{display:flex;flex-wrap:wrap;gap:7px;margin:14px 0}.sources .status{border:1px solid var(--divider-color)}.source-label{font-size:10px;letter-spacing:.5px;margin-bottom:8px;color:var(--primary-color);text-transform:uppercase}.poster img{width:100%;height:100%;object-fit:contain}.media-viewer .time{overflow-wrap:anywhere}.stats.multi{grid-template-columns:repeat(3,minmax(0,1fr))}.stats.multi .stat ha-icon{display:none}
      .compact .viewer{padding:12px}.compact .programme{margin-top:10px;padding:10px}.compact .list{gap:8px}.compact .clients{gap:6px}.compact .client{padding:8px 10px}
      .channel-card .channel-title{font-size:19px;overflow-wrap:anywhere}.connection-count{display:flex;align-items:center;gap:5px;margin-top:5px;color:var(--secondary-text-color);font-size:12px}.connection-count ha-icon{--mdc-icon-size:17px}
      .clients{list-style:none;padding:0;margin:16px 0 0;display:grid;gap:9px}.client{padding:11px 12px;border:1px solid var(--divider-color);border-radius:11px;min-width:0}.client .name{font-size:14px;flex-wrap:wrap}.client .name>span:first-of-type{overflow-wrap:anywhere;min-width:0}.client .time{font-size:11px}.client .session-stop{margin-top:4px}.client-details{margin-top:4px;border:0}.client-details summary{font-size:11px}.client-details dl{margin-top:3px}.dvr-badge{border-radius:5px;padding:2px 6px;font-size:10px;font-weight:500;background:var(--dispatcharr-tint);color:var(--primary-color)}
      .logo{grid-template-columns:minmax(0,1fr);grid-template-rows:minmax(0,1fr)}.logo img{min-width:0;min-height:0}
      .preview-clients{margin:12px 0 0;display:grid;gap:6px;list-style:none;padding:0}.preview-client{display:flex;align-items:baseline;justify-content:space-between;gap:10px;font-size:12px}.preview-name{min-width:0;overflow-wrap:anywhere}.preview-client .time{flex-shrink:0;font-size:11px;margin:0}.layout-details>.clients{margin-top:0}.layout-details>.channel-details{margin-top:12px}
      .body[data-layout="list"] .viewer{padding:12px}.body[data-layout="list"] .programme{margin-top:10px;padding:10px}.body[data-layout="list"] .channel-title{font-size:17px}.body[data-layout="list"] .quality{margin-top:8px}.body[data-layout="list"] .preview-clients{margin-top:10px}
      .body[data-layout="tiles"] .identity{display:block;text-align:center}.body[data-layout="tiles"] .logo{width:84px;height:84px;margin:0 auto 12px}.body[data-layout="tiles"] .logo img{width:72px;height:72px}.body[data-layout="tiles"] .poster{height:112px}.body[data-layout="tiles"] .poster img{width:100%;height:100%}.body[data-layout="tiles"] .connection-count,.body[data-layout="tiles"] .name{justify-content:center}.body[data-layout="tiles"] .preview-clients{display:flex;justify-content:center;flex-wrap:wrap;gap:4px 12px}.body[data-layout="tiles"] .preview-client .time{display:none}.body[data-layout="tiles"] .media-viewer .who{display:flex;flex-direction:column}.body[data-layout="tiles"] .media-viewer .channel{order:-1;font-size:17px;font-weight:650;margin-bottom:5px}.body[data-layout="tiles"] .media-viewer .name{font-size:14px}.body[data-layout="tiles"] .chips{justify-content:center}.body[data-layout="tiles"] .quality{text-align:center}
      @container(min-width:680px){.body:not([data-columns="1"]) .list{grid-template-columns:repeat(2,minmax(0,1fr))}}
      @container(min-width:1000px){.body:is([data-columns="auto"],[data-columns="3"]) .list{grid-template-columns:repeat(3,minmax(0,1fr))}}
      .body[data-layout="list"] .list{grid-template-columns:1fr}
      @container(min-width:760px){
        .body[data-layout="list"] .viewer{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1.2fr) minmax(0,1fr);grid-template-areas:"source source source" "identity programme preview" "identity quality preview" "details details details";gap:0 18px;align-items:start}
        .body[data-layout="list"] .source-label{grid-area:source;margin-bottom:8px}.body[data-layout="list"] .identity{grid-area:identity}.body[data-layout="list"] .programme{grid-area:programme;margin:0}.body[data-layout="list"] .quality{grid-area:quality}.body[data-layout="list"] .preview-clients{grid-area:preview;margin:0}.body[data-layout="list"] .layout-details,.body[data-layout="list"] .media-details{grid-area:details}.body[data-layout="list"] .logo{width:48px;height:48px;flex-basis:48px}.body[data-layout="list"] .logo img{width:40px;height:40px}.body[data-layout="list"] .poster img{width:100%;height:100%}
        .body[data-layout="list"] .media-viewer .quality{grid-area:preview;margin:0}
      }
      .body.hide-quality .quality,.body.hide-progress .programme{display:none}
      .list>.viewer:only-child{grid-column:1/-1}
      @container(max-width:420px){.body{padding:16px}.heading>ha-icon{display:none}.heading h2{font-size:19px}.heading .muted{font-size:11px}.status{font-size:11px;padding:5px 8px}.stat{padding:12px}.viewer{padding:13px}.logo{width:56px;height:56px;flex-basis:56px}.logo img{width:46px;height:46px}}
    </style><ha-card><div class="body"></div><div class="notice" role="status" aria-live="polite"></div></ha-card><dialog aria-labelledby="confirm-title"><h3 id="confirm-title"></h3><p class="target"></p><p class="warning"></p><div class="dialog-actions"><button class="cancel"></button><button class="confirm danger"></button></div></dialog>`;
    this.shadowRoot.querySelector(".cancel").onclick = () => this.shadowRoot.querySelector("dialog").close();
    this.shadowRoot.querySelector(".confirm").onclick = () => this._execute();
  }
  static async getConfigElement() {
    // HA loads form controls lazily. Load its public card editor before creating
    // our form so opening this editor first also works in a fresh browser.
    if (!customElements.get("ha-form")) {
      const helpers = await window.loadCardHelpers();
      const card = helpers.createCardElement({ type: "entities", entities: [] });
      await card.constructor.getConfigElement();
      await customElements.whenDefined("ha-form");
    }
    return document.createElement("dispatcharr-card-editor");
  }
  static getStubConfig(hass) { return { entity: candidates(hass)[0]?.entity_id || "", show_controls: true }; }
  setConfig(config) { this._config = cardConfig(config); this._render(); }
  set hass(hass) {
    const previous = this._hass;
    this._hass = hass;
    const id = this._config?.entity;
    if (!previous || previous.states[id] !== hass.states[id] || this._mediaState(previous) !== this._mediaState(hass) || previous.language !== hass.language || previous.user !== hass.user) this._render();
  }
  getCardSize() { const height = this.shadowRoot.querySelector("ha-card")?.offsetHeight; return height ? Math.ceil(height / 50) : 3; }
  getGridOptions() { return { columns: 12, min_columns: 6, rows: "auto" }; }
  connectedCallback() { this._timer = window.setInterval(() => this._tick(), 1000); this._render(); }
  disconnectedCallback() {
    clearInterval(this._timer);
    for (const item of this._logos.values()) if (item.url) URL.revokeObjectURL(item.url);
    this._logos.clear();
  }
  _state() { return this._hass?.states[this._config?.entity]; }
  _mediaState(hass = this._hass) { return Object.values(hass?.states || {}).find(s => s.attributes.viewer_entity_id === this._config?.entity && Array.isArray(s.attributes.media_sources)); }
  _lastSuccess() {
    const stamp = Object.values(this._hass?.states || {}).find(s => s.attributes.viewer_entity_id === this._config?.entity && !Array.isArray(s.attributes.media_sources));
    return stamp && !["unknown", "unavailable"].includes(stamp.state) ? stamp.state : null;
  }
  _locale() { return language(this._hass, this._config?.language); }
  _t(key) { return messages[this._locale()][key] || key; }
  _value(value) { return value === null || value === undefined || value === "" ? this._t("unknown") : String(value); }
  _notice(text, error = false) {
    const node = this.shadowRoot.querySelector(".notice"); node.textContent = text; node.classList.toggle("error", error);
    node.setAttribute("role", error ? "alert" : "status");
  }
  _render() {
    if (!this._config || !this._hass) return;
    const body = this.shadowRoot.querySelector(".body");
    body.classList.toggle("compact", Boolean(this._config.compact));
    body.classList.toggle("hide-quality", !this._config.show_quality);
    body.classList.toggle("hide-progress", !this._config.show_progress);
    body.dataset.layout = this._config.layout; body.dataset.columns = this._config.columns;
    // Capture the visible state before replacing nodes: native toggle events
    // can still be queued when a coordinator update arrives immediately.
    for (const details of body.querySelectorAll("details[data-details-key]")) {
      details.open ? this._details.add(details.dataset.detailsKey) : this._details.delete(details.dataset.detailsKey);
    }
    body.replaceChildren();
    const state = this._state();
    const live = state && !["unavailable", "unknown"].includes(state.state);
    const data = state?.attributes || {};
    const media = this._mediaState()?.attributes || {};
    const sources = media.media_sources || [];
    const sessions = media.sessions || [];
    const allLive = live && sources.every(s => s.connected);
    const anyLive = live || sources.some(s => s.connected);
    body.lang = this._locale();
    const header = el("header"), heading = el("div", null, "heading"), headingText = el("div");
    headingText.append(el("h2", this._config.title || this._t("title")), el("span", this._t("overview"), "muted"));
    heading.append(icon("television-play"), headingText); header.append(heading);
    const status = el("span", null, allLive ? "status" : "status offline"); status.append(el("i", null, "dot"), el("span", this._t(allLive ? "online" : anyLive ? "partial" : "offline"))); header.append(status); body.append(header);
    if (sources.length) {
      const strip = el("div", null, "sources");
      for (const s of [{ name: "Dispatcharr", connected: live, session_count: live ? state.state : null, last_success: data.last_success || this._lastSuccess() }, ...sources]) {
        const badge = el("span", null, s.connected ? "status" : "status offline");
        badge.append(el("i", null, "dot"), el("span", `${s.name}: ${s.connected ? this._value(s.session_count) : this._t(s.error || "offline")}`));
        badge.title = `${this._t("last")}: ${s.last_success ? new Date(s.last_success).toLocaleString(this._locale()) : this._t("unknown")}`; strip.append(badge);
      }
      body.append(strip);
    }
    if ((!state || !live) && !sources.length) {
      body.append(el("p", this._t(!this._config.entity ? "configure" : !state ? "gone" : "offline"), "empty"));
      if (state || this._lastSuccess()) body.append(this._serverDetails(data, live, sources));
      return;
    }
    const stats = el("div", null, sources.length ? "stats multi" : "stats");
    const counts = [["channels", live ? data.active_channels : null], ["proxyClients", live ? state.state : null]];
    if (sources.length) counts.push(["mediaSessions", sources.some(s => s.connected) ? sessions.length : null]);
    for (const [key, value] of counts) {
      const stat = el("div", null, "stat"); stat.append(icon(key === "channels" ? "television" : "account-multiple-outline"), el("strong", this._value(value)), el("span", this._t(key))); stats.append(stat);
    }
    body.append(stats);
    const rows = live ? data.viewers || [] : [];
    const list = el("div", null, "list");
    if (!rows.length && !sessions.length) {
      const empty = el("div", null, "empty"), icon = el("ha-icon"); icon.setAttribute("icon", "mdi:television-off");
      empty.append(icon, el("strong", this._t(allLive ? "empty" : "offline")), el("span", this._t(allLive ? "emptyHint" : "incomplete"), "muted")); list.append(empty);
    }
    for (const group of channelGroups(rows, data.entry_id)) list.append(this._channel(group, data));
    for (const row of sessions) list.append(this._mediaViewer(row, media));
    body.append(list);
    const footer = el("div", null, "footer");
    if (data.warnings?.length) footer.append(el("div", this._t("metadata")));
    if (footer.childElementCount) body.append(footer);
    body.append(this._serverDetails(data, live, sources));
    const needed = new Set(rows.filter(r => r.logo_id).map(r => `${data.entry_id}/${r.logo_id}`));
    for (const row of sessions) if (row.image_key) needed.add(`${media.entry_id}/media/${row.source_id}/${row.image_key}`);
    for (const [key, value] of this._logos) if (!needed.has(key)) { if (value.url) URL.revokeObjectURL(value.url); this._logos.delete(key); }
    this._tick();
  }
  _serverDetails(data, live, sources) {
    const details = this._expandable("sources", "source", "server-details"), dl = el("dl");
    for (const source of [{ name: "Dispatcharr", connected: live, last_success: data.last_success || this._lastSuccess() }, ...sources]) {
      dl.append(el("dt", source.name), el("dd", `${this._t(source.connected ? "online" : source.error || "offline")} · ${this._t("last")}: ${source.last_success ? new Date(source.last_success).toLocaleString(this._locale()) : this._t("unknown")}`));
    }
    details.append(dl); return details;
  }
  _clientName(row) { return this._value(row.device_alias || row.username || (isDvr(row) ? this._t("dvr") : row.device_description)); }
  _expandable(key, label, cls) {
    const details = el("details", null, cls);
    details.dataset.detailsKey = key;
    details.open = this._details.has(key);
    details.ontoggle = () => { if (details.isConnected) details.open ? this._details.add(key) : this._details.delete(key); };
    details.append(el("summary", this._t(label)));
    return details;
  }
  _channel(group, data) {
    // All shared fields are normalized from this UUID's channel record by HA.
    const row = group.rows[0];
    const node = el("article", null, "viewer channel-card");
    if (this._mediaState()?.attributes.media_sources?.length) node.append(el("div", "Dispatcharr", "source-label"));
    const identity = el("div", null, "identity");
    const logo = el("div", this._t("noLogo"), "logo");
    if (Number.isInteger(row.logo_id) && row.logo_id > 0) this._logo(logo, data.entry_id, row.logo_id);
    const who = el("div", null, "who");
    who.append(el("strong", this._value(row.channel_name), "channel-title"));
    const count = el("div", null, "connection-count"), recordings = group.rows.filter(isDvr).length;
    count.append(icon("connection"), el("span", `${group.rows.length} ${this._t(group.rows.length === 1 ? "oneClient" : "clients")}${recordings ? ` · ${recordings} DVR` : ""}`));
    who.append(count); identity.append(logo, who); node.append(identity);
    const programme = el("div", null, "programme");
    if (row.programme && row.programme.end * 1000 > Date.now()) {
      programme.append(el("span", this._t("now"), "eyebrow"));
      const title = el("div", this._value(row.programme.title), "programme-title"); programme.append(title);
      const line = el("div", null, "programme-line");
      const fmt = (stamp) => new Date(stamp * 1000).toLocaleTimeString(this._locale(), { hour: "2-digit", minute: "2-digit" });
      line.append(el("span", `${fmt(row.programme.start)} – ${fmt(row.programme.end)}`));
      const percent = el("span"); line.append(percent); programme.append(line);
      const progress = el("progress"); progress.max = 100; progress.dataset.start = row.programme.start; progress.dataset.end = row.programme.end;
      progress.setAttribute("aria-label", this._value(row.programme.title)); programme.append(progress);
    } else programme.append(el("span", this._t("noEpg"), "muted"));
    node.append(programme);
    const clients = el("ul", null, "clients"); clients.setAttribute("aria-label", this._t("clients"));
    for (const client of group.rows) clients.append(this._client(client, data, group));
    if (this._config.layout === "grid") node.append(clients);
    else {
      const preview = el("ul", null, "preview-clients"); preview.setAttribute("aria-label", this._t("clients"));
      for (const client of group.rows) {
        const item = el("li", null, "preview-client");
        item.append(el("span", `${this._clientName(client)}${isDvr(client) ? " · DVR" : ""}`, "preview-name"));
        const elapsed = el("span", this._t("unknown"), "time");
        if (client.connected_at) elapsed.dataset.since = String(client.connected_at);
        item.append(elapsed); preview.append(item);
      }
      node.append(preview);
    }
    const quality = el("div", null, "quality"), chips = el("div", null, "chips");
    quality.append(el("span", this._t("quality"), "eyebrow"));
    for (const [label, value] of [["resolution", row.source_resolution], ["fps", row.source_fps != null ? `${row.source_fps} fps` : null], ["video", row.video_codec], ["audio", row.audio_codec]]) {
      const chip = el("span", this._value(value), "chip"); chip.title = `${this._t(label)}: ${this._value(value)}`;
      chip.setAttribute("aria-label", chip.title); chips.append(chip);
    }
    quality.append(chips, el("div", `${this._t("bitrate")}: ${row.average_bitrate_kbps != null ? `${(row.average_bitrate_kbps / 1000).toLocaleString(this._locale(), { minimumFractionDigits: 2, maximumFractionDigits: 2 })} Mbit/s` : this._t("unknown")}`, "bitrate")); node.append(quality);
    const details = this._expandable(group.key, "channelDetails", "channel-details");
    const dl = el("dl");
    for (const [key, value] of [["provider", row.provider], ["providerProfile", row.provider_profile], ["streamProfile", row.stream_profile], ["proxy", row.proxy_state]]) dl.append(el("dt", this._t(key)), el("dd", this._value(value)));
    details.append(dl);
    if (this._config.layout === "grid") node.append(details);
    else {
      const connections = this._expandable(JSON.stringify(["connections", group.key]), "connectionsDetails", "layout-details");
      connections.append(clients, details); node.append(connections);
    }
    if (group.known && this._config.show_controls && data.control_enabled && this._hass.user?.is_admin) {
      const all = el("button", this._t("stopAll"), "danger"); all.disabled = Boolean(this._busy); all.onclick = () => this._ask(row, data.entry_id, true); details.append(all);
    }
    return node;
  }
  _client(row, data, group) {
    const node = el("li", null, "client"), name = el("strong", null, "name");
    name.append(icon(isDvr(row) ? "record-rec" : "account-outline"), el("span", this._clientName(row)));
    if (isDvr(row)) name.append(el("span", "DVR", "dvr-badge"));
    node.append(name);
    if (row.device_alias && row.username) node.append(el("div", row.username, "muted"));
    const time = el("div", null, "time"); time.append(el("span", `${this._t("connected")}: `));
    const elapsed = el("span", this._t("unknown"));
    if (row.connected_at) elapsed.dataset.since = String(row.connected_at);
    time.append(elapsed); node.append(time);
    const key = JSON.stringify(["client", group.key, row.client_id]);
    const details = this._expandable(key, "clientDetails", "client-details"), dl = el("dl");
    for (const [label, value] of [["connection", row.connection_status === "connected" ? this._t("online") : row.connection_status], ["playback", row.playback_status], ["device", row.device_description], ["outputProfile", row.output_profile], ["format", row.output_format], ["userId", row.user_id], ["clientId", row.client_id]]) dl.append(el("dt", this._t(label)), el("dd", this._value(value)));
    details.append(dl); node.append(details);
    if (group.known && row.client_id && this._config.show_controls && data.control_enabled && this._hass.user?.is_admin) {
      const stop = el("button", null, "session-stop"); stop.append(icon("stop-circle-outline"), el("span", this._t("stop")));
      stop.disabled = Boolean(this._busy); stop.onclick = () => this._ask(row, data.entry_id, false); node.append(stop);
    }
    return node;
  }
  _mediaViewer(row, data) {
    const node = el("article", null, "viewer media-viewer");
    node.append(el("div", `${this._value(row.source_name)} · ${this._value(row.source_type)}`, "source-label"));
    const identity = el("div", null, "identity"), poster = el("div", this._t("noPoster"), "logo poster"), who = el("div", null, "who");
    if (row.image_key) this._logo(poster, data.entry_id, row.image_key, row.source_id);
    const name = el("strong", null, "name"); name.append(icon("account-outline"), el("span", this._value(row.device_alias || row.username || row.device_name)));
    who.append(name, el("span", this._value(row.title), "channel"));
    if (row.series_title) who.append(el("div", `${row.series_title}${row.season != null && row.episode != null ? ` · S${row.season} E${row.episode}` : ""}`, "muted"));
    who.append(el("div", `${this._value(row.device_name)} · ${row.playback_status ? this._t(row.playback_status) : this._t("unknown")}`, "time"));
    identity.append(poster, who); node.append(identity);
    const programme = el("div", null, "programme"); programme.append(el("span", this._t("position"), "eyebrow"));
    if (row.programme && row.programme.end > Date.now() / 1000) {
      programme.firstElementChild.textContent = this._t("now");
      programme.append(el("div", this._value(row.programme.title), "programme-title"));
      const line = el("div", null, "programme-line"), fmt = stamp => new Date(stamp * 1000).toLocaleTimeString(this._locale(), {hour:"2-digit",minute:"2-digit"});
      line.append(el("span", `${fmt(row.programme.start)} – ${fmt(row.programme.end)}`), el("span"));
      const progress = el("progress"); progress.max = 100; progress.dataset.start = row.programme.start; progress.dataset.end = row.programme.end; progress.setAttribute("aria-label", this._value(row.programme.title));
      programme.append(line, progress);
    } else if (Number.isFinite(row.position_seconds) && Number.isFinite(row.duration_seconds) && row.duration_seconds > 0) {
      const line = el("div", null, "programme-line"); line.append(el("span"), el("span"));
      const progress = el("progress"); progress.max = 100; progress.dataset.position = row.position_seconds; progress.dataset.duration = row.duration_seconds; progress.dataset.observed = row.observed_at; progress.dataset.playing = row.playback_status === "playing" ? "1" : "0";
      progress.setAttribute("aria-label", this._t("position")); programme.append(line, progress);
    } else programme.append(el("span", this._t("unknown"), "muted"));
    node.append(programme);
    const quality = el("div", null, "quality"); quality.append(el("span", this._t("quality"), "eyebrow"));
    const chips = el("div", null, "chips");
    for (const value of [row.source_resolution, row.source_fps != null ? `${row.source_fps} fps` : null, row.video_codec, row.audio_codec]) chips.append(el("span", this._value(value), "chip"));
    quality.append(chips, el("div", `${this._t("nominalBitrate")}: ${row.source_bitrate_kbps != null ? `${(row.source_bitrate_kbps / 1000).toLocaleString(this._locale())} Mbit/s` : this._t("unknown")}`, "bitrate")); node.append(quality);
    const key = JSON.stringify(["media", data.entry_id, row.source_id, row.session_key || row.session_id]);
    const details = this._expandable(key, "details", "media-details");
    const dl = el("dl");
    for (const [label, value] of [["source", row.source_name], ["sourceUserId", row.user_id], ["sessionId", row.session_id], ["itemId", row.item_id], ["device", row.device_id], ["method", row.play_method], ["output", [row.output_resolution, row.output_fps != null ? `${row.output_fps} fps` : null, row.output_video_codec, row.output_audio_codec, row.output_bitrate_kbps != null ? `${(row.output_bitrate_kbps / 1000).toLocaleString(this._locale())} Mbit/s` : null].filter(Boolean).join(" · ")]]) dl.append(el("dt", this._t(label)), el("dd", this._value(value)));
    details.append(dl); node.append(details);
    const source = data.media_sources?.find(s => s.id === row.source_id);
    if (this._config.show_controls && source?.control_enabled && row.can_stop && this._hass.user?.is_admin) {
      const actions = el("div", null, "actions"), stop = el("button", this._t("stop"), "session-stop"); stop.disabled = Boolean(this._busy); stop.onclick = () => this._ask(row, data.entry_id, false); actions.append(stop);
      (this._config.layout === "grid" ? node : details).append(actions);
    }
    return node;
  }
  async _logo(node, entry, id, source) {
    const key = source ? `${entry}/media/${source}/${id}` : `${entry}/${id}`;
    let cached = this._logos.get(key);
    if (cached && !cached.url && Date.now() - cached.created > 60000) cached = null;
    if (!cached) {
      cached = { created: Date.now() }; this._logos.set(key, cached);
      cached.promise = (async () => {
        try {
          const path = source ? `/api/dispatcharr/media_image/${encodeURIComponent(entry)}/${encodeURIComponent(source)}/${encodeURIComponent(id)}` : `/api/dispatcharr/logo/${encodeURIComponent(entry)}/${id}`;
          const response = await this._hass.fetchWithAuth(path);
          if (!response.ok) return;
          const blob = await response.blob();
          if (!this.isConnected || this._logos.get(key) !== cached) return;
          cached.url = URL.createObjectURL(blob);
        } catch { /* Keep the explicit missing-logo placeholder. */ }
      })();
    }
    await cached.promise;
    if (cached.url && node.isConnected) { const img = el("img"); img.alt = ""; img.src = cached.url; img.onerror = () => node.replaceChildren(document.createTextNode(this._t("noLogo"))); node.replaceChildren(img); }
  }
  _tick() {
    const now = Date.now() / 1000;
    for (const node of this.shadowRoot.querySelectorAll("[data-since]")) node.textContent = duration(now - Number(node.dataset.since));
    for (const progress of this.shadowRoot.querySelectorAll("progress")) {
      if (progress.dataset.position !== undefined) {
        const length = Number(progress.dataset.duration), elapsed = progress.dataset.playing === "1" ? Math.max(0, now - Number(progress.dataset.observed)) : 0;
        const position = Math.min(length, Number(progress.dataset.position) + elapsed);
        progress.value = position / length * 100;
        progress.previousElementSibling.firstElementChild.textContent = `${duration(position)} / ${duration(length)}`;
        progress.previousElementSibling.lastElementChild.textContent = `${Math.floor(progress.value)} %`; continue;
      }
      const start = Number(progress.dataset.start), end = Number(progress.dataset.end);
      if (now >= end) { progress.closest(".programme").replaceChildren(el("span", this._t("noEpg"), "muted")); continue; }
      progress.value = Math.min(100, Math.max(0, (now - start) / (end - start) * 100));
      progress.previousElementSibling.lastElementChild.textContent = `${Math.floor(progress.value)} %`;
    }
  }
  _ask(row, entry, all) {
    this._pending = { row, entry, all };
    const dialog = this.shadowRoot.querySelector("dialog");
    dialog.querySelector("h3").textContent = this._t(row.source_id ? "mediaConfirm" : all ? "allConfirm" : "singleConfirm");
    dialog.querySelector(".target").textContent = `${this._value(row.channel_name)} · ${all ? this._t("clients") : this._clientName(row)}`;
    dialog.querySelector(".warning").textContent = all ? this._t("allWarning") : `${this._t("clientId")}: ${row.client_id}${isDvr(row) ? ` — ${this._t("dvrWarning")}` : ""}`;
    if (row.source_id) {
      dialog.querySelector(".target").textContent = `${row.source_name} · ${this._value(row.username || row.device_name)} · ${this._value(row.title)}`;
      dialog.querySelector(".warning").textContent = `${this._t("sessionId")}: ${row.session_id}`;
    }
    dialog.querySelector(".cancel").textContent = this._t("cancel"); dialog.querySelector(".confirm").textContent = this._t("confirm"); dialog.showModal();
  }
  async _execute() {
    const pending = this._pending;
    if (!pending || this._busy) return;
    this._pending = null; this.shadowRoot.querySelector("dialog").close(); this._busy = true;
    this._notice(this._t("stopping")); this._render();
    try {
      if (pending.row.source_id) {
        await this._hass.callService("dispatcharr", "stop_media_session", {config_entry_id: pending.entry, source_id: pending.row.source_id, session_id: pending.row.session_id, item_id: pending.row.item_id});
      } else {
        const data = { config_entry_id: pending.entry, channel_uuid: pending.row.channel_uuid };
        if (pending.all) data.confirm_all = true; else data.client_id = pending.row.client_id;
        await this._hass.callService("dispatcharr", pending.all ? "stop_channel" : "stop_session", data);
      }
      this._notice(this._t("stopped"));
    } catch (error) { this._notice(error?.message || String(error), true); }
    finally { this._busy = false; this._render(); }
  }
}

class DispatcharrCardEditor extends HTMLElement {
  constructor() { super(); this.attachShadow({ mode: "open" }); }
  setConfig(config) { this._config = cardConfig(config); this._render(); }
  set hass(hass) { this._hass = hass; this._render(); }
  _render() {
    if (!this._hass || !this._config) return;
    if (!this._form) {
      this._form = document.createElement("ha-form");
      this._form.addEventListener("value-changed", event => {
        event.stopPropagation(); this._config = cardConfig({ ...this._config, ...event.detail.value }); this._render();
        this.dispatchEvent(new CustomEvent("config-changed", { detail: { config: this._config }, bubbles: true, composed: true }));
      }); this.shadowRoot.append(this._form);
    }
    const m = messages[language(this._hass)];
    this._form.hass = this._hass; this._form.data = this._config;
    this._form.schema = [
      { name: "entity", required: true, selector: { select: { options: candidates(this._hass).map(s => ({ value: s.entity_id, label: s.attributes.friendly_name || s.entity_id })), mode: "dropdown" } } },
      { name: "title", selector: { text: {} } },
      { name: "language", selector: { select: { options: [{ value: "auto", label: m.auto }, { value: "en", label: "English" }, { value: "de", label: "Deutsch" }], mode: "dropdown" } } },
      { name: "layout", selector: { select: { options: ["grid", "list", "tiles"].map(value => ({ value, label: m[value] })), mode: "dropdown" } } },
      ...(this._config.layout === "list" ? [] : [{ name: "columns", selector: { select: { options: [{ value: "auto", label: m.automatic }, ...["1", "2", "3"].map(value => ({ value, label: value }))], mode: "dropdown" } } }]),
      { name: "compact", selector: { boolean: {} } },
      { name: "show_quality", selector: { boolean: {} } },
      { name: "show_progress", selector: { boolean: {} } },
      { name: "show_controls", selector: { boolean: {} } },
    ];
    this._form.computeLabel = ({ name }) => ({ entity: m.entity, title: m.cardTitle, language: m.language, layout: m.layout, columns: m.columns, compact: m.spacing, show_quality: m.showQuality, show_progress: m.showProgress, show_controls: m.controls }[name]);
    this._form.computeHelper = ({ name }) => name === "layout" ? m.layoutHint : undefined;
  }
}
if (!customElements.get("dispatcharr-card")) customElements.define("dispatcharr-card", DispatcharrCard);
if (!customElements.get("dispatcharr-card-editor")) customElements.define("dispatcharr-card-editor", DispatcharrCardEditor);
window.customCards = window.customCards || [];
if (!window.customCards.some(c => c.type === "dispatcharr-card")) window.customCards.push({ type: "dispatcharr-card", name: "Dispatcharr", description: "Live viewers, channel logos and session controls. English / Deutsch.", preview: true });
