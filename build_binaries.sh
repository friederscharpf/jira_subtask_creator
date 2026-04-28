#!/usr/bin/env bash

set -e

SCRIPT_NAME="$(basename "$0")"

APP_NAME="jira_subtask_creator"

LINUX_IMAGE="jira-subtask-linux"
WINDOWS_IMAGE="jira-subtask-windows"

LINUX_DOCKERFILE="Dockerfile.linux"
WINDOWS_DOCKERFILE="Dockerfile.windows"

OUT_LINUX="./bin/linux"
OUT_WINDOWS="./bin/windows"

DOCKER_CMD="docker"

BUILD_LINUX=false
BUILD_WINDOWS=false


# =============================================================================
# COLORS
# =============================================================================

if [ -t 1 ]; then
    C_RESET="\033[0m"
    C_GREEN="\033[32m"
    C_YELLOW="\033[33m"
    C_RED="\033[31m"
    C_BLUE="\033[34m"
else
    C_RESET=""
    C_GREEN=""
    C_YELLOW=""
    C_RED=""
    C_BLUE=""
fi


info() {
    echo -e "${C_BLUE}[INFO]${C_RESET} $1"
}

ok() {
    echo -e "${C_GREEN}[OK]${C_RESET} $1"
}

warn() {
    echo -e "${C_YELLOW}[WARN]${C_RESET} $1"
}

error() {
    echo -e "${C_RED}[FEHLER]${C_RESET} $1"
}


# =============================================================================
# HELP
# =============================================================================

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

Besonderheiten:
  - Falls Docker nur mit sudo nutzbar ist, verwendet das Script automatisch sudo docker.
  - Falls chmod ohne sudo fehlschlägt, verwendet das Script automatisch sudo chmod.
  - Falls ${LINUX_DOCKERFILE} oder ${WINDOWS_DOCKERFILE} fehlen, werden sie automatisch erzeugt.
  - Falls vorhandene Dockerfiles nicht exakt dem erwarteten Inhalt entsprechen,
    werden sie gesichert und anschließend korrekt neu erzeugt.
  - Backups werden nicht überschrieben:
      Dockerfile.linux_bu
      Dockerfile.linux_bu1
      Dockerfile.linux_bu2
      ...
  - Docker Build Cache wird genutzt, solange Docker ihn nicht selbst invalidiert.
EOF
}


# =============================================================================
# CHECKS
# =============================================================================

check_docker() {
    if ! command -v docker >/dev/null 2>&1; then
        error "Docker ist nicht installiert oder nicht im PATH verfügbar."
        echo "Bitte Docker installieren, z.B. Docker Desktop oder Docker Engine."
        exit 1
    fi

    if docker ps >/dev/null 2>&1; then
        DOCKER_CMD="docker"
        ok "Docker ist ohne sudo nutzbar."
        return
    fi

    if command -v sudo >/dev/null 2>&1 && sudo docker ps >/dev/null 2>&1; then
        DOCKER_CMD="sudo docker"
        warn "Docker wird mit sudo ausgeführt."
        return
    fi

    error "Docker ist installiert, aber nicht nutzbar."
    echo
    echo "Mögliche Ursachen:"
    echo "  - Docker-Daemon läuft nicht"
    echo "  - Benutzer hat keine Berechtigung auf Docker zuzugreifen"
    echo
    echo "Lösungen:"
    echo "  - Docker starten"
    echo "  - Benutzer zur Docker-Gruppe hinzufügen:"
    echo "      sudo usermod -aG docker \$USER"
    echo "      Danach neu anmelden."
    echo "  - Oder das Script mit sudo ausführen."
    exit 1
}


check_source_file() {
    if [ ! -f "${APP_NAME}.py" ]; then
        error "${APP_NAME}.py wurde im aktuellen Verzeichnis nicht gefunden."
        exit 1
    fi
}


safe_chmod_x() {
    local target_file="$1"

    if chmod +x "$target_file" >/dev/null 2>&1; then
        return
    fi

    if command -v sudo >/dev/null 2>&1 && sudo chmod +x "$target_file" >/dev/null 2>&1; then
        warn "chmod wurde mit sudo ausgeführt: $target_file"
        return
    fi

    error "Konnte Datei nicht ausführbar machen: $target_file"
    echo "Bitte manuell ausführen:"
    echo "  sudo chmod +x \"$target_file\""
    exit 1
}


# =============================================================================
# DOCKERFILE BACKUP / VALIDATION
# =============================================================================

backup_file_without_overwrite() {
    local file="$1"
    local backup="${file}_bu"
    local counter=0

    while [ -e "$backup" ]; do
        counter=$((counter + 1))
        backup="${file}_bu${counter}"
    done

    mv "$file" "$backup"
    warn "Vorhandenes Dockerfile wurde gesichert als: $backup"
}


