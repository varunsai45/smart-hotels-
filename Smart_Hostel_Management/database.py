import sqlite3
from pathlib import Path
from contextlib import contextmanager

DB_PATH = Path(__file__).parent / "data" / "hostel.db"
DB_PATH.parent.mkdir(exist_ok=True)

@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH, timeout=15)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_db():
    with get_db() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'admin',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS rooms (
            room_id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_number TEXT UNIQUE NOT NULL,
            capacity INTEGER NOT NULL CHECK(capacity > 0),
            monthly_fee REAL NOT NULL CHECK(monthly_fee >= 0),
            room_type TEXT DEFAULT 'Standard',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS students (
            student_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT,
            course TEXT,
            guardian_name TEXT,
            guardian_phone TEXT,
            joining_date TEXT NOT NULL,
            room_id INTEGER,
            active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(room_id) REFERENCES rooms(room_id) ON DELETE SET NULL
        );

        CREATE TABLE IF NOT EXISTS payments (
            payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            amount REAL NOT NULL CHECK(amount > 0),
            payment_month TEXT NOT NULL,
            payment_date TEXT NOT NULL,
            method TEXT NOT NULL DEFAULT 'Cash',
            reference TEXT,
            notes TEXT,
            FOREIGN KEY(student_id) REFERENCES students(student_id)
        );

        CREATE TABLE IF NOT EXISTS complaints (
            complaint_id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            category TEXT NOT NULL,
            description TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Pending',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(student_id) REFERENCES students(student_id)
        );

        CREATE TABLE IF NOT EXISTS visitors (
            visitor_id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            visitor_name TEXT NOT NULL,
            visitor_phone TEXT,
            purpose TEXT,
            entry_time TEXT NOT NULL,
            exit_time TEXT,
            FOREIGN KEY(student_id) REFERENCES students(student_id)
        );
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_students_room ON students(room_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_payments_student ON payments(student_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_complaints_status ON complaints(status)")
