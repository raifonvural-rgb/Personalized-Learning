"""
Migration of legacy JSON assignments into SQLite.

Migration preserves original assignment identities
and historical performance associations.

Transaction management belongs to the caller.
"""

import json
from pathlib import Path

from performance_models import (
    validate_identifier,
    validate_timestamp,
    utc_now,
)


DATA_DIR = Path(__file__).resolve().parent / "data"

LEGACY_ASSIGNMENTS_FILE = DATA_DIR / "assignments.json"


def load_legacy_assignments():

    if not LEGACY_ASSIGNMENTS_FILE.exists():
        return []

    with LEGACY_ASSIGNMENTS_FILE.open(
        "r", encoding="utf-8"
    ) as file:
        records = json.load(file)

    if not isinstance(records, dict):
        raise ValueError(
            "Invalid legacy assignment storage format"
        )

    assignments = []
    seen_ids = set()

    for student_key, record in records.items():

        if not isinstance(record, dict):
            raise ValueError(
                "Invalid legacy assignment record"
            )

        assignment_id = validate_identifier(
            record.get("id"),
            "assignment_id"
        )

        student_id = validate_identifier(
            record.get("student_id"),
            "student_id"
        )

        activity_id = validate_identifier(
            record.get("activity_id"),
            "activity_id"
        )

        assigned_at = record.get("assigned_at")

        validate_timestamp(
            assigned_at,
            "assigned_at"
        )

        if student_key != student_id:
            raise ValueError(
                "Legacy assignment student mismatch"
            )

        if assignment_id in seen_ids:
            raise ValueError(
                "Duplicate legacy assignment ID"
            )

        seen_ids.add(assignment_id)

        assignments.append({
            "assignment_id": assignment_id,
            "student_id": student_id,
            "activity_id": activity_id,
            "assigned_at": assigned_at,
        })

    return assignments