write_expected_linux_dockerfile() {
    local target="$1"

    cat > "$target" <<'EOF'
FROM python:3.12-slim

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    binutils \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir pyinstaller requests

COPY jira_subtask_creator.py .

RUN pyinstaller \
    --onefile \
    --name jira_subtask_creator \
    jira_subtask_creator.py

CMD ["bash"]
EOF
}


write_expected_windows_dockerfile() {
    local target="$1"

    cat > "$target" <<'EOF'
FROM cdrx/pyinstaller-windows:python3

WORKDIR /src

COPY jira_subtask_creator.py .

RUN python -m pip install requests==2.31.0

RUN pyinstaller \
    --onefile \
    --name jira_subtask_creator \
    jira_subtask_creator.py

CMD ["bash"]
EOF
}


ensure_dockerfile_exact() {
    local dockerfile="$1"
    local type="$2"
    local tmp_expected

    tmp_expected="$(mktemp)"

    if [ "$type" = "linux" ]; then
        write_expected_linux_dockerfile "$tmp_expected"
    elif [ "$type" = "windows" ]; then
        write_expected_windows_dockerfile "$tmp_expected"
    else
        rm -f "$tmp_expected"
        error "Interner Fehler: unbekannter Dockerfile-Typ '$type'"
        exit 1
    fi

    if [ ! -f "$dockerfile" ]; then
        warn "$dockerfile fehlt und wird erzeugt."
        cp "$tmp_expected" "$dockerfile"
        rm -f "$tmp_expected"
        ok "$dockerfile erzeugt."
        return
    fi

    if cmp -s "$dockerfile" "$tmp_expected"; then
        info "$dockerfile vorhanden und exakt korrekt."
        rm -f "$tmp_expected"
        return
    fi

    warn "$dockerfile existiert, entspricht aber nicht dem erwarteten Inhalt."
    backup_file_without_overwrite "$dockerfile"
    cp "$tmp_expected" "$dockerfile"
    rm -f "$tmp_expected"
    ok "$dockerfile wurde korrekt neu erzeugt."
}


# =============================================================================
# DOCKERFILE GENERATION
# =============================================================================

create_linux_dockerfile_if_missing_or_wrong() {
    ensure_dockerfile_exact "$LINUX_DOCKERFILE" "linux"
}


create_windows_dockerfile_if_missing_or_wrong() {
    ensure_dockerfile_exact "$WINDOWS_DOCKERFILE" "windows"
}


# =============================================================================
# BUILD FUNCTIONS
# =============================================================================

build_linux() {
    echo
    echo "========================================"
    echo "Erzeuge Linux Binary"
    echo "========================================"

    create_linux_dockerfile_if_missing_or_wrong

    mkdir -p "$OUT_LINUX"

    info "Docker Image bauen: $LINUX_IMAGE"
    $DOCKER_CMD build \
        --progress=plain \
        -f "$LINUX_DOCKERFILE" \
        -t "$LINUX_IMAGE" \
        .

    info "Binary aus Container extrahieren..."
    container_id="$($DOCKER_CMD create "$LINUX_IMAGE")"

    $DOCKER_CMD cp "$container_id:/build/dist/${APP_NAME}" "$OUT_LINUX/${APP_NAME}"
    $DOCKER_CMD rm "$container_id" >/dev/null

    safe_chmod_x "$OUT_LINUX/${APP_NAME}"

    ok "Linux Binary erstellt: $OUT_LINUX/${APP_NAME}"
}


build_windows() {
    echo
    echo "========================================"
    echo "Erzeuge Windows EXE"
    echo "========================================"

    create_windows_dockerfile_if_missing_or_wrong

    mkdir -p "$OUT_WINDOWS"

    info "Docker Image bauen: $WINDOWS_IMAGE"
    $DOCKER_CMD build \
        --progress=plain \
        -f "$WINDOWS_DOCKERFILE" \
        -t "$WINDOWS_IMAGE" \
        .

    info "EXE aus Container extrahieren..."
    container_id="$($DOCKER_CMD create "$WINDOWS_IMAGE")"

    $DOCKER_CMD cp "$container_id:/src/dist/${APP_NAME}.exe" "$OUT_WINDOWS/${APP_NAME}.exe"
    $DOCKER_CMD rm "$container_id" >/dev/null

    ok "Windows EXE erstellt: $OUT_WINDOWS/${APP_NAME}.exe"
}


# =============================================================================
# ARGUMENT PARSING
# =============================================================================

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
            error "Unbekannte Option: $1"
            echo
            show_help
            exit 1
            ;;
    esac
    shift
done


# =============================================================================
# MAIN
# =============================================================================

check_docker
check_source_file

if [ "$BUILD_LINUX" = true ]; then
    build_linux
fi

if [ "$BUILD_WINDOWS" = true ]; then
    build_windows
fi

echo
ok "Fertig."