#!/bin/bash
#
# Upgrade PostgreSQL Docker container with minimal downtime.
#
# Two-phase operation:
#   Phase 1 (prepare): Dump live DB, build a staging postgres container, restore
#                      into it. The site stays up throughout.
#   Phase 2 (swap):    Stop old container, swap in the staging one. A few seconds
#                      of downtime. Run this right before deploying new app code.
#
# Usage:
#   ./scripts/upgrade-postgres.sh prepare [OPTIONS]
#   ./scripts/upgrade-postgres.sh swap    [OPTIONS]
#
# Options:
#   --container NAME    Container name (default: lutrisdb)
#   --target VERSION    Target PostgreSQL version (default: 16)
#   --dump-path PATH    Where to store the dump file (default: /tmp/<container>_dump.sql)
#   --dry-run           Show what would be done without executing
#
# Typical production workflow:
#   1. ./scripts/upgrade-postgres.sh prepare        # site stays up
#   2. ./scripts/upgrade-postgres.sh swap            # seconds of downtime
#   3. ./scripts/prod-deploy.sh --prod               # deploys new Django + migrates

set -euo pipefail

CONTAINER="lutrisdb"
TARGET_VERSION="16"
DUMP_PATH=""
DRY_RUN=false

COMMAND="${1:-}"
if [[ "$COMMAND" != "prepare" && "$COMMAND" != "swap" ]]; then
    echo "Usage: $0 {prepare|swap} [OPTIONS]"
    echo ""
    echo "  prepare  Build staging postgres (site stays up)"
    echo "  swap     Swap staging into production (brief downtime)"
    exit 1
fi
shift

while [[ $# -gt 0 ]]; do
    case "$1" in
        --container)  CONTAINER="$2"; shift 2 ;;
        --target)     TARGET_VERSION="$2"; shift 2 ;;
        --dump-path)  DUMP_PATH="$2"; shift 2 ;;
        --dry-run)    DRY_RUN=true; shift ;;
        *)            echo "Unknown option: $1"; exit 1 ;;
    esac
done

DUMP_PATH="${DUMP_PATH:-/tmp/${CONTAINER}_dump.sql}"
BACKUP_NAME="${CONTAINER}-pg-backup"
STAGING_NAME="${CONTAINER}-pg${TARGET_VERSION}-staging"

# --- Helper: gather info from the live container ---

gather_info() {
    CURRENT_IMAGE=$(docker inspect "$CONTAINER" --format '{{.Config.Image}}' 2>/dev/null) || {
        echo "ERROR: Container '$CONTAINER' not found"
        exit 1
    }

    PG_USER=$(docker inspect "$CONTAINER" --format '{{range .Config.Env}}{{println .}}{{end}}' | grep POSTGRES_USER | cut -d= -f2)
    PG_PASS=$(docker inspect "$CONTAINER" --format '{{range .Config.Env}}{{println .}}{{end}}' | grep POSTGRES_PASSWORD | cut -d= -f2)
    PG_DB=$(docker inspect "$CONTAINER" --format '{{range .Config.Env}}{{println .}}{{end}}' | grep POSTGRES_DB | cut -d= -f2)

    HOST_PORT=$(docker inspect "$CONTAINER" --format '{{(index (index .HostConfig.PortBindings "5432/tcp") 0).HostPort}}' 2>/dev/null || echo "5432")

    # Collect named volume mounts (exclude pgdata — new container creates its own)
    VOLUME_ARGS=""
    while IFS= read -r line; do
        vol_name=$(echo "$line" | cut -d: -f1)
        vol_dest=$(echo "$line" | cut -d: -f2)
        if [[ "$vol_dest" == "/var/lib/postgresql/data" ]]; then
            continue
        fi
        VOLUME_ARGS="$VOLUME_ARGS -v $vol_name:$vol_dest"
    done < <(docker inspect "$CONTAINER" --format '{{range .Mounts}}{{if eq .Type "volume"}}{{.Name}}:{{.Destination}}{{"\n"}}{{end}}{{end}}' | grep -v '^$')

    RESTART_POLICY=$(docker inspect "$CONTAINER" --format '{{.HostConfig.RestartPolicy.Name}}')
}

