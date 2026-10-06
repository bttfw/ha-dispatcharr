# Setup screenshot provenance

Captured on 2026-10-06 in the real Home Assistant 2026.9.4 frontend with the
unmodified Dispatcharr integration 0.2.0, running in a disposable Docker Desktop
container. Both English and German use Home Assistant's actual translations.

The only connected source was `tests/support/fake_dispatcharr.py` on the test
container's loopback interface. The dashboard images show its empty-session mode.
No real media server, IPTV stream, production credential or private hostname was
used. All credential inputs were checked to be empty before capture. The example
`127.0.0.1:8919` address is a fixture, not an address users should copy.

Images are cropped to the native dialog or integration controls and are kept in
documentation only. The 14 PNGs total less than 370 KiB. No generated UI
mockups or altered labels are used. The English `Viewers` entity name remains in
the German editor because the test integration was initially created in English.

| Prefix | Screen |
| --- | --- |
| `01` | Initial Dispatcharr-only setup |
| `02` | Integration page and Configure gear |
| `03` | Options menu with Media servers |
| `04` | Add/edit media-server menu |
| `05` | Media-server credentials form |
| `06` | Dashboard card picker filtered to Dispatcharr, By card selected |
| `07` | Visual card editor with viewer sensor and preview |

The suffix identifies the UI language: `en` or `de`.
