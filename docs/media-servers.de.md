# Jellyfin, Emby und Plex

[English](media-servers.md) · [Testnachweise](validation.md)

**0.2.0** enthält Jellyfin, Emby und Plex als optionale Quellen in der bestehenden
Dispatcharr-Karte. Reguläre Releases liegen auf `main`, künftige Vorabversionen
auf `beta`. Name, Integrations-Domain und bestehende Entitäts-IDs bleiben erhalten.

![Gemeinsame Quellen mit synthetischen Beispieldaten](screenshots/desktop-de.png)

## Einrichtung über die Oberfläche

1. Das Repository wie in der Hauptanleitung als HACS-Repository hinzufügen.
2. Dispatcharr in HACS auf **v0.2.0** installieren oder aktualisieren. Falls beim
   Wechsel von 0.2.0b1 noch die Vorabversion ausgewählt ist: **Menü → Erneut
   herunterladen → Benötigst du eine andere Version? → Release → v0.2.0**.
3. Herunterladen, Home Assistant neu starten und das Dashboard einmal neu laden.
4. **Einstellungen → Geräte & Dienste → Dispatcharr → Konfigurieren →
   Medienserver → Server hinzufügen** öffnen.
5. Servertyp, URL und API-Key/Token angeben. Der Anzeigename ist optional.
   Serveridentität und Zugriff auf Sessions werden beim Speichern geprüft.
6. Weitere Server auf dieselbe Weise hinzufügen. Auch mehrere Server desselben
   Typs sind möglich. Die vorhandene Karte zeigt sie automatisch zusammen an.

Bereits in 0.2.0b1 eingerichtete Server, Aliase, Steuerungsoptionen und Dashboards
bleiben erhalten. Die Integration zum Aktualisieren nicht entfernen.

Unter **Medienserver → Server bearbeiten oder entfernen** lassen sich
Verbindungen ändern. Beim Bearbeiten bedeutet ein leeres Schlüsselfeld:
bisherigen Schlüssel behalten. Entfernen löscht nur diese Verbindung.

Jellyfin und Emby benötigen einen Administrator-API-Key. Plex benötigt den
**X-Plex-Token** des Eigentümers eines verknüpften Servers. Ein kurz gültiger
*Claim-Token* dient zur Servereinrichtung und ist kein API-Token für die Integration.

## Darstellung und Bedienung

Alle Quellen werden getrennt abgefragt und angezeigt. Unten unter **Server**
stehen Verbindungsstatus und letzte erfolgreiche Aktualisierung jeder Quelle.
Ein ausgefallener Server blendet die anderen Quellen nicht aus.

Dispatcharr-Kanäle, Dispatcharr-Clients und Medien-Sessions bleiben getrennte
Zähler. Gezählt werden Verbindungen, keine eindeutigen Personen. Eine Wiedergabe
über Dispatcharr und Jellyfin kann deshalb in beiden Quellen auftauchen. Gleiche
Namen oder IP-Adressen reichen nicht aus, um Benutzer zusammenzuführen.

Die Karte zeigt gemeldete Benutzer/Geräte, Titel, Wiedergabestatus, Fortschritt,
Bilder und Qualitätsdaten. Fehlende Werte bleiben unbekannt. Quellqualität und
transkodierte Ausgabe werden getrennt dargestellt. Reine Anmeldungen ohne
Wiedergabe zählen nicht als Zuschauer.

Unter **Konfigurieren → Geräte-Aliase** lassen sich auch beobachtete Mediengeräte
benennen. Die Zuordnung erfolgt je Server über dessen tatsächliche Geräte-ID.

Zum Beenden müssen sowohl der Schalter **Steuerung aktivieren** als auch die
Option **Beenden auf diesem Server erlauben** eingeschaltet sein. Nur
HA-Administratoren können Aktionen auslösen. Die aktuelle Session und Medien-ID
werden unmittelbar vorher geprüft; danach wird der tatsächliche Status abgefragt.

## Bekannte Grenzen

- **Jellyfin:** Zwei echte Testbrowser spielten einen selbst erzeugten Clip.
  Über die HA-Karte wurde genau einer beendet; der andere spielte weiter.
- **Emby 4.10.1.0:** Die Anzeige funktionierte. Der getestete Webclient ignorierte
  jedoch einen zugestellten Stop-Befehl. Die Integration meldet dann ausdrücklich,
  dass das Beenden nicht bestätigt werden konnte.
- **Plex 1.43.4:** Zwei kontrollierte Sessions wurden angezeigt. Liefert Plex für
  mehrere Wiedergaben dieselbe ID zum Beenden, bleiben beide sichtbar und diese
  Aktion wird gesperrt. Der Testserver verweigerte die native Beenden-Funktion
  außerdem mit HTTP 401 trotz gültigem Token; auch das wird als verweigerte Aktion
  behandelt.

Es gibt keine automatische Ersatzaktion zum Beenden eines ganzen Kanals, Servers
oder Containers. Die bisherigen Dispatcharr-Aktionen bleiben unverändert.
Die Integration startet selbst keine Wiedergaben und lädt keine Schlüssel in die
Karte. Auch der reguläre Release behält die genannten Client-/API-Grenzen bei.
