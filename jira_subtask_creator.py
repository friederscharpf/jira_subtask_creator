#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import glob
import argparse
import requests
import pydoc
from requests.auth import HTTPBasicAuth

APP_VERSION = "V1.2"

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
   - über Menü
   - manuell per exakter Eingabe
   - über Filtermodus (-f / --filter)
   - direkt per Parameter (-s / --sprint)

2. Sprint wird validiert (inkl. Statusprüfung)
   - nur active und future erlaubt
   - closed wird blockiert

3. Alle Issues im Sprint werden geladen

4. Nur Haupt-Issues werden verarbeitet

5. Labels bestimmen Subtask-Definitionen

6. Fehlende Subtasks werden erstellt

7. Bereits vorhandene Subtasks werden übersprungen

8. Ergebnisbericht wird ausgegeben

9. Vor Programmende muss der Benutzer mit ENTER bestätigen.
   Das gilt auch für Fehlerfälle, damit sich ein Windows-Konsolenfenster beim
   Start per Doppelklick nicht sofort schließt.

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

Das Programm benötigt Rechte zum:

1. Lesen von Boards und Sprints
2. Suchen und Lesen von Jira Issues
3. Erstellen von Issues / Subtasks

Hinweis zu Atlassian API Tokens:

Für dieses Tool wird aktuell ein klassischer / unscoped Atlassian API Token
empfohlen, da die verwendete Jira Software Agile API:

    /rest/agile/1.0/board
    /rest/agile/1.0/board/{{id}}/sprint

mit scoped API Tokens je nach Atlassian Cloud Umgebung mit Fehlern wie:

    401: Client must be authenticated to access this resource

fehlschlagen kann, obwohl scheinbar passende Scopes gesetzt wurden.

Bei einem klassischen API Token muss zusätzlich der Jira Benutzer, zu dem der
API Token gehört, im jeweiligen Projekt ausreichende Jira-Projektrechte besitzen:

- Boards und Sprints sehen
- Issues im Sprint sehen
- Issues/Subtasks erstellen
- Subtask-Issue-Type im Projekt verwenden dürfen

Wenn das Lesen funktioniert, aber das Erstellen fehlschlägt, fehlt meist eine
Write-Berechtigung oder das Projekt erlaubt dem Benutzer keine Subtask-Erstellung.

===============================================================================
SPRINT VERHALTEN
===============================================================================

-------------------------------------------------
Menümodus
-------------------------------------------------

Aufruf ohne weitere Optionen:

    python jira_subtask_creator.py

oder als Binary:

    jira_subtask_creator.exe

Verhalten:

- Es erscheint ein interaktives Menü.
- Dort kann die Sprintauswahl per exaktem Namen gewählt werden.
- Dort kann die Sprintauswahl per Liste/Filter gewählt werden.
- Dry-Run kann im Menü umgeschaltet werden.
- Die Hilfe kann im Menü angezeigt werden.
- Nach dem Beenden der Hilfe mit ENTER kommt der Benutzer zurück ins Menü.
- ENTER ohne Auswahl beendet das Programm.

-------------------------------------------------
Standardmodus per Kommandozeile
-------------------------------------------------

Aufruf:

    python jira_subtask_creator.py -s "Sprint Team 2"
    python jira_subtask_creator.py --sprint "Sprint Team 2"

Verhalten:

- Sprintname muss exakt übergeben werden.
- Der Parameter -s / --sprint benötigt zwingend einen String.
- Ein leerer String ist ungültig.
- closed Sprint wird blockiert.
- active/future erlaubt.

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
    python jira_subtask_creator.py -s "Sprint Team 2" --dry-run

Im Menümodus wird Dry-Run über Menüpunkt 3 umgeschaltet:

    3. Dry-Run [ ]
    3. Dry-Run [x]

===============================================================================
HILFE IM MENÜ
===============================================================================

Ab Version V1.2 kann die Hilfe auch direkt im interaktiven Menü ausgewählt
werden.

Verhalten:

- Die Hilfe wird in einer Pager-Ansicht angezeigt, sofern das Terminal dies
  unterstützt.
- Dadurch kann die Hilfe auch in kleinen Terminalfenstern besser gelesen werden.
- Nach dem Schließen bzw. Beenden der Hilfe kommt der Benutzer wieder zurück
  ins Menü.
- Die Kommandozeilenoption -h / --help zeigt weiterhin die Hilfe an und beendet
  das Programm danach mit ENTER-Bestätigung.

Hinweis:

