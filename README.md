# Jira Subtask Creator

**Hinweis:** Diese README ist zuerst auf Deutsch geschrieben. Die englische Version mit gleichem Inhalt befindet sich weiter unten.  
**Note:** This README is written in German first. The English version with the same content is provided below.

**DISCLAIMER:** This script was mainly created from ChatGPT. Please use with care! In case of any doubts about security reasons please check source code first or do not use this script.

---

# Deutsch

## Zweck

`jira_subtask_creator.py` automatisiert das Erstellen von Jira-Unteraufgaben für Issues innerhalb eines ausgewählten Jira-Sprints.

Das Tool liest Issues aus einem Sprint, prüft deren Jira-Labels und erstellt anhand lokaler Subtask-Definitionsdateien automatisch passende Unteraufgaben.

## Hauptfunktionen

- Auswahl eines Sprints per Menü, exaktem Namen oder Filterliste
- Unterstützung für aktive und zukünftige Sprints
- Geschlossene Sprints werden blockiert
- Erstellung von Subtasks anhand von Jira-Labels
- Keine doppelten Subtasks bei bereits vorhandenen Unteraufgaben
- Dry-Run-Modus zur Simulation
- Report mit gruppierter Ausgabe nach Label
- Nutzbar als Python-Skript, Linux-Binary oder Windows-EXE
- Hilfe direkt im Menü verfügbar
- Scrollbare Hilfe in kompatiblen Terminals (Pager-Unterstützung)
- Automatische Erkennung, ob ein Terminal-Pager verfügbar ist

## Benötigte Struktur

```text
jira_subtask_creator.py
confluence_login.txt
Subtasks/
    Subtasks_Impl.txt
    Subtasks_Test.txt
```

Bei Verwendung als Binary:

```text
jira_subtask_creator
confluence_login.txt
Subtasks/
    Subtasks_Impl.txt
```

Oder unter Windows:

```text
jira_subtask_creator.exe
confluence_login.txt
Subtasks/
    Subtasks_Impl.txt
```

## Login-Datei

Die Datei `confluence_login.txt` muss im gleichen Verzeichnis wie das Skript oder die Binary liegen.

Format:

```text
https://your-domain.atlassian.net
email@example.com
API_TOKEN
```

Die Datei sollte nicht ins Git-Repository eingecheckt werden.

## Subtask-Definitionen

Subtask-Dateien liegen im Ordner `Subtasks/`.

Namensschema:

```text
Subtasks_<LABEL>.txt
```

Beispiel:

```text
Subtasks_Impl.txt
```

Diese Datei gilt für alle Jira-Issues mit dem Label:

```text
Impl
```

Beispielinhalt:

```text
Implementierung durchführen
Unit Tests erstellen
Review durchführen
```

Jede nicht-leere Zeile wird als eigener Subtask-Titel verwendet.

## Nutzung

Interaktives Menü:

```bash
python jira_subtask_creator.py
```

Exakter Sprintname:

```bash
python jira_subtask_creator.py -s "Sprint Team 2"
```

Sprintauswahl aus Liste:

```bash
python jira_subtask_creator.py -f
```

Sprintauswahl mit Filter:

```bash
python jira_subtask_creator.py -f "Team 2"
```

Simulation ohne Änderungen:

```bash
python jira_subtask_creator.py --dry-run
python jira_subtask_creator.py -f "Team 2" --dry-run
```

Hilfe anzeigen:

```bash
python jira_subtask_creator.py -h
```

## Hilfeverhalten (neu in V1.2)

- In echten Terminals (z. B. Linux Shell):
  - Anzeige über einen Pager (z. B. less)
  - Scrollen möglich
  - Beenden mit q
  - Keine zusätzliche ENTER-Bestätigung notwendig

- In einfachen Konsolen (Windows EXE, IDEs):
  - Vollständige Ausgabe der Hilfe
  - Danach ENTER zur Rückkehr ins Menü erforderlich

Das Verhalten wird automatisch erkannt.

## Token und Rechte

Empfohlen wird ein klassischer Atlassian API Token.

Der Jira-Benutzer des Tokens benötigt Rechte zum:

- Anzeigen von Boards und Sprints
- Anzeigen von Issues
- Erstellen von Issues
- Erstellen von Subtasks

