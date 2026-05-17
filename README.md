## Installation und Ausführung des Projekts

Dieses Projekt ist vollständig containerisiert und kann mithilfe von Docker Compose gestartet werden.  
Die Umgebung besteht aus dem Python-Backend, dem Frontend, einer SQLite Datenbank sowie dem OWASP Juice Shop als Testanwendung.

## Hinweis

Die Nutzung des Crawlers gegen fremde, öffentliche oder produktive Systeme ist ohne ausdrückliche schriftliche Zustimmung der jeweiligen Betreiber:innen nicht erlaubt und kann gegen geltendes Recht verstoßen.

### Voraussetzungen

Für die Ausführung werden folgende Komponenten benötigt:

- Windows 11, Linux oder macOS
- Docker Desktop mit Docker Compose
- Ein gültiger OpenAI API-Key
- IDE (empfohlen: VS Code)

Hinweis: Für die Nutzung der OpenAI API können Kosten entstehen. Der API-Key ist nicht im Repository enthalten und muss selbst erstellt werden.

Das Projekt wurde erfolgreich mit folgenden Docker-Versionen getestet:

Docker Version 28.4.0
Docker Version 28.5.1

## Anleitung

- ZIP-Ordner herunterladen
- Ordner entpacken
- im Ordner PythonCrawler\app\ai_integration die Datei .env.example durch eine .env mit einem gültigen OpenAI API-Key ersetzen
- Docker Desktop starten
- VS Code starten
- Projektordner in VS Code öffnen
- Neues Terminal in VS Code öffnen
- in den Ordner PythonCrawler navigieren
- Command eingeben: 'docker compose up -d --build' (das Downloaden der benötigten Daten dauert anfangs ein paar Minuten)
- Logs können mit folgenden Command überprüft werden: 'docker compose logs -f'
- Nach erfolgreichen Build sollten nun 3 Container und ein Volume gebaut sein
- unter 'http://localhost:3001' ist nun das Frontend aufrufbar
- Tiefe und Basisurl müssen manuell eingestellt werden
- Run Crawler klicken
- der Durchlauf dauert je nach Tiefe ein paar Minuten, da die Berichterstellung viel Zeit benötigt
- Nach erfolgreichen Scan werden die Daten im Frontend angezeigt
