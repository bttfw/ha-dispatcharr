# Streams aller konfigurierten Server zählen

[English](stream-counter.md)

Ab **0.4.1** erhält jede Integrationsinstanz den Sensor **Streams insgesamt**.
Er addiert Dispatcharr-Client-Verbindungen und die gemeldeten Sessions aller
eingerichteten Jellyfin-, Plex- und Emby-Server. Ein Dispatcharr-Client plus eine
Jellyfin-Session ergibt **2**. Zwei Clients auf demselben Sender plus diese
Jellyfin-Session ergeben **3**; **Aktive Kanäle** bleibt dabei **1**.

Der bisherige Sensor **Zuschauer** zählt weiterhin nur Dispatcharr. **Medien-Sessions**
zählt weiterhin die Medienserver. Die drei getrennten Kartenzähler behalten ihre
Bedeutung. Anzeige-Filter einer Karte verändern den Gesamtsensor nicht.

## Gesamtzähler für ein Dashboard-Badge auswählen

1. Dispatcharr in HACS auf **v0.4.1** aktualisieren und Home Assistant neu starten.
2. Dashboard öffnen und **Dashboard bearbeiten** wählen.
3. Das bisherige Streams-Badge bearbeiten und bei **Entität** den Sensor
   **Streams insgesamt** der richtigen Dispatcharr-Instanz auswählen. Name und
   Symbol können unverändert bleiben.
4. Speichern und die Bearbeitung beenden. Für ein neues Badge **Badge hinzufügen →
   Entität** wählen und denselben Sensor verwenden.

Der Sensor ist auch unter **Einstellungen → Geräte & Dienste → Dispatcharr →
Gerät der Instanz** sowie in der normalen Entitätsauswahl verfügbar. Die Entity-ID
hängt von Instanzname und HA-Sprache ab; deshalb nach dem angezeigten Namen suchen.
Die Integration ändert vorhandene Dashboards nicht automatisch.

## Was gezählt wird

- Jede gemeldete Dispatcharr-Client-Verbindung einschließlich DVR sowie jede
  Medienserver-Session einschließlich gemeldeter pausierter Wiedergaben zählt eins.
- Server werden unabhängig addiert. Namen, Titel, IP-Adressen und Session-IDs
  verschiedener Server dienen nicht dazu, vermeintlich gleiche Personen oder
  Wiedergaben zusammenzufassen. Nutzt ein Medienserver Dispatcharr als Quelle,
  können Verbindungen auf beiden Seiten gemeldet werden. Der Zähler zeigt keine
  Anzahl eindeutiger Personen.
- Beide bestehenden Datenabfragen aktualisieren den Sensor. Es werden keine
  Wiedergaben gestartet oder zusätzlichen Polling-/EPG-Abfragen erzeugt.
- Bei Ausfällen erscheint die bekannte Teilsumme erreichbarer Quellen.
  `complete: false` und `unavailable_sources` kennzeichnen unvollständige Werte.
  Fehlende Zähler bleiben unbekannt; alte Daten werden nicht weitergezählt.
  Sind alle Quellen ausgefallen, ist der Sensor nicht verfügbar. Null setzt
  voraus, dass mindestens eine Quelle erfolgreich keine Verbindungen meldet.

Die Attribute `dispatcharr_clients` und `media_sessions` zeigen die Aufteilung.
Dieser Übersichtssensor enthält keine Zuschauernamen, Stream-URLs oder Zugangsdaten.
