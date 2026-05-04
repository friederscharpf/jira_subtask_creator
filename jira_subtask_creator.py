#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import glob
import argparse
import requests
import pydoc
from requests.auth import HTTPBasicAuth

APP_VERSION = "V1.3"

DOCUMENTATION = f"""
===============================================================================
File         : jira_subtask_creator.py
Version      : {APP_VERSION}
Author       : ChatGPT

===============================================================================
IMPORTANT DOCUMENTATION NOTE
===============================================================================

This documentation is intentionally complete and must not be shortened in future
versions. Existing sections must be kept. Future changes should only extend this
documentation, not remove or reduce existing content.

===============================================================================
PURPOSE
===============================================================================

This program automates the creation of Jira subtasks for issues inside a
selected sprint in Jira Cloud.

It connects to the Jira REST API, reads issues from a sprint, checks their Jira
labels, and creates subtasks based on local label-specific definition files.

===============================================================================
BASIC WORKFLOW
===============================================================================

1. A sprint is selected:
   - via interactive menu
   - by entering the exact sprint name
   - via filter mode (-f / --filter)
   - directly via command line option (-s / --sprint)

2. The sprint is validated, including state checking:
   - active and future sprints are allowed
   - closed sprints are blocked

3. All issues in the sprint are loaded

4. Only parent issues are processed

5. Labels determine the matching subtask definitions

6. Missing subtasks are created

7. Already existing subtasks are skipped

8. A result report is printed

9. Before the program exits, the user must confirm with ENTER.
   This also applies to error cases so that a Windows console window does not
   close immediately when the EXE is started by double-click.

===============================================================================
SUBTASK DEFINITIONS
===============================================================================

Directory:

    ./Subtasks/

Files:

    Subtasks_<LABEL>.txt

Examples:

    Subtasks_Impl.txt
    Subtasks_Test.txt
    Subtasks_Spez.txt

Content:

    One line = one subtask title

Example file:

    Subtasks/Subtasks_Impl.txt

Example content:

    Implement feature
    Create unit tests
    Perform review

Important:

- The part after "Subtasks_" and before ".txt" is the Jira label.
- The file "Subtasks_Impl.txt" applies to issues with the Jira label "Impl".
- The label must exist exactly like this on the Jira issue.
- Each non-empty line is used as one subtask title.
- Duplicate lines inside one definition file are removed internally.
- Already existing subtasks with the same title are not created again.

===============================================================================
LOGIN FILE
===============================================================================

confluence_login.txt with 3 lines:

    https://your-domain.atlassian.net
    email@domain.com
    API_TOKEN

Example:

    https://example.atlassian.net
    max.mustermann@example.com
    ATATT3xFfGF0...

Important:

- The file must be located in the same directory as jira_subtask_creator.py.
- The first line is the Jira Cloud base URL.
- The second line is the Atlassian login email address.
- The third line is the Atlassian API token.
- Empty lines are ignored.
- This file should not be committed to a Git repository.

===============================================================================
TOKEN / PERMISSIONS / SCOPES
===============================================================================

The program requires permissions to:

1. Read boards and sprints
2. Search and read Jira issues
3. Create issues / subtasks

Note about Atlassian API tokens:

A classic / unscoped Atlassian API token is currently recommended for this tool
because the Jira Software Agile API endpoints used by this program:

    /rest/agile/1.0/board
    /rest/agile/1.0/board/{{id}}/sprint

may fail with scoped API tokens in some Atlassian Cloud environments with errors
such as:

    401: Client must be authenticated to access this resource

even if apparently matching scopes were configured.

When using a classic API token, the Jira user associated with the token must also
have sufficient project permissions:

- view boards and sprints
- view issues in the sprint
- create issues/subtasks
- use the Sub-task issue type in the project

If reading works but creating subtasks fails, the user usually lacks write
permissions or the project does not allow the user to create subtasks.

===============================================================================
SPRINT BEHAVIOR
===============================================================================

-------------------------------------------------
Interactive menu mode
-------------------------------------------------

Call without further options:

    python jira_subtask_creator.py

or as binary:

    jira_subtask_creator.exe

Behavior:

- An interactive menu is shown.
- The sprint can be selected by exact name.
- The sprint can be selected from an existing sprint list with optional filter.
- Dry-run can be toggled in the menu.
- Help can be displayed from the menu.
- After closing the help view, the user returns to the menu.
- ENTER without a selection exits the program.

-------------------------------------------------
Command line mode with exact sprint name
-------------------------------------------------

Call:

    python jira_subtask_creator.py -s "Sprint Team 2"
    python jira_subtask_creator.py --sprint "Sprint Team 2"

Behavior:

- The sprint name must be passed exactly.
- The parameter -s / --sprint requires a non-empty string.
- An empty string is invalid.
- Closed sprints are blocked.
- Active and future sprints are allowed.

-------------------------------------------------
Filter mode (-f / --filter)
-------------------------------------------------

Call:

    -f
    -f ""
    -f "Team 2"

Behavior:

- Shows all active and future sprints.
- Closed sprints are not shown.
- An optional filter string can be used.
- Selection is done by number.
- ENTER exits the program.

Examples:

    python jira_subtask_creator.py -f
    python jira_subtask_creator.py --filter
    python jira_subtask_creator.py -f ""
    python jira_subtask_creator.py -f "Team 2"

===============================================================================
DRY RUN
===============================================================================

--dry-run:

- simulation only
- no changes are made in Jira
- same report as productive mode

Examples:

    python jira_subtask_creator.py --dry-run
    python jira_subtask_creator.py -f "Team 2" --dry-run
    python jira_subtask_creator.py -s "Sprint Team 2" --dry-run

In menu mode, dry-run is toggled using menu item 3:

    3. Dry-Run [ ]
    3. Dry-Run [x]

===============================================================================
HELP IN MENU
===============================================================================

Starting with version V1.2, help can also be opened directly from the interactive
menu.

Behavior:

- Help is displayed through a pager if the terminal supports it.
- This makes the help readable even in small terminal windows.
- After closing the help view, the user returns to the menu.
- The command line option -h / --help still displays help and then exits after
  ENTER confirmation.

Note:

The actual scrolling behavior depends on the terminal and operating system. On
Linux, a terminal pager is typically used. On Windows, help is at least printed
completely and then the user can continue with ENTER if needed.

Additional technical logic:

- If the program detects that it is running in an interactive terminal, help is
  printed through pydoc.pager().
- In terminals with a working pager, the user can close the pager and then
  return directly to the menu.
- If no interactive terminal is detected, help is printed directly and the user
  must confirm with ENTER before the program returns to the menu or exits.
- This avoids an unnecessary extra ENTER confirmation in real pager terminals.
- At the same time, simple terminals, Windows EXE starts, and environments
  without a pager remain readable.

===============================================================================
LANGUAGE / TERMINAL COMPATIBILITY
===============================================================================

Starting with version V1.3, all program text, help text, user interaction text,
and documentation text are written in English only.

Background:

Earlier versions contained German text and umlauts. Some terminals, especially
classic Windows cmd.exe configurations, can display such characters incorrectly.
Instead of maintaining separate Unicode and ASCII variants, the complete program
text was changed to English ASCII-friendly text.

Behavior:

- The program no longer prints German umlauts in help and documentation.
- Output is easier to read in Linux terminals, Windows PowerShell, Windows cmd,
  remote shells, and minimal terminal environments.
- No automatic umlaut replacement is needed anymore.
- The code remains easier to maintain because only one text variant exists.

===============================================================================
REQUIRED FILE AND DIRECTORY STRUCTURE
===============================================================================

Minimal required structure:

    jira_subtask_creator.py
    confluence_login.txt
    Subtasks/
        Subtasks_Impl.txt

Example with multiple label files:

    jira_subtask_creator.py
    confluence_login.txt
    Subtasks/
        Subtasks_Impl.txt
        Subtasks_Test.txt
        Subtasks_Spez.txt

When using a binary / EXE:

    jira_subtask_creator
    confluence_login.txt
    Subtasks/
        Subtasks_Impl.txt

or on Windows:

    jira_subtask_creator.exe
    confluence_login.txt
    Subtasks/
        Subtasks_Impl.txt

Important:

- confluence_login.txt is not embedded into the binary.
- The Subtasks directory is not embedded into the binary.
- Both must be located next to the script or binary when the program is started.

===============================================================================
EXAMPLE WORKFLOW
===============================================================================

1. Create confluence_login.txt

    https://example.atlassian.net
    max.mustermann@example.com
    API_TOKEN

2. Create a subtask definition file

    Subtasks/Subtasks_Impl.txt

3. Add subtask titles

    Implement feature
    Create unit tests
    Perform review

4. Add the label "Impl" to a Jira issue inside the selected sprint

5. Start the program

    python jira_subtask_creator.py

6. Select the sprint in the menu

7. The program creates the missing subtasks

===============================================================================
RESULT REPORT
===============================================================================

At the end, a report is printed.

For every parent issue, the report shows:

- Jira key
- Issue type
- Summary
- Matching label
- Created subtasks per label
- Skipped subtasks per label

Skipped means:

- the subtask already existed
- or the subtask could not be created

If an issue has multiple labels for which matching subtask definition files
exist, created and skipped subtasks are grouped by label. This makes it clear
which label and definition file caused each subtask to be created or skipped.

Subtasks themselves are not processed as parent issues.

===============================================================================
WINDOWS / EXE BEHAVIOR
===============================================================================

Starting with version V1.1, the program always waits for ENTER before exiting.

This is especially important when the Windows EXE is started by double-click.
Without this confirmation, the console window would close immediately at the end
or on errors, so the user could not read the message.

===============================================================================
CHANGES IN V0.7
===============================================================================

- Explicit message for closed sprints
- No subtask creation for closed sprints
- Clear abort message including sprint name
- Consistent sprint state validation in standard mode

===============================================================================
CHANGES IN V1.0
===============================================================================

- V0.7 was accepted as the first stable major version
- Program version is centrally defined through APP_VERSION
- Program output and help use APP_VERSION
- Help was extended for binary / EXE usage
- Help describes required files and directories in more detail
- Help describes recommended token permissions and scopes
- Documentation describes usage as Python script and as binary / EXE
- Report shows created and skipped subtasks grouped by label

===============================================================================
CHANGES IN V1.1
===============================================================================

- Program waits for ENTER before every regular exit
- Program also waits for ENTER in error cases
- Improved behavior when starting the Windows EXE by double-click
- New interactive main menu when started without options
- Dry-run can be toggled in the menu using [ ] / [x]
- New command line option -s / --sprint for exact sprint selection
- -s / --sprint requires a non-empty sprint name

===============================================================================
CHANGES IN V1.2
===============================================================================

- Help is now available directly in the interactive menu
- Help returns to the menu after the help view is closed
- Help output uses a pager if supported by the terminal
- Menu was extended with a help item
- Documentation was extended with menu help behavior
- Help output distinguishes between interactive terminal and simple output mode
  without pager
- If a working pager is available, no additional ENTER confirmation is needed
- Without an interactive pager, ENTER is requested before returning to the menu
  or exiting

===============================================================================
CHANGES IN V1.3
===============================================================================

- All program text was changed to English
- All help text was changed to English
- All documentation text was changed to English
- German umlauts and German user interaction text were removed
- Output is now more portable across Linux, Windows PowerShell, Windows cmd, and
  minimal terminal environments

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
V0.1  Label system
V0.2  Search API + dry-run
V0.3  Subtask output filtering
V0.4  Sprint filter mode
V0.5  Stabilization + dry-run fix
V0.6  Closed sprint handling + messages
V0.7  Explicit closed-sprint message before processing
V1.0  First stable major version based on V0.7
      Central version definition through APP_VERSION
      Extended help for binary / EXE usage
      Extended description of required files
      Extended description of API token permissions
      Report output grouped by created and skipped subtasks per label
V1.1  Windows / EXE behavior improved
      ENTER confirmation before program exit and in error cases
      Interactive main menu when started without options
      Dry-run toggle in menu
      New option -s / --sprint for direct exact sprint selection
V1.2  Help added to interactive menu
      Help output with pager support added
      Return to menu after help view added
      Pager / non-pager behavior improved
V1.3  Complete switch to English-only output and documentation
      Removed need for umlaut / Unicode fallback handling

===============================================================================
"""

