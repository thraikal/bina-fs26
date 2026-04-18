# Bina: Gruppenarbeit

## Fragen

Inwieweit lassen sich Gesundheitskosten in der Schweiz durch demografische (insbesondere Altersstruktur) und regionale Faktoren erklären und welche Segmente verursachen die grösste Systembelastung?

1. Wie entwickeln sich die Gesundheitskosten über die Zeit?
2. Wie unterscheiden sich Kosten nach Alter und Region?
3. Welchen Anteil haben ältere Altersgruppen (66+) an den Gesamtkosten und wie verändert sich dieser über die Zeit?
4. Lassen sich auf Basis von Altersstruktur und Kosten klare Segmente (Cluster) identifizieren?
5. Welche Faktoren erklären die Unterschiede zwischen diesen Segmenten und welche sollten priorisiert werden?

Ziel ist es, datenbasierte Entscheidungsgrundlagen für die Priorisierung von Massnahmen im Gesundheitssystem abzuleiten.

## Setup

1. Create a virtual environment

```bash
python -m venv <name-of-venv>
source venv/bin/activate
```

2. Install dependencies

```bash
pip install -r requirements.txt
```

## Dashboard

1. Run:

```bash
python src/app.py
```

2. Open `http://127.0.0.1:8050/` in your browser.

## Sources

[Gesundheitskosten](https://www.bfs.admin.ch/asset/de/DF_COU_HEALTH_COSTS)

[Bevölkerungsdaten](https://www.bfs.admin.ch/bfs/de/home/statistiken/bevoelkerung.assetdetail.36074768.html)