Das tatsächliche Scroll-Verhalten hängt vom verwendeten Terminal und Betriebssystem
ab. Unter Linux wird typischerweise ein Terminal-Pager verwendet. Unter Windows
wird die Hilfe mindestens vollständig ausgegeben und anschließend mit ENTER
beendet.

Zusätzliche technische Logik:

- Wenn das Programm erkennt, dass es in einem interaktiven Terminal ausgeführt
  wird, wird die Hilfe über pydoc.pager() ausgegeben.
- In Terminals mit funktionierendem Pager kann der Benutzer die Hilfe über den
  Pager schließen und kommt anschließend direkt zurück ins Menü.
- Wenn kein interaktives Terminal erkannt wird, wird die Hilfe direkt ausgegeben
  und der Benutzer muss mit ENTER bestätigen, bevor das Programm ins Menü
  zurückkehrt bzw. beendet wird.
- Dadurch wird vermieden, dass bei echten Pager-Terminals eine zusätzliche
  unnötige ENTER-Bestätigung erforderlich ist.
- Gleichzeitig bleibt das Verhalten für einfache Terminals, Windows-EXE-Starts
  und Umgebungen ohne Pager sicher lesbar.

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

    python jira_subtask_creator.py

6. Im Menü Sprintauswahl wählen

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
WINDOWS / EXE VERHALTEN
===============================================================================

Ab Version V1.1 wartet das Programm vor dem Beenden immer auf eine
ENTER-Bestätigung.

Dies ist besonders wichtig, wenn die Windows EXE per Doppelklick gestartet wird.
Ohne diese Bestätigung würde sich das Konsolenfenster bei Programmende oder bei
einem Fehler sofort schließen, sodass der Benutzer die Meldung nicht lesen kann.

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
NEUERUNG V1.1
===============================================================================

✔ Programm wartet vor jedem regulären Beenden auf ENTER
✔ Programm wartet auch bei Fehlerfällen auf ENTER
✔ Besseres Verhalten beim Start der Windows EXE per Doppelklick
✔ Neuer Menümodus beim Start ohne Kommandozeilenoptionen
✔ Dry-Run kann im Menü per [ ] / [x] umgeschaltet werden
✔ Neue Kommandozeilenoption -s / --sprint für exakte Sprintauswahl
✔ -s / --sprint benötigt einen nicht-leeren Sprintnamen

===============================================================================
NEUERUNG V1.2
===============================================================================

✔ Hilfe ist nun auch direkt im interaktiven Menü auswählbar
✔ Hilfe kehrt nach ENTER wieder ins Menü zurück
✔ Hilfeausgabe nutzt eine Pager-Ausgabe, sofern vom Terminal unterstützt
✔ Menü wurde um einen Hilfe-Menüpunkt erweitert
✔ Dokumentation wurde um das Hilfeverhalten im Menü erweitert
✔ Hilfeausgabe unterscheidet zwischen interaktivem Terminal und einfachem
  Ausgabemodus ohne Pager
✔ Bei funktionierendem Pager ist keine zusätzliche ENTER-Bestätigung nötig
✔ Ohne interaktiven Pager wird ENTER zur Rückkehr ins Menü bzw. zum Beenden
  abgefragt

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
V1.1  Windows-/EXE-Verhalten verbessert
      ENTER-Bestätigung vor Programmende und in Fehlerfällen
      Interaktives Hauptmenü beim Start ohne Optionen
      Dry-Run im Menü umschaltbar
      Neue Option -s / --sprint für direkte exakte Sprintauswahl
V1.2  Hilfe im interaktiven Menü ergänzt
      Hilfeausgabe mit Pager-Unterstützung ergänzt
      Rückkehr ins Menü nach Hilfeanzeige ergänzt
      Pager-/Nicht-Pager-Verhalten für Hilfeausgabe verbessert

===============================================================================
"""

__doc__ = DOCUMENTATION

LOGIN_FILE = "confluence_login.txt"
SUBTASK_DIR = "Subtasks"


# ============================================================================
# EXIT / PAUSE HANDLING
# ============================================================================

def wait_for_enter(message="ENTER zum Beenden..."):
    try:
        input(message)
    except EOFError:
        pass


def exit_with_enter(code=0, message=None):
    if message:
        print(message)
    wait_for_enter("ENTER zum Beenden...")
    sys.exit(code)


# ============================================================================
# ARGUMENT PARSER
# ============================================================================

class PausingArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        print(f"Fehler: {message}")
        print()
        self.print_help()
        print()
        exit_with_enter(2)


# ============================================================================
# HELP
# ============================================================================

def get_help_text():
    return f"""