__doc__ = DOCUMENTATION

LOGIN_FILE = "confluence_login.txt"
SUBTASK_DIR = "Subtasks"


# ============================================================================
# EXIT / PAUSE HANDLING
# ============================================================================

def wait_for_enter(message="ENTER to exit..."):
    try:
        input(message)
    except EOFError:
        pass


def exit_with_enter(code=0, message=None):
    if message:
        print(message)
    wait_for_enter("ENTER to exit...")
    sys.exit(code)


# ============================================================================
# ARGUMENT PARSER
# ============================================================================

class PausingArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        print(f"Error: {message}")
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
CALL
===============================================================================

Python script:

  python jira_subtask_creator.py
  python jira_subtask_creator.py -s "Sprint Team 2"
  python jira_subtask_creator.py -f
  python jira_subtask_creator.py -f "Team 2"
  python jira_subtask_creator.py --dry-run

Linux binary:

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
OPTIONS
===============================================================================

  -s, --sprint TEXT     Select sprint by exact sprint name.
                        TEXT is required and must not be empty.

  -f, --filter [TEXT]   Select sprint from a list.
                        Without TEXT, all open/active sprints are shown.
                        With TEXT, only sprints whose name contains this text
                        are shown.

  --dry-run             Simulation.
                        No changes are made in Jira.

  -h, --help            Show this help.

