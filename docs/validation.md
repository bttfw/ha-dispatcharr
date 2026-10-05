# Prüfbericht zur Erstversion

Stand: 6. Oktober 2026. Geprüft mit **Home Assistant 2026.9.4** und
**Dispatcharr 0.31.0**. Andere Versionen sind damit nicht automatisch verifiziert.

## Reale Installation: ausschließlich lesend

Die installierten Versionen und HACS wurden an der vorhandenen Umgebung geprüft.
Ein gültiger Dispatcharr-Key wurde akzeptiert, ein absichtlich ungültiger Key
mit HTTP 401 abgewiesen. Status, Benutzer-IDs, gezielte Kanalmetadaten, aktuelle
EPG-Daten, Provider-/Profilverzeichnisse und die Berechtigungen der Stoppendpunkte
wurden gegen den offiziellen API-Vertrag geprüft. `OPTIONS` prüft Berechtigungen,
ohne eine Stoppaktion auszuführen.

Während der Bestandsprüfung waren keine Zuschauer aktiv. Deshalb sind echte
aktive Zuschauer, deren Qualitätswerte und ein echter Client-Abbruch **noch
nicht live abgenommen**. Dafür wäre eine ausdrücklich freigegebene Testsession
mit tatsächlicher Client-ID erforderlich. Es wurde weder ein IPTV-Stream
gestartet noch eine vorhandene Session beendet. Während dieser Bestandsprüfung
blieb das produktive HA unverändert.

## Automatische Tests

**60 Tests bestanden** gegen die tatsächlichen Klassen aus dem offiziellen
HA-Container `ghcr.io/home-assistant/home-assistant:2026.9.4`.
Die API-Gegenstelle ist vollständig synthetisch.

| Prüfung | Ergebnis |
| --- | --- |
| Zwei Zuschauer desselben Kanals | Ein Kanal, zwei Clients; korrekte Zuordnung über User-ID |
| Mehr als zehn Zuschauer | Gekürzte Übersicht erkannt, vollständige Details geladen |
| Einzelner Clientstopp | Exakte ID; zweiter Client bleibt; kein Kanalstopp als Ersatz |
| Gesamten Kanal stoppen | Eigene Aktion; explizite Bestätigung erforderlich |
| Abgelaufene IDs / scheinbar erfolgreicher Stopp | Vor- und Nachprüfung; verständlicher Fehler |
| Steuerung aus / fehlende Adminrechte | Aktion vor dem API-Schreibzugriff abgewiesen |
| Ungültiger Key / HTTP 403 / API-Ausfall | Einrichtungs- und Laufzeitfehler korrekt behandelt |
| Wiederverbindung | Gemeinsamer Coordinator aktualisiert Verfügbarkeit und Daten |
| Fehlende Identitäten, Metadaten und EPG | Unbekannt; keine Namensheuristik oder erfundenen Werte |
| Metadaten-/EPG-Caches | Unterschiedliche Intervalle; nur aktive UUIDs; Wiederholungen nach Fehler |
| URL und Pagination | Keine Credentials in URLs; fremde Weiterleitungen abgewiesen |
| API-Key in Antworten | Nicht in Sensordaten oder Diagnosen übernommen |
| Stabile IDs | Gleiche Entität bei neuem Coordinator; Timestamp-Verweis folgt Registry-Umbenennung |
| GUI-Konfiguration | Nur URL/Key erforderlich; getrennte Optionen, Aliase, Intervallgrenzen |

Ruff, Python-Formatierung und JavaScript-Syntaxprüfung bestehen ebenfalls.
GitHub Actions führt zusätzlich **hassfest** und die **HACS-Validierung** aus.
Die HACS-Prüfung überspringt ausschließlich `brands`, da keine Aufnahme in das
offizielle HA-Markenverzeichnis behauptet wird.

Aus dem Repository auf Linux/macOS, beziehungsweise mit einem passenden
absoluten Bind-Mount unter Docker Desktop:

```sh
docker run --rm --entrypoint /bin/sh \
  -v "$PWD:/work" -w /work \
  ghcr.io/home-assistant/home-assistant:2026.9.4 \
  -c 'pip install -r requirements-test.txt && python -m pytest -q && ruff check custom_components tests && ruff format --check custom_components tests'
node --check custom_components/dispatcharr/www/dispatcharr-card.js
```

Die Warnung zur `HomeAssistantApplication`-Vererbung stammt aus HA/aiohttp;
sie ist kein fehlgeschlagener Integrationstest.

## Browserprüfung mit echtem HA-Frontend

