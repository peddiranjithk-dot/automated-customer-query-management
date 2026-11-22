import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent / "queries.db"


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS queries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_id TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                subject TEXT NOT NULL,
                message TEXT NOT NULL,
                category TEXT,
                priority TEXT,
                sentiment TEXT,
                status TEXT DEFAULT 'Open',
                auto_reply TEXT,
                agent_reply TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        """)


def create_query(name, email, subject, message, analysis):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_conn() as conn:
        cur = conn.execute(
            """INSERT INTO queries
               (ticket_id, name, email, subject, message, category, priority, sentiment,
                status, auto_reply, created_at, updated_at)
               VALUES ('TMP', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (name, email, subject, message, analysis["category"], analysis["priority"],
             analysis["sentiment"],
             "Auto-Resolved" if analysis["auto_reply"] else "Open",
             analysis["auto_reply"], now, now),
        )
        ticket_id = f"TKT-{datetime.now():%Y%m}-{cur.lastrowid:05d}"
        conn.execute("UPDATE queries SET ticket_id=? WHERE id=?", (ticket_id, cur.lastrowid))
    return ticket_id


def get_by_ticket(ticket_id):
    with get_conn() as conn:
        return conn.execute("SELECT * FROM queries WHERE ticket_id=?",
                            (ticket_id.strip().upper(),)).fetchone()


def get_by_id(qid):
    with get_conn() as conn:
        return conn.execute("SELECT * FROM queries WHERE id=?", (qid,)).fetchone()


def list_queries(status=None, category=None, search=None):
    sql, params = "SELECT * FROM queries WHERE 1=1", []
    if status:
        sql += " AND status=?"
        params.append(status)
    if category:
        sql += " AND category=?"
        params.append(category)
    if search:
        sql += " AND (subject LIKE ? OR message LIKE ? OR ticket_id LIKE ? OR email LIKE ?)"
        params += [f"%{search}%"] * 4
    sql += (" ORDER BY CASE priority WHEN 'Urgent' THEN 0 WHEN 'High' THEN 1 ELSE 2 END,"
            " created_at DESC")
    with get_conn() as conn:
        return conn.execute(sql, params).fetchall()


def update_query(qid, status, agent_reply):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_conn() as conn:
        conn.execute("UPDATE queries SET status=?, agent_reply=?, updated_at=? WHERE id=?",
                     (status, agent_reply, now, qid))


def stats():
    with get_conn() as conn:
        total = conn.execute("SELECT COUNT(*) FROM queries").fetchone()[0]
        by_status = conn.execute(
            "SELECT status, COUNT(*) c FROM queries GROUP BY status").fetchall()
        by_cat = conn.execute(
            "SELECT category, COUNT(*) c FROM queries GROUP BY category ORDER BY c DESC").fetchall()
        auto = conn.execute(
            "SELECT COUNT(*) FROM queries WHERE status='Auto-Resolved'").fetchone()[0]
    return {
        "total": total,
        "by_status": {r["status"]: r["c"] for r in by_status},
        "by_category": {r["category"]: r["c"] for r in by_cat},
        "auto_rate": round(100 * auto / total, 1) if total else 0,
    }
