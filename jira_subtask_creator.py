#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
===============================================================================
Datei        : jira_subtask_creator.py
Version      : V0.7
Autor        : ChatGPT

===============================================================================
WICHTIGER HINWEIS ZUR DOKUMENTATION
===============================================================================

Diese Dokumentation ist vollständig und darf in zukünftigen Versionen nicht
gekürzt werden. Es sind nur Erweiterungen erlaubt, keine Entfernung von
bestehenden Abschnitten.

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

2. Sprint wird validiert (inkl. Statusprüfung)
   - nur active und future erlaubt
   - closed wird blockiert

3. Alle Issues im Sprint werden geladen

4. Nur Haupt-Issues werden verarbeitet

5. Labels bestimmen Subtask-Definitionen

6. Fehlende Subtasks werden erstellt

7. Bereits vorhandene Subtasks werden übersprungen

8. Ergebnisbericht wird ausgegeben

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

Inhalt:

    Eine Zeile = ein Subtask Titel

===============================================================================
LOGIN DATEI
===============================================================================

confluence_login.txt (3 Zeilen):

    https://your-domain.atlassian.net
    email@domain.com
    API_TOKEN

===============================================================================
SPRINT VERHALTEN
===============================================================================

-------------------------------------------------
Standardmodus
-------------------------------------------------

Aufruf:

    python jira_subtask_creator.py

Verhalten:

- Sprintname muss exakt eingegeben werden
- ENTER = Exit
- closed Sprint wird blockiert
- active/future erlaubt

-------------------------------------------------
Filtermodus (-f / --filter)
-------------------------------------------------
Aufruf:

    -f
    -f ""
    -f "Team 2"

VERHALTEN:

- zeigt ALLE active + future Sprints (geschlossene Sprints werden nicht angezeigt)
- optional Filterstring möglich
- Auswahl per Nummer
- ENTER = Exit

===============================================================================
DRY RUN
===============================================================================

--dry-run:

- Simulation
- keine Änderungen in Jira
- gleiche Ausgabe wie produktiv mit vollständigem Report

===============================================================================
NEUERUNG V0.7
===============================================================================

✔ Explizite Meldung bei geschlossenem Sprint
✔ keine Subtask-Erstellung bei geschlossenen Sprints
✔ klare Abbruchmeldung inkl. Sprintname
✔ konsistente Statusprüfung im Standardmodus

===============================================================================
JIRA API
===============================================================================

- /rest/api/3/search/jql
- /rest/agile/1.0/board
- /rest/agile/1.0/board/{id}/sprint

===============================================================================
CHANGELOG
===============================================================================

V0.0  Initial
V0.1  Label-System
V0.2  Search API + Dry Run
V0.3  Subtask Filterung
V0.4  Sprint Filtermodus
V0.5  Stabilisierung + Dry Run fix
V0.6  Closed Sprint Handling + Messages
V0.7  Explizite Closed-Sprint Meldung vor Verarbeitung

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
Jira Subtask Creator V0.7

Aufruf:
  python jira_subtask_creator.py
  python jira_subtask_creator.py -f
  python jira_subtask_creator.py -f "Team 2"
  python jira_subtask_creator.py --dry-run

Optionen:
  -f, --filter [TEXT]   Sprintauswahl aus Liste (optional gefiltert)
  --dry-run             Keine Änderungen durchführen
  -h, --help            Hilfe anzeigen

Wichtige Regeln:
  - nur active und future Sprints erlaubt (closed Sprints werden abgelehnt)
  - Subtasks werden nur bei active und future Sprints erstellt
  - leere Eingaben beenden das Programm
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
        label = os.path.basename(file).replace("Subtasks_", "").replace(".txt", "")

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

def sprint_label(s):
    return f"{s['name']} ({s.get('state','')})"

def select_sprint_filtered(base_url, auth, filter_string=None):
    sprints = fetch_all_sprints(base_url, auth)

    sprints = [s for s in sprints if not is_closed_sprint(s)]

    if filter_string is not None:
        sprints = [s for s in sprints if filter_string.lower() in s["name"].lower()]

    if not sprints:
        print("Keine offenen/aktiven Sprints gefunden.")
        input("ENTER zum Beenden...")
        sys.exit(0)

    print("\nVerfügbare offene/aktive Sprints:\n")

    for i, s in enumerate(sprints, 1):
        print(f"{i}. {sprint_label(s)}")

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

            # >>> NEU V0.7: EXPLIZITE CLOSED MESSAGE <<<
            if is_closed_sprint(s):
                print("\n========================================")
                print(f"SPRINT GESCHLOSSEN: {sprint_name}")
                print("Es werden KEINE Subtasks erstellt.")
                print("========================================\n")
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
    parser.add_argument("-f", "--filter", nargs="?", const="")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("-h", "--help", action="store_true")

    args = parser.parse_args()

    if args.help:
        show_help()

    print("Jira Subtask Creator V0.7")
    print("-------------------------")

    base_url, user, token = read_login()
    auth = HTTPBasicAuth(user, token)

    definitions = load_subtask_definitions()

    if args.filter is not None:
        sprint_name = select_sprint_filtered(base_url, auth, args.filter)
    else:
        sprint_name = input("Sprintname (exakt, ENTER = Beenden): ").strip()

        if sprint_name == "":
            print("Programm wird beendet.")
            input("ENTER zum Bestätigen...")
            sys.exit(0)

        if not validate_exact_sprint(base_url, auth, sprint_name):
            print("Sprint nicht gefunden.")
            input("ENTER zum Beenden...")
            sys.exit(0)

    print(f"\nSprint: {sprint_name}")

    print("Lade Issues...")

    issues = search_issues_in_sprint(base_url, auth, sprint_name)
    issues = [i for i in issues if not is_subtask(i)]

    print(f"{len(issues)} Issues gefunden.\n")

    report = []

    for issue in issues:

        fields = issue["fields"]
        labels = fields.get("labels", [])

        existing = {s["fields"]["summary"] for s in fields.get("subtasks", [])}

        created, skipped = [], []

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
    print("REPORT")
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