Scoped API Tokens können bei der verwendeten Jira Software Agile API je nach Atlassian-Umgebung mit `401` fehlschlagen. In diesem Fall sollte ein klassischer API Token verwendet werden.

## Build als Binary

Das Repository kann optional Dockerfiles und ein Build-Skript enthalten, um ausführbare Dateien zu erzeugen:

```bash
./build_binaries.sh -l
./build_binaries.sh -w
./build_binaries.sh -a
```

Ausgabe:

```text
bin/linux/jira_subtask_creator
bin/windows/jira_subtask_creator.exe
```

## Hinweise

`confluence_login.txt` und der Ordner `Subtasks/` werden nicht in die Binary eingebettet. Sie müssen neben der Binary liegen.

## Lizenz

Dieses Projekt unterliegt der Apache-Lizenz 2.0. Weitere Informationen finden Sie in der Datei "LICENSE".

---

# English

## Purpose

`jira_subtask_creator.py` automates the creation of Jira subtasks for issues inside a selected Jira sprint.

The tool reads issues from a sprint, checks their Jira labels, and creates matching subtasks based on local subtask definition files.

## Main Features

- Sprint selection via menu, exact name, or filtered list
- Supports active and future sprints
- Closed sprints are blocked
- Creates subtasks based on Jira labels
- Avoids duplicate subtasks if they already exist
- Dry-run mode for simulation
- Report grouped by label
- Usable as Python script, Linux binary, or Windows EXE
- Help available directly in the menu
- Scrollable help in supported terminals (pager support)
- Automatic detection of pager capability

## Required Structure

```text
jira_subtask_creator.py
confluence_login.txt
Subtasks/
    Subtasks_Impl.txt
    Subtasks_Test.txt
```

When using a binary:

```text
jira_subtask_creator
confluence_login.txt
Subtasks/
    Subtasks_Impl.txt
```

Or on Windows:

```text
jira_subtask_creator.exe
confluence_login.txt
Subtasks/
    Subtasks_Impl.txt
```

## Login File

The file `confluence_login.txt` must be located in the same directory as the script or binary.

Format:

```text
https://your-domain.atlassian.net
email@example.com
API_TOKEN
```

This file should not be committed to the Git repository.

## Subtask Definitions

Subtask files are stored in the `Subtasks/` directory.

Naming scheme:

```text
Subtasks_<LABEL>.txt
```

Example:

```text
Subtasks_Impl.txt
```

This file applies to all Jira issues with the label:

```text
Impl
```

Example content:

```text
Implement implementation
Create unit tests
Perform review
```

Each non-empty line is used as one subtask title.

## Usage

Interactive menu:

```bash
python jira_subtask_creator.py
```

Exact sprint name:

```bash
python jira_subtask_creator.py -s "Sprint Team 2"
```

Sprint selection from list:

```bash
python jira_subtask_creator.py -f
```

Sprint selection with filter:

```bash
python jira_subtask_creator.py -f "Team 2"
```

Simulation without changes:

```bash
python jira_subtask_creator.py --dry-run
python jira_subtask_creator.py -f "Team 2" --dry-run
```

Show help:

```bash
python jira_subtask_creator.py -h
```

## Help Behavior (new in V1.2)

- In real terminals:
  - Uses pager (for example less)
  - Scrollable output
  - Exit with q
  - No additional ENTER confirmation required

- In simple consoles (Windows EXE, IDEs):
  - Full output is printed
  - ENTER required to return

Behavior is detected automatically.

## Token and Permissions

A classic Atlassian API token is recommended.

The Jira user associated with the token needs permissions to:

- View boards and sprints
- View issues
- Create issues
- Create subtasks

Scoped API tokens may fail with `401` on the Jira Software Agile API depending on the Atlassian environment. In that case, use a classic API token.

## Building Binaries

The repository may optionally contain Dockerfiles and a build script to generate executable files:

```bash
./build_binaries.sh -l
./build_binaries.sh -w
./build_binaries.sh -a
```

Output:

```text
bin/linux/jira_subtask_creator
bin/windows/jira_subtask_creator.exe
```

## Notes

`confluence_login.txt` and the `Subtasks/` directory are not embedded into the binary. They must be placed next to the binary.

## License

This project is licensed under the Apache License 2.0. See the LICENSE file for details.