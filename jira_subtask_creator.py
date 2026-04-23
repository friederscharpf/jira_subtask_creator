#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
===============================================================================
Datei        : jira_subtask_creator.py
Version      : V0.1
Autor        : ChatGPT

===============================================================================
BESCHREIBUNG
===============================================================================

Dieses Python-Programm verbindet sich mit einer Atlassian JIRA Cloud Instanz
über die REST API und erstellt automatisch Unteraufgaben (Subtasks) für alle
Issues eines angegebenen Sprints.

Dabei werden automatisch alle Definitionsdateien im Unterordner:

    ./Subtasks/

eingelesen.

Beispiele:

    Subtasks/Subtasks_Impl.txt
    Subtasks/Subtasks_Spez.txt
    Subtasks/Subtasks_Test.txt

Der Dateiname bestimmt das erforderliche Label / Stichwort.

Beispiel:

    Subtasks_Impl.txt

=> Alle Issues im Sprint, die das Label:

    Impl

besitzen, erhalten die dort definierten Unteraufgaben.

-------------------------------------------------------------------------------
UNTERSTÜTZTE ISSUE-TYPEN
-------------------------------------------------------------------------------

Es werden ALLE Issue-Typen berücksichtigt:

- Story
- Task
- Bug
- Epic (falls im Sprint)
- Eigene Custom Typen
- usw.

Nur bereits vorhandene Unteraufgaben selbst werden ignoriert.

-------------------------------------------------------------------------------
WICHTIGE FUNKTIONEN
-------------------------------------------------------------------------------

✔ Sprint darf aktiv, geplant oder im Backlog sein  
✔ Alle Subtask-Dateien werden automatisch erkannt  
✔ Labels werden ausgewertet  
✔ Vorhandene Unteraufgaben werden erkannt  
✔ Doppelte Unteraufgaben werden nicht erneut angelegt  
✔ Abschließende Übersichtsausgabe je Issue

-------------------------------------------------------------------------------
DATEISTRUKTUR
-------------------------------------------------------------------------------

jira_subtask_creator.py
confluence_login.txt
Subtasks/
    Subtasks_Impl.txt
    Subtasks_Spez.txt
    Subtasks_Test.txt

-------------------------------------------------------------------------------
DATEI: confluence_login.txt
-------------------------------------------------------------------------------

3 Zeilen:

    https://deinfirma.atlassian.net
    deine.mail@firma.de
    API_TOKEN

-------------------------------------------------------------------------------
DATEI: Subtasks/Subtasks_Impl.txt
-------------------------------------------------------------------------------

Eine Zeile = ein Subtask Titel

Beispiel:

    Code erstellen
    Unit Test erstellen
    Review durchführen

-------------------------------------------------------------------------------
VERWENDUNG
-------------------------------------------------------------------------------

Start:

    python jira_subtask_creator.py

Dann Sprintname eingeben:

    Sprint 42

-------------------------------------------------------------------------------
CHANGELOG
-------------------------------------------------------------------------------

V0.0
- Erstversion

V0.1
- Programmname angepasst
- Subtasks Ordner eingeführt
- Mehrere Subtask-Dateien möglich
- Label-Auswertung statt Summary Text
- Alle Issue Typen erlaubt
- Sprintstatus irrelevant
- Übersicht am Ende
- Vorhandene Unteraufgaben erkennen

