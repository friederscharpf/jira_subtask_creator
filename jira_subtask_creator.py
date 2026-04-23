#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
===============================================================================
Datei        : jira_subtask_creator.py
Version      : V0.3
Autor        : ChatGPT

===============================================================================
BESCHREIBUNG
===============================================================================

Dieses Python-Programm verbindet sich mit Atlassian Jira Cloud über die REST API
und erstellt automatisch Unteraufgaben (Subtasks) für Issues eines angegebenen
Sprints.

Die anzulegenden Unteraufgaben werden aus Textdateien im Unterordner:

    ./Subtasks/

geladen.

Beispiele:

    Subtasks/Subtasks_Impl.txt
    Subtasks/Subtasks_Test.txt
    Subtasks/Subtasks_Spez.txt

Der Dateiname definiert das benötigte Label.

Beispiel:

    Subtasks_Impl.txt

=> Alle Issues im Sprint mit dem Label:

    Impl

erhalten die darin definierten Unteraufgaben.

===============================================================================
UNTERSTÜTZTE ISSUE-TYPEN
===============================================================================

Es werden alle normalen Sprint-Issues berücksichtigt, z.B.:

- Story
- Task
- Bug
- Epic (falls im Sprint)
- Eigene Custom Typen

Bereits vorhandene Subtasks werden erkannt.

Reine Subtasks selbst werden NICHT separat verarbeitet und NICHT separat in der
Ergebnisübersicht angezeigt.

===============================================================================
FUNKTIONEN
===============================================================================

✔ Jira Cloud Search API (/rest/api/3/search/jql)
✔ Sprint darf aktiv / geplant / backlog sein
✔ Mehrere Label-Dateien möglich
✔ Vorhandene Unteraufgaben erkennen
✔ Keine doppelten Unteraufgaben erstellen
✔ Pagination für große Sprints
✔ Dry-Run Modus
✔ Abschlussübersicht je Haupt-Issue

===============================================================================
VERZEICHNISSTRUKTUR
===============================================================================

jira_subtask_creator.py
confluence_login.txt
Subtasks/
    Subtasks_Impl.txt
    Subtasks_Test.txt
    Subtasks_Spez.txt

===============================================================================
DATEI: confluence_login.txt
===============================================================================

Die Datei muss im gleichen Verzeichnis liegen.

Inhalt (3 Zeilen):

    https://deinfirma.atlassian.net
    deine.mail@firma.de
    API_TOKEN

Zeile 1 = Jira URL
Zeile 2 = Login Mailadresse
Zeile 3 = Atlassian API Token

API Token erstellen:

https://id.atlassian.com/manage-profile/security/api-tokens

===============================================================================
DATEI: Subtasks/Subtasks_Impl.txt
===============================================================================

Eine Zeile = ein Unteraufgaben-Titel

Beispiel:

    Code erstellen
    Unit Test erstellen
    Review durchführen

===============================================================================
VERWENDUNG
===============================================================================

Normal starten:

    python jira_subtask_creator.py

Dry Run (nur anzeigen, nichts erstellen):

    python jira_subtask_creator.py --dry-run

Danach Sprintnamen eingeben:

    Sprint Team 2

===============================================================================
ERGEBNISÜBERSICHT
===============================================================================

Für jedes Haupt-Issue wird angezeigt:

- Welche Unteraufgaben erstellt wurden
- Welche bereits vorhanden waren
- Welche übersprungen wurden

Subtasks selbst erscheinen NICHT als eigener Eintrag.

===============================================================================
CHANGELOG
===============================================================================

V0.0
- Erstversion

V0.1
- Mehrere Definitionsdateien
- Labels statt Summary Text
- Alle Issue Typen

V0.2
- Neue Jira Search API
- Pagination
- Dry Run
- Verbesserte Fehlerbehandlung

V0.3
- Subtasks werden nicht mehr separat in Übersicht angezeigt
- Nur Haupt-Issues werden verarbeitet

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
# HILFSFUNKTIONEN
# ============================================================================

def read_login():
    """Liest Login-Datei ein."""
    if not os.path.exists(LOGIN_FILE):
        sys.exit(f"Fehler: {LOGIN_FILE} nicht gefunden.")

    with open(LOGIN_FILE, "r", encoding="utf-8") as f:
        lines = [x.strip() for x in f.readlines() if x.strip()]

    if len(lines) < 3:
        sys.exit("Fehler: confluence_login.txt benötigt 3 Zeilen.")

    return lines[0], lines[1], lines[2]


