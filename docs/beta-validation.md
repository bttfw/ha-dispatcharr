# Media-server validation record — 6 October 2026

These checks were performed on 0.2.0b1. Release 0.2.0 promotes the same runtime
behavior, updates the version and GUI menu label, and publishes current guides.
The release workflow runs the same 84 backend tests and card checks again.

Verified versions: Home Assistant **2026.9.4**, Dispatcharr **0.31.0**,
Jellyfin **12.1.0**, Emby **4.10.1.0**, Plex **1.43.4.10903-e5521bd8c**.
Jellyfin's live OpenAPI schema was inspected. Existing Jellyfin and Dispatcharr
were queried read-only; production libraries and playback were untouched.

## Automated checks

**84 backend tests** passed using real HA classes in its official container on
Unraid. Ruff, JavaScript syntax and the Chromium card suite also passed.

The tests cover independent concurrent sources, identical names and IDs across
servers, missing metadata, invalid keys, redirects, outages/recovery, device
aliases, disabled controls, stale item IDs, exact targeting and unconfirmed stops.
Card checks exercise partial failures, paused progress, source-specific actions,
language selection and mobile/wide layouts with synthetic data.

## Live checks using owned test material

Labelled, isolated test containers used an owned generated video clip. A second
Jellyfin container used the exact image of the existing installation.

- Actual HA options flows added all three server types and two Jellyfin instances.
  German form labels and password inputs were inspected in the frontend.
- Valid credentials worked and deliberately invalid credentials failed for every
  server type.
- Two real Jellyfin browser players played the same clip. A card action stopped
  exactly one; the other continued. The second was then stopped and verified.
- Two real Emby browser players appeared with reported resolution, frame rate and
  codecs. A native stop command reached a browser, but the shipped 4.10.1.0 web
  client did not stop. HA reported the unconfirmed result without a fallback.
- Two controlled Plex protocol clients consumed test media and reported playback
  through the timeline API. Both appeared in HA. The official Plex player UI was
  not tested.
- Those Plex sessions had different sessionKey values but the same Session.id.
  Both rows are now preserved and ambiguous termination is disabled and tested.
- A separate Plex HLS test session received HTTP 401 from the native termination
  endpoint with a valid token. This feature/permission denial is handled explicitly;
  successful live Plex termination is not claimed.
- The live card showed Jellyfin, Emby and Plex playback simultaneously. Dispatcharr
  stayed connected with zero viewers after the owner's real stream ended. No extra
  IPTV playback was started for the test.
- Stopping only the Emby test container marked that source unavailable while the
  other three source types stayed connected. Restarting it restored connectivity.
- Desktop and 390-pixel mobile views rendered the sources without JavaScript
  errors or horizontal overflow.

The [media-server guide](media-servers.md) describes the remaining control limits. No independent
security audit or agent-performed termination of real IPTV playback is claimed.
