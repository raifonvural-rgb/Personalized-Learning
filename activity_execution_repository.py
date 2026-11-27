"""
Persistent operational state for activity execution.

Write operations participate in caller-managed
database transactions.
"""

from activity_execution_models import (
    build_execution_state,
    validate_execution_transition,
)

from performance_database import database_transaction

from performance_models import (
    validate_identifier,
    validate_nonnegative_integer,
    decode_json_object,
    utc_now,
)

from performance_storage import find_session

import json


def require_transaction(connection):

    if not connection.in_transaction:

        raise RuntimeError(
            "An active database transaction is required"
        )


def decode_execution_state(row):

    if row is None:
        return None

    return dict(row)


def decode_execution_round(row):

    if row is None:
        return None

    record = dict(row)

    record["presentation_snapshot"] = (
        decode_json_object(
            record["presentation_snapshot"],
            "presentation_snapshot"
        )
    )

    record["selected_alternatives"] = json.loads(
        record["selected_alternatives"]
    )

    record["first_attempt_required"] = bool(
        record["first_attempt_required"]
    )

    return record


def find_execution_state(connection, session_id):

    return connection.execute("""
        SELECT *
        FROM activity_execution_states
        WHERE session_id = ?
    """, (session_id,)).fetchone()


def find_execution_round(
    connection,
    session_id,
    round_number
):

    return connection.execute("""
        SELECT *
        FROM activity_execution_rounds
        WHERE session_id = ?
          AND round_number = ?
    """, (
        session_id,
        round_number,
    )).fetchone()


def find_current_round(connection, session_id):

    state = find_execution_state(
        connection,
        session_id
    )

    if state is None:
        return None

    if state["current_round_number"] == 0:
        return None

    record = find_execution_round(
        connection,
        session_id,
        state["current_round_number"]
    )

    if record is None:

        raise RuntimeError(
            "Current execution round is missing"
        )

    return record


def initialize_execution_state(
    connection,
    session_id
):

    require_transaction(connection)

    session_id = validate_identifier(
        session_id,
        "session_id"
    )

    learning_session = find_session(
        connection,
        session_id
    )

    if learning_session is None:

        raise ValueError(
            "Learning session does not exist"
        )

    if learning_session["status"] != "ACTIVE":

        raise ValueError(
            "Learning session is not active"
        )

    if learning_session["assignment_id"] is None:

        raise ValueError(
            "Assignment-bound session is required"
        )

    assignment = connection.execute("""
        SELECT *
        FROM assignments
        WHERE assignment_id = ?
    """, (
        learning_session["assignment_id"],
    )).fetchone()

    if (
        assignment is None
        or assignment["status"] != "IN_PROGRESS"
        or assignment["student_id"] !=
            learning_session["student_id"]
        or assignment["activity_id"] !=
            learning_session["activity_id"]
    ):

        raise ValueError(
            "Invalid execution assignment association"
        )

    existing = find_execution_state(
        connection,
        session_id
    )

    if existing is not None:

        if existing["status"] in (
            "COMPLETED",
            "INTERRUPTED",
        ):

            raise ValueError(
                "Execution state is already terminal"
            )

        return decode_execution_state(existing)

    record = build_execution_state(session_id)

    connection.execute("""
        INSERT INTO activity_execution_states (
            session_id,
            status,
            current_round_number,
            completion_event_id,
            created_at,
            updated_at
        )
        VALUES (
            :session_id,
            :status,
            :current_round_number,
            :completion_event_id,
            :created_at,
            :updated_at
        )
    """, record)

    return decode_execution_state(record)


def get_execution_state(session_id):

    session_id = validate_identifier(
        session_id,
        "session_id"
    )

    with database_transaction() as connection:

        state = find_execution_state(
            connection,
            session_id
        )

        if state is None:
            return None

        current_round = find_current_round(
            connection,
            session_id
        )

        return {
            "execution_state":
                decode_execution_state(state),

            "current_round":
                decode_execution_round(current_round),
        }


def transition_execution_state(
    connection,
    session_id,
    target_status,
    current_round_number=None,
    completion_event_id=None
):

    require_transaction(connection)

    session_id = validate_identifier(
        session_id,
        "session_id"
    )

    state = find_execution_state(
        connection,
        session_id
    )

    if state is None:

        raise ValueError(
            "Execution state does not exist"
        )

    target_status = validate_execution_transition(
        state["status"],
        target_status
    )

    # Successful completion requires dedicated
    # educational verification operations.

    if target_status in (
        "SUCCESS_CONFIRMED",
        "COMPLETED",
    ):

        raise ValueError(
            "Dedicated completion operation required"
        )

    if completion_event_id is not None:

        raise ValueError(
            "Completion evidence requires a "
            "dedicated completion operation"
        )

    if current_round_number is None:

        current_round_number = (
            state["current_round_number"]
        )

    current_round_number = (
        validate_nonnegative_integer(
            current_round_number,
            "current_round_number"
        )
    )

    previous_round_number = (
        state["current_round_number"]
    )

    if current_round_number < previous_round_number:

        raise ValueError(
            "Execution round cannot move backwards"
        )

    if current_round_number > previous_round_number + 1:

        raise ValueError(
            "Execution rounds cannot be skipped"
        )

    if (
        current_round_number != previous_round_number
        and target_status != "AWAITING_RESPONSE"
    ):

        raise ValueError(
            "Invalid execution round advancement"
        )

    if current_round_number > 0:

        round_record = find_execution_round(
            connection,
            session_id,
            current_round_number
        )

        if round_record is None:

            raise ValueError(
                "Execution round does not exist"
            )

        expected_round_status = {
            "AWAITING_RESPONSE": "ACTIVE",
            "REPEAT_REQUIRED": "REPEAT_REQUIRED",
        }.get(target_status)

        if (
            expected_round_status is not None
            and round_record["status"] !=
                expected_round_status
        ):

            raise ValueError(
                "Execution and round status mismatch"
            )

        if (
            target_status == "INTERRUPTED"
            and round_record["status"] == "ACTIVE"
        ):

            raise ValueError(
                "Active round must be interrupted first"
            )

    result = connection.execute("""
        UPDATE activity_execution_states

        SET status = ?,
            current_round_number = ?,
            updated_at = ?

        WHERE session_id = ?
          AND status = ?
          AND current_round_number = ?
    """, (
        target_status,
        current_round_number,
        utc_now(),
        session_id,
        state["status"],
        previous_round_number,
    ))

    if result.rowcount != 1:

        raise RuntimeError(
            "Execution state transition failed"
        )

    return decode_execution_state(
        find_execution_state(
            connection,
            session_id
        )
    )