Jira Subtask Creator {APP_VERSION}

===============================================================================
AUFRUF
===============================================================================

Python Skript:

  python jira_subtask_creator.py
  python jira_subtask_creator.py -s "Sprint Team 2"
  python jira_subtask_creator.py -f
  python jira_subtask_creator.py -f "Team 2"
  python jira_subtask_creator.py --dry-run

Linux Binary:

  ./jira_subtask_creator
  ./jira_subtask_creator -s "Sprint Team 2"
  ./jira_subtask_creator -f
  ./jira_subtask_creator -f "Team 2"
  ./jira_subtask_creator --dry-run

Windows EXE:

  jira_subtask_creator.exe
  jira_subtask_creator.exe -s "Sprint Team 2"
  jira_subtask_creator.exe -f
  jira_subtask_creator.exe -f "Team 2"
  jira_subtask_creator.exe --dry-run

===============================================================================
OPTIONEN
===============================================================================

  -s, --sprint TEXT     Sprintauswahl per exaktem Sprintnamen.
                        TEXT ist zwingend erforderlich und darf nicht leer sein.

  -f, --filter [TEXT]   Sprintauswahl aus Liste.
                        Ohne TEXT werden alle offenen/aktiven Sprints angezeigt.
                        Mit TEXT werden nur Sprints angezeigt, deren Name diesen
                        Text enthält.

  --dry-run             Simulation.
                        Es werden keine Änderungen in Jira durchgeführt.

  -h, --help            Diese Hilfe anzeigen.

===============================================================================
MENÜMODUS
===============================================================================

Wenn das Programm ohne Optionen gestartet wird, erscheint ein Menü:

  1. Sprint per exaktem Namen auswählen
  2. Sprint aus vorhandenen Sprints auswählen
  3. Dry-Run [ ] / [x]
  4. Hilfe anzeigen
  ENTER = Beenden

Wenn die Hilfe über das Menü geöffnet wird, kommt der Benutzer nach dem Beenden
der Hilfe wieder zurück ins Menü.

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
TOKEN / RECHTE
===============================================================================

Empfohlen wird ein klassischer Atlassian API Token.

Der Benutzer des Tokens benötigt im Jira Projekt Rechte zum:

  - Boards und Sprints sehen
  - Issues ansehen
  - Issues erstellen
  - Subtasks erstellen