# =============================================
# PHASE 1: PREPARE
# =============================================

if [[ "$COMMAND" == "prepare" ]]; then

    gather_info

    echo "==> Current container: $CONTAINER ($CURRENT_IMAGE)"
    echo "    Database: $PG_DB, User: $PG_USER, Port: $HOST_PORT"
    echo ""

    if $DRY_RUN; then
        echo "==> [DRY RUN] Would perform the following:"
        echo "    1. Dump from live $CONTAINER to $DUMP_PATH"
        echo "    2. Start staging container $STAGING_NAME (no port binding)"
        echo "    3. Restore dump into staging"
        echo "    Site stays up throughout."
        exit 0
    fi

    # Step 1: Dump from live container
    echo "==> Step 1: Dumping from live container..."
    docker exec "$CONTAINER" pg_dumpall -U "$PG_USER" > "$DUMP_PATH"
    DUMP_SIZE=$(du -h "$DUMP_PATH" | cut -f1)
    echo "    Dump complete: $DUMP_PATH ($DUMP_SIZE)"

    # Step 2: Start staging container (no port binding — no conflict)
    echo "==> Step 2: Starting staging postgres:$TARGET_VERSION..."

    if docker inspect "$STAGING_NAME" &>/dev/null; then
        echo "    Removing previous staging container..."
        docker rm -f "$STAGING_NAME" > /dev/null
    fi

    docker run -d \
        --name "$STAGING_NAME" \
        -e POSTGRES_DB="$PG_DB" \
        -e POSTGRES_USER="$PG_USER" \
        -e POSTGRES_PASSWORD="$PG_PASS" \
        $VOLUME_ARGS \
        "postgres:$TARGET_VERSION" > /dev/null

    echo "    Waiting for staging to be ready..."
    for i in $(seq 1 30); do
        if docker exec "$STAGING_NAME" pg_isready -U "$PG_USER" &>/dev/null; then
            break
        fi
        sleep 1
    done

    if ! docker exec "$STAGING_NAME" pg_isready -U "$PG_USER" &>/dev/null; then
        echo "ERROR: Staging container did not become ready in 30 seconds"
        docker rm -f "$STAGING_NAME" > /dev/null 2>&1
        exit 1
    fi

    # Step 3: Restore into staging
    echo "==> Step 3: Restoring dump into staging..."
    docker exec -i "$STAGING_NAME" psql -U "$PG_USER" -d "$PG_DB" < "$DUMP_PATH" > /dev/null 2>&1
    echo "    Restore complete"

    # Fix password hash for scram-sha-256 (pg14+ default auth method)
    docker exec "$STAGING_NAME" psql -U "$PG_USER" -d "$PG_DB" \
        -c "ALTER USER $PG_USER WITH PASSWORD '$PG_PASS';" > /dev/null 2>&1

    # Verify staging
    TABLE_COUNT=$(docker exec "$STAGING_NAME" psql -U "$PG_USER" -d "$PG_DB" -t \
        -c "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public';" | xargs)
    NEW_PG_VER=$(docker exec "$STAGING_NAME" psql -U "$PG_USER" -d "$PG_DB" -t \
        -c "SHOW server_version;" | xargs)
    echo "    Staging verified: PostgreSQL $NEW_PG_VER, $TABLE_COUNT public tables"

    if [[ "$TABLE_COUNT" -lt 1 ]]; then
        echo "ERROR: Staging database appears empty. Aborting."
        docker rm -f "$STAGING_NAME" > /dev/null 2>&1
        exit 1
    fi

    # Stop staging — it's ready and waiting
    docker stop "$STAGING_NAME" > /dev/null

    echo ""
    echo "==> Prepare complete! Staging container '$STAGING_NAME' is ready."
    echo "    Site has been up the whole time."
    echo ""
    echo "    When ready, run:"
    echo "      $0 swap"
    exit 0
fi

# =============================================
# PHASE 2: SWAP
# =============================================

