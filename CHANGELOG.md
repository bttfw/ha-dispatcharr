# Changelog

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