Scoped API Tokens können bei der Jira Software Agile API je nach Atlassian Cloud
Umgebung mit 401 fehlschlagen.

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
"""


def show_help(exit_after=True):
    help_text = get_help_text()

    if sys.stdout.isatty():
        pydoc.pager(help_text)
    else:
        print(help_text)
        wait_for_enter("ENTER zum Fortfahren...")

    if exit_after:
        exit_with_enter(0)


# ============================================================================
# LOGIN
# ============================================================================

def read_login():
    if not os.path.exists(LOGIN_FILE):
        raise RuntimeError(f"Fehler: {LOGIN_FILE} nicht gefunden.")

    with open(LOGIN_FILE, "r", encoding="utf-8") as f:
        lines = [l.strip() for l in f.readlines() if l.strip()]

    if len(lines) < 3:
        raise RuntimeError(f"Fehler: {LOGIN_FILE} muss mindestens 3 nicht-leere Zeilen enthalten, siehe Hlfe -h or --help")

    return lines[0], lines[1], lines[2]


# ============================================================================
# SUBTASKS
# ============================================================================

def load_subtask_definitions():
    result = {}

    if not os.path.isdir(SUBTASK_DIR):
        raise RuntimeError(f"Fehler: Ordner '{SUBTASK_DIR}' fehlt.")

    files = glob.glob(os.path.join(SUBTASK_DIR, "Subtasks_*.txt"))

    if not files:
        raise RuntimeError(f"Fehler: Keine Dateien 'Subtasks_*.txt' im Ordner '{SUBTASK_DIR}' gefunden.")

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
        raise RuntimeError(f"{r.status_code}: {r.text}")
    return r.json()


def jira_post(base_url, auth, endpoint, payload):
    r = requests.post(
        base_url + endpoint,
        auth=auth,
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    if not r.ok:
        raise RuntimeError(f"{r.status_code}: {r.text}")
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
        exit_with_enter(0, "Keine offenen/aktiven Sprints gefunden.")

    print("\nVerfügbare offene/aktive Sprints:\n")

    for i, s in enumerate(sprints, 1):
        print(f"{i}. {sprint_label(s)}")

    while True:
        choice = input("\nSprint auswählen (ENTER = Abbruch): ").strip()

        if choice == "":
            print("Programm wird beendet.")
            exit_with_enter(0)

        if choice.isdigit() and 1 <= int(choice) <= len(sprints):
            return sprints[int(choice) - 1]["name"]

        print("Ungültige Auswahl.")
        print("Programm wird beendet.")
        exit_with_enter(0)


def validate_exact_sprint(base_url, auth, sprint_name):
    sprints = fetch_all_sprints(base_url, auth)

    for s in sprints:
        if s["name"] == sprint_name:

            if is_closed_sprint(s):
                print("\n========================================")
                print(f"SPRINT GESCHLOSSEN: {sprint_name}")
                print("Es werden KEINE Subtasks erstellt.")
                print("========================================\n")
                exit_with_enter(0)

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
# MENU
# ============================================================================

def show_main_menu(dry_run):
    dry_run_marker = "[x]" if dry_run else "[ ]"

    print("\n" + "=" * 72)
    print(f"Jira Subtask Creator {APP_VERSION}")
    print("=" * 72)
    print("1. Sprint per exaktem Namen auswählen")
    print("2. Sprint aus vorhandenen Sprints auswählen")
    print(f"3. Dry-Run {dry_run_marker}")
    print("4. Hilfe anzeigen")
    print()
    print("ENTER = Beenden")


def menu_select_sprint(base_url, auth, initial_dry_run):
    dry_run = initial_dry_run

    while True:
        show_main_menu(dry_run)
        choice = input("\nAuswahl: ").strip()

        if choice == "":
            print("Programm wird beendet.")
            exit_with_enter(0)

        if choice == "1":
            sprint_name = input("Sprintname (exakt, ENTER = Beenden): ").strip()

            if sprint_name == "":
                print()
                exit_with_enter(0)

            if not validate_exact_sprint(base_url, auth, sprint_name):
                print("Sprint nicht gefunden.")
                exit_with_enter(0)

            return sprint_name, dry_run

        if choice == "2":
            filter_string = input("Filtertext optional (ENTER = alle offenen/aktiven Sprints): ").strip()
            sprint_name = select_sprint_filtered(base_url, auth, filter_string)
            return sprint_name, dry_run

        if choice == "3":
            dry_run = not dry_run
            continue

        if choice == "4":
            show_help(exit_after=False)
            continue

        print("Ungültige Auswahl.")


# ============================================================================
# PROCESSING
# ============================================================================

def process_sprint(base_url, auth, definitions, sprint_name, dry_run):
    print(f"\nSprint: {sprint_name}")

    if dry_run:
        print("DRY-RUN aktiv - es werden keine Änderungen in Jira durchgeführt.")

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

                if dry_run:
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


# ============================================================================
# MAIN
# ============================================================================

def option_present(short_option, long_option):
    for arg in sys.argv[1:]:
        if arg == short_option or arg == long_option or arg.startswith(long_option + "="):
            return True
    return False


def main():

    parser = PausingArgumentParser(add_help=False)
    parser.add_argument("-s", "--sprint", default="")
    parser.add_argument("-f", "--filter", nargs="?", const="", default=None)
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

    sprint_option_used = option_present("-s", "--sprint")
    filter_option_used = args.filter is not None

    if sprint_option_used and filter_option_used:
        exit_with_enter(2, "Fehler: -s/--sprint und -f/--filter dürfen nicht gemeinsam verwendet werden.")

    if sprint_option_used:
        sprint_name = args.sprint.strip()

        if sprint_name == "":
            exit_with_enter(2, "Fehler: -s/--sprint benötigt einen nicht-leeren Sprintnamen.")

        if not validate_exact_sprint(base_url, auth, sprint_name):
            print("Sprint nicht gefunden.")
            exit_with_enter(0)

        dry_run = args.dry_run

    elif filter_option_used:
        sprint_name = select_sprint_filtered(base_url, auth, args.filter)
        dry_run = args.dry_run

    else:
        sprint_name, dry_run = menu_select_sprint(base_url, auth, args.dry_run)

    process_sprint(base_url, auth, definitions, sprint_name, dry_run)


if __name__ == "__main__":
    try:
        main()
        exit_with_enter(0)
    except SystemExit:
        raise
    except KeyboardInterrupt:
        print("\nProgramm wurde durch Benutzer abgebrochen.")
        exit_with_enter(1)
    except Exception as e:
        print("\nFEHLER:")
        print(e)
        exit_with_enter(1)