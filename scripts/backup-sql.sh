#!/bin/bash
# Nightly production database backup.
# Deployed on anaheim as /home/strider/.cron/backup-sql.sh, run from strider's
# crontab at 00:00 local. Credentials come from ~/.pgpass.
set -uo pipefail

POSTGRES_PORT=5434
BACKUP_PATH=/home/strider/volumes/lutris-sqldumps
LOG_FILE=/home/strider/volumes/logs/backup-sql.log
KEEP_DAYS=14

log() {
    echo "$(date -Is) $*" >> "$LOG_FILE"
}

cd "$BACKUP_PATH" || exit 1
backup_file="lutris-$(date +%Y-%m-%d-%H-%M).pgdump"

# Custom format compresses while writing: no uncompressed-tar peak, no gzip step.
if ! pg_dump --format=custom -h localhost -p "$POSTGRES_PORT" -U lutris -f "$backup_file" lutris; then
    log "FAILED: pg_dump exited non-zero, partial file removed"
    echo "pg_dump failed" >&2
    rm -f "$backup_file"
    exit 1
fi

# Verify the dump is readable before trusting it or pruning anything.
if ! pg_restore --list "$backup_file" > /dev/null; then
    log "FAILED: $backup_file is not a valid dump, removed"
    echo "dump verification failed" >&2
    rm -f "$backup_file"
    exit 1
fi

ln -f "$backup_file" latest.pgdump
log "OK: $backup_file ($(du -h "$backup_file" | cut -f1))"

# Retention: keep the earliest dump of each month forever, plus everything
# from the last KEEP_DAYS days. Only runs after a verified backup.
declare -A month_seen
for f in $(ls lutris-*.tar.gz lutris-*.pgdump 2>/dev/null | sort); do
    month=${f:7:7}  # YYYY-MM from lutris-YYYY-MM-DD-HH-MM
    if [[ -z "${month_seen[$month]:-}" ]]; then
        month_seen[$month]=1
        continue
    fi
    if [[ -n "$(find "$f" -mtime -"$KEEP_DAYS" 2>/dev/null)" ]]; then
        continue
    fi
    log "PRUNE: $f"
    rm -f "$f"
done
