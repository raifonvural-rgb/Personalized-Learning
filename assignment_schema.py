"""
SQLite schema for teacher-controlled multiple assignments.

Introduced in database schema version 2.

Design decisions:
    DD-059: Shared transactional storage.
    DD-060: Independent assignment identity.
    DD-061: Separate enablement and lifecycle status.
    DD-062: One executing assignment per student.
    DD-063: Interrupted assignments return to pending.
    DD-064: Preserve completed assignments.
    DD-065: Ordered assignments represent the sequence.
"""


ASSIGNMENT_SCHEMA_STATEMENTS = (

    """
    CREATE TABLE IF NOT EXISTS assignments (
        assignment_id TEXT PRIMARY KEY NOT NULL,

        student_id TEXT NOT NULL,
        activity_id TEXT NOT NULL,

        sequence_order INTEGER NOT NULL CHECK (
            typeof(sequence_order) = 'integer'
            AND sequence_order > 0
        ),

        enabled INTEGER NOT NULL DEFAULT 1 CHECK (
            enabled IN (0, 1)
        ),

        status TEXT NOT NULL DEFAULT 'PENDING' CHECK (
            status IN (
                'PENDING',
                'IN_PROGRESS',
                'COMPLETED',
                'CANCELLED'
            )
        ),

        assigned_at TEXT NOT NULL,
        started_at TEXT,
        completed_at TEXT,
        updated_at TEXT NOT NULL,

        CHECK (
            status != 'IN_PROGRESS'
            OR started_at IS NOT NULL
        ),

        CHECK (
            status != 'IN_PROGRESS'
            OR enabled = 1
        ),

        CHECK (
            (
                status = 'COMPLETED'
                AND completed_at IS NOT NULL
                AND started_at IS NOT NULL
            )
            OR
            (
                status != 'COMPLETED'
                AND completed_at IS NULL
            )
        )
    )
    """,

    """
    CREATE UNIQUE INDEX IF NOT EXISTS
        uq_student_in_progress_assignment
    ON assignments (student_id)
    WHERE status = 'IN_PROGRESS'
    """,

    """
    CREATE UNIQUE INDEX IF NOT EXISTS
        uq_student_pending_sequence_order
    ON assignments (student_id, sequence_order)
    WHERE status IN ('PENDING', 'IN_PROGRESS')
    """,

    """
    CREATE INDEX IF NOT EXISTS
        idx_assignments_student_status_order
    ON assignments (
        student_id,
        status,
        enabled,
        sequence_order
    )
    """,

    """
    CREATE INDEX IF NOT EXISTS
        idx_assignments_student_activity
    ON assignments (student_id, activity_id)
    """

)


def create_assignment_schema(connection):
    """
    Create assignment tables and indexes using
    the caller's existing database transaction.

    Transaction management remains the caller's
    responsibility.
    """

    for statement in ASSIGNMENT_SCHEMA_STATEMENTS:
        connection.execute(statement)
