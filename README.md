# BINA Case Study: Gesundheitskosten, Alterung & Prämienbelastung in der Schweiz

## Einleitung
Diese Anwendung zeigt die Entwicklung der Gesundheitskosten in der Schweiz über die Zeit und analysiert die Auswirkungen auf die Alterung und Prämienbelastung.

## Fragestellung
Welche Kantone stehen aufgrund von Gesundheitskosten, Alterung und Prämienbelastung unter dem grössten Druck, und welche Entwicklung ist bis 2030 zu erwarten?
1. Welche Kantone haben die höchsten Gesundheitskosten pro Kopf, und wie hat sich dieser Druck seit 2011 entwickelt?
2. In welchen Kantonen passen Prämienniveau und Gesundheitskostenbelastung zusammen und wo gibt es Auffälligkeiten?
3. Wie stark hängt die kantonale Kostenbelastung mit dem Anteil älterer Bevölkerung zusammen?
4. Welche Kantone bilden ähnliche Belastungssegmente, und wie entwickeln sich diese bis 2030?

Ziel ist es, datenbasierte Entscheidungsgrundlagen für die Priorisierung von Massnahmen im Gesundheitssystem abzuleiten.

## Setup

Python-Installation wird vorausgesetzt.

1. Virtuelle Umgebung erstellen

```bash
python -m venv <name-of-venv>
source venv/bin/activate
```

2. Dependencies installieren

```bash
pip install -r requirements.txt
```

## Dashboard starten

1. Befehl ausführen

```bash
python src/04-information-presentation/app.py
```

2. `http://127.0.0.1:8050/` im Browser öffnen

## Datenquellen

- [Gesundheitskosten (bfs.admin.ch)](https://www.bfs.admin.ch/asset/de/DF_COU_HEALTH_COSTS)
- [Bevölkerungsdaten (bfs.admin.ch)](https://www.bfs.admin.ch/bfs/de/home/statistiken/bevoelkerung.assetdetail.36074768.html)
