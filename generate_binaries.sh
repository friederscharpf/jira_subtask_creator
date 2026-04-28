#!/usr/bin/env bash

set -e

SCRIPT_NAME="$(basename "$0")"

LINUX_IMAGE="jira-subtask-linux"
WINDOWS_IMAGE="jira-subtask-windows"

LINUX_DOCKERFILE="Dockerfile.linux"
WINDOWS_DOCKERFILE="Dockerfile.windows"

OUT_LINUX="./bin/linux"
OUT_WINDOWS="./bin/windows"

APP_NAME="jira_subtask_creator"

DOCKER_CMD="docker"

show_help() {
    cat <<EOF
Jira Subtask Creator Build Script

Verwendung:
  ./$SCRIPT_NAME [OPTIONEN]

Optionen:
  -l              Linux Binary erzeugen
  -w              Windows EXE erzeugen
  -a              Linux und Windows erzeugen
  -h, --help      Hilfe anzeigen

Beispiele:
  ./$SCRIPT_NAME -l
  ./$SCRIPT_NAME -w
  ./$SCRIPT_NAME -a
  ./$SCRIPT_NAME -l -w

Ausgabe:
  ./bin/linux/${APP_NAME}
  ./bin/windows/${APP_NAME}.exe

Voraussetzungen:
  - Docker muss installiert sein
  - Docker-Daemon muss laufen
  - ${APP_NAME}.py muss im aktuellen Verzeichnis liegen
  - ${LINUX_DOCKERFILE} und ${WINDOWS_DOCKERFILE} müssen vorhanden sein
EOF
}

check_docker() {
    if ! command -v docker >/dev/null 2>&1; then
        echo "Fehler: Docker ist nicht installiert oder nicht im PATH verfügbar."
        echo "Bitte Docker installieren (Docker Desktop oder Docker Engine)."
        exit 1
    fi

    # Test ohne sudo
    if docker ps >/dev/null 2>&1; then
        DOCKER_CMD="docker"
        return
    fi

    # Test mit sudo
    if command -v sudo >/dev/null 2>&1 && sudo docker ps >/dev/null 2>&1; then
        DOCKER_CMD="sudo docker"
        echo "Hinweis: Docker wird mit sudo ausgeführt."
        return
    fi

    echo "Fehler: Docker ist installiert, aber nicht nutzbar."
    echo
    echo "Mögliche Ursachen:"
    echo "  - Docker-Daemon läuft nicht"
    echo "  - Benutzer hat keine Berechtigung (Gruppe 'docker')"
    echo
    echo "Lösungen:"
    echo "  → Docker starten"
    echo "  → oder Benutzer zur Docker-Gruppe hinzufügen:"
    echo "      sudo usermod -aG docker \$USER"
    echo "      (danach neu anmelden)"
    echo "  → oder Script mit sudo ausführen"
    exit 1
}

check_files() {
    if [ ! -f "${APP_NAME}.py" ]; then
        echo "Fehler: ${APP_NAME}.py wurde im aktuellen Verzeichnis nicht gefunden."
        exit 1
    fi
}


build_linux() {
    echo
    echo "========================================"
    echo "Erzeuge Linux Binary"
    echo "========================================"

    if [ ! -f "$LINUX_DOCKERFILE" ]; then
        echo "Fehler: $LINUX_DOCKERFILE nicht gefunden."
        exit 1
    fi

    mkdir -p "$OUT_LINUX"

    $DOCKER_CMD build -f "$LINUX_DOCKERFILE" -t "$LINUX_IMAGE" .

    container_id="$($DOCKER_CMD create "$LINUX_IMAGE")"
    $DOCKER_CMD cp "$container_id:/build/dist/${APP_NAME}" "$OUT_LINUX/${APP_NAME}"
    $DOCKER_CMD rm "$container_id" >/dev/null

    chmod +x "$OUT_LINUX/${APP_NAME}"

    echo "Linux Binary erstellt:"
    echo "  $OUT_LINUX/${APP_NAME}"
}


build_windows() {
    echo
    echo "========================================"
    echo "Erzeuge Windows EXE"
    echo "========================================"

    if [ ! -f "$WINDOWS_DOCKERFILE" ]; then
        echo "Fehler: $WINDOWS_DOCKERFILE nicht gefunden."
        exit 1
    fi

    mkdir -p "$OUT_WINDOWS"

    $DOCKER_CMD build -f "$WINDOWS_DOCKERFILE" -t "$WINDOWS_IMAGE" .

    container_id="$($DOCKER_CMD create "$WINDOWS_IMAGE")"
    $DOCKER_CMD cp "$container_id:/build/dist/${APP_NAME}.exe" "$OUT_WINDOWS/${APP_NAME}.exe"
    $DOCKER_CMD rm "$container_id" >/dev/null

    echo "Windows EXE erstellt:"
    echo "  $OUT_WINDOWS/${APP_NAME}.exe"
}


BUILD_LINUX=false
BUILD_WINDOWS=false

if [ "$#" -eq 0 ]; then
    show_help
    exit 0
fi

while [ "$#" -gt 0 ]; do
    case "$1" in
        -l)
            BUILD_LINUX=true
            ;;
        -w)
            BUILD_WINDOWS=true
            ;;
        -a)
            BUILD_LINUX=true
            BUILD_WINDOWS=true
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            echo "Unbekannte Option: $1"
            echo
            show_help
            exit 1
            ;;
    esac
    shift
done

check_docker
check_files

if [ "$BUILD_LINUX" = true ]; then
    build_linux
fi

if [ "$BUILD_WINDOWS" = true ]; then
    build_windows
fi

echo
echo "Fertig."