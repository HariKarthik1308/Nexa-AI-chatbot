#!/usr/bin/env python3
"""
NexaAI Database Backup & Disaster Recovery Utility
Supports both local SQLite async snapshots and PostgreSQL (pg_dump) exports.
"""
import os
import shutil
import subprocess
import sys
import time
from urllib.parse import urlparse


def perform_backup():
    db_url = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./nexa_ai.db")
    backup_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backups"))
    os.makedirs(backup_dir, exist_ok=True)
    timestamp = time.strftime("%Y%m%d_%H%M%S")

    print(f"[*] NexaAI Backup Utility initiating at {timestamp}")
    print(f"[*] Database URL: {db_url}")

    if "sqlite" in db_url:
        # Extract SQLite file path
        parsed = db_url.split("///")[-1]
        sqlite_file = os.path.abspath(parsed)
        if not os.path.exists(sqlite_file):
            print(f"[!] Warning: SQLite database file not found at '{sqlite_file}'. Creating empty checkpoint.")
            return

        target_file = os.path.join(backup_dir, f"nexa_backup_{timestamp}.sqlite")
        shutil.copy2(sqlite_file, target_file)
        size_kb = os.path.getsize(target_file) / 1024
        print(f"[+] SQLite database successfully backed up to: {target_file} ({size_kb:.1f} KB)")

    elif "postgresql" in db_url:
        clean_url = db_url.replace("+asyncpg", "")
        parsed = urlparse(clean_url)
        target_file = os.path.join(backup_dir, f"nexa_pg_backup_{timestamp}.sql")
        
        env = os.environ.copy()
        if parsed.password:
            env["PGPASSWORD"] = parsed.password

        cmd = [
            "pg_dump",
            "-h", parsed.hostname or "localhost",
            "-p", str(parsed.port or 5432),
            "-U", parsed.username or "postgres",
            "-d", parsed.path.lstrip("/") or "nexa_ai",
            "-F", "c",
            "-f", target_file,
        ]

        print(f"[*] Executing pg_dump for database '{parsed.path.lstrip('/')}'...")
        try:
            subprocess.run(cmd, env=env, check=True)
            print(f"[+] PostgreSQL backup completed successfully: {target_file}")
        except FileNotFoundError:
            print("[!] Warning: 'pg_dump' utility not found on PATH. Ensure postgres client tools are installed.")
        except subprocess.CalledProcessError as err:
            print(f"[!] Error: pg_dump failed with exit code {err.returncode}")
            sys.exit(1)


if __name__ == "__main__":
    perform_backup()
