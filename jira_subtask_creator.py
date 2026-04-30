#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import glob
import argparse
import requests
from requests.auth import HTTPBasicAuth

APP_VERSION = "V1.0"

DOCUMENTATION = f"""
===============================================================================
Datei        : jira_subtask_creator.py
Version      : {APP_VERSION}
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

Beispiel Datei:

    Subtasks/Subtasks_Impl.txt

Beispiel Inhalt:

    Implementierung durchführen
    Unit Tests erstellen
    Review durchführen

Wichtig:

- Der Teil nach "Subtasks_" und vor ".txt" ist das Jira Label.
- Die Datei "Subtasks_Impl.txt" gilt also für Issues mit dem Label "Impl".
- Das Label muss exakt so im Jira Issue vorhanden sein.
- Jede nicht-leere Zeile wird als eigener Subtask-Titel verwendet.
- Doppelte Zeilen innerhalb einer Datei werden intern entfernt.
- Bereits vorhandene Subtasks mit gleichem Titel werden nicht erneut erstellt.

===============================================================================
LOGIN DATEI
===============================================================================

confluence_login.txt (3 Zeilen):

    https://your-domain.atlassian.net
    email@domain.com
    API_TOKEN

Beispiel:

    https://example.atlassian.net
    max.mustermann@example.com
    ATATT3xFfGF0...

Wichtig:

- Die Datei muss im gleichen Verzeichnis wie jira_subtask_creator.py liegen.
- Die erste Zeile ist die Jira Cloud Basis-URL.
- Die zweite Zeile ist die Atlassian Login-E-Mail-Adresse.
- Die dritte Zeile ist der Atlassian API Token.
- Leerzeilen werden ignoriert.
- Die Datei sollte nicht in ein Git Repository eingecheckt werden.

===============================================================================
TOKEN / RECHTE / SCOPES
===============================================================================

Hinweis zu scoped API Tokens:

Für dieses Tool wird aktuell ein klassischer / unscoped Atlassian API Token
empfohlen, da die verwendete Jira Software Agile API
/rest/agile/1.0/board und /rest/agile/1.0/board/{id}/sprint mit scoped API
Tokens je nach Atlassian Cloud Umgebung mit 401 fehlschlagen kann.

Wenn ein scoped Token verwendet wird und der Fehler
"401: Client must be authenticated to access this resource" beim Zugriff auf
/rest/agile/1.0/board erscheint, sollte ein klassischer API Token verwendet
werden.


Scoped Token:

Das Programm benötigt keinen API Token mit Vollzugriff, wenn ein Token mit
Scopes verwendet wird.

Benötigt werden mindestens Rechte zum:

1. Lesen von Boards und Sprints
2. Suchen und Lesen von Jira Issues
3. Erstellen von Issues / Subtasks

Empfohlene klassische Jira Scopes:

    read:jira-work
    write:jira-work
    read:jira-user

Bei granularen Jira / Jira Software Scopes können zusätzlich bzw. alternativ
folgende Berechtigungen nötig sein:

    read:board-scope:jira-software
    read:sprint:jira-software
    read:issue-details:jira
    read:project:jira
    write:issue:jira

Zusätzlich muss der Jira Benutzer, zu dem der API Token gehört, im jeweiligen
Projekt ausreichende Jira-Projektrechte besitzen:

- Boards und Sprints sehen
- Issues im Sprint sehen
- Issues/Subtasks erstellen
- Subtask-Issue-Type im Projekt verwenden dürfen

Hinweis:

Die exakten Scopes können je nach Atlassian Cloud Umgebung, Token-Typ,
Service-Account-Konfiguration und Jira-Projektberechtigungen abweichen.
Wenn das Lesen funktioniert, aber das Erstellen fehlschlägt, fehlt meist eine
Write-Berechtigung oder das Projekt erlaubt dem Benutzer keine Subtask-Erstellung.

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

Beispiel:

    python jira_subtask_creator.py

Danach Eingabe:

    Sprintname (exakt, ENTER = Beenden): Sprint Team 2

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

Beispiele:

    python jira_subtask_creator.py -f
    python jira_subtask_creator.py --filter
    python jira_subtask_creator.py -f ""
    python jira_subtask_creator.py -f "Team 2"

===============================================================================
DRY RUN
===============================================================================

--dry-run:

- Simulation
- keine Änderungen in Jira
- gleiche Ausgabe wie produktiv mit vollständigem Report

Beispiele:

    python jira_subtask_creator.py --dry-run
    python jira_subtask_creator.py -f "Team 2" --dry-run

===============================================================================
BENÖTIGTE DATEI- UND ORDNERSTRUKTUR
===============================================================================

Minimal erforderlich:

    jira_subtask_creator.py
    confluence_login.txt
    Subtasks/
        Subtasks_Impl.txt

Beispiel mit mehreren Label-Dateien:

    jira_subtask_creator.py
    confluence_login.txt
    Subtasks/
        Subtasks_Impl.txt
        Subtasks_Test.txt
        Subtasks_Spez.txt

Bei Verwendung als Binary / EXE:

    jira_subtask_creator
    confluence_login.txt
    Subtasks/
        Subtasks_Impl.txt

oder unter Windows:

    jira_subtask_creator.exe
    confluence_login.txt
    Subtasks/
        Subtasks_Impl.txt

Wichtig:

- confluence_login.txt wird nicht in die Binary eingebettet.
- Der Ordner Subtasks wird nicht in die Binary eingebettet.
- Beide müssen beim Start neben dem Skript bzw. neben der Binary liegen.

===============================================================================
BEISPIELABLAUF
===============================================================================

1. confluence_login.txt anlegen

    https://example.atlassian.net
    max.mustermann@example.com
    API_TOKEN

2. Subtask-Datei anlegen

    Subtasks/Subtasks_Impl.txt

3. Subtask-Titel eintragen

    Implementierung durchführen
    Unit Tests erstellen
    Review durchführen

4. In Jira einem Issue im Sprint das Label "Impl" geben

5. Programm starten

    python jira_subtask_creator.py -f

6. Sprint auswählen

7. Programm erstellt die fehlenden Subtasks

===============================================================================
ERGEBNISBERICHT
===============================================================================

Am Ende wird ein Report ausgegeben.

Für jedes Haupt-Issue wird angezeigt:

- Jira Key
- Issue Typ
- Summary
- verwendetes Label
- erstellte Subtasks je Label
- übersprungene Subtasks je Label

Übersprungen bedeutet:

- Subtask war bereits vorhanden
- oder Subtask konnte nicht erstellt werden

Wenn ein Issue mehrere Labels besitzt, zu denen Subtask-Dateien existieren,
werden die erstellten und übersprungenen Subtasks im Report je Label gruppiert.
Dadurch ist eindeutig sichtbar, aus welcher Subtask-Definitionsdatei bzw. durch
welches Jira Label die jeweilige Unteraufgabe erzeugt oder übersprungen wurde.

Subtasks selbst werden nicht als eigene Haupt-Issues verarbeitet.

===============================================================================
NEUERUNG V0.7
===============================================================================

✔ Explizite Meldung bei geschlossenem Sprint
✔ keine Subtask-Erstellung bei geschlossenen Sprints
✔ klare Abbruchmeldung inkl. Sprintname
✔ konsistente Statusprüfung im Standardmodus

===============================================================================
NEUERUNG V1.0
===============================================================================

✔ V0.7 wurde als erste stabile Hauptversion übernommen
✔ Programmversion wird zentral über APP_VERSION definiert
✔ Programmausgabe und Hilfe verwenden APP_VERSION
✔ Hilfe wurde für Binary-/EXE-Nutzung erweitert
✔ Hilfe beschreibt benötigte Dateien und Ordner ausführlicher
✔ Hilfe beschreibt empfohlene Token-Rechte und Scopes
✔ Dokumentation beschreibt Nutzung als Python-Skript und als Binary/EXE
✔ Report zeigt erstellte und übersprungene Subtasks gruppiert je Label

===============================================================================
JIRA API
===============================================================================

- /rest/api/3/search/jql
- /rest/api/3/issue
- /rest/agile/1.0/board
- /rest/agile/1.0/board/{{id}}/sprint

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
V1.0  Erste stabile Hauptversion auf Basis von V0.7
      Zentrale Versionsdefinition über APP_VERSION
      Erweiterte Hilfe für Binary-/EXE-Nutzung
      Erweiterte Beschreibung der benötigten Dateien
      Erweiterte Beschreibung der API-Token-Rechte
      Reportausgabe gruppiert erstellte und übersprungene Subtasks je Label

===============================================================================
"""

