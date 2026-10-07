# Choose a card layout

**English** | [Deutsch](card-layouts.de.md) · [Setup guide](setup.md)

From **0.3.0**, each card offers **Grid**, **Compact list** and **Logo tiles**.
Open **Edit dashboard → Edit card → Layout**, choose an option and **Save**.
After updating through HACS, restart Home Assistant and reload the dashboard.
Existing cards keep the grid view. No YAML is needed.

![Actual Home Assistant visual editor](screenshots/setup/07-card-editor-en.png)

| Setting | Effect |
| --- | --- |
| Layout | Grid, Compact list or Logo tiles |
| Maximum columns | Automatic, 1, 2 or 3; available for grid and tiles |
| Compact spacing | Reduces padding and gaps |
| Show source quality | Shows or hides resolution, frame rate, codecs and bitrate |
| Show EPG / playback progress | Shows or hides the programme/playback progress panel |
| Show action buttons | Controls button visibility; server permissions and the integration's control switch still apply |

Columns are a **maximum**, not a forced count. Narrow cards use one column;
wider cards can use two or three. The list always uses one column. Set the card's
overall width in the HA dashboard: selecting three columns cannot make a narrow
dashboard section wider. A single channel/session uses the available width.

These options apply to each card separately. You can add another Dispatcharr card
with a different layout without adding another integration or polling coordinator.
Older cards using compact mode keep their hidden quality panel until you enable it.

## Grid

Channel artwork, programme and source quality appear once per channel. Each
Dispatcharr connection remains visible below, with its own duration and controls.
Media-server sessions remain separate.

![Grid with four sources](screenshots/layout-grid-en.png)

<details>
<summary>Grid on a phone</summary>

![Mobile grid](screenshots/layout-grid-mobile-en.png)

</details>

## Compact list

Wide cards arrange identity, programme and connections side by side in each row.
On a phone these sections stack. Open **Connections & details** for individual
Dispatcharr connection details and actions. Media-session actions are under **Details**.

![Compact list with four sources](screenshots/layout-list-en.png)

<details>
<summary>Compact list on a phone</summary>

![Mobile compact list](screenshots/layout-list-mobile-en.png)

</details>

## Logo tiles

Larger centred logos and posters emphasise the channel or media title. Names and
DVR markers stay visible. Open **Connections & details** for individual connection
durations and actions; media-session actions are under **Details**.

![Logo tiles with four sources](screenshots/layout-tiles-en.png)

<details>
<summary>Logo tiles on a phone</summary>

![Mobile logo tiles](screenshots/layout-tiles-mobile-en.png)

</details>

All layouts use the same actual channel/session IDs. **End session** still targets
one connection; **Channel details → Stop channel for everyone** is a separate,
confirmed action. In the list and tiles, open **Connections & details** first.
Changing layouts does not start playback or change server configuration.

## Server status

Open **Server** at the bottom of any layout to see the connection status and last
successful update for Dispatcharr and each optional media server. This also works
with Dispatcharr alone and during a disconnection. From 0.3.1, the card omits the
routine footer explanations and duplicate timestamp. Actual errors remain visible.

![Expanded server status with fictional data](screenshots/server-details-en.png)

All screenshots show fictional users, artwork, programmes and measurements rendered
in the real Home Assistant frontend. They contain no real viewer data or credentials.
