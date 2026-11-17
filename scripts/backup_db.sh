#!/usr/bin/env bash
# NexaAI Automated Database Backup Script
set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-./backups}"
mkdir -p "$BACKUP_DIR"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

if [ -n "${DATABASE_URL:-}" ] && [[ "$DATABASE_URL" == *"postgres"* ]]; then
    BACKUP_FILE="$BACKUP_DIR/nexa_pg_$TIMESTAMP.sql"
    echo "[*] Backing up PostgreSQL database to $BACKUP_FILE"
    pg_dump "$DATABASE_URL" > "$BACKUP_FILE"
    echo "[+] Backup successfully saved: $BACKUP_FILE"
else
    DB_FILE="${SQLITE_PATH:-./nexa_ai.db}"
    if [ -f "$DB_FILE" ]; then
        BACKUP_FILE="$BACKUP_DIR/nexa_sqlite_$TIMESTAMP.db"
        cp "$DB_FILE" "$BACKUP_FILE"
        echo "[+] SQLite database backed up to $BACKUP_FILE"
    else
        echo "[!] No database file found to backup."
    fi
fi
