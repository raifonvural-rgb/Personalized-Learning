"""
Verify educational completion using recorded
performance evidence and persistent execution state.
"""

from activity_execution_repository import (
    require_transaction,
    find_execution_state,
    find_current_round,
    decode_execution_round,
)

from activity_response_evaluator import (
    evaluate_response,
)

from performance_models import (
    validate_identifier,
)

from performance_storage import (
    find_session,
    decode_event,
)


def require_evidence(condition, message):

    if not condition:
        raise ValueError(message)


def verify_educational_completion(
    connection,
    session_id
):
    """
    Independently reconstruct the final question
    round from its recorded response events.

    This function does not modify database records.
    """

    require_transaction(connection)

    session_id = validate_identifier(
        session_id,
        "session_id"
    )

    learning_session = find_session(
        connection,
        session_id
    )

    require_evidence(
        learning_session is not None
        and learning_session["status"] == "ACTIVE",
        "Active learning session required"
    )

    state = find_execution_state(
        connection,
        session_id
    )

    require_evidence(
        state is not None
        and state["status"] == "SUCCESS_CONFIRMED",
        "Educational success has not been confirmed"
    )

    current_round = decode_execution_round(
        find_current_round(
            connection,
            session_id
        )
    )

    require_evidence(
        current_round is not None
        and current_round["status"] ==
            "SUCCESS_CONFIRMED",
        "Successful question round required"
    )

    question_id = current_round["question_id"]

    completion_event_id = state[
        "completion_event_id"
    ]

    require_evidence(
        completion_event_id is not None
        and completion_event_id ==
            current_round["completion_event_id"],
        "Completion evidence association mismatch"
    )

    presentation = current_round[
        "presentation_snapshot"
    ]

    events = connection.execute("""
        SELECT *
        FROM performance_events
        WHERE session_id = ?
          AND question_id = ?
        ORDER BY sequence_number
    """, (
        session_id,
        question_id,
    )).fetchall()

    events = [
        decode_event(event)
        for event in events
    ]

    presentation_events = [
        event
        for event in events
        if event["event_type"] ==
            "QUESTION_PRESENTED"
    ]

    response_events = [
        event
        for event in events
        if event["event_type"] ==
            "RESPONSE_SUBMITTED"
    ]

    completion_events = [
        event
        for event in events
        if event["event_type"] ==
            "QUESTION_COMPLETED"
    ]

    require_evidence(
        len(presentation_events) == 1,
        "Expected exactly one presentation event"
    )

    require_evidence(
        len(completion_events) == 1,
        "Expected exactly one completion event"
    )

    require_evidence(
        len(response_events) > 0,
        "No response evidence available"
    )

    presentation_event = presentation_events[0]

    completion_event = completion_events[0]

    require_evidence(
        presentation_event["event_id"] ==
            current_round["presentation_event_id"],
        "Presentation evidence mismatch"
    )

    require_evidence(
        completion_event["event_id"] ==
            completion_event_id,
        "Completion event mismatch"
    )

    require_evidence(
        presentation_event["source"] == "SYSTEM"
        and completion_event["source"] == "SYSTEM",
        "Invalid evidence source"
    )

    presentation_payload = presentation_event[
        "payload"
    ]

    require_evidence(
        presentation_payload["presented_choices"] ==
            presentation["presented_choices"]
        and presentation_payload["target_answer"] ==
            presentation["target_answer"]
        and presentation_payload["activity_type"] ==
            presentation["activity_type"]
        and presentation_payload["instruction"] ==
            presentation["instruction"]
        and presentation_payload["sequence_number"] ==
            current_round["round_number"],
        "Recorded presentation mismatch"
    )

    require_evidence(
        presentation_payload[
            "presentation_context"
        ]["correct_index"] ==
            presentation["correct_index"],
        "Correct answer position mismatch"
    )

    attempt_count = 0

    selected_alternatives = []

    final_decision = None

    for event in response_events:

        require_evidence(
            event["source"] == "SYSTEM",
            "Invalid response evidence source"
        )

        require_evidence(
            presentation_event["sequence_number"]
            < event["sequence_number"]
            < completion_event["sequence_number"],
            "Invalid response event sequence"
        )

        if final_decision is not None:

            require_evidence(
                final_decision["evaluation"] !=
                    "CORRECT",
                "Response recorded after correct answer"
            )

        payload = event["payload"]

        decision = evaluate_response(
            presentation=presentation,

            round_number=current_round[
                "round_number"
            ],

            previous_attempt_count=attempt_count,

            previously_selected_alternatives=
                selected_alternatives,

            selected_position=payload[
                "selected_position"
            ],
        )

        require_evidence(
            payload["attempt_number"] ==
                decision["attempt_number"],
            "Recorded attempt number mismatch"
        )

        require_evidence(
            payload["evaluation"] ==
                decision["evaluation"],
            "Recorded response evaluation mismatch"
        )

        require_evidence(
            payload["response"] ==
                presentation["presented_choices"][
                    decision["selected_position"]
                ],
            "Recorded response content mismatch"
        )

        require_evidence(
            payload.get("progression_decision") ==
                decision,
            "Recorded progression decision mismatch"
        )

        attempt_count = decision["attempt_number"]

        selected_alternatives = decision[
            "selected_alternatives"
        ]

        final_decision = decision

    require_evidence(
        attempt_count ==
            current_round["attempt_count"],
        "Persistent attempt count mismatch"
    )

    require_evidence(
        selected_alternatives ==
            current_round["selected_alternatives"],
        "Persistent selected alternatives mismatch"
    )

    require_evidence(
        final_decision["completion_authorized"]
            is True,
        "Educational completion criteria not satisfied"
    )

    completion_payload = completion_event[
        "payload"
    ]

    require_evidence(
        completion_payload["outcome"] == "CORRECT"
        and completion_payload.get(
            "completion_authorized"
        ) is True,
        "Invalid completion outcome"
    )

    require_evidence(
        completion_payload.get("response_event_id") ==
            response_events[-1]["event_id"],
        "Completion response association mismatch"
    )

    require_evidence(
        completion_payload.get("decision_reason") ==
            final_decision["decision_reason"],
        "Completion decision reason mismatch"
    )

    require_evidence(
        completion_payload.get("round_number") ==
            current_round["round_number"],
        "Completion round number mismatch"
    )

    return {
        "verified": True,
        "session_id": session_id,
        "question_id": question_id,
        "round_number": current_round["round_number"],
        "attempt_count": attempt_count,

        "completion_event_id":
            completion_event_id,

        "final_response_event_id":
            response_events[-1]["event_id"],

        "decision_reason":
            final_decision["decision_reason"],
    }