def import_legacy_assignments(connection):

    records = load_legacy_assignments()

    imported = 0
    existing = 0

    for record in records:

        assignment_id = record["assignment_id"]

        previous = connection.execute("""
            SELECT *
            FROM assignments
            WHERE assignment_id = ?
        """, (assignment_id,)).fetchone()

        if previous is not None:

            identity_fields = (
                "student_id",
                "activity_id",
                "assigned_at",
            )

            for field in identity_fields:

                if previous[field] != record[field]:
                    raise ValueError(
                        "Conflicting migrated assignment"
                    )

            existing += 1
            continue

        sessions = connection.execute("""
            SELECT *
            FROM learning_sessions
            WHERE assignment_id = ?
            ORDER BY started_at, session_id
        """, (assignment_id,)).fetchall()

        for learning_session in sessions:

            if (
                learning_session["student_id"]
                != record["student_id"]
                or
                learning_session["activity_id"]
                != record["activity_id"]
            ):
                raise ValueError(
                    "Historical assignment association mismatch"
                )

        active_sessions = [
            learning_session
            for learning_session in sessions
            if learning_session["status"] == "ACTIVE"
        ]

        if len(active_sessions) > 1:
            raise ValueError(
                "Multiple active sessions for assignment"
            )

        started_at = (
            sessions[0]["started_at"]
            if sessions else None
        )

        status = (
            "IN_PROGRESS"
            if active_sessions
            else "PENDING"
        )

        connection.execute("""
            INSERT INTO assignments (
                assignment_id,
                student_id,
                activity_id,
                sequence_order,
                enabled,
                status,
                assigned_at,
                started_at,
                completed_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            assignment_id,
            record["student_id"],
            record["activity_id"],
            1,
            1,
            status,
            record["assigned_at"],
            started_at,
            None,
            utc_now(),
        ))

        imported += 1

    return {
        "legacy_records": len(records),
        "imported": imported,
        "already_imported": existing,
    }


def reconcile_orphaned_active_sessions(connection):
    """
    Interrupt active assignment-bound sessions whose
    assignments are absent from the migrated storage.

    Historical sessions and existing events are preserved.

    Transaction management belongs to the caller.
    """

    from performance_models import (
        SessionStatus,
        EventType,
        EventSource,
        build_event_record,
    )

    from performance_storage import (
        next_event_sequence,
        insert_event,
    )

    orphaned_sessions = connection.execute("""
        SELECT learning_sessions.*
        FROM learning_sessions

        LEFT JOIN assignments
            ON assignments.assignment_id =
               learning_sessions.assignment_id

        WHERE learning_sessions.status = 'ACTIVE'
          AND learning_sessions.assignment_id IS NOT NULL
          AND assignments.assignment_id IS NULL

        ORDER BY learning_sessions.started_at,
                 learning_sessions.session_id
    """).fetchall()

    interrupted = 0

    for learning_session in orphaned_sessions:

        session_id = learning_session["session_id"]

        ended_at = utc_now()

        reason = "ASSIGNMENT_MISSING_DURING_MIGRATION"

        result = connection.execute("""
            UPDATE learning_sessions
            SET ended_at = ?,
                status = ?,
                termination_reason = ?

            WHERE session_id = ?
              AND status = 'ACTIVE'
        """, (
            ended_at,
            SessionStatus.INTERRUPTED.value,
            reason,
            session_id,
        ))

        if result.rowcount != 1:
            raise RuntimeError(
                "Unexpected session reconciliation result"
            )

        event = build_event_record(
            session_id=session_id,

            sequence_number=next_event_sequence(
                connection,
                session_id
            ),

            event_type=EventType.SESSION_ENDED,
            source=EventSource.SYSTEM,

            occurred_at=ended_at,

            payload={
                "status": SessionStatus.INTERRUPTED.value,
                "termination_reason": reason,
            },
        )

        insert_event(connection, event)

        interrupted += 1

    return {
        "orphaned_active_sessions": len(orphaned_sessions),
        "interrupted_sessions": interrupted,
    }


def reconcile_migrated_active_sessions(connection):
    """
    Interrupt legacy active sessions associated with
    successfully migrated assignments.

    Return unfinished assignments to PENDING so that
    they can restart under the new execution engine.

    Transaction management belongs to the caller.
    """

    from performance_models import SessionStatus

    from performance_storage import (
        end_learning_session_in_transaction,
    )

    if not connection.in_transaction:

        raise RuntimeError(
            "Session reconciliation requires a transaction"
        )

    active_sessions = connection.execute("""
        SELECT
            s.session_id,
            s.assignment_id,
            s.student_id,
            s.activity_id,

            a.student_id AS assignment_student_id,
            a.activity_id AS assignment_activity_id,
            a.status AS assignment_status

        FROM learning_sessions AS s

        INNER JOIN assignments AS a
            ON a.assignment_id = s.assignment_id

        WHERE s.status = 'ACTIVE'

        ORDER BY s.started_at, s.session_id
    """).fetchall()

    interrupted = 0

    returned_to_pending = 0

    for learning_session in active_sessions:

        if (
            learning_session["student_id"] !=
                learning_session["assignment_student_id"]

            or learning_session["activity_id"] !=
                learning_session["assignment_activity_id"]
        ):

            raise ValueError(
                "Migrated session association mismatch"
            )

        if (
            learning_session["assignment_status"]
            != "IN_PROGRESS"
        ):

            raise ValueError(
                "Migrated active assignment is not in progress"
            )

        ended_session = (
            end_learning_session_in_transaction(
                connection=connection,

                session_id=learning_session[
                    "session_id"
                ],

                status=SessionStatus.INTERRUPTED,

                termination_reason=(
                    "LEGACY_EXECUTION_STATE_UNAVAILABLE"
                ),
            )
        )

        result = connection.execute("""
            UPDATE assignments

            SET status = 'PENDING',
                updated_at = ?

            WHERE assignment_id = ?
              AND student_id = ?
              AND status = 'IN_PROGRESS'
        """, (
            ended_session["ended_at"],

            learning_session["assignment_id"],

            learning_session["student_id"],
        ))

        if result.rowcount != 1:

            raise RuntimeError(
                "Migrated assignment reconciliation failed"
            )

        interrupted += 1

        returned_to_pending += 1

    return {
        "matched_legacy_active_sessions":
            len(active_sessions),

        "matched_sessions_interrupted":
            interrupted,

        "assignments_returned_to_pending":
            returned_to_pending,
    }
