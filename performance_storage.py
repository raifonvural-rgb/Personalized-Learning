"""
Persistent storage for learning sessions and performance events.

Performance events are append-only historical observations.

Session lifecycle changes and their corresponding events
are recorded within the same database transaction.

This module does not perform educational interpretation.
"""

from performance_database import database_transaction
from performance_event_validation import validate_event_payload

from performance_models import (
    LearningMode,
    SessionStatus,
    EventSource,
    EventType,
    build_session_record,
    build_event_record,
    decode_json_object,
    validate_identifier,
    validate_enum,
    validate_positive_integer,
    validate_timestamp,
    utc_now
)


def decode_session(row):

    if row is None:
        return None

    result = dict(row)

    result["activity_snapshot"] = decode_json_object(
        result["activity_snapshot"],
        "activity_snapshot"
    )

    return result


def decode_event(row):

    if row is None:
        return None

    result = dict(row)

    result["payload"] = decode_json_object(
        result["payload"],
        "payload"
    )

    return result


def insert_session(connection, record):

    connection.execute(
        """
        INSERT INTO learning_sessions (
            session_id,
            student_id,
            assignment_id,
            activity_id,
            achievement_code,
            learning_mode,
            activity_snapshot,
            started_at,
            ended_at,
            status,
            termination_reason
        )
        VALUES (
            :session_id,
            :student_id,
            :assignment_id,
            :activity_id,
            :achievement_code,
            :learning_mode,
            :activity_snapshot,
            :started_at,
            :ended_at,
            :status,
            :termination_reason
        )
        """,
        record
    )


def insert_event(connection, record):

    validate_event_payload(
        event_type=record["event_type"],
        source=record["source"],
        payload=decode_json_object(
            record["payload"],
            "payload"
        )
    )

    connection.execute(
        """
        INSERT INTO performance_events (
            event_id,
            session_id,
            question_id,
            attempt_id,
            sequence_number,
            event_type,
            occurred_at,
            recorded_at,
            source,
            payload,
            schema_version
        )
        VALUES (
            :event_id,
            :session_id,
            :question_id,
            :attempt_id,
            :sequence_number,
            :event_type,
            :occurred_at,
            :recorded_at,
            :source,
            :payload,
            :schema_version
        )
        """,
        record
    )


def find_session(connection, session_id):

    return connection.execute(
        """
        SELECT *
        FROM learning_sessions
        WHERE session_id = ?
        """,
        (session_id,)
    ).fetchone()


def next_event_sequence(connection, session_id):

    row = connection.execute(
        """
        SELECT COALESCE(MAX(sequence_number), 0) + 1
            AS next_sequence
        FROM performance_events
        WHERE session_id = ?
        """,
        (session_id,)
    ).fetchone()

    return row["next_sequence"]


def create_learning_session_in_transaction(
    connection,
    student_id,
    learning_mode,
    activity_snapshot,
    assignment_id=None,
    activity_id=None,
    achievement_code=None
):
    """
    Create a permanent learning session and its initial event.

    Both records are committed together.
    """

    if not connection.in_transaction:
        raise RuntimeError(
            "An active database transaction is required."
        )


    record = build_session_record(
        student_id=student_id,
        learning_mode=learning_mode,
        activity_snapshot=activity_snapshot,
        assignment_id=assignment_id,
        activity_id=activity_id,
        achievement_code=achievement_code
    )


    assignment_id = record["assignment_id"]

    if assignment_id is not None:

        existing = connection.execute(
            '''
            SELECT *
            FROM learning_sessions
            WHERE assignment_id = ?
              AND status = 'ACTIVE'
            ''',
            (assignment_id,)
        ).fetchone()

        if existing is not None:

            association_fields = (
                "student_id",
                "assignment_id",
                "activity_id",
                "achievement_code",
                "learning_mode"
            )

            for field in association_fields:

                if existing[field] != record[field]:

                    raise ValueError(
                        "Active session association mismatch: "
                        + field
                    )

            existing_snapshot = decode_json_object(
                existing["activity_snapshot"],
                "activity_snapshot"
            )

            requested_snapshot = decode_json_object(
                record["activity_snapshot"],
                "activity_snapshot"
            )

            if existing_snapshot != requested_snapshot:

                raise ValueError(
                    "Active session configuration mismatch."
                )

            return decode_session(existing)

    insert_session(connection, record)

    event = build_event_record(
        session_id=record["session_id"],
        sequence_number=1,
        event_type=EventType.SESSION_STARTED,
        source=EventSource.SYSTEM,
        occurred_at=record["started_at"],
        payload={
            "learning_mode": record["learning_mode"],
            "assignment_id": record["assignment_id"],
            "activity_id": record["activity_id"],
            "achievement_code": record["achievement_code"]
        }
    )

    insert_event(connection, event)

    return decode_session(record)


