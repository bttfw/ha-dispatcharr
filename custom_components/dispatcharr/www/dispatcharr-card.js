/* Independent Dispatcharr card. No external libraries, playback or credentials. */
const messages = {
  de: {
    title: "Dispatcharr", viewers: "Zuschauer", channels: "Aktive Kanäle", online: "Verbunden", offline: "Verbindung unterbrochen",
    empty: "Niemand schaut gerade", emptyHint: "Neue Verbindungen erscheinen automatisch.", unknown: "Unbekannt", noEpg: "Keine aktuellen EPG-Daten",
    noLogo: "Kein Logo", last: "Zuletzt aktualisiert", details: "Details", provider: "Provider", providerProfile: "Provider-Profil",
    streamProfile: "Stream-Profil", outputProfile: "Ausgabeprofil", format: "Ausgabeformat", quality: "Quelle", bitrate: "Ø Datenrate",
    stop: "Session beenden", stopAll: "Kanal für alle beenden", confirm: "Beenden", cancel: "Abbrechen", disabled: "Steuerung ist ausgeschaltet",
    singleConfirm: "Nur diese Client-Session beenden?", allConfirm: "Diesen Kanal für ALLE verbundenen Zuschauer beenden?",
    stopping: "Beenden wird geprüft …", stopped: "Beendet und Status erneut abgefragt.", admin: "Steuerung nur für HA-Administratoren",
    proxy: "Kanal-Proxy", playback: "Wiedergabestatus des Geräts", connected: "Verbunden seit", metadata: "Einige Zusatzdaten sind derzeit nicht verfügbar.",
    entity: "Zuschauer-Sensor", cardTitle: "Titel", compact: "Kompakte Ansicht", controls: "Aktionsschaltflächen anzeigen",
    configure: "Bitte einen Dispatcharr-Zuschauer-Sensor auswählen.", gone: "Die Integration oder der ausgewählte Sensor ist nicht verfügbar.",
    allWarning: "Dies betrifft alle Zuschauer dieses Kanals, auch inzwischen hinzugekommene.", connection: "Verbindung",
  },
  en: {
    title: "Dispatcharr", viewers: "Viewers", channels: "Active channels", online: "Connected", offline: "Connection lost",
    empty: "Nobody is watching", emptyHint: "New connections appear automatically.", unknown: "Unknown", noEpg: "No current EPG data",
    noLogo: "No logo", last: "Last updated", details: "Details", provider: "Provider", providerProfile: "Provider profile",
    streamProfile: "Stream profile", outputProfile: "Output profile", format: "Output format", quality: "Source", bitrate: "Avg. data rate",
    stop: "End session", stopAll: "Stop channel for everyone", confirm: "Stop", cancel: "Cancel", disabled: "Controls are disabled",
    singleConfirm: "End only this client session?", allConfirm: "Stop this channel for ALL connected viewers?",
    stopping: "Checking stop …", stopped: "Stopped and actual status refreshed.", admin: "Controls require an HA administrator",
    proxy: "Channel proxy", playback: "Device playback state", connected: "Connected for", metadata: "Some additional data is currently unavailable.",
    entity: "Viewer sensor", cardTitle: "Title", compact: "Compact view", controls: "Show action buttons",
    configure: "Select a Dispatcharr viewer sensor.", gone: "The integration or selected sensor is unavailable.",
    allWarning: "This affects all viewers of this channel, including viewers who connected meanwhile.", connection: "Connection",
  },
};
const el = (tag, text, cls) => {
  const node = document.createElement(tag);
  if (text !== undefined && text !== null) node.textContent = String(text);
  if (cls) node.className = cls;
  return node;
};
const language = (hass) => hass?.language?.startsWith("de") ? "de" : "en";
const candidates = (hass) => Object.values(hass?.states || {}).filter(s => s.entity_id.startsWith("sensor.") && s.attributes.entry_id && Array.isArray(s.attributes.viewers));
const duration = (seconds) => {
  const s = Math.max(0, Math.floor(seconds));
  return s >= 3600 ? `${Math.floor(s / 3600)}h ${Math.floor((s % 3600) / 60)}m` : `${Math.floor(s / 60)}m ${s % 60}s`;
};

class DispatcharrCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._logos = new Map();
    this._details = new Set();
    this.shadowRoot.innerHTML = `<style>
      :host{display:block;color:var(--primary-text-color);font-family:var(--paper-font-body1_-_font-family,inherit)}
      ha-card{overflow:hidden;background:var(--ha-card-background,var(--card-background-color));border-radius:var(--ha-card-border-radius,12px)}
      .body{padding:20px}h2{font-size:20px;font-weight:500;margin:0}header{display:flex;gap:12px;justify-content:space-between;align-items:center;flex-wrap:wrap}
      .status,.muted,.time{color:var(--secondary-text-color);font-size:13px}.status{display:flex;align-items:center;gap:7px}.dot{width:8px;height:8px;background:var(--success-color,#43a047);border-radius:50%}
      .offline .dot{background:var(--error-color,#db4437)}.stats{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin:20px 0 16px}.stat{padding:12px 16px;border:1px solid var(--divider-color);border-radius:12px}.stat strong{display:block;font-size:28px;font-weight:500;margin-bottom:3px}.stat span{font-size:13px;color:var(--secondary-text-color)}
      .list{display:grid;gap:12px}.viewer{border:1px solid var(--divider-color);border-radius:12px;padding:16px;min-width:0}.identity{display:flex;gap:12px;align-items:center}.logo{width:52px;height:52px;flex:0 0 52px;background:var(--secondary-background-color);border-radius:10px;display:grid;place-items:center;overflow:hidden;text-align:center;font-size:10px;color:var(--secondary-text-color)}
      .logo img{width:44px;height:44px;object-fit:contain}.who{min-width:0;flex:1}.who strong,.channel{display:block;overflow-wrap:anywhere}.channel{margin-top:3px;color:var(--secondary-text-color);font-size:14px}.time{margin-top:7px}
      .programme{margin-top:14px;font-size:14px;overflow-wrap:anywhere}.programme-title{font-weight:500}.programme-line{display:flex;justify-content:space-between;gap:8px;margin:7px 0;font-size:12px;color:var(--secondary-text-color)}progress{display:block;width:100%;height:5px;accent-color:var(--primary-color);border:0;border-radius:8px;overflow:hidden}progress::-webkit-progress-bar{background:var(--divider-color)}progress::-webkit-progress-value{background:var(--primary-color)}
      .quality{font-size:12px;color:var(--secondary-text-color);margin-top:12px;line-height:1.7}.actions{display:flex;gap:8px;flex-wrap:wrap;margin-top:12px}button{font:inherit;cursor:pointer;min-height:44px;border:1px solid var(--divider-color);border-radius:8px;padding:8px 12px;background:transparent;color:var(--primary-color)}button:hover{background:var(--secondary-background-color)}button:focus-visible,summary:focus-visible{outline:2px solid var(--primary-color);outline-offset:3px}button:disabled{opacity:.5;cursor:default}.danger{color:var(--error-color,#db4437)}
      details{margin-top:12px;font-size:13px}summary{cursor:pointer;color:var(--primary-color);min-height:32px;line-height:32px}dl{display:grid;grid-template-columns:minmax(90px,1fr) minmax(0,1.5fr);gap:8px;margin:8px 0}dt{color:var(--secondary-text-color)}dd{margin:0;overflow-wrap:anywhere}
      .empty{text-align:center;padding:32px 12px}.empty ha-icon{--mdc-icon-size:36px;color:var(--secondary-text-color);margin-bottom:12px}.empty strong{display:block;font-weight:500;margin-bottom:8px}.footer{margin-top:16px;font-size:12px;color:var(--secondary-text-color);line-height:1.8}.notice{padding:0 20px 16px;font-size:14px;overflow-wrap:anywhere}.notice:empty{display:none}.notice.error{color:var(--error-color,#db4437)}
      dialog{border:1px solid var(--divider-color);border-radius:16px;color:var(--primary-text-color);background:var(--card-background-color,#fff);padding:24px;max-width:min(440px,calc(100vw - 64px));box-shadow:0 8px 36px #0004}dialog::backdrop{background:#0007}dialog h3{margin-top:0;font-size:18px}dialog p{overflow-wrap:anywhere;line-height:1.5}.dialog-actions{display:flex;justify-content:flex-end;gap:12px;margin-top:20px}
      .compact .viewer{padding:12px}.compact .quality{display:none}@media(max-width:420px){.body{padding:16px}.stat{padding:10px 12px}.viewer{padding:12px}.logo{width:44px;height:44px;flex-basis:44px}.logo img{width:38px;height:38px}h2{font-size:18px}}
    </style><ha-card><div class="body"></div><div class="notice" role="status" aria-live="polite"></div></ha-card><dialog aria-labelledby="confirm-title"><h3 id="confirm-title"></h3><p class="target"></p><p class="warning"></p><div class="dialog-actions"><button class="cancel"></button><button class="confirm danger"></button></div></dialog>`;
    this.shadowRoot.querySelector(".cancel").onclick = () => this.shadowRoot.querySelector("dialog").close();
    this.shadowRoot.querySelector(".confirm").onclick = () => this._execute();
  }
  static getConfigElement() { return document.createElement("dispatcharr-card-editor"); }
  static getStubConfig(hass) { return { entity: candidates(hass)[0]?.entity_id || "", show_controls: true }; }
  setConfig(config) { this._config = { title: "Dispatcharr", compact: false, show_controls: true, ...config }; this._render(); }
  set hass(hass) {
    const previous = this._hass;
    this._hass = hass;
    const id = this._config?.entity;
    if (!previous || previous.states[id] !== hass.states[id] || previous.language !== hass.language || previous.user !== hass.user) this._render();
  }
  getCardSize() { return 3 + Math.min(this._state()?.attributes.viewers?.length || 0, 10) * 3; }
  getGridOptions() { return { columns: 12, min_columns: 6, rows: "auto" }; }
  connectedCallback() { this._timer = window.setInterval(() => this._tick(), 1000); this._render(); }
  disconnectedCallback() {
    clearInterval(this._timer);
    for (const item of this._logos.values()) if (item.url) URL.revokeObjectURL(item.url);
    this._logos.clear();
  }
  _state() { return this._hass?.states[this._config?.entity]; }
  _t(key) { return messages[language(this._hass)][key] || key; }
  _value(value) { return value === null || value === undefined || value === "" ? this._t("unknown") : String(value); }
  _notice(text, error = false) {
    const node = this.shadowRoot.querySelector(".notice"); node.textContent = text; node.classList.toggle("error", error);
    node.setAttribute("role", error ? "alert" : "status");
  }
  _render() {
    if (!this._config || !this._hass) return;
    const body = this.shadowRoot.querySelector(".body");
    body.classList.toggle("compact", Boolean(this._config.compact));
    body.replaceChildren();
    const state = this._state();
    const live = state && !["unavailable", "unknown"].includes(state.state);
    const data = state?.attributes || {};
    const header = el("header"); header.append(el("h2", this._config.title || this._t("title")));
    const status = el("span", null, live ? "status" : "status offline"); status.append(el("i", null, "dot"), el("span", this._t(live ? "online" : "offline"))); header.append(status); body.append(header);
    if (!state || !live) {
      body.append(el("p", this._t(!this._config.entity ? "configure" : !state ? "gone" : "offline"), "empty"));
      if (data.last_success) body.append(el("div", `${this._t("last")}: ${new Date(data.last_success).toLocaleString(this._hass.language)}`, "footer"));
      return;
    }
    const stats = el("div", null, "stats");
    for (const [key, value] of [["channels", data.active_channels], ["viewers", state.state]]) {
      const stat = el("div", null, "stat"); stat.append(el("strong", this._value(value)), el("span", this._t(key))); stats.append(stat);
    }
    body.append(stats);
    const rows = data.viewers || [];
    const list = el("div", null, "list");
    if (!rows.length) {
      const empty = el("div", null, "empty"), icon = el("ha-icon"); icon.setAttribute("icon", "mdi:television-off");
      empty.append(icon, el("strong", this._t("empty")), el("span", this._t("emptyHint"), "muted")); list.append(empty);
    }
    for (const row of rows) list.append(this._viewer(row, data));
    body.append(list);
    const footer = el("div", null, "footer");
    if (data.warnings?.length) footer.append(el("div", this._t("metadata")));
    if (!data.control_enabled) footer.append(el("div", this._t("disabled")));
    else if (!this._hass.user?.is_admin) footer.append(el("div", this._t("admin")));
    footer.append(el("div", `${this._t("last")}: ${data.last_success ? new Date(data.last_success).toLocaleTimeString(this._hass.language) : this._t("unknown")}`)); body.append(footer);
    const needed = new Set(rows.filter(r => r.logo_id).map(r => `${data.entry_id}/${r.logo_id}`));
    for (const [key, value] of this._logos) if (!needed.has(key)) { if (value.url) URL.revokeObjectURL(value.url); this._logos.delete(key); }
    this._tick();
  }
  _viewer(row, data) {
    const node = el("article", null, "viewer");
    const identity = el("div", null, "identity");
    const logo = el("div", this._t("noLogo"), "logo");
    if (Number.isInteger(row.logo_id) && row.logo_id > 0) this._logo(logo, data.entry_id, row.logo_id);
    const who = el("div", null, "who");
    who.append(el("strong", this._value(row.device_alias || row.username || row.device_description)), el("span", this._value(row.channel_name), "channel"));
    if (row.device_alias && row.username) who.append(el("span", row.username, "muted"));
    const time = el("div", null, "time");
    time.append(el("span", `${this._t("connected")}: `));
    const elapsed = el("span", this._t("unknown"));
    if (row.connected_at) elapsed.dataset.since = String(row.connected_at);
    time.append(elapsed); who.append(time); identity.append(logo, who); node.append(identity);
    const programme = el("div", null, "programme");
    if (row.programme && row.programme.end * 1000 > Date.now()) {
      const title = el("div", this._value(row.programme.title), "programme-title"); programme.append(title);
      const line = el("div", null, "programme-line");
      const fmt = (stamp) => new Date(stamp * 1000).toLocaleTimeString(this._hass.language, { hour: "2-digit", minute: "2-digit" });
      line.append(el("span", `${fmt(row.programme.start)} – ${fmt(row.programme.end)}`));
      const percent = el("span"); line.append(percent); programme.append(line);
      const progress = el("progress"); progress.max = 100; progress.dataset.start = row.programme.start; progress.dataset.end = row.programme.end;
      progress.setAttribute("aria-label", this._value(row.programme.title)); programme.append(progress);
    } else programme.append(el("span", this._t("noEpg"), "muted"));
    node.append(programme);
    const qualities = [this._value(row.source_resolution), row.source_fps != null ? `${row.source_fps} fps` : this._t("unknown"), this._value(row.video_codec), this._value(row.audio_codec)];
    node.append(el("div", `${this._t("quality")}: ${qualities.join(" · ")}\n${this._t("bitrate")}: ${row.average_bitrate_kbps != null ? `${(row.average_bitrate_kbps / 1000).toFixed(2)} Mbit/s` : this._t("unknown")}`, "quality"));
    const details = el("details"); const rowKey = `${row.channel_uuid}/${row.client_id}`;
    details.open = this._details.has(rowKey); details.ontoggle = () => details.open ? this._details.add(rowKey) : this._details.delete(rowKey);
    details.append(el("summary", this._t("details")));
    const dl = el("dl");
    for (const [key, value] of [["provider", row.provider], ["providerProfile", row.provider_profile], ["streamProfile", row.stream_profile], ["outputProfile", row.output_profile], ["format", row.output_format], ["proxy", row.proxy_state], ["playback", row.playback_status]]) dl.append(el("dt", this._t(key)), el("dd", this._value(value)));
    dl.append(el("dt", "Dispatcharr User ID"), el("dd", this._value(row.user_id)), el("dt", "Client ID"), el("dd", row.client_id)); details.append(dl); node.append(details);
    if (this._config.show_controls && data.control_enabled && this._hass.user?.is_admin) {
      const actions = el("div", null, "actions"), stop = el("button", this._t("stop"));
      stop.disabled = Boolean(this._busy); stop.onclick = () => this._ask(row, data.entry_id, false); actions.append(stop); node.append(actions);
      const all = el("button", this._t("stopAll"), "danger"); all.disabled = Boolean(this._busy); all.onclick = () => this._ask(row, data.entry_id, true); details.append(all);
    }
    return node;
  }
  async _logo(node, entry, id) {
    const key = `${entry}/${id}`;
    let cached = this._logos.get(key);
    if (!cached) {
      cached = {}; this._logos.set(key, cached);
      cached.promise = (async () => {
        try {
          const response = await this._hass.fetchWithAuth(`/api/dispatcharr/logo/${encodeURIComponent(entry)}/${id}`);
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
      const start = Number(progress.dataset.start), end = Number(progress.dataset.end);
      if (now >= end) { progress.closest(".programme").replaceChildren(el("span", this._t("noEpg"), "muted")); continue; }
      progress.value = Math.min(100, Math.max(0, (now - start) / (end - start) * 100));
      progress.previousElementSibling.lastElementChild.textContent = `${Math.floor(progress.value)} %`;
    }
  }
  _ask(row, entry, all) {
    this._pending = { row, entry, all };
    const dialog = this.shadowRoot.querySelector("dialog");
    dialog.querySelector("h3").textContent = this._t(all ? "allConfirm" : "singleConfirm");
    dialog.querySelector(".target").textContent = `${this._value(row.channel_name)} · ${all ? this._t("viewers") : this._value(row.device_alias || row.username || row.device_description)}`;
    dialog.querySelector(".warning").textContent = all ? this._t("allWarning") : `Client ID: ${row.client_id}`;
    dialog.querySelector(".cancel").textContent = this._t("cancel"); dialog.querySelector(".confirm").textContent = this._t("confirm"); dialog.showModal();
  }
  async _execute() {
    const pending = this._pending;
    if (!pending || this._busy) return;
    this._pending = null; this.shadowRoot.querySelector("dialog").close(); this._busy = true;
    this._notice(this._t("stopping")); this._render();
    try {
      const data = { config_entry_id: pending.entry, channel_uuid: pending.row.channel_uuid };
      if (pending.all) data.confirm_all = true; else data.client_id = pending.row.client_id;
      await this._hass.callService("dispatcharr", pending.all ? "stop_channel" : "stop_session", data);
      this._notice(this._t("stopped"));
    } catch (error) { this._notice(error?.message || String(error), true); }
    finally { this._busy = false; this._render(); }
  }
}

class DispatcharrCardEditor extends HTMLElement {
  constructor() { super(); this.attachShadow({ mode: "open" }); }
  setConfig(config) { this._config = { ...config }; this._render(); }
  set hass(hass) { this._hass = hass; this._render(); }
  _render() {
    if (!this._hass || !this._config) return;
    if (!this._form) {
      this._form = document.createElement("ha-form");
      this._form.addEventListener("value-changed", event => {
        event.stopPropagation(); this._config = { ...this._config, ...event.detail.value };
        this.dispatchEvent(new CustomEvent("config-changed", { detail: { config: this._config }, bubbles: true, composed: true }));
      }); this.shadowRoot.append(this._form);
    }
    const m = messages[language(this._hass)];
    this._form.hass = this._hass; this._form.data = this._config;
    this._form.schema = [
      { name: "entity", required: true, selector: { select: { options: candidates(this._hass).map(s => ({ value: s.entity_id, label: s.attributes.friendly_name || s.entity_id })), mode: "dropdown" } } },
      { name: "title", selector: { text: {} } },
      { name: "compact", selector: { boolean: {} } },
      { name: "show_controls", selector: { boolean: {} } },
    ];
    this._form.computeLabel = ({ name }) => ({ entity: m.entity, title: m.cardTitle, compact: m.compact, show_controls: m.controls }[name]);
  }
}
if (!customElements.get("dispatcharr-card")) customElements.define("dispatcharr-card", DispatcharrCard);
if (!customElements.get("dispatcharr-card-editor")) customElements.define("dispatcharr-card-editor", DispatcharrCardEditor);
window.customCards = window.customCards || [];
if (!window.customCards.some(c => c.type === "dispatcharr-card")) window.customCards.push({ type: "dispatcharr-card", name: "Dispatcharr", description: "Live viewers, channel logos and safe session controls / Live-Zuschauer und Senderlogos", preview: true });
