# AI transparency notice

This integration was developed with **OpenAI Codex (AI)** under the repository
owner's direction. The AI contribution includes architecture, Python backend
implementation, the JavaScript dashboard card, tests, original project branding, documentation and release
preparation. The **AI-assisted** badge is a project disclosure, not a GitHub
certification or an assertion that the code has received independent human review.

## Sources and independence

The project was implemented independently using official Home Assistant
developer documentation and Dispatcharr's documented API and official source.
No implementation was copied from an existing Dispatcharr integration for
Home Assistant. The verified contract and source links are in
[architecture.md](docs/architecture.md).

## Verification and limits

The initial implementation passed 60 automated tests against Home Assistant
2026.9.4, plus hassfest, HACS validation, Ruff and JavaScript syntax checks.
Browser checks exercised the actual HA frontend with synthetic API data,
including multiple viewers, exact client stops, separate whole-channel stops,
missing metadata, outages, recovery and a visual card editor. Twelve fresh
browser sessions checked startup and editor loading.

The installed Dispatcharr 0.31.0 API was also checked read-only by the agent.
The repository owner separately confirmed successfully ending one real IPTV
client session. This is an owner-reported functional test. Automated stop checks use
synthetic sessions; the agent did not terminate real IPTV playback. Source
quality fields and device playback state are shown only when the API provides
them; unsupported or missing information is not invented.

These checks do not constitute an independent security audit or guarantee that
the implementation is error-free. No independent human code review is claimed.
See the [validation report](docs/validation.md) for the tested scope.

## Contributions

Pull request titles and descriptions are written in English. Contributors
should disclose AI use accurately, identify the tool and affected work, and
distinguish automated checks from human review and actual live validation.
