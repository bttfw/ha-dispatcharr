# Setup screenshot provenance

Screens `01`–`06` were captured on 2026-10-06 in the real Home Assistant 2026.9.4 frontend with the
unmodified Dispatcharr integration 0.2.0, running in a disposable Docker Desktop
container. Both English and German use Home Assistant's actual translations.

The only connected source was `tests/support/fake_dispatcharr.py` on the test
container's loopback interface. The dashboard images show its empty-session mode.
No real media server, IPTV stream, production credential or private hostname was
used. All credential inputs were checked to be empty before capture. The example
`127.0.0.1:8919` address is a fixture, not an address users should copy.

Images are cropped to the native dialog or integration controls and are kept in
documentation only. No generated UI mockups or altered control labels are used.

Screen `07` was refreshed for 0.3.0 in the real HA frontend, with the candidate
card module loaded only in an isolated browser context. It shows native editor
controls with synthetic entity state and a fictional friendly name. Configuration
events were applied to that fixture only; no production dashboard was modified.

| Prefix | Screen |
| --- | --- |
| `01` | Initial Dispatcharr-only setup |
| `02` | Integration page and Configure gear |
| `03` | Options menu with Media servers |
| `04` | Add/edit media-server menu |
| `05` | Media-server credentials form |
| `06` | Dashboard card picker filtered to Dispatcharr, By card selected |
| `07` | Visual card editor with viewer sensor, layouts, columns and display switches |

The suffix identifies the UI language: `en` or `de`.