def create_learning_session(
    student_id,
    learning_mode,
    activity_snapshot,
    assignment_id=None,
    activity_id=None,
    achievement_code=None
):
    """Execute using an independent write transaction."""

    with database_transaction(write=True) as connection:

        return create_learning_session_in_transaction(
            connection=connection,
            student_id=student_id,
            learning_mode=learning_mode,
            activity_snapshot=activity_snapshot,
            assignment_id=assignment_id,
            activity_id=activity_id,
            achievement_code=achievement_code
        )


def get_learning_session(session_id):

    session_id = validate_identifier(
        session_id,
        "session_id"
    )

    with database_transaction() as connection:

        row = find_session(connection, session_id)

        return decode_session(row)


def validate_event_associations(connection, record):

    session_id = record["session_id"]
    question_id = record["question_id"]
    attempt_id = record["attempt_id"]
    event_type = record["event_type"]

    if question_id is not None:

        question = connection.execute(
            """
            SELECT event_id
            FROM performance_events
            WHERE session_id = ?
              AND question_id = ?
              AND event_type = 'QUESTION_PRESENTED'
            LIMIT 1
            """,
            (session_id, question_id)
        ).fetchone()

        if event_type == EventType.QUESTION_PRESENTED.value:

            if question is not None:
                raise ValueError(
                    "Question has already been presented."
                )

            if attempt_id is not None:
                raise ValueError(
                    "Question presentation cannot have an attempt ID."
                )

        elif question is None:

            raise ValueError(
                "Question does not belong to this session."
            )

        completed = connection.execute(
            """
            SELECT event_id
            FROM performance_events
            WHERE session_id = ?
              AND question_id = ?
              AND event_type = 'QUESTION_COMPLETED'
            LIMIT 1
            """,
            (session_id, question_id)
        ).fetchone()

        if completed is not None and event_type in (
            EventType.RESPONSE_SUBMITTED.value,
            EventType.QUESTION_COMPLETED.value
        ):
            raise ValueError(
                "Question has already been completed."
            )

    if attempt_id is not None:

        attempt = connection.execute(
            """
            SELECT question_id
            FROM performance_events
            WHERE session_id = ?
              AND attempt_id = ?
              AND event_type = 'RESPONSE_SUBMITTED'
            LIMIT 1
            """,
            (session_id, attempt_id)
        ).fetchone()

        if event_type == EventType.RESPONSE_SUBMITTED.value:

            if attempt is not None:
                raise ValueError(
                    "Response attempt has already been recorded."
                )

        elif (
            attempt is None
            or attempt["question_id"] != question_id
        ):

            raise ValueError(
                "Attempt does not belong to this question."
            )


def append_performance_event_in_transaction(
    connection,
    session_id,
    event_type,
    source,
    payload,
    question_id=None,
    attempt_id=None,
    occurred_at=None,
    event_id=None
):
    """
    Append an observation to an existing learning session.

    Reusing an event identifier with identical content
    returns the original event instead of inserting a duplicate.
    """

    if not connection.in_transaction:
        raise RuntimeError(
            "An active database transaction is required."
        )


    session_id = validate_identifier(
        session_id,
        "session_id"
    )

    event_type = validate_enum(
        event_type,
        EventType,
        "event_type"
    )

    if event_type in (
        EventType.SESSION_STARTED.value,
        EventType.SESSION_ENDED.value
    ):
        raise ValueError(
            "Lifecycle events require dedicated session operations."
        )


    session = find_session(connection, session_id)

    if session is None:
        raise ValueError(
            "Learning session does not exist."
        )

    sequence_number = next_event_sequence(
        connection,
        session_id
    )

    record = build_event_record(
        session_id=session_id,
        sequence_number=sequence_number,
        event_type=event_type,
        source=source,
        payload=payload,
        question_id=question_id,
        attempt_id=attempt_id,
        occurred_at=occurred_at,
        event_id=event_id
    )

    existing = connection.execute(
        """
        SELECT *
        FROM performance_events
        WHERE event_id = ?
        """,
        (record["event_id"],)
    ).fetchone()

    if existing is not None:

        comparison_fields = (
            "session_id",
            "question_id",
            "attempt_id",
            "event_type",
            "source",
            "payload",
            "schema_version"
        )

        if any(
            existing[field] != record[field]
            for field in comparison_fields
        ):
            raise ValueError(
                "Event identifier conflicts with existing data."
            )

        if (
            occurred_at is not None
            and existing["occurred_at"] != record["occurred_at"]
        ):
            raise ValueError(
                "Event identifier conflicts with existing timestamp."
            )

        return decode_event(existing)

    if (
        session["status"] != SessionStatus.ACTIVE.value
        and event_type !=
        EventType.TEACHER_OBSERVATION_RECORDED.value
    ):
        raise ValueError(
            "Learning session is no longer active."
        )

    validate_event_associations(
        connection,
        record
    )

    insert_event(connection, record)

    return decode_event(record)