===============================================================================
MENU MODE
===============================================================================

If the program is started without options, an interactive menu is shown:

  1. Select sprint by exact name
  2. Select sprint from existing sprints
  3. Dry-Run [ ] / [x]
  4. Show help
  ENTER = Exit

If help is opened from the menu, the user returns to the menu after closing the
help view.

===============================================================================
REQUIRED FILES
===============================================================================

The following must be located in the same directory as the script or binary:

  confluence_login.txt
  Subtasks/

Example structure:

  jira_subtask_creator
  confluence_login.txt
  Subtasks/
      Subtasks_Impl.txt
      Subtasks_Test.txt

Or on Windows:

  jira_subtask_creator.exe
  confluence_login.txt
  Subtasks/
      Subtasks_Impl.txt
      Subtasks_Test.txt

===============================================================================
FILE: confluence_login.txt
===============================================================================

The file must contain exactly this information:

  Line 1: Jira Cloud URL
  Line 2: Login email address
  Line 3: Atlassian API token

Example:

  https://example.atlassian.net
  max.mustermann@example.com
  ATATT3xFfGF0...

Important:

  - Do not commit this file to Git.
  - Treat the token like a password.
  - The token must belong to the user specified in line 2.

===============================================================================
DIRECTORY: Subtasks
===============================================================================

