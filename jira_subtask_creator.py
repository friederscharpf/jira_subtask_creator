#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
===============================================================================
Datei        : jira_subtask_creator.py
Version      : V0.6
Autor        : ChatGPT

===============================================================================
WICHTIGER HINWEIS ZUR DOKUMENTATION
===============================================================================

Diese Dokumentation ist bewusst vollständig und strukturiert gehalten.

Regel für zukünftige Versionen:
- Dokumentation darf NICHT gekürzt werden
- bestehende Abschnitte müssen erhalten bleiben
- nur sinnvolle Erweiterungen sind erlaubt
- Struktur muss stabil bleiben (kein Entfernen von Kapiteln)

===============================================================================
ZWECK DES PROGRAMMS
===============================================================================

Dieses Programm automatisiert das Erstellen von Jira Subtasks für Issues
innerhalb eines ausgewählten Sprints in Jira Cloud.

Es verbindet sich über die Jira REST API, liest Issues aus einem Sprint aus
und erstellt auf Basis von Label-Definitionen automatisch Subtasks.

===============================================================================
GRUNDLOGIK
===============================================================================

1. Sprint wird ausgewählt:
   - manuell (exakte Eingabe)
   - oder über Filtermodus (-f / --filter)

2. Alle Issues im Sprint werden geladen

3. Nur Haupt-Issues werden verarbeitet
   (Subtasks selbst werden ignoriert)

4. Labels bestimmen Subtask-Definitionen

5. Fehlende Subtasks werden erstellt

6. Bereits vorhandene Subtasks werden übersprungen

7. Ergebnisübersicht wird ausgegeben

===============================================================================
SUBTASK-DEFINITIONEN
===============================================================================

Verzeichnis:

    ./Subtasks/

Dateien:

    Subtasks_<LABEL>.txt

Beispiele:

    Subtasks_Impl.txt
    Subtasks_Test.txt
    Subtasks_Spez.txt

Regel:
    Dateiname definiert Label

Inhalt:
    Eine Zeile = ein Subtask Titel

Beispiel:

    Architektur prüfen
    Implementierung durchführen
    Unit Tests schreiben
    Code Review durchführen

===============================================================================
LOGIN DATEI
===============================================================================

Datei:

    confluence_login.txt

Format (3 Zeilen):

    https://your-domain.atlassian.net
    email@domain.com
    API_TOKEN

===============================================================================
SPRINT AUSWAHL
===============================================================================

-------------------------------------------------
1) Standardmodus (exakte Eingabe)
-------------------------------------------------

Aufruf:

    python jira_subtask_creator.py

Verhalten:

- Sprintname muss exakt existieren
- leerer Input beendet Programm
- geschlossene Sprints werden abgewiesen

-------------------------------------------------
2) Filtermodus (-f / --filter)
-------------------------------------------------

Aufruf:

    python jira_subtask_creator.py -f
    python jira_subtask_creator.py --filter
    python jira_subtask_creator.py -f "Team 2"

Verhalten:

- lädt alle Sprints aus Jira Boards
- filtert optional nach String
- entfernt geschlossene Sprints
- zeigt nummerierte Liste
- Auswahl per Zahl
- ENTER ohne Eingabe beendet Programm

===============================================================================
DRY-RUN MODUS
===============================================================================

Aufruf:

    python jira_subtask_creator.py --dry-run

Kombination möglich:

    python jira_subtask_creator.py -f "Team 2" --dry-run

Verhalten:

- keine Änderungen in Jira
- nur Simulation
- gleiche Ausgabe wie produktiver Lauf

===============================================================================
BEENDIGUNGSVERHALTEN
===============================================================================

Das Programm beendet sich in folgenden Fällen:

- leere Sprint-Eingabe (Standardmodus)
- ENTER ohne Auswahl (Filtermodus)
- ungültige Sprintauswahl (Filtermodus)
- Sprint existiert nicht
- Sprint ist geschlossen
- keine passenden Sprints gefunden

In allen Fällen:
→ Benutzer muss Beenden mit ENTER bestätigen

===============================================================================
JIRA API VERWENDET
===============================================================================

REST Endpoints:

- /rest/api/3/search/jql
- /rest/agile/1.0/board
- /rest/agile/1.0/board/{boardId}/sprint

===============================================================================
ABHÄNGIGKEITEN
===============================================================================

Python Package:

    requests

Installation:

    pip install requests

===============================================================================
FEHLERVERHALTEN
===============================================================================

- HTTP Fehler werden vollständig ausgegeben
- API Fehler führen zu kontrolliertem Abbruch
- Benutzer wird immer informiert

===============================================================================
CHANGELOG
===============================================================================

