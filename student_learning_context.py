from flask import session

from performance_models import validate_identifier

from performance_lifecycle import PERFORMANCE_SESSION_KEY


STUDENT_SESSION_KEY = "learning_student_id"

ASSIGNMENT_SESSION_KEY = "learning_assignment_id"


def get_learning_context():

    return {
        "student_id": session.get(
            STUDENT_SESSION_KEY
        ),
        "assignment_id": session.get(
            ASSIGNMENT_SESSION_KEY
        ),
        "performance_session_id": session.get(
            PERFORMANCE_SESSION_KEY
        ),
    }


def has_learning_context():

    context = get_learning_context()

    return any(
        value is not None
        for value in context.values()
    )


def has_complete_learning_context():

    context = get_learning_context()

    return all(
        isinstance(value, str) and bool(value.strip())
        for value in context.values()
    )


def bind_learning_context(
    student_id,
    assignment_id,
    performance_session_id
):

    student_id = validate_identifier(
        student_id,
        "student_id"
    )

    assignment_id = validate_identifier(
        assignment_id,
        "assignment_id"
    )

    performance_session_id = validate_identifier(
        performance_session_id,
        "performance_session_id"
    )

    session[STUDENT_SESSION_KEY] = student_id

    session[ASSIGNMENT_SESSION_KEY] = assignment_id

    session[PERFORMANCE_SESSION_KEY] = (
        performance_session_id
    )

    return get_learning_context()


def clear_assignment_context():

    session.pop(
        ASSIGNMENT_SESSION_KEY,
        None
    )

    session.pop(
        PERFORMANCE_SESSION_KEY,
        None
    )


def clear_learning_context():

    clear_assignment_context()

    session.pop(
        STUDENT_SESSION_KEY,
        None
    )