Eine separate HA-Installation in **Docker Desktop**, ausschließlich am lokalen
Loopback-Port veröffentlicht, lief mit zwei getrennten Integrationseinträgen:
reale Dispatcharr-Instanz mit abgeschalteter Steuerung sowie synthetische
API mit freigegebenen Testaktionen. Die synthetische API ist unter
[`tests/support/fake_dispatcharr.py`](../tests/support/fake_dispatcharr.py)
enthalten und erzeugt keine IPTV-Wiedergaben.

Mit Chromium/Playwright über die tatsächlich gerenderte Oberfläche geprüft:

- Helle und dunkle Darstellung, Desktop und 390 Pixel breites Smartphone.
- Zwei Clients desselben Kanals und eine automatisch aktualisierte Liste mit
  15 Clients; getrennte Kanal- und Zuschauerzähler.
- Bestätigungsdialog abbrechen; danach weiterhin beide Clients vorhanden.
- Nur `client_0` beenden; `client_1` mit Benutzer Sam bleibt sichtbar.
- Kanalaktion separat bestätigen; anschließend „Niemand schaut gerade“.
- Fehlende EPG-, Logo- und Qualitätsdaten; Verbindungsabbruch und Erholung.
- Neuladen während des Ausfalls; letzter erfolgreicher Zeitpunkt bleibt sichtbar.
- Visuellen Editor öffnen, Titel ändern und über HA speichern.
- Zwölf frische Browserkontexte einschließlich Editor als Regressionstest.
- Keine Dispatcharr-Requests oder Dispatcharr-Keys in den Browser-URLs.
- Neustart und mehrfaches Neuladen der Testintegration mit bestehenden Entitäten.

Die Kartenregistrierung wartet auf die HA-Anwendung, damit ein Austausch des
Custom-Element-Registers beim Start keine gelegentlichen Konfigurationsfehler
erzeugt. Diese Fehlerklasse ist auch im
[offiziellen Frontend-Issue #52960](https://github.com/home-assistant/frontend/issues/52960)
beschrieben. HA-Formulare für den Editor werden vor dessen Erstellung geladen.

Der Browser-Regressionstest ist als `tests/browser_smoke.py` enthalten.
Er setzt einen angemeldeten, privaten Playwright-Storage-State und ein
Testdashboard mit zwei synthetischen Zuschauern voraus:

```sh
pip install playwright
python -m playwright install chromium
python tests/browser_smoke.py --storage-state .local/browser-storage.json
```

Er akzeptiert ausschließlich ein lokales Test-HA, öffnet den Editor und bricht
ihn wieder ab. Die Storage-Datei enthält Test-Anmeldedaten und darf nicht ins Git.
Die vollständigen Stopp- und Ausfallszenarien wurden zusätzlich im Browser
durchgeführt; der kleine Browser-Smoke-Test allein deckt sie nicht ab.

## Darstellung

Alle dargestellten Personen, Programme und Qualitätswerte in diesen Bildern
stammen ausdrücklich aus der synthetischen Test-API. Das weiße Testlogo prüft
den authentifizierten Bildtransport; es ist kein echter Sender.

| Smartphone, dunkles Theme | Fehlende Metadaten |
| --- | --- |
| ![Karte auf dem Smartphone](screenshots/mobile.png) | ![Fehlende Metadaten](screenshots/missing.png) |

![Verbindungsabbruch mit letztem erfolgreichen Zeitpunkt](screenshots/offline.png)

## Aufräumen

## Installation im produktiven Home Assistant

Nach Abschluss der isolierten Tests wurde 0.1.0 über die echte HACS-Oberfläche
als benutzerdefiniertes Repository installiert. Die HA-Konfigurationsprüfung
meldete keine Fehler. Nach dem erforderlichen Neustart wurde die Verbindung
über den normalen Einrichtungsdialog mit URL und API-Key erstellt.

Die neue Dashboard-Ansicht wurde auf Desktop und Smartphone im echten
HA-Frontend geprüft: Verbindung aktiv, null Kanäle, null Zuschauer,
„Niemand schaut gerade“, aktuelle Zeit und abgeschaltete Steuerung.
Es gab keine JavaScript-Fehler. Die bisherigen Dashboard-Ansichten wurden
vorher gesichert und beim Ergänzen unverändert erhalten.

## Aufräumen

Temporäre Unraid-Testcontainer, deren Testverzeichnis und das dafür geladene
HA-Image wurden nach dem Wechsel zu Docker Desktop entfernt. Docker-Desktop-
Testcontainer werden nach Abschluss ebenfalls entfernt; Testläufe verwenden
`--rm`. Es verbleibt kein dauerhaft laufender Testdienst auf Unraid.
