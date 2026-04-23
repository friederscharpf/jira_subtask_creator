#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
===============================================================================
Datei        : jira_subtask_creator.py
Version      : V0.5
Autor        : ChatGPT

===============================================================================
ZWECK DES PROGRAMMS
===============================================================================

Dieses Programm automatisiert das Erstellen von Jira Subtasks für Issues
innerhalb eines ausgewählten Sprints in Jira Cloud.

Es verbindet sich über die Jira REST API, liest Issues aus einem Sprint aus
und erstellt anhand von Label-basierten Definitionen automatisch Subtasks.

===============================================================================
GRUNDPRINZIP
===============================================================================

1. Sprint wird ausgewählt:
   - manuell (exakte Eingabe)
   - oder über Filtermodus (-f / --filter)

2. Alle Issues des Sprints werden geladen

3. Nur Haupt-Issues werden verarbeitet (keine Subtasks als eigenständige Ziele)

4. Labels der Issues werden mit Definitionsdateien abgeglichen

5. Subtasks werden erstellt, falls sie noch nicht existieren

6. Ausgabe einer vollständigen Ergebnisübersicht

===============================================================================
SUBTASK-DEFINITIONEN
===============================================================================

Ordnerstruktur:

    ./Subtasks/

Dateien:

    Subtasks_Impl.txt
    Subtasks_Test.txt
    Subtasks_Spez.txt

Regel:

    Subtasks_<LABEL>.txt  → Label = <LABEL>

Inhalt:

    Eine Zeile = ein Subtask Titel

Beispiel:

    Architektur prüfen
    Implementierung
    Unit Tests
    Code Review

===============================================================================
LOGIN DATEI
===============================================================================

Datei:

    confluence_login.txt

Format:

    https://your-domain.atlassian.net
    email@domain.com
    API_TOKEN

===============================================================================
SPRINT AUSWAHL
===============================================================================

--------------------------
Standardmodus
--------------------------

Aufruf:

    python jira_subtask_creator.py

Verhalten:

- Sprintname muss exakt existieren
- wenn nicht gefunden → Fehler + Abbruch

--------------------------
Filtermodus
--------------------------

Aufruf:

    python jira_subtask_creator.py -f
    python jira_subtask_creator.py --filter

Optional:

    python jira_subtask_creator.py -f "Team 2"

Verhalten:

- lädt alle Sprints aus Jira Boards
- filtert optional nach String
- zeigt nummerierte Liste
- Auswahl über Nummer

===============================================================================
DRY RUN MODUS
===============================================================================

Aufruf:

    python jira_subtask_creator.py --dry-run

oder kombiniert:

    python jira_subtask_creator.py -f "Team 2" --dry-run

Verhalten:

✔ keine Subtasks werden erstellt
✔ nur Simulation
✔ gleiche Ausgabe wie produktiv

===============================================================================
NEUERUNGEN IN V0.5
===============================================================================

✔ DRY-RUN wieder vollständig integriert
✔ kompatibel mit Filtermodus
✔ kompatibel mit Standardmodus
✔ stabile Sprintvalidierung
✔ keine Funktionsentfernung mehr

===============================================================================
JIRA API
===============================================================================

Verwendet:

- /rest/api/3/search/jql
- /rest/agile/1.0/board
- /rest/agile/1.0/board/{id}/sprint

===============================================================================
CHANGELOG
===============================================================================

V0.0
- Initialversion

V0.1
- Label System

V0.2
- Jira Search API Update
- Pagination
- Dry Run

V0.3
- Subtask-Filtern aus Ergebnisliste

V0.4
- Sprint Filtermodus (-f / --filter)

V0.5
- Dry Run wieder vollständig integriert
- Stabilisierung aller Modi

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
    if not os.path.exists(LOGIN_FILE):
        sys.exit(f"Fehler: {LOGIN_FILE} nicht gefunden.")

    with open(LOGIN_FILE, "r", encoding="utf-8") as f:
        lines = [l.strip() for l in f.readlines() if l.strip()]

    if len(lines) < 3:
        sys.exit("Fehler: Login-Datei benötigt 3 Zeilen.")

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
            tasks = [x.strip() for x in f.readlines() if x.strip()]

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
# SPRINT HANDLING
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


def select_sprint_filtered(base_url, auth, filter_string=None):
    sprints = fetch_all_sprints(base_url, auth)

    if filter_string is not None:
        sprints = [s for s in sprints if filter_string.lower() in s["name"].lower()]

    if not sprints:
        print("Keine Sprints gefunden.")
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
        print("Ungültige Eingabe.")


def validate_exact_sprint(base_url, auth, sprint_name):
    sprints = fetch_all_sprints(base_url, auth)
    return any(s["name"] == sprint_name for s in sprints)


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

    parser = argparse.ArgumentParser()

    parser.add_argument("-f", "--filter", nargs="?", const=None)
    parser.add_argument("--dry-run", action="store_true")

    args = parser.parse_args()

    print("Jira Subtask Creator V0.5")
    print("-------------------------")

    if args.dry_run:
        print("DRY RUN aktiv (keine Änderungen)\n")

    base_url, user, token = read_login()
    auth = HTTPBasicAuth(user, token)

    definitions = load_subtask_definitions()

    # ------------------------------------------------------------------------
    # Sprint Auswahl
    # ------------------------------------------------------------------------

    if args.filter is not None:
        sprint_name = select_sprint_filtered(base_url, auth, args.filter)
    else:
        sprint_name = input("Sprintname (exakt): ").strip()

        if not validate_exact_sprint(base_url, auth, sprint_name):
            print("Fehler: Sprint nicht gefunden.")
            sys.exit(0)

    print(f"\nSprint: {sprint_name}")

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