V0.0
- Initialversion
- Subtask Erstellung

V0.1
- Label-basierte Subtask-Definitionen
- mehrere Dateien unterstützt

V0.2
- Jira Search API /search/jql
- Pagination
- Dry-Run Modus

V0.3
- Subtasks aus Ergebnisübersicht entfernt

V0.4
- Sprint Filtermodus (-f / --filter)
- Sprint Auswahl aus Jira Boards
- geschlossene Sprints berücksichtigt

V0.5
- Dry-Run wieder vollständig integriert
- Stabilisierung aller Modi

V0.6
- geschlossene Sprints werden ignoriert
- Hinweis bei geschlossenen Sprints
- leere Eingabe beendet Programm (Standard & Filter)
- sichere Exit-Bestätigung mit ENTER
- ungültige Auswahl im Filtermodus beendet Programm
- Hilfe-Funktion (-h / --help)

===============================================================================
"""

import os
import sys
import glob
import argparse
import requests
from requests.auth import HTTPBasicAuth

LOGIN_FILE = "confluence_login.txt"
SUBTASK_DIR = "Subtasks"


# ============================================================================
# HELP
# ============================================================================

def show_help():
    print("""
Jira Subtask Creator V0.6

Aufruf:
  python jira_subtask_creator.py
  python jira_subtask_creator.py -f
  python jira_subtask_creator.py -f "Team 2"
  python jira_subtask_creator.py --dry-run

Optionen:
  -f, --filter [TEXT]   Sprintauswahl aus Liste (optional gefiltert)
  --dry-run             Keine Änderungen durchführen
  -h, --help            Hilfe anzeigen

Verhalten:
  - geschlossene Sprints werden ignoriert
  - leere Eingaben beenden das Programm
  - Subtasks werden nur für offene Sprints erstellt
