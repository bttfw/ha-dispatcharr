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

Submission status: [PR #11610](https://github.com/hacs/default/pull/11610) was
closed and withdrawn at the repository owner's request on 6 October 2026, before
acceptance, while further improvements are developed. It is not currently pending
review. Installation and updates through the HACS custom repository remain available.

Follow the PR's **Conversation** and **Checks** tabs, or use **Subscribe** for
GitHub notifications. `Open` means pending; `Merged` means accepted. Inclusion
then follows a scheduled HACS scan. Review timing is outside this project's control.
The bot asks submitters to wait for reviewer feedback rather than posting status
requests or duplicate submissions.

Future integration releases do not require new catalog submissions. Publish a
GitHub release after validation; HACS detects it as an update. Detecting an update
does not install it automatically: users normally initiate installation through
HA's update entity, followed by a restart for this integration. This also works
while the repository is installed as a custom repository.
