# Jellyfin, Emby and Plex

[Deutsch](media-servers.de.md) · [Validation evidence](validation.md)

Version **0.2.0** includes optional Jellyfin, Emby and Plex servers in the existing
Dispatcharr card. Stable releases are published from `main`; future prereleases
use `beta`. The project name, domain and existing entity IDs remain unchanged.

![Concurrent sources using synthetic demo data](screenshots/desktop-en.png)

## Install and configure without YAML

1. Add this repository to HACS as described in the main README.
2. Install or update **Dispatcharr** to **v0.2.0** in HACS. When upgrading from
   0.2.0b1, choose **menu → Redownload → Need a different version? → Release →
   v0.2.0** if HACS still has the prerelease selected.
3. Restart Home Assistant and reload the dashboard once.
4. Open **Settings → Devices & services → Dispatcharr → Configure → Media
   servers → Add server**.
5. Select Jellyfin, Emby or Plex, then enter its URL and API key/token. The display
   name is optional. The integration validates server identity and session access.
6. Repeat for other servers. Multiple instances of the same type are supported.
   Your existing Dispatcharr card automatically includes the additional sessions.

Existing 0.2.0b1 server connections, aliases, control choices and dashboards are
preserved; do not remove and re-add the integration to upgrade.

Use **Media servers → Edit or remove server** to change a connection.
An empty key field during editing keeps the saved key. Removing a connection does
not stop playback or delete anything on the media server.

For Jellyfin and Emby, create an administrator API key in the server's dashboard.
For Plex, use the owner's **X-Plex-Token** for a server linked to that account.
A short-lived Plex *claim token* sets up a server; it is not the integration's
API credential. Never paste credentials into issues, screenshots or card settings.

## What the card shows

- Independent source status and counts; expand **Server** below the card for each
  server's last successful update.
- Dispatcharr channels and proxy clients stay separate from media sessions.
  These count connections, not unique people. A media player consuming Dispatcharr
  may appear in both sources; names or IP addresses do not cause automatic merging.
- Actual server user/device IDs, reported names, title, series/episode details,
  playback state, progress and available artwork.
- Source quality stays separate from reported transcoded output. Missing fields
  remain unknown; a frame-rate label or a title is not a measurement.
- **Configure → Device aliases** also offers observed media devices. Their aliases
  use the configured source and its actual device ID.

Only active playback is listed. Merely signing into a server does not count as
watching. An unavailable source does not hide healthy sources or leave its old
sessions looking live. A separate `Media sessions` sensor provides normalized
attributes; existing Dispatcharr sensors keep their original meaning.

## Controls and current limits

Controls require the integration's **Enable controls** switch, the individual
server's **Allow stop actions** option, and an HA administrator. Confirm the
selected session in the card. Before sending a command, the backend rechecks the
actual session and current item IDs, then queries the resulting state. It never
substitutes a channel stop or a server/container stop.

- **Jellyfin:** two real test browsers played an owned generated clip; ending one
  through the HA card stopped exactly that player while the other continued.
- **Emby 4.10.1.0 web client:** monitoring worked, but the tested browser ignored a
  delivered native stop command. The integration correctly reported the stop as
  unconfirmed. Remote control depends on the client honoring the server command.
- **Plex 1.43.4:** monitoring was verified with two controlled player sessions.
  PMS can return different `sessionKey` values with the same termination
  `Session.id`; both rows remain visible and their ambiguous stop actions are
  disabled. The isolated server also returned HTTP 401 for its native termination
  feature with a valid token. The integration reports denied controls, not success
  or a request to replace an otherwise valid key.

The regular release retains these client/API limits; it does not claim that
every client can be forcibly stopped.
Dispatcharr's exact-client and separate whole-channel actions remain unchanged.

## API and implementation

Each configured instance uses shared async coordinators, with one session request
per media server and poll interval. Requests run concurrently and failures are
isolated by source. Existing Dispatcharr metadata/EPG caching remains separate.
Artwork is requested lazily through an authenticated HA backend route and a bounded
cache. No integration feature starts playback. Credentials never enter card
configuration, state attributes, image URLs or diagnostics.

Contracts were checked against the live Jellyfin 12.1.0 OpenAPI schema, the
[Emby session API](https://dev.emby.media/reference/RestAPI/SessionsService.html),
and the [official Plex Media Server API](https://developer.plex.tv/pms/).
The live environment and control-test limits are recorded in the validation report.
