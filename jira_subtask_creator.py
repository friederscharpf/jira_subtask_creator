#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
===============================================================================
Datei        : jira_subtask_creator.py
Version      : V0.4
Autor        : ChatGPT

===============================================================================
ZWECK DES PROGRAMMS
===============================================================================

Dieses Python-Programm automatisiert das Erstellen von Jira Subtasks für
Issues innerhalb eines ausgewählten Sprints in Jira Cloud.

Es verbindet sich über die Jira REST API und analysiert alle Issues eines
Sprints. Basierend auf Labels in den Issues werden definierte Unteraufgaben
(Subtasks) automatisch erzeugt.

===============================================================================
GRUNDPRINZIP
===============================================================================

1. Sprint wird ausgewählt (manuell oder über Filtermodus)
2. Alle Issues im Sprint werden geladen
3. Für jedes Issue werden Labels ausgewertet
4. Passende Subtask-Definitionen werden aus Dateien geladen
5. Fehlende Subtasks werden automatisch erstellt
6. Bestehende Subtasks werden ignoriert
7. Abschlussbericht wird ausgegeben

===============================================================================
SUBTASK-DEFINITIONEN
===============================================================================

Pfad:

    ./Subtasks/

Dateibenennung:

    Subtasks_<LABEL>.txt

Beispiele:

    Subtasks_Impl.txt   -> Label "Impl"
    Subtasks_Test.txt   -> Label "Test"
    Subtasks_Spez.txt   -> Label "Spez"

Inhalt:
    Eine Zeile = ein Subtask Titel

Beispiel:

    Architektur prüfen
    Unit Tests schreiben
    Code implementieren
    Review durchführen

===============================================================================
JIRA LOGIN DATEI
===============================================================================

Datei:

    confluence_login.txt

Format (3 Zeilen):

    https://deine-domain.atlassian.net
    email@domain.com
    API_TOKEN

===============================================================================
SPRINT AUSWAHL MODI
===============================================================================

----------------------------
1) Standardmodus (exakte Eingabe)
----------------------------

Aufruf:

    python jira_subtask_creator.py

Dann Eingabe:

    Sprint Name exakt wie in Jira

Verhalten:
- Sprint muss exakt existieren
- Wenn nicht gefunden → Abbruch mit Fehlermeldung

----------------------------
2) Filtermodus (-f / --filter)
----------------------------

Aufruf:

    python jira_subtask_creator.py --filter
    python jira_subtask_creator.py -f

ODER mit Filterstring:

    python jira_subtask_creator.py -f "Team 2"

Verhalten:
- lädt alle Sprints aus Jira Boards
- optional Filter auf Sprintnamen
- zeigt nummerierte Liste
- Nutzer wählt Sprint per Zahl

===============================================================================
NEUE FUNKTIONEN IN V0.4
===============================================================================

✔ Sprint-Auswahl über Jira Agile API
✔ Filtermodus für Sprintauswahl
✔ Sprint-Suche über Boards
✔ Exakte Sprintvalidierung im Standardmodus
✔ Verbesserte Benutzerführung
✔ stabile Issue-Erkennung (nur Haupt-Issues)
✔ Subtasks werden nicht separat verarbeitet

===============================================================================
JIRA API VERWENDET
===============================================================================

- /rest/api/3/search/jql
- /rest/agile/1.0/board
- /rest/agile/1.0/board/{boardId}/sprint

===============================================================================
VERHALTEN BEI FEHLERN
===============================================================================

- Kein Sprint gefunden → Programm beendet sich sauber
- API Fehler → Ausgabe des HTTP Fehlers
- Ungültige Auswahl → erneute Eingabe

===============================================================================
ABHÄNGIGKEITEN
===============================================================================

Python Pakete:

    requests

Installation:

    pip install requests

===============================================================================
CHANGELOG
===============================================================================

V0.0
- Initialversion

V0.1
- Label-System eingeführt
- mehrere Subtask-Dateien unterstützt

V0.2
- Jira Search API aktualisiert
- Pagination
- Dry Run

V0.3
- Subtasks aus Ausgabe entfernt
- nur Haupt-Issues verarbeitet

