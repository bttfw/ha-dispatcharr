# Architecture and verified API contract

Design presented before implementation on 2026-10-05. Independent repository,
implementation, and architecture. The original 0.1.x scope was Dispatcharr.
Version 0.2.0 adds optional concurrent Jellyfin, Emby and Plex sources; see the
[media-server API and architecture](media-servers.md#api-and-implementation).
The Dispatcharr contracts below remain unchanged.

## Evidence

Live read-only verification: Home Assistant **2026.9.4**, HACS installed,
Dispatcharr **0.31.0**. Valid API key: HTTP 200. Deliberately invalid key:
HTTP 401. No active channels during initial inspection. No stream was opened
and no client or channel was stopped by these checks.

Official Dispatcharr tag `v0.31.0`, commit
`bcbb68c4f054ee56383a41604cfcd7302b85da66` was independently fetched.

| Capability | Verified contract |
| --- | --- |
| Authentication | `X-API-Key` header; `/api/accounts/users/me/` identifies the key owner |
| Authorization | `IsAdmin`: authenticated user with `user_level >= 10` for proxy status and stops |
| Version | `GET /api/core/version/` |
| Active channels | `GET /proxy/ts/status`, object with `channels` and `count` |
| Full channel detail | `GET /proxy/ts/status/{channel_uuid}` |
| Client truncation | Basic status limits `clients` to ten; compare with `client_count` and fetch detail |
| Stop one client | `POST /proxy/ts/stop_client/{channel_uuid}`, body `{"client_id": "actual ID"}` |
| Stop all viewers of a channel | `POST /proxy/ts/stop/{channel_uuid}` |
| Channel metadata | `POST /api/channels/channels/by-uuids/`, body `{"uuids": [...]}` |
| Current EPG only | `POST /api/epg/current-programs/`, body `{"channel_uuids": [...]}` |
| User identity | `user_id` joined to `/api/accounts/users/` by numeric ID |
| Provider | `m3u_profile_id` joined to the nested profiles in `/api/m3u/accounts/` |
| Output profile | `output_profile_id` joined to `/api/core/outputprofiles/` |
| Logos | numeric logo ID via `/api/channels/logos/{id}/cache/` |

Source references:

- [Authentication](https://github.com/Dispatcharr/Dispatcharr/blob/v0.31.0/apps/accounts/authentication.py)
- [Permissions](https://github.com/Dispatcharr/Dispatcharr/blob/v0.31.0/apps/accounts/permissions.py)
- [Proxy views](https://github.com/Dispatcharr/Dispatcharr/blob/v0.31.0/apps/proxy/live_proxy/views.py)
- [Status and truncation](https://github.com/Dispatcharr/Dispatcharr/blob/v0.31.0/apps/proxy/live_proxy/channel_status.py)
- [Stop implementation](https://github.com/Dispatcharr/Dispatcharr/blob/v0.31.0/apps/proxy/live_proxy/services/channel_service.py)
- [Channel metadata](https://github.com/Dispatcharr/Dispatcharr/blob/v0.31.0/apps/channels/api_views.py)
- [Current programmes](https://github.com/Dispatcharr/Dispatcharr/blob/v0.31.0/apps/epg/api_views.py)
- [Official API documentation](https://dispatcharr.github.io/Dispatcharr-Docs/api/)

## Structure

One asynchronous API client and DataUpdateCoordinator per config entry. Stable
entities identify the installation using the HA config entry ID, which survives
URL changes. URLs are used only to prevent duplicate configuration, never as
entity unique IDs. Sessions are transient rows, not permanently registered
entities. Multiple instances have isolated credentials, caches and controls.

Status defaults to 10 seconds. Metadata defaults to 15 minutes; new active
channel UUIDs trigger a targeted fetch. EPG defaults to 60 seconds, restricted
to active channels. Logos are cached in the backend for an hour. No XMLTV,
playlist, stream probe, or playback endpoint is used. Expired EPG is hidden.

Core REST integration was considered: it requires YAML and does not provide
the requested config/options flows or safe session actions. Standard entities
and tile cards support summary counters. They do not directly render a changing
array of viewers with per-row images, programme progress, and ID-bound actions.
Therefore a bundled custom card provides that list with a visual editor; native
entities remain usable in standard cards. No external custom cards are required.

The bundled card is automatically registered in HA's Lovelace resource collection.
Its versioned module URL is updated in place, and duplicates for this exact local
card path are removed. Other resources are preserved. This avoids depending on a
previously cached app shell loading a newly added frontend extra module. YAML-owned
resource collections are left unchanged and use the extra-module fallback.

Setup asks for URL and API key only. Reconfigure and reauthentication are GUI
flows. Options have controls, device aliases and a separate advanced menu.
Aliases identify a user-supplied mapping of observed IP plus User-Agent; this
is not proof of a physical device and can collide behind a shared proxy.

## Control and data safety

Controls default off and require a Home Assistant administrator. Immediately
before a stop, refresh the channel detail and check the actual session ID.
The API can acknowledge an already-expired client; a successful POST is not
proof that it stopped. Re-query actual status, report pending/failed confirmation
accurately, and never substitute a channel stop for a client stop. Channel stop
requires a separate explicit confirmation flag and card confirmation dialog.

Only allowlisted response fields enter HA. Account API responses contain API
keys; these are discarded immediately, along with credentials and upstream URLs.
Diagnostics contain counts, configuration intervals, versions and capabilities,
not config entry data, usernames, client IDs, IPs, aliases or raw API responses.
Logo requests use authenticated HA requests and backend numeric-ID lookup. The
Dispatcharr key never appears in image URLs, browser configuration or logs.
Redirects are rejected so custom authentication headers cannot leave the server.

The UI labels connection state and channel proxy state accurately. Dispatcharr
does not expose trustworthy device pause/play state. Video fields describe the
source channel, not guaranteed output quality after per-client transcoding.
Missing identities, EPG, logos and quality measurements remain unknown.

From 0.2.1, the card groups Dispatcharr client rows by the actual channel UUID
within the selected configuration entry. Channel metadata is rendered once and each
client keeps its own identity, duration, output fields and stop action. Missing
or malformed UUIDs are never grouped together. Media-server sessions remain
separate; names and titles are not cross-server identity keys. This is a frontend
change with no additional API calls or polling changes.

The DVR indicator uses only the exact reported User-Agent format generated by
[`dispatcharr_dvr_user_agent()` in official v0.31.0 core/utils.py](https://github.com/Dispatcharr/Dispatcharr/blob/v0.31.0/core/utils.py).
It labels a reported proxy-client type, not verified recording completion or
ownership. Original device descriptions remain available in connection details.

From 0.3.0, per-card `layout` (`grid`, `list`, `tiles`), `columns` (`auto`, `1`,
`2`, `3`), `compact`, `show_quality` and `show_progress` options are normalized
and exposed in the native visual editor. CSS container queries use the card's
available width, independently of HA's dashboard grid. All layouts share the same
grouping and action handlers. Missing options preserve the previous grid layout;
legacy compact configurations keep quality hidden until explicitly changed.

## Validation and open acceptance item

Automated tests cover shared-channel viewers (including >10), exact client stop,
stale IDs, missing metadata, permissions, malformed responses, outages/recovery,
caching, config flows, reload and multiple instances. Live read-only checks use
the installed Dispatcharr. Live stop tests require explicit authorization for
the particular test sessions and are not silently replaced by stopping users.

HA sources: [Coordinator](https://developers.home-assistant.io/docs/integration_fetching_data/),
[config flow](https://developers.home-assistant.io/docs/config_entries_config_flow_handler/),
[options](https://developers.home-assistant.io/docs/config_entries_options_flow_handler/),
[custom cards/editor](https://developers.home-assistant.io/docs/frontend/custom-ui/custom-card/),
[HACS packaging](https://www.hacs.xyz/docs/publish/integration/).
