# Changelog

## Unreleased

- Remove the always-visible source/count explanation, disabled/admin control hints
  and duplicate update time from the dashboard footer in every layout.
- Keep connection status and last successful update under the expandable Server
  section for Dispatcharr and all optional media servers, including outages and
  Dispatcharr-only setups. Preserve its expanded state during updates.
- Retain actual metadata warnings and existing control permissions. Refresh the
  English/German desktop and phone screenshots and server-detail guide images.
- Require meaningful English changelog entries and matching GitHub release notes
  for every future release in the contributor instructions.

## 0.3.0 — 2026-10-06

- Add Grid, Compact list and Logo tiles to the English/German visual card editor.
- Configure responsive maximum columns, compact spacing and independent source
  quality and EPG/playback progress visibility per card, without YAML.
- Keep grouped channels and exact-session actions in every layout; list/tile
  details expand without losing their state during updates. Existing cards retain
  the grid layout and legacy compact cards retain their hidden quality panel.
- Fit portrait artwork inside its container without clipping.
- Add layout regression coverage and native HA editor checks. Refresh desktop,
  phone and editor screenshots and publish illustrated English/German layout guides.

## 0.2.1 — 2026-10-06

- Refresh English/German desktop and mobile dashboard screenshots for grouped
  channels, including viewer/DVR connections and empty, offline and missing-data
  states.
- Group Dispatcharr connections by channel UUID in the dashboard: show the logo,
  current programme and source quality once, with individual client rows below.
- Identify reported Dispatcharr DVR clients, retain separate connection durations,
  output profiles and exact-client actions, and warn that channel stops include DVR.
- Preserve expanded connection details across status updates. Keep separate
  channels with identical names and unrelated media-server sessions distinct.
- Update test tooling to pytest 9.1.1, pytest-asyncio 1.4.0,
  pytest-aiohttp 1.1.1 and Ruff 0.16.10, and use actions/checkout v7 in CI.
- Address GHSA-6w46-j5rx-g56g (CVE-2025-71176) in the pytest development
  dependency. These test packages are not installed by the integration in HA.
- Add weekly Dependabot version-update PRs targeting `beta`, plus security alerts
  and security-update PRs targeting `main`. Updates still require review and checks.
- Add English and German setup walkthroughs with native Home Assistant screenshots:
  initial Dispatcharr connection, optional media-server credentials and dashboard card.
- Explain the Configure gear, the card picker's By card tab, frontend reloads after
  initial setup, and the separate HACS 2.0.5 missing-brand-icon issue.

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
