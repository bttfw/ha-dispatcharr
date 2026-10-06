# Changelog

## 0.2.0 — 2026-10-06

- Release concurrent Dispatcharr, Jellyfin, Emby and Plex monitoring on `main`.
  Optional media servers are available in the regular HACS release and GUI.
- Preserve existing Dispatcharr entities, configured beta media servers, aliases,
  controls and dashboards when upgrading from 0.1.x or 0.2.0b1.
- Remove the beta label from media-server options and publish English/German
  setup guides for the regular release.
- Keep the verified behavior of 0.2.0b1: shared polling, isolated source failures,
  actual user/device IDs, artwork, progress and available source/output quality.
- Retain the documented client/API control limits: the tested Emby web client
  ignored its native stop, and Plex denied native termination with a valid token.
  Ambiguous Plex stop IDs remain disabled; no replacement stop action is used.
- Validate with 84 backend tests, Chromium card checks, Ruff, hassfest and HACS.
  The beta was also installed in production HA with Dispatcharr and Jellyfin
  connected, actual playback visible, and desktop/mobile checks passing.

## 0.2.0b1 — 2026-10-06 (prerelease)

- Add optional Jellyfin, Emby and Plex connections through bilingual GUI options.
  All sources run concurrently, including independent movie/episode playback.
- Keep per-source failures and last-success times separate, including when
  Dispatcharr is unavailable during startup. Preserve existing entities and cards.
- Display actual media users/devices, playback progress, available artwork and
  source/output quality, with device aliases scoped to server and device IDs.
- Add administrator-only native media-session controls with independent opt-in,
  current-item checks, status verification and no replacement stop actions.
- Preserve separate Plex playback rows when termination IDs overlap; disable
  ambiguous actions. Handle Plex termination-feature denial with a valid token.
- Test concurrent sources, metadata gaps, invalid keys, outages, recovery, exact
  targeting, duplicate Plex IDs, aliases and the real HA configuration interface.
- Document successful isolated Jellyfin stop tests and current Emby/Plex control
  limitations. Publish only as an opt-in beta, keeping stable 0.1.3 unchanged.

## 0.1.3 — 2026-10-06

- Fixed the dashboard's "Custom element doesn't exist: dispatcharr-card" error
  when an existing browser or companion-app session did not load the extra module.
- Automatically register the card as a Lovelace JavaScript module, update its
  versioned URL, and remove duplicate entries for this bundled card only.
- Preserve YAML-managed resources and use the extra-module fallback in that mode.
- Test initial registration, upgrades, repeated/multiple-instance setup and
  preservation of unrelated resources.

## 0.1.2 — 2026-10-06

- Refreshed theme-aware card with larger logos, clear viewer identities, source
  quality chips and two columns when the card has enough space.
- Visual card-language selection: follow Home Assistant, English or German.
- Translated identity labels, localized numbers and explicit documentation links.
- Original bundled brand icons and light/dark logos for Home Assistant and HACS.
- Chromium regression checks for language changes, mobile/wide layouts, missing
  data and exact-client versus whole-channel confirmations.
- Full HACS validation with no ignored brand check.

No changes to backend polling or session-control semantics.

## 0.1.1 — 2026-10-06

- English README and HACS description, with a separate German guide.
- English dashboard preview using synthetic data.
- Test, release, MIT license and AI-assisted badges.
- Explicit Codex development disclosure, English transparency notice and PR template.
- Production HACS installation and dashboard display verified; no real client stopped.

No functional changes to session control or polling.

## 0.1.0 — 2026-10-06

Initial independent implementation, based on official Home Assistant developer
documentation and the verified Dispatcharr 0.31.0 API.

### Added

- HACS installation layout and bundled dashboard card with visual editor.
- GUI setup with URL and API key, reconfiguration, reauthentication, advanced
  options, multiple instances and observed-device aliases.
- Stable connectivity, last-success, channel-count and viewer-count entities.
- Viewer rows with actual user/client IDs, cached logos, current EPG/progress,
  measured source fields and expandable provider/profile details.
- Disabled-by-default controls, administrator enforcement, exact-client stops
  and a separate explicitly confirmed whole-channel stop.
- Full details for truncated client lists, fresh preflight checks, status
  verification after actions and explicit stale-session handling.
- Coordinated asynchronous polling, separate metadata/EPG caches, bounded
  authenticated logo cache, credential-safe errors and minimal diagnostics.
- German/English UI, theme support and mobile layout.
- API, lifecycle, permission, outage/recovery and configuration tests;
  HACS, hassfest and code checks in GitHub Actions.

### Limitations

- Live TV through Dispatcharr's TS proxy only; no VOD/DVR or direct playback.
- Actual device play/pause state is unavailable in the verified API.
- Measurements describe the source, not client-transcoded output.
- No real client termination without an explicitly authorized test session.
  Isolated synthetic client and channel stops are tested.
