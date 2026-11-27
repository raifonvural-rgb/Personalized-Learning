"""
Server-controlled repetition round generation.

Repetition preserves the educational target and
approved alternatives while changing their order.
"""

from copy import deepcopy
from random import SystemRandom

from activity_execution_repository import (
    require_transaction,
    find_execution_state,
    find_current_round,
    decode_execution_round,
)

from activity_round_service import (
    persist_question_round,
)

from performance_database import (
    database_transaction,
)

from performance_models import (
    validate_identifier,
    validate_nonnegative_integer,
)

from performance_storage import find_session


def build_repetition_presentation(
    previous_presentation
):
    """
    Reorder the same alternatives while ensuring
    that the correct answer changes position.
    """

    if not isinstance(previous_presentation, dict):

        raise ValueError(
            "Invalid previous presentation"
        )

    presentation = deepcopy(
        previous_presentation
    )

    choices = presentation["presented_choices"]

    if not isinstance(choices, list) or len(choices) < 2:

        raise ValueError(
            "At least two alternatives are required"
        )

    previous_correct_index = (
        validate_nonnegative_integer(
            presentation["correct_index"],
            "correct_index"
        )
    )

    if previous_correct_index >= len(choices):

        raise ValueError(
            "Invalid correct alternative position"
        )

    randomizer = SystemRandom()

    available_positions = [
        position

        for position in range(len(choices))

        if position != previous_correct_index
    ]

    new_correct_index = randomizer.choice(
        available_positions
    )

    incorrect_choices = [
        choice

        for position, choice in enumerate(choices)

        if position != previous_correct_index
    ]

    randomizer.shuffle(
        incorrect_choices
    )

    correct_choice = choices[
        previous_correct_index
    ]

    incorrect_choices.insert(
        new_correct_index,
        correct_choice
    )

    presentation["presented_choices"] = (
        incorrect_choices
    )

    presentation["correct_index"] = (
        new_correct_index
    )

    return presentation


def start_repetition_in_transaction(
    connection,
    session_id,
    previous_question_id
):
    """
    Start a repetition round authorized by the
    server-controlled educational execution state.
    """

    require_transaction(connection)

    session_id = validate_identifier(
        session_id,
        "session_id"
    )

    previous_question_id = validate_identifier(
        previous_question_id,
        "previous_question_id"
    )

    learning_session = find_session(
        connection,
        session_id
    )

    if (
        learning_session is None
        or learning_session["status"] != "ACTIVE"
    ):

        raise ValueError(
            "Active learning session required"
        )

    state = find_execution_state(
        connection,
        session_id
    )

    if state is None:

        raise ValueError(
            "Execution state does not exist"
        )

    current_round = decode_execution_round(
        find_current_round(
            connection,
            session_id
        )
    )

    if current_round is None:

        raise ValueError(
            "Previous question round does not exist"
        )

    # A repeated request must not create
    # an additional repetition round.

    if (
        state["status"] == "AWAITING_RESPONSE"
        and current_round["round_number"] > 1
        and current_round["status"] == "ACTIVE"
    ):

        previous_round = connection.execute("""
            SELECT question_id, status
            FROM activity_execution_rounds
            WHERE session_id = ?
              AND round_number = ?
        """, (
            session_id,
            current_round["round_number"] - 1,
        )).fetchone()

        if (
            previous_round is not None
            and previous_round["question_id"] ==
                previous_question_id
            and previous_round["status"] ==
                "REPEAT_REQUIRED"
        ):

            return {
                "round": current_round,
                "duplicate_request": True,
            }

    if state["status"] != "REPEAT_REQUIRED":

        raise ValueError(
            "Repetition has not been authorized"
        )

    if (
        current_round["question_id"] !=
            previous_question_id
        or current_round["status"] !=
            "REPEAT_REQUIRED"
    ):

        raise ValueError(
            "Invalid previous question association"
        )

    if current_round["completion_event_id"] is None:

        raise RuntimeError(
            "Repetition evidence is missing"
        )

    presentation = build_repetition_presentation(
        current_round["presentation_snapshot"]
    )

    new_round = persist_question_round(
        connection=connection,
        session_id=session_id,
        presentation=presentation,
    )

    return {
        "round": new_round,
        "duplicate_request": False,
    }


def start_repetition_round(
    session_id,
    previous_question_id
):

    with database_transaction(write=True) as connection:

        return start_repetition_in_transaction(
            connection=connection,
            session_id=session_id,
            previous_question_id=previous_question_id,
        )