def append_performance_event(
    session_id,
    event_type,
    source,
    payload,
    question_id=None,
    attempt_id=None,
    occurred_at=None,
    event_id=None
):
    """Append an event using an independent transaction."""

    with database_transaction(write=True) as connection:

        return append_performance_event_in_transaction(
            connection=connection,
            session_id=session_id,
            event_type=event_type,
            source=source,
            payload=payload,
            question_id=question_id,
            attempt_id=attempt_id,
            occurred_at=occurred_at,
            event_id=event_id
        )



def end_learning_session_in_transaction(
    connection,
    session_id,
    status=SessionStatus.TERMINATED,
    termination_reason=None
):
    """
    End a learning session and append its lifecycle event.

    Repeated termination requests preserve the original
    termination record.
    """

    if not connection.in_transaction:
        raise RuntimeError(
            "An active database transaction is required."
        )


    session_id = validate_identifier(
        session_id,
        "session_id"
    )

    status = validate_enum(
        status,
        SessionStatus,
        "status"
    )

    if status == SessionStatus.ACTIVE.value:

        raise ValueError(
            "Ending a session requires a terminal status."
        )

    if termination_reason is not None:

        termination_reason = validate_identifier(
            termination_reason,
            "termination_reason"
        )


    session = find_session(connection, session_id)

    if session is None:
        raise ValueError(
            "Learning session does not exist."
        )

    if session["status"] != SessionStatus.ACTIVE.value:

        return decode_session(session)

    ended_at = utc_now()

    connection.execute(
        """
        UPDATE learning_sessions
        SET ended_at = ?,
            status = ?,
            termination_reason = ?
        WHERE session_id = ?
        """,
        (
            ended_at,
            status,
            termination_reason,
            session_id
        )
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
            "status": status,
            "termination_reason": termination_reason
        }
    )

    insert_event(connection, event)

    return decode_session(
        find_session(connection, session_id)
    )


def end_learning_session(
    session_id,
    status=SessionStatus.TERMINATED,
    termination_reason=None
):
    """Execute using an independent write transaction."""

    with database_transaction(write=True) as connection:

        return end_learning_session_in_transaction(
            connection=connection,
            session_id=session_id,
            status=status,
            termination_reason=termination_reason
        )


def list_student_sessions(
    student_id,
    achievement_code=None,
    limit=100,
    offset=0
):
    """Retrieve historical sessions for a student."""

    student_id = validate_identifier(
        student_id,
        "student_id"
    )

    limit = validate_positive_integer(
        limit,
        "limit"
    )

    if limit > 1000:
        raise ValueError(
            "Maximum session retrieval limit is 1000."
        )

    if (
        isinstance(offset, bool)
        or not isinstance(offset, int)
        or offset < 0
    ):
        raise ValueError(
            "Offset must be a non-negative integer."
        )

    query = """
        SELECT *
        FROM learning_sessions
        WHERE student_id = ?
    """

    parameters = [student_id]

    if achievement_code is not None:

        achievement_code = validate_identifier(
            achievement_code,
            "achievement_code"
        )

        query += " AND achievement_code = ?"
        parameters.append(achievement_code)

    query += """
        ORDER BY started_at DESC, session_id DESC
        LIMIT ? OFFSET ?
    """

    parameters.extend([limit, offset])

    with database_transaction() as connection:

        rows = connection.execute(
            query,
            parameters
        ).fetchall()

        return [
            decode_session(row)
            for row in rows
        ]


def list_session_events(session_id):

    """Retrieve the complete recorded event sequence."""

    session_id = validate_identifier(
        session_id,
        "session_id"
    )

    with database_transaction() as connection:

        if find_session(connection, session_id) is None:
            raise ValueError(
                "Learning session does not exist."
            )

        rows = connection.execute(
            """
            SELECT *
            FROM performance_events
            WHERE session_id = ?
            ORDER BY sequence_number
            """,
            (session_id,)
        ).fetchall()

        return [
            decode_event(row)
            for row in rows
        ]