def load_subtask_definitions():
    """
    Lädt alle Dateien:
        Subtasks/Subtasks_*.txt

    Rückgabe:
        {
            "Impl": ["Code erstellen", "Review"],
            "Test": [...]
        }
    """
    result = {}

    if not os.path.isdir(SUBTASK_DIR):
        sys.exit(f"Fehler: Ordner '{SUBTASK_DIR}' fehlt.")

    files = glob.glob(os.path.join(SUBTASK_DIR, "Subtasks_*.txt"))

    for file in files:
        filename = os.path.basename(file)

        label = filename.replace("Subtasks_", "").replace(".txt", "").strip()

        with open(file, "r", encoding="utf-8") as f:
            tasks = [x.strip() for x in f.readlines() if x.strip()]

        if tasks:
            # doppelte Einträge entfernen
            result[label] = list(dict.fromkeys(tasks))

    return result


def jira_get(base_url, auth, endpoint, params=None):
    """HTTP GET an Jira."""
    r = requests.get(base_url + endpoint, auth=auth, params=params)

    if not r.ok:
        raise Exception(f"{r.status_code}: {r.text}")

    return r.json()


def jira_post(base_url, auth, endpoint, payload):
    """HTTP POST an Jira."""
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
# JIRA FUNKTIONEN
# ============================================================================

def search_issues_in_sprint(base_url, auth, sprint_name):
    """
    Lädt alle Issues des angegebenen Sprints mit Pagination.
    """
    start_at = 0
    max_results = 100
    all_issues = []

    while True:

        params = {
            "jql": f'sprint = "{sprint_name}" ORDER BY key',
            "startAt": start_at,
            "maxResults": max_results,
            "fields": "summary,labels,issuetype,project,subtasks,parent"
        }

        data = jira_get(base_url, auth, "/rest/api/3/search/jql", params)

        issues = data.get("issues", [])
        all_issues.extend(issues)

        if len(issues) < max_results:
            break

        start_at += max_results

    return all_issues


def is_subtask(issue):
    """
    Erkennt, ob Issue selbst ein Subtask ist.
    """
    fields = issue["fields"]

    if fields.get("parent"):
        return True

    issuetype = fields.get("issuetype", {})
    return issuetype.get("subtask", False)


def create_subtask(base_url, auth, issue, title):
    """
    Erstellt Unteraufgabe.
    """
    payload = {
        "fields": {
            "project": {
                "key": issue["fields"]["project"]["key"]
            },
            "parent": {
                "key": issue["key"]
            },
            "summary": title,
            "issuetype": {
                "name": "Sub-task"
            }
        }
    }

    return jira_post(base_url, auth, "/rest/api/3/issue", payload)


# ============================================================================
# MAIN
# ============================================================================

def main():

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Nur anzeigen, nichts erstellen"
    )

    args = parser.parse_args()

    print("Jira Subtask Creator V0.3")
    print("-------------------------")

    if args.dry_run:
        print("DRY RUN aktiv - keine Änderungen werden durchgeführt.\n")

    sprint = input("Sprintname eingeben: ").strip()

    if not sprint:
        print("Abbruch.")
        return

    base_url, user, token = read_login()
    auth = HTTPBasicAuth(user, token)

    definitions = load_subtask_definitions()

    print("\nGefundene Regeln:")

    for label, tasks in definitions.items():
        print(f"  {label}: {len(tasks)} Einträge")

    print("\nLade Sprint Issues...")

    try:
        issues = search_issues_in_sprint(base_url, auth, sprint)
    except Exception as e:
        print(f"\nFehler beim Laden: {e}")
        return

    # Nur Haupt-Issues behalten
    issues = [x for x in issues if not is_subtask(x)]

    print(f"{len(issues)} Haupt-Issues gefunden.")

    report = []

    for issue in issues:

        key = issue["key"]
        fields = issue["fields"]

        issue_type = fields["issuetype"]["name"]
        summary = fields["summary"]
        labels = fields.get("labels", [])

        existing = set()

        for sub in fields.get("subtasks", []):
            existing.add(sub["fields"]["summary"])

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
                    created.append(task + " [DRY RUN]")
                    existing.add(task)
                    continue

                try:
                    create_subtask(base_url, auth, issue, task)
                    created.append(task)
                    existing.add(task)

                except Exception:
                    skipped.append(task + " [Fehler]")

        report.append({
            "key": key,
            "type": issue_type,
            "summary": summary,
            "created": created,
            "skipped": skipped
        })

    # ========================================================================
    # AUSGABE
    # ========================================================================

    print("\n" + "=" * 72)
    print("ERGEBNISÜBERSICHT")
    print("=" * 72)

    for item in report:

        print(f"\n{item['key']} [{item['type']}] {item['summary']}")

        if item["created"]:
            print("  Erstellt:")
            for x in item["created"]:
                print(f"    + {x}")

        if item["skipped"]:
            print("  Bereits vorhanden / übersprungen:")
            for x in item["skipped"]:
                print(f"    - {x}")

        if not item["created"] and not item["skipped"]:
            print("  Keine Aktion.")

    print("\nFertig.")


if __name__ == "__main__":
    main()