"""
Deterministic educational response evaluation.

Independent of database persistence, browser behavior,
animation and audio presentation.
"""

from activity_execution_models import (
    ExecutionStatus,
    RoundStatus,
    FeedbackType,
    validate_round_progress,
    requires_first_attempt_success,
)

from performance_models import (
    ResponseEvaluation,
    validate_positive_integer,
    validate_nonnegative_integer,
)


def evaluate_response(
    presentation,
    round_number,
    previous_attempt_count,
    previously_selected_alternatives,
    selected_position
):
    """
    Evaluate a multiple-choice response and determine
    the next educational execution state.

    This function does not modify its input arguments
    or perform database operations.
    """

    if not isinstance(presentation, dict):

        raise ValueError(
            "Invalid question presentation"
        )

    round_number = validate_positive_integer(
        round_number,
        "round_number"
    )

    choices = presentation.get(
        "presented_choices"
    )

    if not isinstance(choices, list) or len(choices) < 2:

        raise ValueError(
            "At least two alternatives are required"
        )

    alternative_count = len(choices)

    correct_index = validate_nonnegative_integer(
        presentation.get("correct_index"),
        "correct_index"
    )

    if correct_index >= alternative_count:

        raise ValueError(
            "Correct alternative is out of range"
        )

    selected_position = validate_nonnegative_integer(
        selected_position,
        "selected_position"
    )

    if selected_position >= alternative_count:

        raise ValueError(
            "Selected alternative is out of range"
        )

    previous_progress = validate_round_progress(
        attempt_count=previous_attempt_count,
        selected_alternatives=previously_selected_alternatives,
        alternative_count=alternative_count,
    )

    selected_alternatives = list(
        previous_progress["selected_alternatives"]
    )

    if correct_index in selected_alternatives:

        raise ValueError(
            "Round already contains a correct response"
        )

    attempt_number = (
        previous_progress["attempt_count"] + 1
    )

    repeated_selection = (
        selected_position in selected_alternatives
    )

    if not repeated_selection:

        selected_alternatives.append(
            selected_position
        )

    distinct_selection_count = len(
        selected_alternatives
    )

    exhausted_alternatives = (
        distinct_selection_count == alternative_count
    )

    first_attempt_required = (
        requires_first_attempt_success(
            round_number
        )
    )

    is_correct = (
        selected_position == correct_index
    )

    first_attempt_correct = (
        is_correct and attempt_number == 1
    )

    completion_authorized = False

    if not is_correct:

        evaluation = ResponseEvaluation.INCORRECT

        feedback = FeedbackType.ENCOURAGEMENT

        execution_status = (
            ExecutionStatus.AWAITING_RESPONSE
        )

        round_status = RoundStatus.ACTIVE

        next_action = "CONTINUE"

        decision_reason = "INCORRECT_RESPONSE"

    elif (
        first_attempt_required
        and not first_attempt_correct
    ):

        evaluation = ResponseEvaluation.CORRECT

        feedback = FeedbackType.DISCOVERY

        execution_status = (
            ExecutionStatus.REPEAT_REQUIRED
        )

        round_status = RoundStatus.REPEAT_REQUIRED

        next_action = "REPEAT"

        decision_reason = (
            "REPETITION_FIRST_ATTEMPT_NOT_SATISFIED"
        )

    elif exhausted_alternatives:

        evaluation = ResponseEvaluation.CORRECT

        feedback = FeedbackType.DISCOVERY

        execution_status = (
            ExecutionStatus.REPEAT_REQUIRED
        )

        round_status = RoundStatus.REPEAT_REQUIRED

        next_action = "REPEAT"

        decision_reason = (
            "ALL_ALTERNATIVES_EXHAUSTED"
        )

    else:

        evaluation = ResponseEvaluation.CORRECT

        feedback = FeedbackType.SUCCESS

        execution_status = (
            ExecutionStatus.SUCCESS_CONFIRMED
        )

        round_status = RoundStatus.SUCCESS_CONFIRMED

        next_action = "AUTHORIZE_COMPLETION"

        completion_authorized = True

        if first_attempt_correct:

            decision_reason = "FIRST_ATTEMPT_CORRECT"

        else:

            decision_reason = (
                "CORRECT_BEFORE_EXHAUSTING_ALTERNATIVES"
            )

    return {
        "round_number": round_number,

        "attempt_number": attempt_number,

        "selected_position": selected_position,

        "selected_alternatives": selected_alternatives,

        "distinct_selection_count":
            distinct_selection_count,

        "alternative_count": alternative_count,

        "repeated_selection": repeated_selection,

        "exhausted_alternatives":
            exhausted_alternatives,

        "first_attempt_required":
            first_attempt_required,

        "first_attempt_correct":
            first_attempt_correct,

        "evaluation": evaluation.value,

        "feedback_type": feedback.value,

        "execution_status": execution_status.value,

        "round_status": round_status.value,

        "next_action": next_action,

        "decision_reason": decision_reason,

        "completion_authorized":
            completion_authorized,
    }