if [[ "$COMMAND" == "swap" ]]; then

    # Verify staging container exists
    if ! docker inspect "$STAGING_NAME" &>/dev/null; then
        echo "ERROR: Staging container '$STAGING_NAME' not found."
        echo "       Run '$0 prepare' first."
        exit 1
    fi

    gather_info

    echo "==> Current container: $CONTAINER ($CURRENT_IMAGE), port $HOST_PORT"
    echo "    Staging container: $STAGING_NAME"
    echo ""

    if $DRY_RUN; then
        echo "==> [DRY RUN] Would perform the following:"
        echo "    1. Stop $CONTAINER"
        echo "    2. Rename $CONTAINER → $BACKUP_NAME"
        echo "    3. Recreate $CONTAINER from staging data on port $HOST_PORT"
        echo "    Downtime: ~5-10 seconds"
        exit 0
    fi

    # Get the staging container's data volume
    STAGING_DATA_VOL=$(docker inspect "$STAGING_NAME" --format \
        '{{range .Mounts}}{{if eq .Destination "/var/lib/postgresql/data"}}{{.Name}}{{end}}{{end}}')

    if [[ -z "$STAGING_DATA_VOL" ]]; then
        echo "ERROR: Could not find data volume on staging container"
        exit 1
    fi

    echo "==> Swapping (downtime starts now)..."

    # Stop old container
    docker stop "$CONTAINER" > /dev/null

    # Remove any previous backup
    if docker inspect "$BACKUP_NAME" &>/dev/null; then
        docker rm "$BACKUP_NAME" > /dev/null
    fi

    # Old → backup
    docker rename "$CONTAINER" "$BACKUP_NAME"

    # Remove the stopped staging container (keeps its data volume)
    docker rm "$STAGING_NAME" > /dev/null

    # Create the production container using the staging data volume
    docker run -d \
        --name "$CONTAINER" \
        -e POSTGRES_DB="$PG_DB" \
        -e POSTGRES_USER="$PG_USER" \
        -e POSTGRES_PASSWORD="$PG_PASS" \
        -p "$HOST_PORT":5432 \
        -v "$STAGING_DATA_VOL":/var/lib/postgresql/data \
        $VOLUME_ARGS \
        --restart "$RESTART_POLICY" \
        "postgres:$TARGET_VERSION" > /dev/null

    # Wait for ready
    for i in $(seq 1 15); do
        if docker exec "$CONTAINER" pg_isready -U "$PG_USER" &>/dev/null; then
            break
        fi
        sleep 1
    done

    if ! docker exec "$CONTAINER" pg_isready -U "$PG_USER" &>/dev/null; then
        echo "ERROR: New container did not start. Rolling back..."
        docker stop "$CONTAINER" > /dev/null 2>&1 && docker rm "$CONTAINER" > /dev/null 2>&1
        docker rename "$BACKUP_NAME" "$CONTAINER"
        docker start "$CONTAINER"
        echo "    Rolled back to previous version."
        exit 1
    fi

    echo "    Swap complete (downtime ends)"

    # Verify
    echo ""
    echo "==> Verifying..."
    NEW_VERSION=$(docker exec "$CONTAINER" psql -U "$PG_USER" -d "$PG_DB" -t \
        -c "SELECT version();" | head -1 | xargs)
    echo "    PostgreSQL version: $NEW_VERSION"

    TABLE_COUNT=$(docker exec "$CONTAINER" psql -U "$PG_USER" -d "$PG_DB" -t \
        -c "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public';" | xargs)
    echo "    Public tables: $TABLE_COUNT"

    echo ""
    echo "==> Upgrade complete!"
    echo "    Old container preserved as '$BACKUP_NAME' for rollback."
    echo ""
    echo "    Next: deploy Django 5.2 and run migrations"
    echo ""
    echo "    To roll back:"
    echo "      docker stop $CONTAINER && docker rm $CONTAINER"
    echo "      docker rename $BACKUP_NAME $CONTAINER"
    echo "      docker start $CONTAINER"
    echo ""
    echo "    To clean up after verifying:"
    echo "      docker rm $BACKUP_NAME"
    echo "      rm ${DUMP_PATH}"
    exit 0
fi
