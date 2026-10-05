# HACS catalog submission

[English guide](../README.md) | [Deutsche Anleitung](README.de.md)

The integration is already available as a HACS custom repository. Inclusion in
the default catalog requires a separate maintainer review; it does not make this
an official Dispatcharr or Home Assistant Core integration.

Requirements checked against the [HACS publishing guide](https://www.hacs.xyz/docs/publish/include/):

- Public repository, description, topics, issue tracker and GUI documentation.
- One integration with a valid manifest and `hacs.json`.
- HACS and hassfest actions passing without ignored checks.
- A release published after those checks pass.
- An owner-submitted PR adding `bttfw/ha-dispatcharr` alphabetically to the
  `integration` list in [`hacs/default`](https://github.com/hacs/default).

Brand assets are bundled in `custom_components/dispatcharr/brand/`, as supported
by [Home Assistant since 2026.3](https://developers.home-assistant.io/docs/core/integration/brand_images/).
The original SVG source is in `docs/brand/icon.svg`; `scripts/build_brand.py`
renders the PNGs. The mark is covered by this project's MIT license and identifies
the independent community integration.

Submission status: preparation in progress. No catalog acceptance is claimed.
The submission PR must be in English, disclose AI development, and link the
successful validation runs and release. Only the HACS maintainers can accept it.
