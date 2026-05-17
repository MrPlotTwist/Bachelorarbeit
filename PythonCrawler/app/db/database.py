import sqlite3
import datetime
import json
import os

DB_PATH = os.getenv("DB_PATH", "crawler.db")

def get_connection():
    con = sqlite3.connect(DB_PATH)
    con.execute("PRAGMA foreign_keys = ON")
    return con


def init_db():
    con = get_connection()
    cur = con.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS runs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        start_url TEXT,
        started_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        finished_at TEXT,
        status TEXT NOT NULL DEFAULT 'running',
        report_filename TEXT,
        report_created_at TEXT
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS targets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        run_id INTEGER NOT NULL,
        base_url TEXT NOT NULL,
        headers_json TEXT,
        last_scanned_at TEXT,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(run_id, base_url),
        FOREIGN KEY (run_id) REFERENCES runs(id) ON DELETE CASCADE
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS forms (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        target_id INTEGER NOT NULL,
        page_url TEXT NOT NULL,
        action_url TEXT,
        method TEXT,
        form_name TEXT,
        form_structure_json TEXT,
        discovered_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (target_id) REFERENCES targets(id) ON DELETE CASCADE
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS vulnerabilities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        target_id INTEGER NOT NULL,
        form_id INTEGER,
        page_url TEXT,
        type TEXT NOT NULL,
        severity TEXT NOT NULL,
        parameter_name TEXT,
        payload TEXT,
        evidence TEXT,
        status TEXT NOT NULL DEFAULT 'open',
        discovered_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (target_id) REFERENCES targets(id) ON DELETE CASCADE,
        FOREIGN KEY (form_id) REFERENCES forms(id) ON DELETE SET NULL
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS discovered_credentials (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        target_id INTEGER NOT NULL,
        form_id INTEGER,
        login_token TEXT,
        username TEXT,
        password TEXT,
        discovered_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (target_id) REFERENCES targets(id) ON DELETE CASCADE,
        FOREIGN KEY (form_id) REFERENCES forms(id) ON DELETE SET NULL
    )
    """)
    con.commit()
    cur.close()
    con.close()


def readDB(conn):
    cur = conn.cursor()
    cur.execute("SELECT * FROM targets")
    rows = cur.fetchall()

    print("TARGETS:")
    for row in rows:
        print(row)

    cur.close()


def create_run(start_url: str | None = None):
    con = get_connection()
    cur = con.cursor()

    cur.execute("""
    INSERT INTO runs (start_url, status)
    VALUES (?, 'running')
    """, (start_url,))

    run_id = cur.lastrowid

    con.commit()
    cur.close()
    con.close()

    return run_id

def update_run_report(run_id: int, report_filename: str):
    now = datetime.datetime.now().isoformat()

    con = get_connection()
    cur = con.cursor()

    cur.execute("""
    UPDATE runs
    SET report_filename = ?, report_created_at = ?
    WHERE id = ?
    """, (report_filename, now, run_id))

    con.commit()
    cur.close()
    con.close()

def finish_run(run_id: int, status: str = "finished"):
    now = datetime.datetime.now().isoformat()

    con = get_connection()
    cur = con.cursor()

    cur.execute("""
    UPDATE runs
    SET finished_at = ?, status = ?
    WHERE id = ?
    """, (now, status, run_id))

    con.commit()
    cur.close()
    con.close()


def insert_into_targets(
    base_url: str,
    run_id: int,
    headers_json: str | None = None
):
    now = datetime.datetime.now().isoformat()

    con = get_connection()
    cur = con.cursor()

    cur.execute("""
    INSERT OR IGNORE INTO targets (base_url, run_id, headers_json, last_scanned_at, created_at)
    VALUES (?, ?, ?, ?, ?)
    """, (base_url, run_id, headers_json, now, now))

    con.commit()

    cur.execute("""
    SELECT id
    FROM targets
    WHERE base_url = ? AND run_id = ?
    """, (base_url, run_id))

    row = cur.fetchone()

    cur.close()
    con.close()

    return row[0] if row else None


def insert_into_forms(
    target_id: int,
    page_url: str,
    action_url: str | None,
    method: str | None,
    form_name: str | None,
    form_structure_json: str | None
):
    con = get_connection()
    cur = con.cursor()

    cur.execute("""
    INSERT INTO forms (target_id, page_url, action_url, method, form_name, form_structure_json)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (target_id, page_url, action_url, method, form_name, form_structure_json))

    form_id = cur.lastrowid

    con.commit()
    cur.close()
    con.close()

    return form_id


def insert_into_vulnerabilities(
    target_id: int,
    form_id: int | None,
    page_url: str | None,
    vul_type: str,
    severity: str,
    parameter_name: str | None,
    payload: str | None,
    evidence: str | None
):
    con = get_connection()
    cur = con.cursor()

    cur.execute("""
    INSERT INTO vulnerabilities (
        target_id, form_id, page_url, type, severity, parameter_name, payload, evidence
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (target_id, form_id, page_url, vul_type, severity, parameter_name, payload, evidence))

    vuln_id = cur.lastrowid

    con.commit()
    cur.close()
    con.close()

    return vuln_id


def insert_into_discovered_credentials(
    target_id: int,
    form_id: int | None,
    login_token: str | None,
    username: str | None,
    password: str | None
):
    con = get_connection()
    cur = con.cursor()

    cur.execute("""
    INSERT INTO discovered_credentials (target_id, form_id, login_token, username, password)
    VALUES (?, ?, ?, ?, ?)
    """, (target_id, form_id, login_token, username, password))

    cred_id = cur.lastrowid

    con.commit()
    cur.close()
    con.close()

    return cred_id


def get_run_results(run_id: int):
    con = get_connection()
    cur = con.cursor()

    cur.execute("SELECT * FROM runs WHERE id = ?", (run_id,))
    run_row = cur.fetchone()

    cur.execute("SELECT * FROM targets WHERE run_id = ?", (run_id,))
    targets = cur.fetchall()

    results = []

    for target in targets:
        target_id = target[0]

        cur.execute("SELECT * FROM forms WHERE target_id = ?", (target_id,))
        forms = cur.fetchall()

        cur.execute("SELECT * FROM vulnerabilities WHERE target_id = ?", (target_id,))
        vulnerabilities = cur.fetchall()

        cur.execute("SELECT * FROM discovered_credentials WHERE target_id = ?", (target_id,))
        credentials = cur.fetchall()

        results.append({
            "target": target,
            "forms": forms,
            "vulnerabilities": vulnerabilities,
            "credentials": credentials
        })

    cur.close()
    con.close()

    return {
        "run": run_row,
        "targets": results
    }
