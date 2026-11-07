# Count streams from all configured servers

[Deutsch](stream-counter.de.md)

From **0.4.1**, each integration instance creates a **Total streams** sensor.
It adds Dispatcharr client connections to the sessions reported by its configured
Jellyfin, Plex and Emby servers. For example, one Dispatcharr client plus one
Jellyfin session gives **2**. Two clients sharing a channel plus that same Jellyfin
session give **3**, while **Active channels** remains **1**.

The existing **Viewers** sensor remains Dispatcharr-only. **Media sessions**
remains the combined media-server count. The three separate card counters retain
their meanings. Card display filters do not change the total sensor.

## Select the total in a dashboard badge

1. Update Dispatcharr to **v0.4.1** in HACS and restart Home Assistant.
2. Open your dashboard and select **Edit dashboard**.
3. Edit the existing Streams badge and change its **Entity** to the Dispatcharr
   instance's **Total streams** sensor. Keep your preferred badge name and icon.
4. Save the badge and finish editing. To add a new badge, choose **Add badge →
   Entity** and select the same sensor.

The sensor is also available under **Settings → Devices & services → Dispatcharr →
the instance's device** and in the ordinary entity picker. Entity IDs depend on
the instance name and HA language; select the entity by its displayed name.
The integration does not rewrite existing dashboards automatically.

## What is counted

- Each reported Dispatcharr client, including DVR, and each media-server session,
  including a session reported as paused, contributes one connection.
- Independent servers are added together. Names, titles, IP addresses and session
  IDs from different servers are not used to infer that two connections are the
  same person or playback. A media server using Dispatcharr as its upstream may
  therefore report connections on both sides; this is not a unique-viewer metric.
- Updates follow both existing coordinators. The sensor does not start playback,
  download extra EPG data or add polling requests.
- During an outage, the state is the known subtotal from reachable sources.
  Attributes `complete: false` and `unavailable_sources` identify partial results;
  unavailable source counts are unknown, never reused from stale data. If all
  sources are unavailable, the sensor is unavailable. Zero is reported only when
  at least one source has successfully reported no connections.

The breakdown attributes are `dispatcharr_clients` and `media_sessions`; no
viewer names, stream URLs or credentials are attached to this summary sensor.