This directory contains the subtask definitions.

File naming scheme:

  Subtasks_<LABEL>.txt

Examples:

  Subtasks_Impl.txt
  Subtasks_Test.txt
  Subtasks_Spez.txt

Meaning:

  Subtasks_Impl.txt

  applies to Jira issues with the label "Impl"

File content:

  One line = one subtask title

Example content:

  Implement feature
  Create unit tests
  Perform review

===============================================================================
TOKEN / PERMISSIONS
===============================================================================

A classic Atlassian API token is recommended.

The token user needs Jira project permissions to:

  - view boards and sprints
  - view issues
  - create issues
  - create subtasks

Scoped API tokens may fail with 401 on the Jira Software Agile API depending on
the Atlassian Cloud environment.

===============================================================================
REPORT
===============================================================================

The report shows for every parent issue:

  - Jira key
  - Issue type
  - Summary
  - Label
  - Created subtasks
  - Skipped subtasks

If an issue has multiple labels and matching subtask definition files exist,
the output is grouped by label.

===============================================================================
IMPORTANT RULES
===============================================================================

  - Only active and future sprints are allowed.
  - Closed sprints are rejected.
  - Subtasks are only created for active and future sprints.
  - Empty inputs exit the program.
  - Existing subtasks are not created again.
  - Subtasks themselves are not processed further.

