"""
Persistent operational state for server-controlled
educational activity execution.

Performance events remain the authoritative
historical observations.
"""

EXECUTION_SCHEMA_STATEMENTS = (

    """
    CREATE TABLE IF NOT EXISTS activity_execution_states (

        session_id TEXT PRIMARY KEY NOT NULL,

        status TEXT NOT NULL DEFAULT 'READY'
            CHECK (
                status IN (
                    'READY',
                    'AWAITING_RESPONSE',
                    'REPEAT_REQUIRED',
                    'SUCCESS_CONFIRMED',
                    'COMPLETED',
                    'INTERRUPTED'
                )
            ),

        current_round_number INTEGER NOT NULL DEFAULT 0
            CHECK (current_round_number >= 0),

        completion_event_id TEXT,

        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,

        FOREIGN KEY (session_id)
            REFERENCES learning_sessions(session_id)
            ON DELETE RESTRICT,

        FOREIGN KEY (completion_event_id)
            REFERENCES performance_events(event_id)
            ON DELETE RESTRICT,

        CHECK (
            status NOT IN (
                'SUCCESS_CONFIRMED',
                'COMPLETED'
            )
            OR completion_event_id IS NOT NULL
        ),

        CHECK (
            status != 'READY'
            OR current_round_number = 0
        ),

        CHECK (
            status NOT IN (
                'AWAITING_RESPONSE',
                'REPEAT_REQUIRED',
                'SUCCESS_CONFIRMED',
                'COMPLETED'
            )
            OR current_round_number > 0
        )
    )
    """,

    """
    CREATE TABLE IF NOT EXISTS activity_execution_rounds (

        question_id TEXT PRIMARY KEY NOT NULL,

        session_id TEXT NOT NULL,

        round_number INTEGER NOT NULL
            CHECK (round_number > 0),

        status TEXT NOT NULL
            CHECK (
                status IN (
                    'ACTIVE',
                    'REPEAT_REQUIRED',
                    'SUCCESS_CONFIRMED',
                    'INTERRUPTED'
                )
            ),

        presentation_snapshot TEXT NOT NULL
            CHECK (
                json_valid(presentation_snapshot)
                AND json_type(presentation_snapshot) = 'object'
            ),

        first_attempt_required INTEGER NOT NULL
            CHECK (first_attempt_required IN (0, 1)),

        attempt_count INTEGER NOT NULL DEFAULT 0
            CHECK (attempt_count >= 0),

        selected_alternatives TEXT NOT NULL DEFAULT '[]'
            CHECK (
                json_valid(selected_alternatives)
                AND json_type(selected_alternatives) = 'array'
            ),

        presentation_event_id TEXT NOT NULL,

        completion_event_id TEXT,

        presented_at TEXT NOT NULL,
        ended_at TEXT,

        FOREIGN KEY (session_id)
            REFERENCES activity_execution_states(session_id)
            ON DELETE RESTRICT,

        FOREIGN KEY (presentation_event_id)
            REFERENCES performance_events(event_id)
            ON DELETE RESTRICT,

        FOREIGN KEY (completion_event_id)
            REFERENCES performance_events(event_id)
            ON DELETE RESTRICT,

        UNIQUE (session_id, round_number),

        CHECK (
            (status = 'ACTIVE' AND ended_at IS NULL)
            OR
            (status != 'ACTIVE' AND ended_at IS NOT NULL)
        ),

        CHECK (
            status NOT IN (
                'REPEAT_REQUIRED',
                'SUCCESS_CONFIRMED'
            )
            OR completion_event_id IS NOT NULL
        ),

        CHECK (
            (round_number = 1 AND first_attempt_required = 0)
            OR
            (round_number > 1 AND first_attempt_required = 1)
        )
    )
    """,

    """
    CREATE UNIQUE INDEX IF NOT EXISTS
        uq_active_execution_round

    ON activity_execution_rounds (session_id)

    WHERE status = 'ACTIVE'
    """,

)


def create_activity_execution_schema(connection):

    for statement in EXECUTION_SCHEMA_STATEMENTS:

        connection.execute(statement)
