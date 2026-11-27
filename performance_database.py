"""
SQLite database infrastructure for student performance recording.

Existing profile, activity and assignment storage remains unchanged.

Performance events constitute the authoritative historical record
of learning interactions.
"""

import sqlite3
from contextlib import contextmanager
from pathlib import Path


DATA_DIR = Path(__file__).resolve().parent / "data"
DATABASE_PATH = DATA_DIR / "performance.db"

SCHEMA_VERSION = 2


SCHEMA_STATEMENTS = (

    """
    CREATE TABLE IF NOT EXISTS schema_metadata (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL
    )
    """,

    """
    CREATE TABLE IF NOT EXISTS learning_sessions (
        session_id TEXT PRIMARY KEY,

        student_id TEXT NOT NULL,
        assignment_id TEXT,
        activity_id TEXT,
        achievement_code TEXT,

        learning_mode TEXT NOT NULL CHECK (
            learning_mode IN (
                'COMPUTER_BASED',
                'TEACHER_ASSISTED',
                'TEACHER_LED'
            )
        ),

        activity_snapshot TEXT NOT NULL CHECK (
            json_valid(activity_snapshot)
        ),

        started_at TEXT NOT NULL,
        ended_at TEXT,

        status TEXT NOT NULL DEFAULT 'ACTIVE' CHECK (
            status IN (
                'ACTIVE',
                'COMPLETED',
                'TERMINATED',
                'INTERRUPTED'
            )
        ),

        termination_reason TEXT,

        CHECK (
            (status = 'ACTIVE' AND ended_at IS NULL)
            OR
            (status != 'ACTIVE' AND ended_at IS NOT NULL)
        )
    )
    """,

    """
    CREATE TABLE IF NOT EXISTS performance_events (
        event_id TEXT PRIMARY KEY,

        session_id TEXT NOT NULL,

        question_id TEXT,
        attempt_id TEXT,

        sequence_number INTEGER NOT NULL CHECK (
            sequence_number > 0
        ),

        event_type TEXT NOT NULL,

        occurred_at TEXT NOT NULL,
        recorded_at TEXT NOT NULL,

        source TEXT NOT NULL CHECK (
            source IN ('SYSTEM', 'TEACHER')
        ),

        payload TEXT NOT NULL CHECK (
            json_valid(payload)
        ),

        schema_version INTEGER NOT NULL CHECK (
            schema_version > 0
        ),

        FOREIGN KEY (session_id)
            REFERENCES learning_sessions(session_id)
            ON DELETE RESTRICT,

        UNIQUE (session_id, sequence_number)
    )
    """,

    """
    CREATE INDEX IF NOT EXISTS idx_sessions_student
    ON learning_sessions(student_id, started_at)
    """,

    """
    CREATE INDEX IF NOT EXISTS idx_sessions_achievement
    ON learning_sessions(student_id, achievement_code, started_at)
    """,

    """
    CREATE INDEX IF NOT EXISTS idx_sessions_assignment
    ON learning_sessions(assignment_id)
    """,

    """
    CREATE INDEX IF NOT EXISTS idx_sessions_activity
    ON learning_sessions(activity_id)
    """,

    """
    CREATE INDEX IF NOT EXISTS idx_events_question
    ON performance_events(session_id, question_id)
    """,

    """
    CREATE INDEX IF NOT EXISTS idx_events_type
    ON performance_events(session_id, event_type)
    """,

    """
    CREATE INDEX IF NOT EXISTS idx_events_attempt
    ON performance_events(session_id, attempt_id)
    """

)


def get_connection():
    """
    Open a configured database connection.

    Each operation obtains its own connection.
    Connections are not shared between Flask requests.
    """

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(
        DATABASE_PATH,
        timeout=10.0,
        isolation_level=None
    )

    connection.row_factory = sqlite3.Row

    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA busy_timeout = 10000")
    connection.execute("PRAGMA synchronous = FULL")

    return connection


@contextmanager
def database_transaction(write=False):
    """
    Manage an explicit database transaction.

    Write transactions acquire a reserved write lock
    before reading or modifying shared state.
    """

    connection = get_connection()

    try:
        if write:
            connection.execute("BEGIN IMMEDIATE")
        else:
            connection.execute("BEGIN")

        yield connection

        connection.commit()

    except BaseException:
        connection.rollback()
        raise

    finally:
        connection.close()


def ensure_active_assignment_uniqueness():
    """
    Allow multiple historical sessions for an assignment,
    but no more than one active session.
    """

    with database_transaction(write=True) as connection:

        connection.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS
                uq_active_performance_assignment
            ON learning_sessions (assignment_id)
            WHERE assignment_id IS NOT NULL
              AND status = 'ACTIVE'
        """)


def initialize_database():
    """
    Initialize the performance database.

    Initialization is repeatable and preserves existing records.
    Unsupported schema versions are rejected.
    """

    connection = get_connection()

    try:
        journal_mode = connection.execute(
            "PRAGMA journal_mode = WAL"
        ).fetchone()[0]

        if journal_mode.lower() != "wal":
            raise RuntimeError(
                "Unable to enable SQLite WAL mode."
            )

        connection.execute("BEGIN IMMEDIATE")

        connection.execute(SCHEMA_STATEMENTS[0])

        version_record = connection.execute(
            """
            SELECT value
            FROM schema_metadata
            WHERE key = 'schema_version'
            """
        ).fetchone()

        if version_record is not None:

            existing_version = int(version_record["value"])

            if (
                existing_version < 1
                or existing_version > SCHEMA_VERSION
            ):
                raise RuntimeError(
                    f"Unsupported performance database schema: "
                    f"{existing_version}. "
                    f"Maximum supported: {SCHEMA_VERSION}."
                )

        for statement in SCHEMA_STATEMENTS[1:]:
            connection.execute(statement)

        if version_record is None:

            connection.execute(
                """
                INSERT INTO schema_metadata (key, value)
                VALUES ('schema_version', ?)
                """,
                ("1",)
            )

            existing_version = 1

        if existing_version < SCHEMA_VERSION:

            from database_migrations import migrate_database

            migrate_database(
                connection,
                current_version=existing_version,
                target_version=SCHEMA_VERSION
            )

        connection.commit()

    except BaseException:
        connection.rollback()
        raise

    finally:
        connection.close()


if __name__ == "__main__":

    initialize_database()

    print("Performance database initialized.")
    print("Database:", DATABASE_PATH)
    print("Schema version:", SCHEMA_VERSION)
