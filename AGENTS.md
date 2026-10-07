# Contributor and coding-agent instructions

These rules apply to the entire repository. Follow the repository owner's current
instructions when they change the scope or priorities.

## Project and evidence

- Keep this an independently implemented project. Do not copy code from another
  Dispatcharr Home Assistant integration.
- Use official Home Assistant developer documentation and documented or
  source-verified server APIs. Verify the installed versions before live testing.
- From 0.2.0, stable supports Dispatcharr with optional Jellyfin, Plex and Emby
  servers; all configured sources must work concurrently. Keep the current
  project name and logo until a separate decision.
- Identify users, sessions, channels and servers by their actual IDs. Never merge
  sessions or assign users merely because names, titles or IP addresses match.
- Missing values remain unknown. Distinguish source quality from transcoded output,
  connected proxy clients from end users, and playback position from connection age.

## Home Assistant and implementation

- Keep setup, options and normal dashboard use available through the HA GUI.
  Provide English and German strings and a visual editor for the bundled card.
- Keep existing entity IDs, options and dashboards compatible with updates.
  Support multiple instances, restarts, reloads and independent source failures.
- Use shared asynchronous polling per configured source. Cache metadata and images
  separately; never download the complete EPG on each status refresh.
- Do not start streams or extra IPTV playback to populate the dashboard.
- Keep credentials in the backend. Do not put tokens in browser URLs, state
  attributes, diagnostics, screenshots, fixtures, PRs or logs. Bound responses and
  caches, validate URLs and prevent credential-bearing redirects.
- Keep optional sources optional. An unavailable server must not hide successfully
  updated sessions from the other servers.

## Session controls and live testing

- Session actions must target the selected server and actual session ID. Check
  current membership before the action and query the actual state afterward.
- Never substitute a whole-channel, process or container stop for a client stop.
  Whole-channel termination is a separate, clearly labelled, confirmed action.
- Require enabled controls and an HA administrator. Handle expired IDs, denied
  permissions and unconfirmed stops without inventing success.
- Do not interrupt real users. Live termination tests require an explicitly
  authorized test session. Use synthetic fixtures for routine control tests.
- Record test containers, temporary files and credentials as they are created.
  Remove only resources created for that test run and verify cleanup. Do not stop
  unrelated services or delete production data. Never bypass a rejected operation.

## Branches, validation and contribution workflow

- `main` is the stable release branch. Use focused fix branches for stable defects.
  Use `beta` and feature branches targeting it for new features. Publish beta
  builds as GitHub prereleases; stable promotion requires the owner's request.
- An owner-approved promotion of user-visible changes to `main` includes a stable
  release unless the owner explicitly asks to defer publishing. Finish the version
  bump, changelog, protected PR checks, release package and GitHub release; a merge
  alone does not make an update available in HACS. Development-only dependency or
  documentation maintenance does not require a new integration release.
- Keep `.github/dependabot.yml` on the default branch. Routine dependency updates
  target `beta`; Dependabot security updates target `main`. Review changes and
  require the existing CI checks before merging; do not enable automatic merging.
  Update the pinned HA test image, shell-installed Playwright and floating action
  references manually when needed; they are not covered by these version updates.
- Follow the owner's current decision on HACS catalog submission. The existing
  application is hacs/default#11610, reopened at the owner's request on 2026-10-06.
  Reuse that application; do not submit duplicates, request reviews or claim
  acceptance before HACS maintainers merge it.
- Add meaningful regression tests for bugs and behavioral changes. Cover shared
  channels, exact-session targeting, missing data, authentication failures,
  disconnections, recovery and concurrent sources where relevant.
- Follow `.github/workflows/validate.yml`: the backend tests run in the pinned
  official HA image; run Ruff and the Chromium card tests when relevant. Never
  disable validation checks to obtain a passing result.
- Validate GUI changes in the real HA frontend as well as isolated card tests.
  State clearly which evidence is synthetic, live, or reported by the owner.
- Keep public documentation, commits and PRs in English. Update the German guide
  for user-visible changes. PRs should explain the problem, resulting behavior and
  validation; the central AI transparency notice is sufficient disclosure.
- Commit coherent changes regularly. Inspect the diff for secrets and unrelated
  edits. Preserve branch protection; report push failures immediately rather than
  claiming the work was published.
- Update the changelog and both integration version constants together when
  preparing a release. Use `scripts/build_release.py`; never package `.local/`.
- Every future release must include a versioned English entry in `CHANGELOG.md`
  and matching, meaningful GitHub release notes describing the changes, relevant
  validation and any upgrade steps. Do not publish empty release notes or rely
  only on a commit list.
