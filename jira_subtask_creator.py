#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
===============================================================================
Datei        : jira_subtask_creator.py
Version      : V0.2
Autor        : ChatGPT

===============================================================================
BESCHREIBUNG
===============================================================================

Dieses Python-Programm verbindet sich mit Atlassian Jira Cloud über die REST API
und erstellt automatisch Unteraufgaben (Subtasks) für alle Issues eines
angegebenen Sprints.

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

=> Alle Issues im Sprint mit Label:

    Impl

erhalten die darin definierten Unteraufgaben.

===============================================================================
NEUERUNGEN IN V0.2
===============================================================================

✔ Jira Cloud neue Search API (/search/jql)
✔ Pagination für >100 / >200 Issues
✔ robuste Fehlerausgabe
✔ Dry-Run Modus (nur anzeigen, nichts anlegen)
✔ doppelte Unteraufgaben verhindern
✔ Abschlussübersicht verbessert
✔ internes Logging in Konsole

===============================================================================
VERZEICHNISSTRUKTUR
===============================================================================

jira_subtask_creator.py
confluence_login.txt
Subtasks/
    Subtasks_Impl.txt
    Subtasks_Test.txt

===============================================================================
LOGIN DATEI
===============================================================================

Datei: confluence_login.txt

Zeile 1:
    https://deinfirma.atlassian.net

Zeile 2:
    deine.mail@firma.de

Zeile 3:
    API_TOKEN

===============================================================================
VERWENDUNG
===============================================================================

Normal:

    python jira_subtask_creator.py

Dry Run:

    python jira_subtask_creator.py --dry-run

===============================================================================
CHANGELOG
===============================================================================

V0.0
- Erstversion

V0.1
- Labels / mehrere Dateien / Übersicht

V0.2
- neue Jira Search API
- Pagination
- Dry Run
- Verbesserungen

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
    if not os.path.exists(LOGIN_FILE):
        sys.exit(f"Fehler: {LOGIN_FILE} nicht gefunden.")

    with open(LOGIN_FILE, "r", encoding="utf-8") as f:
        lines = [x.strip() for x in f.readlines() if x.strip()]

    if len(lines) < 3:
        sys.exit("Fehler: confluence_login.txt benötigt 3 Zeilen.")

    return lines[0], lines[1], lines[2]


def load_subtask_definitions():
    """
    Lädt alle Dateien Subtasks_*.txt
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
            result[label] = list(dict.fromkeys(tasks))

    return result


def jira_get(base_url, auth, endpoint, params=None):
    url = base_url + endpoint
    r = requests.get(url, auth=auth, params=params)

    if not r.ok:
        raise Exception(f"{r.status_code}: {r.text}")

    return r.json()


def jira_post(base_url, auth, endpoint, payload):
    url = base_url + endpoint
    headers = {"Content-Type": "application/json"}

    r = requests.post(url, auth=auth, json=payload, headers=headers)

    if not r.ok:
        raise Exception(f"{r.status_code}: {r.text}")

    return r.json()


# ============================================================================
# JIRA FUNKTIONEN
# ============================================================================

def search_issues_in_sprint(base_url, auth, sprint_name):
    """
    Holt alle Issues eines Sprints per Pagination.
    """
    start_at = 0
    max_results = 100
    all_issues = []

    while True:
        params = {
            "jql": f'sprint = "{sprint_name}" ORDER BY key',
            "startAt": start_at,
            "maxResults": max_results,
            "fields": "summary,labels,issuetype,project,subtasks"
        }

        data = jira_get(base_url, auth, "/rest/api/3/search/jql", params)

        issues = data.get("issues", [])
        all_issues.extend(issues)

        if len(issues) < max_results:
            break

        start_at += max_results

    return all_issues


def create_subtask(base_url, auth, issue, title):
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
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    print("Jira Subtask Creator V0.2")
    print("-------------------------")

    if args.dry_run:
        print("DRY RUN aktiv - es werden keine Subtasks erstellt.\n")

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

    print(f"{len(issues)} Issues gefunden.\n")

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

                except Exception as e:
                    skipped.append(task + f" [Fehler]")

        report.append({
            "key": key,
            "type": issue_type,
            "summary": summary,
            "created": created,
            "skipped": skipped
        })

    # =========================================================================
    # AUSGABE
    # =========================================================================

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