===============================================================================
"""


def show_help(exit_after=True):
    help_text = get_help_text()

    if sys.stdout.isatty():
        pydoc.pager(help_text)
    else:
        print(help_text)
        wait_for_enter("ENTER to continue...")

    if exit_after:
        exit_with_enter(0)


# ============================================================================
# LOGIN
# ============================================================================

def read_login():
    if not os.path.exists(LOGIN_FILE):
        raise RuntimeError(f"Error: {LOGIN_FILE} not found.")

    with open(LOGIN_FILE, "r", encoding="utf-8") as f:
        lines = [l.strip() for l in f.readlines() if l.strip()]

    if len(lines) < 3:
        raise RuntimeError(
            f"Error: {LOGIN_FILE} must contain at least 3 non-empty lines. "
            f"See help with -h or --help."
        )

    return lines[0], lines[1], lines[2]


# ============================================================================
# SUBTASKS
# ============================================================================

def load_subtask_definitions():
    result = {}

    if not os.path.isdir(SUBTASK_DIR):
        raise RuntimeError(f"Error: directory '{SUBTASK_DIR}' is missing.")

    files = glob.glob(os.path.join(SUBTASK_DIR, "Subtasks_*.txt"))

    if not files:
        raise RuntimeError(
            f"Error: no files matching 'Subtasks_*.txt' found in directory "
            f"'{SUBTASK_DIR}'."
        )

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
        exit_with_enter(0, "No open/active sprints found.")

    print("\nAvailable open/active sprints:\n")

    for i, s in enumerate(sprints, 1):
        print(f"{i}. {sprint_label(s)}")

    while True:
        choice = input("\nSelect sprint (ENTER = abort): ").strip()

        if choice == "":
            print("Program will exit.")
            exit_with_enter(0)

        if choice.isdigit() and 1 <= int(choice) <= len(sprints):
            return sprints[int(choice) - 1]["name"]

        print("Invalid selection.")
        print("Program will exit.")
        exit_with_enter(0)


def validate_exact_sprint(base_url, auth, sprint_name):
    sprints = fetch_all_sprints(base_url, auth)

    for s in sprints:
        if s["name"] == sprint_name:

            if is_closed_sprint(s):
                print("\n========================================")
                print(f"SPRINT CLOSED: {sprint_name}")
                print("NO subtasks will be created.")
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
    print("1. Select sprint by exact name")
    print("2. Select sprint from existing sprints")
    print(f"3. Dry-Run {dry_run_marker}")
    print("4. Show help")
    print()
    print("ENTER = Exit")


def menu_select_sprint(base_url, auth, initial_dry_run):
    dry_run = initial_dry_run

    while True:
        show_main_menu(dry_run)
        choice = input("\nSelection: ").strip()

        if choice == "":
            print("Program will exit.")
            exit_with_enter(0)

        if choice == "1":
            sprint_name = input("Sprint name (exact, ENTER = exit): ").strip()

            if sprint_name == "":
                print()
                exit_with_enter(0)

            if not validate_exact_sprint(base_url, auth, sprint_name):
                print("Sprint not found.")
                exit_with_enter(0)

            return sprint_name, dry_run

        if choice == "2":
            filter_string = input("Optional filter text (ENTER = all open/active sprints): ").strip()
            sprint_name = select_sprint_filtered(base_url, auth, filter_string)
            return sprint_name, dry_run

        if choice == "3":
            dry_run = not dry_run
            continue

        if choice == "4":
            show_help(exit_after=False)
            continue

        print("Invalid selection.")


# ============================================================================
# PROCESSING
# ============================================================================

def process_sprint(base_url, auth, definitions, sprint_name, dry_run):
    print(f"\nSprint: {sprint_name}")

    if dry_run:
        print("DRY-RUN active - no changes will be made in Jira.")

    print("Loading issues...")

    issues = search_issues_in_sprint(base_url, auth, sprint_name)
    issues = [i for i in issues if not is_subtask(i)]

    print(f"{len(issues)} issues found.\n")

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
            print("  No action.")

        for label, label_data in r["labels"].items():
            print(f"\n  Label: {label}")

            if label_data["created"]:
                print("    Created:")
                for c in label_data["created"]:
                    print(f"      + {c}")

            if label_data["skipped"]:
                print("    Skipped:")
                for s in label_data["skipped"]:
                    print(f"      - {s}")

    print("\nDone.")


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
        exit_with_enter(2, "Error: -s/--sprint and -f/--filter must not be used together.")

    if sprint_option_used:
        sprint_name = args.sprint.strip()

        if sprint_name == "":
            exit_with_enter(2, "Error: -s/--sprint requires a non-empty sprint name.")

        if not validate_exact_sprint(base_url, auth, sprint_name):
            print("Sprint not found.")
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
        print("\nProgram was aborted by user.")
        exit_with_enter(1)
    except Exception as e:
        print("\nERROR:")
        print(e)
        exit_with_enter(1)