===============================================================================
"""

import os
import sys
import glob
import requests
from requests.auth import HTTPBasicAuth

LOGIN_FILE = "confluence_login.txt"
SUBTASK_DIR = "Subtasks"


# ============================================================================
# HILFSFUNKTIONEN
# ============================================================================

def read_login():
    if not os.path.exists(LOGIN_FILE):
        print(f"Fehler: {LOGIN_FILE} nicht gefunden.")
        sys.exit(1)

    with open(LOGIN_FILE, "r", encoding="utf-8") as f:
        lines = [x.strip() for x in f.readlines() if x.strip()]

    if len(lines) < 3:
        print("Fehlerhafte Login-Datei.")
        sys.exit(1)

    return lines[0], lines[1], lines[2]


def load_subtask_definitions():
    """
    Lädt alle Dateien Subtasks_*.txt
    Rückgabe:
        {
            "Impl": ["Code", "Test"],
            "Spez": [...]
        }
    """
    result = {}

    if not os.path.isdir(SUBTASK_DIR):
        print(f"Fehler: Ordner '{SUBTASK_DIR}' fehlt.")
        sys.exit(1)

    files = glob.glob(os.path.join(SUBTASK_DIR, "Subtasks_*.txt"))

    for file in files:
        name = os.path.basename(file)
        label = name.replace("Subtasks_", "").replace(".txt", "").strip()

        with open(file, "r", encoding="utf-8") as f:
            tasks = [x.strip() for x in f.readlines() if x.strip()]

        if tasks:
            result[label] = tasks

    return result


def jira_get(base_url, auth, endpoint, params=None):
    url = base_url + endpoint
    r = requests.get(url, auth=auth, params=params)
    r.raise_for_status()
    return r.json()


def jira_post(base_url, auth, endpoint, payload):
    url = base_url + endpoint
    headers = {"Content-Type": "application/json"}
    r = requests.post(url, auth=auth, json=payload, headers=headers)
    r.raise_for_status()
    return r.json()


# ============================================================================
# JIRA FUNKTIONEN
# ============================================================================

def search_issues_in_sprint(base_url, auth, sprint_name):
    """
    Holt alle Issues eines Sprints.
    """
    jql = f'sprint = "{sprint_name}"'

    params = {
        "jql": jql,
        "maxResults": 200,
        "fields": "summary,labels,issuetype,project,subtasks"
    }

    data = jira_get(base_url, auth, "/rest/api/3/search", params)
    return data["issues"]


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
    print("JIRA Subtask Creator V0.1")
    print("--------------------------")

    sprint = input("Sprintname eingeben: ").strip()

    if not sprint:
        print("Kein Sprint angegeben.")
        return

    base_url, user, token = read_login()
    auth = HTTPBasicAuth(user, token)

    definitions = load_subtask_definitions()

    if not definitions:
        print("Keine Subtask Definitionen gefunden.")
        return

    print("\nGefundene Regeln:")
    for label in definitions:
        print(f" - Label '{label}' -> {len(definitions[label])} Subtasks")

    print("\nLade Sprint Issues...")

    try:
        issues = search_issues_in_sprint(base_url, auth, sprint)
    except Exception as e:
        print("Fehler beim Laden:", e)
        return

    if not issues:
        print("Keine Issues gefunden.")
        return

    summary = []

    for issue in issues:

        key = issue["key"]
        fields = issue["fields"]

        issue_type = fields["issuetype"]["name"]
        title = fields["summary"]
        labels = fields.get("labels", [])

        existing = set()
        for s in fields.get("subtasks", []):
            existing.add(s["fields"]["summary"])

        created = []
        skipped = []

        for label in labels:
            if label in definitions:

                for subtask_title in definitions[label]:

                    if subtask_title in existing:
                        skipped.append(subtask_title)
                        continue

                    try:
                        create_subtask(base_url, auth, issue, subtask_title)
                        created.append(subtask_title)
                        existing.add(subtask_title)

                    except Exception:
                        skipped.append(subtask_title)

        summary.append({
            "key": key,
            "type": issue_type,
            "title": title,
            "created": created,
            "skipped": skipped
        })

    # Abschlussbericht
    print("\n")
    print("=" * 70)
    print("ERGEBNISÜBERSICHT")
    print("=" * 70)

    for item in summary:
        print(f"\n{item['key']} [{item['type']}] {item['title']}")

        if item["created"]:
            print("  Erstellt:")
            for x in item["created"]:
                print(f"    + {x}")

        if item["skipped"]:
            print("  Bereits vorhanden / übersprungen:")
            for x in item["skipped"]:
                print(f"    - {x}")

        if not item["created"] and not item["skipped"]:
            print("  Keine passenden Labels / keine Aktion.")

    print("\nFertig.")


if __name__ == "__main__":
    main()