V0.4
- Sprint-Filtermodus (-f / --filter)
- Sprintliste aus Jira Boards
- exakte Sprintvalidierung
- verbesserte Benutzerführung

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
# LOGIN
# ============================================================================

def read_login():
    """Liest Jira Login-Daten aus Datei."""
    if not os.path.exists(LOGIN_FILE):
        sys.exit(f"Fehler: {LOGIN_FILE} nicht gefunden.")

    with open(LOGIN_FILE, "r", encoding="utf-8") as f:
        lines = [l.strip() for l in f.readlines() if l.strip()]

    if len(lines) < 3:
        sys.exit("Fehler: confluence_login.txt benötigt 3 Zeilen.")

    return lines[0], lines[1], lines[2]


# ============================================================================
# SUBTASK DEFINITIONS
# ============================================================================

def load_subtask_definitions():
    """
    Lädt Subtask Definitionen aus ./Subtasks

    Rückgabe:
        {
            "Impl": ["Task1", "Task2"],
            "Test": [...]
        }
    """
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
# JIRA HTTP
# ============================================================================

def jira_get(base_url, auth, endpoint, params=None):
    """GET Request Jira API"""
    r = requests.get(base_url + endpoint, auth=auth, params=params)

    if not r.ok:
        raise Exception(f"{r.status_code}: {r.text}")

    return r.json()


def jira_post(base_url, auth, endpoint, payload):
    """POST Request Jira API"""
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
# SPRINT HANDLING
# ============================================================================

def fetch_all_sprints(base_url, auth):
    """
    Lädt alle Sprints aus allen Boards.
    """
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

            values = data.get("values", [])
            sprints.extend(values)

            if data.get("isLast", True):
                break

            start_at += 50

    # eindeutige Sprints nach Name
    unique = {}
    for s in sprints:
        unique[s["name"]] = s

    return list(unique.values())


def select_sprint_filtered(base_url, auth, filter_string=None):
    """
    Interaktive Sprintauswahl mit optionalem Filter.
    """
    sprints = fetch_all_sprints(base_url, auth)

    if filter_string:
        sprints = [
            s for s in sprints
            if filter_string.lower() in s["name"].lower()
        ]

    if not sprints:
        print("Keine passenden Sprints gefunden.")
        sys.exit(0)

    print("\nVerfügbare Sprints:\n")

    for i, s in enumerate(sprints, 1):
        print(f"{i}. {s['name']}")

    while True:
        try:
            idx = int(input("\nSprint auswählen (Nummer): "))
            if 1 <= idx <= len(sprints):
                return sprints[idx - 1]["name"]
        except ValueError:
            pass

        print("Ungültige Auswahl.")


def validate_exact_sprint(base_url, auth, sprint_name):
    """
    Prüft exakte Übereinstimmung eines Sprints.
    """
    sprints = fetch_all_sprints(base_url, auth)

    return any(s["name"] == sprint_name for s in sprints)


# ============================================================================
# ISSUES
# ============================================================================

def search_issues_in_sprint(base_url, auth, sprint_name):
    """
    Lädt alle Issues eines Sprints (Pagination).
    """
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
    """Erkennt Subtasks und filtert sie aus."""
    return bool(issue["fields"].get("parent"))


def create_subtask(base_url, auth, issue, title):
    """Erstellt Jira Subtask."""
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

    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--filter", nargs="?", const="")
    args = parser.parse_args()

    print("Jira Subtask Creator V0.4")
    print("-------------------------")

    base_url, user, token = read_login()
    auth = HTTPBasicAuth(user, token)

    definitions = load_subtask_definitions()

    # ------------------------------------------------------------------------
    # Sprint Auswahl
    # ------------------------------------------------------------------------

    if args.filter is not None:
        sprint_name = select_sprint_filtered(base_url, auth, args.filter)
    else:
        sprint_name = input("Sprintname (exakt) eingeben: ").strip()

        if not validate_exact_sprint(base_url, auth, sprint_name):
            print("Fehler: Kein exakt passender Sprint gefunden.")
            sys.exit(0)

    print(f"\nVerwendeter Sprint: {sprint_name}")

    # ------------------------------------------------------------------------
    # Issues laden
    # ------------------------------------------------------------------------

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

    # ------------------------------------------------------------------------
    # OUTPUT
    # ------------------------------------------------------------------------

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