__doc__ = DOCUMENTATION

LOGIN_FILE = "confluence_login.txt"
SUBTASK_DIR = "Subtasks"


# ============================================================================
# HELP
# ============================================================================

def show_help():
    print(f"""
Jira Subtask Creator {APP_VERSION}

===============================================================================
AUFRUF
===============================================================================

Python Skript:

  python jira_subtask_creator.py
  python jira_subtask_creator.py -f
  python jira_subtask_creator.py -f "Team 2"
  python jira_subtask_creator.py --dry-run

Linux Binary:

  ./jira_subtask_creator
  ./jira_subtask_creator -f
  ./jira_subtask_creator -f "Team 2"
  ./jira_subtask_creator --dry-run

Windows EXE:

  jira_subtask_creator.exe
  jira_subtask_creator.exe -f
  jira_subtask_creator.exe -f "Team 2"
  jira_subtask_creator.exe --dry-run

===============================================================================
OPTIONEN
===============================================================================

  -f, --filter [TEXT]   Sprintauswahl aus Liste
                        Ohne TEXT werden alle offenen/aktiven Sprints angezeigt.
                        Mit TEXT werden nur Sprints angezeigt, deren Name diesen
                        Text enthält.

  --dry-run             Simulation.
                        Es werden keine Änderungen in Jira durchgeführt.

  -h, --help            Diese Hilfe anzeigen.

===============================================================================
BENÖTIGTE DATEIEN
===============================================================================

Im gleichen Verzeichnis wie das Skript bzw. die Binary müssen liegen:

  confluence_login.txt
  Subtasks/

Beispielstruktur:

  jira_subtask_creator
  confluence_login.txt
  Subtasks/
      Subtasks_Impl.txt
      Subtasks_Test.txt

Oder bei Windows:

  jira_subtask_creator.exe
  confluence_login.txt
  Subtasks/
      Subtasks_Impl.txt
      Subtasks_Test.txt

===============================================================================
DATEI: confluence_login.txt
===============================================================================

Die Datei muss genau diese Informationen enthalten:

  Zeile 1: Jira Cloud URL
  Zeile 2: Login E-Mail-Adresse
  Zeile 3: Atlassian API Token

Beispiel:

  https://example.atlassian.net
  max.mustermann@example.com
  ATATT3xFfGF0...

Wichtig:

  - Die Datei nicht in Git einchecken.
  - Der Token wird wie ein Passwort behandelt.
  - Der Token muss zum Benutzer passen, der in Zeile 2 angegeben ist.

===============================================================================
ORDNER: Subtasks
===============================================================================

In diesem Ordner liegen die Subtask-Definitionen.

Dateinamensschema:

  Subtasks_<LABEL>.txt

Beispiele:

  Subtasks_Impl.txt
  Subtasks_Test.txt
  Subtasks_Spez.txt

Bedeutung:

  Subtasks_Impl.txt

  → gilt für Jira Issues mit dem Label "Impl"

Inhalt der Datei:

  Eine Zeile = ein Subtask-Titel

Beispielinhalt:

  Implementierung durchführen
  Unit Tests erstellen
  Review durchführen

===============================================================================
TOKEN / RECHTE / SCOPES
===============================================================================

Hinweis zu scoped API Tokens:

Für dieses Tool wird aktuell ein klassischer / unscoped Atlassian API Token
empfohlen, da die verwendete Jira Software Agile API
/rest/agile/1.0/board und /rest/agile/1.0/board/{id}/sprint mit scoped API
Tokens je nach Atlassian Cloud Umgebung mit 401 fehlschlagen kann.

Wenn ein scoped Token verwendet wird und der Fehler
"401: Client must be authenticated to access this resource" beim Zugriff auf
/rest/agile/1.0/board erscheint, sollte ein klassischer API Token verwendet
werden.


Scoped Token:

Das Programm benötigt Rechte zum:

  - Lesen von Jira Boards
  - Lesen von Jira Sprints
  - Suchen und Lesen von Jira Issues
  - Erstellen von Jira Subtasks

Empfohlene klassische Jira Scopes:

  read:jira-work
  write:jira-work
  read:jira-user

Bei granularen Jira / Jira Software Scopes können zusätzlich bzw. alternativ
folgende Scopes nötig sein:

  read:board-scope:jira-software
  read:sprint:jira-software
  read:issue-details:jira
  read:project:jira
  write:issue:jira

Zusätzlich benötigt der Benutzer passende Jira-Projektrechte:

  - Issues ansehen
  - Boards/Sprints sehen
  - Issues erstellen
  - Subtasks erstellen

Ein Token mit vollständiger Admin-Freigabe ist dafür normalerweise nicht nötig.

===============================================================================
REPORT
===============================================================================

Der Report zeigt pro Haupt-Issue:

  - Jira Key
  - Issue Typ
  - Summary
  - Label
  - erstellte Subtasks
  - übersprungene Subtasks

Wenn mehrere Labels auf einem Issue vorhanden sind und zu diesen Labels passende
Subtask-Dateien existieren, wird die Ausgabe je Label gruppiert.

Beispiel:

  ABC-123 [Story] Beispiel Issue

    Label: Impl
      Erstellt:
        + Implementierung durchführen
      Übersprungen:
        - Unit Tests erstellen

    Label: Test
      Erstellt:
        + Testfall erstellen

===============================================================================
WICHTIGE REGELN
===============================================================================

  - Nur active und future Sprints erlaubt.
  - Closed Sprints werden abgelehnt.
  - Subtasks werden nur bei active und future Sprints erstellt.
  - Leere Eingaben beenden das Programm.
  - Bereits vorhandene Subtasks werden nicht erneut erstellt.
  - Subtasks selbst werden nicht weiter verarbeitet.

===============================================================================
BEISPIELE
===============================================================================

Alle offenen/aktiven Sprints anzeigen:

  python jira_subtask_creator.py -f

Nur Sprints mit "Team 2" im Namen anzeigen:

  python jira_subtask_creator.py -f "Team 2"

Simulation ohne Änderungen:

  python jira_subtask_creator.py -f "Team 2" --dry-run

Direkte exakte Sprint-Eingabe:

  python jira_subtask_creator.py

===============================================================================
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

    print(f"Jira Subtask Creator {APP_VERSION}")
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

        label_report = {}

        for label in labels:

            if label not in definitions:
                continue

            if label not in label_report:
                label_report[label] = {
                    "created": [],
                    "skipped": []
                }

            for task in definitions[label]:

                if task in existing:
                    label_report[label]["skipped"].append(task)
                    continue

                if args.dry_run:
                    label_report[label]["created"].append(task + " [DRY-RUN]")
                    continue

                try:
                    create_subtask(base_url, auth, issue, task)
                    label_report[label]["created"].append(task)
                    existing.add(task)
                except Exception:
                    label_report[label]["skipped"].append(task)

        report.append({
            "key": issue["key"],
            "type": fields["issuetype"]["name"],
            "summary": fields["summary"],
            "labels": label_report
        })

    print("\n" + "=" * 72)
    print("REPORT")
    print("=" * 72)

    for r in report:
        print(f"\n{r['key']} [{r['type']}] {r['summary']}")

        if not r["labels"]:
            print("  Keine Aktion.")

        for label, label_data in r["labels"].items():
            print(f"\n  Label: {label}")

            if label_data["created"]:
                print("    Erstellt:")
                for c in label_data["created"]:
                    print(f"      + {c}")

            if label_data["skipped"]:
                print("    Übersprungen:")
                for s in label_data["skipped"]:
                    print(f"      - {s}")

    print("\nFertig.")


if __name__ == "__main__":
    main()