# Jira Subtask Creator

**DISCLAIMER:** This script was mainly created with the help of ChatGPT. Please use it with care. If you have any concerns regarding security, review the source code before using it or avoid using it altogether.

---

## Purpose

`jira_subtask_creator.py` automates the creation of Jira subtasks for issues within a selected Jira sprint.

The tool reads issues from a sprint, checks their Jira labels, and creates matching subtasks based on local subtask definition files.

---

## Main Features

- Sprint selection via menu, exact name, or filtered list
- Supports active and future sprints
- Closed sprints are blocked
- Creates subtasks based on Jira labels
- Avoids duplicate subtasks if they already exist
- Dry-run mode for simulation
- Report grouped by label
- Integrated help available in menu and via command line
- Help output supports pager (scrollable in supported terminals)
- Works in Linux, Windows PowerShell, and Windows cmd (ASCII-only output)
- Usable as Python script, Linux binary, or Windows EXE

---

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

---

## Login File

The file `confluence_login.txt` must be located in the same directory as the script or binary.

Format:

```text
https://your-domain.atlassian.net
email@example.com
API_TOKEN
```

Notes:

- Do not commit this file to your repository
- Treat the API token like a password
- The token must belong to the specified user

---

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
Implement feature
Create unit tests
Perform review
```

Each non-empty line is treated as one subtask title.

---

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

---

## Interactive Menu

When started without parameters, the program shows a menu:

```text
1. Select sprint by exact name
2. Select sprint from existing sprints
3. Dry-Run [ ] / [x]
4. Show help
ENTER = Exit
```

Notes:

- Dry-run can be toggled directly in the menu
- Help opens inside a scrollable pager if supported
- After closing help, the user returns to the menu
- ENTER exits the program safely

---

## Help Behavior

- Uses `pydoc.pager()` when running in an interactive terminal
- Allows scrolling in terminals like Linux bash or PowerShell
- Falls back to plain output in simple terminals
- Requires ENTER confirmation only when no pager is available
- Avoids unnecessary extra input when pager is active

---

## Token and Permissions

A classic Atlassian API token is recommended.

The Jira user associated with the token must have permissions to:

- View boards and sprints
- View issues
- Create issues
- Create subtasks

Note:

Scoped API tokens may fail with HTTP 401 when using the Jira Software Agile API, depending on the Atlassian Cloud environment.

---

## Build as Binary

The repository may include Dockerfiles and a build script:

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

---

## Notes

- `confluence_login.txt` is not embedded into the binary
- The `Subtasks/` directory is not embedded into the binary
- Both must be placed next to the binary when running the program
- All output is ASCII-only (no umlauts) for maximum terminal compatibility

---

## License

This project is licensed under the Apache License 2.0. See the LICENSE file for details.
This project is licensed under the Apache License 2.0. See the LICENSE file for details.