"""
SQLite repository for teacher-controlled assignments.

Assignment persistence is independent of presentation
and educational execution logic.
"""

from assignment_models import (
    AssignmentStatus,
    build_assignment_record,
    decode_assignment,
    validate_assignment_status,
)

from performance_database import database_transaction
from performance_models import validate_identifier

from profile_storage import get_profile
from activity_storage import get_activity


def validate_activity_eligibility(student_id, activity_id):

    if get_profile(student_id) is None:
        raise ValueError("Student does not exist")

    activity = get_activity(activity_id)

    if activity is None:
        raise ValueError("Activity does not exist")

    if activity.get("student_id") != student_id:
        raise ValueError(
            "Activity belongs to another student"
        )

    if activity.get("status") != "approved":
        raise ValueError(
            "Only approved activities can be assigned"
        )

    return activity


def find_assignment(connection, assignment_id):

    return connection.execute("""
        SELECT *
        FROM assignments
        WHERE assignment_id = ?
    """, (assignment_id,)).fetchone()


def insert_assignment(connection, record):

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
        VALUES (
            :assignment_id,
            :student_id,
            :activity_id,
            :sequence_order,
            :enabled,
            :status,
            :assigned_at,
            :started_at,
            :completed_at,
            :updated_at
        )
    """, record)


def next_sequence_order(connection, student_id):

    row = connection.execute("""
        SELECT COALESCE(MAX(sequence_order), 0) + 1
            AS next_order
        FROM assignments
        WHERE student_id = ?
    """, (student_id,)).fetchone()

    return row["next_order"]


def create_assignment(
    student_id,
    activity_id,
    enabled=True
):

    student_id = validate_identifier(
        student_id,
        "student_id"
    )

    activity_id = validate_identifier(
        activity_id,
        "activity_id"
    )

    validate_activity_eligibility(
        student_id,
        activity_id
    )

    with database_transaction(write=True) as connection:

        sequence_order = next_sequence_order(
            connection,
            student_id
        )

        record = build_assignment_record(
            student_id=student_id,
            activity_id=activity_id,
            sequence_order=sequence_order,
            enabled=enabled
        )

        insert_assignment(connection, record)

        return decode_assignment(record)


def get_assignment(assignment_id):

    assignment_id = validate_identifier(
        assignment_id,
        "assignment_id"
    )

    with database_transaction() as connection:

        return decode_assignment(
            find_assignment(
                connection,
                assignment_id
            )
        )


def list_student_assignments(
    student_id,
    status=None
):

    student_id = validate_identifier(
        student_id,
        "student_id"
    )

    query = """
        SELECT *
        FROM assignments
        WHERE student_id = ?
    """

    parameters = [student_id]

    if status is not None:

        status = validate_assignment_status(status)

        query += " AND status = ?"
        parameters.append(status)

    query += """
        ORDER BY sequence_order,
                 assigned_at,
                 assignment_id
    """

    with database_transaction() as connection:

        rows = connection.execute(
            query,
            parameters
        ).fetchall()

        return [
            decode_assignment(row)
            for row in rows
        ]


def find_in_progress_assignment(
    connection,
    student_id
):

    return connection.execute("""
        SELECT *
        FROM assignments
        WHERE student_id = ?
          AND status = 'IN_PROGRESS'
    """, (student_id,)).fetchone()


def get_in_progress_assignment(student_id):

    student_id = validate_identifier(
        student_id,
        "student_id"
    )

    with database_transaction() as connection:

        return decode_assignment(
            find_in_progress_assignment(
                connection,
                student_id
            )
        )


def find_next_pending_assignment(
    connection,
    student_id
):

    return connection.execute("""
        SELECT *
        FROM assignments
        WHERE student_id = ?
          AND status = 'PENDING'
          AND enabled = 1

        ORDER BY sequence_order,
                 assigned_at,
                 assignment_id

        LIMIT 1
    """, (student_id,)).fetchone()


def get_next_pending_assignment(student_id):

    student_id = validate_identifier(
        student_id,
        "student_id"
    )

    with database_transaction() as connection:

        return decode_assignment(
            find_next_pending_assignment(
                connection,
                student_id
            )
        )


def require_owned_assignment(
    connection,
    student_id,
    assignment_id
):

    record = find_assignment(
        connection,
        assignment_id
    )

    if record is None:
        raise ValueError("Assignment does not exist")

    if record["student_id"] != student_id:
        raise ValueError(
            "Assignment belongs to another student"
        )

    return record


def set_assignment_enabled(
    student_id,
    assignment_id,
    enabled
):

    from assignment_models import validate_enabled
    from performance_models import utc_now

    student_id = validate_identifier(
        student_id,
        "student_id"
    )

    assignment_id = validate_identifier(
        assignment_id,
        "assignment_id"
    )

    enabled = validate_enabled(enabled)

    with database_transaction(write=True) as connection:

        record = require_owned_assignment(
            connection,
            student_id,
            assignment_id
        )

        if record["status"] != "PENDING":
            raise ValueError(
                "Only pending assignments can be enabled "
                "or disabled directly"
            )

        if enabled:
            validate_activity_eligibility(
                student_id,
                record["activity_id"]
            )

        connection.execute("""
            UPDATE assignments
            SET enabled = ?,
                updated_at = ?
            WHERE assignment_id = ?
        """, (
            enabled,
            utc_now(),
            assignment_id,
        ))

        return decode_assignment(
            find_assignment(
                connection,
                assignment_id
            )
        )


def reorder_pending_assignments(
    student_id,
    ordered_assignment_ids
):

    from performance_models import utc_now

    student_id = validate_identifier(
        student_id,
        "student_id"
    )

    if not isinstance(ordered_assignment_ids, list):
        raise ValueError(
            "Assignment order must be a list"
        )

    ordered_assignment_ids = [
        validate_identifier(
            assignment_id,
            "assignment_id"
        )
        for assignment_id in ordered_assignment_ids
    ]

    if len(ordered_assignment_ids) != len(
        set(ordered_assignment_ids)
    ):
        raise ValueError(
            "Duplicate assignment IDs in sequence"
        )

    with database_transaction(write=True) as connection:

        pending = connection.execute("""
            SELECT assignment_id, sequence_order
            FROM assignments
            WHERE student_id = ?
              AND status = 'PENDING'
            ORDER BY sequence_order
        """, (student_id,)).fetchall()

        existing_ids = {
            record["assignment_id"]
            for record in pending
        }

        if set(ordered_assignment_ids) != existing_ids:
            raise ValueError(
                "Order must contain every pending assignment "
                "exactly once"
            )

        positions = sorted(
            record["sequence_order"]
            for record in pending
        )

        temporary_start = next_sequence_order(
            connection,
            student_id
        )

        timestamp = utc_now()

        # Phase 1: Move pending assignments to unused
        # temporary positions to avoid uniqueness conflicts.

        for index, assignment_id in enumerate(
            ordered_assignment_ids
        ):

            connection.execute("""
                UPDATE assignments
                SET sequence_order = ?
                WHERE assignment_id = ?
            """, (
                temporary_start + index,
                assignment_id,
            ))

        # Phase 2: Apply the requested order using
        # the original available pending positions.

        for assignment_id, position in zip(
            ordered_assignment_ids,
            positions
        ):

            connection.execute("""
                UPDATE assignments
                SET sequence_order = ?,
                    updated_at = ?
                WHERE assignment_id = ?
            """, (
                position,
                timestamp,
                assignment_id,
            ))

        return [
            decode_assignment(
                find_assignment(
                    connection,
                    assignment_id
                )
            )
            for assignment_id in ordered_assignment_ids
        ]


def cancel_pending_assignment(
    student_id,
    assignment_id
):

    from performance_models import utc_now

    student_id = validate_identifier(
        student_id,
        "student_id"
    )

    assignment_id = validate_identifier(
        assignment_id,
        "assignment_id"
    )

    with database_transaction(write=True) as connection:

        record = require_owned_assignment(
            connection,
            student_id,
            assignment_id
        )

        if record["status"] == "CANCELLED":
            return decode_assignment(record)

        if record["status"] != "PENDING":
            raise ValueError(
                "Only pending assignments can be "
                "cancelled directly"
            )

        connection.execute("""
            UPDATE assignments
            SET status = 'CANCELLED',
                enabled = 0,
                updated_at = ?
            WHERE assignment_id = ?
        """, (
            utc_now(),
            assignment_id,
        ))

        return decode_assignment(
            find_assignment(
                connection,
                assignment_id
            )
        )