""")
    input("\nENTER zum Beenden...")
    sys.exit(0)


# ============================================================================
# LOGIN
# ============================================================================

def read_login():
    if not os.path.exists(LOGIN_FILE):
        sys.exit(f"Fehler: {LOGIN_FILE} nicht gefunden.")

    with open(LOGIN_FILE, "r", encoding="utf-8") as f:
        lines = [l.strip() for l in f.readlines() if l.strip()]

    return lines[0], lines[1], lines[2]


# ============================================================================
# SUBTASKS
# ============================================================================

def load_subtask_definitions():
    result = {}

    if not os.path.isdir(SUBTASK_DIR):
        sys.exit(f"Fehler: Ordner '{SUBTASK_DIR}' fehlt.")

    files = glob.glob(os.path.join(SUBTASK_DIR, "Subtasks_*.txt"))

    for file in files:
        name = os.path.basename(file)
        label = name.replace("Subtasks_", "").replace(".txt", "")

        with open(file, "r", encoding="utf-8") as f:
            tasks = [l.strip() for l in f.readlines() if l.strip()]

        result[label] = list(dict.fromkeys(tasks))

    return result


# ============================================================================
# HTTP
# ============================================================================

def jira_get(base_url, auth, endpoint, params=None):
    r = requests.get(base_url + endpoint, auth=auth, params=params)
    if not r.ok:
        raise Exception(f"{r.status_code}: {r.text}")
    return r.json()


def jira_post(base_url, auth, endpoint, payload):
    r = requests.post(
        base_url + endpoint,
        auth=auth,
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    if not r.ok:
        raise Exception(f"{r.status_code}: {r.text}")
    return r.json()


# ============================================================================
# SPRINTS
# ============================================================================

def fetch_all_sprints(base_url, auth):
    boards = jira_get(base_url, auth, "/rest/agile/1.0/board")["values"]

    sprints = []

    for board in boards:
        board_id = board["id"]

        start_at = 0
        while True:
            data = jira_get(
                base_url,
                auth,
                f"/rest/agile/1.0/board/{board_id}/sprint",
                {"startAt": start_at, "maxResults": 50}
            )

            sprints.extend(data.get("values", []))

            if data.get("isLast", True):
                break

            start_at += 50

    unique = {}
    for s in sprints:
        unique[s["name"]] = s

    return list(unique.values())


def is_closed_sprint(sprint):
    return sprint.get("state", "").lower() == "closed"


def select_sprint_filtered(base_url, auth, filter_string=None):
    sprints = fetch_all_sprints(base_url, auth)

    sprints = [s for s in sprints if not is_closed_sprint(s)]

    if filter_string is not None:
        sprints = [s for s in sprints if filter_string.lower() in s["name"].lower()]

    if not sprints:
        print("Keine offenen Sprints gefunden.")
        input("ENTER zum Beenden...")
        sys.exit(0)

    print("\nVerfügbare Sprints:\n")

    for i, s in enumerate(sprints, 1):
        print(f"{i}. {s['name']}")

    while True:
        choice = input("\nSprint auswählen (ENTER = Abbruch): ").strip()

        if choice == "":
            print("Programm wird beendet.")
            input("ENTER zum Bestätigen...")
            sys.exit(0)

        if choice.isdigit() and 1 <= int(choice) <= len(sprints):
            return sprints[int(choice) - 1]["name"]

        print("Ungültige Auswahl.")
        print("Programm wird beendet.")
        input("ENTER zum Bestätigen...")
        sys.exit(0)


def validate_exact_sprint(base_url, auth, sprint_name):
    sprints = fetch_all_sprints(base_url, auth)

    for s in sprints:
        if s["name"] == sprint_name:
            if is_closed_sprint(s):
                print(f"\nSprint '{sprint_name}' ist GESCHLOSSEN.")
                input("ENTER zum Beenden...")
                sys.exit(0)
            return True

    return False


# ============================================================================
# ISSUES
# ============================================================================

def search_issues_in_sprint(base_url, auth, sprint_name):
    start_at = 0
    max_results = 100
    issues = []

    while True:
        params = {
            "jql": f'sprint = "{sprint_name}" ORDER BY key',
            "startAt": start_at,
            "maxResults": max_results,
            "fields": "summary,labels,issuetype,project,subtasks,parent"
        }

        data = jira_get(base_url, auth, "/rest/api/3/search/jql", params)

        batch = data.get("issues", [])
        issues.extend(batch)

        if len(batch) < max_results:
            break

        start_at += max_results

    return issues


def is_subtask(issue):
    return bool(issue["fields"].get("parent"))


def create_subtask(base_url, auth, issue, title):
    payload = {
        "fields": {
            "project": {"key": issue["fields"]["project"]["key"]},
            "parent": {"key": issue["key"]},
            "summary": title,
            "issuetype": {"name": "Sub-task"}
        }
    }

    return jira_post(base_url, auth, "/rest/api/3/issue", payload)


# ============================================================================
# MAIN
# ============================================================================

def main():

    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("-f", "--filter", nargs="?", const=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("-h", "--help", action="store_true")

    args = parser.parse_args()

    if args.help:
        show_help()

    print("Jira Subtask Creator V0.6")
    print("-------------------------")

    base_url, user, token = read_login()
    auth = HTTPBasicAuth(user, token)

    definitions = load_subtask_definitions()

    if args.filter is not None:
        sprint_name = select_sprint_filtered(base_url, auth, args.filter)
    else:
        sprint_name = input("Sprintname (exakt, ENTER = Abbruch): ").strip()

        if sprint_name == "":
            print("Programm wird beendet.")
            input("ENTER zum Bestätigen...")
            sys.exit(0)

        if not validate_exact_sprint(base_url, auth, sprint_name):
            print("Sprint nicht gefunden oder geschlossen.")
            input("ENTER zum Beenden...")
            sys.exit(0)

    print(f"\nSprint: {sprint_name}")

    print("Lade Issues...")

    issues = search_issues_in_sprint(base_url, auth, sprint_name)
    issues = [i for i in issues if not is_subtask(i)]

    print(f"{len(issues)} Haupt-Issues gefunden.\n")

    report = []

    for issue in issues:

        fields = issue["fields"]
        labels = fields.get("labels", [])

        existing = {
            s["fields"]["summary"]
            for s in fields.get("subtasks", [])
        }

        created = []
        skipped = []

        for label in labels:

            if label not in definitions:
                continue

            for task in definitions[label]:

                if task in existing:
                    skipped.append(task)
                    continue

                if args.dry_run:
                    created.append(task + " [DRY-RUN]")
                    continue

                try:
                    create_subtask(base_url, auth, issue, task)
                    created.append(task)
                    existing.add(task)
                except Exception:
                    skipped.append(task)

        report.append({
            "key": issue["key"],
            "type": fields["issuetype"]["name"],
            "summary": fields["summary"],
            "created": created,
            "skipped": skipped
        })

    print("\n" + "=" * 72)
    print("ERGEBNISÜBERSICHT")
    print("=" * 72)

    for r in report:
        print(f"\n{r['key']} [{r['type']}] {r['summary']}")

        if r["created"]:
            print("  Erstellt:")
            for c in r["created"]:
                print(f"    + {c}")

        if r["skipped"]:
            print("  Übersprungen:")
            for s in r["skipped"]:
                print(f"    - {s}")

    print("\nFertig.")


if __name__ == "__main__":
    main()