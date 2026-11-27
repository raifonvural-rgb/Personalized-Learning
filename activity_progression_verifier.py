"""
Reconstruct and verify educational progression
across all question rounds in a learning session.
"""

from activity_execution_repository import (
    require_transaction,
    decode_execution_round,
)

from activity_history_verifier import (
    verify_presentation_history,
    require_consistency,
)

from activity_response_evaluator import (
    evaluate_response,
)

from performance_storage import decode_event


def verify_round_progression(
    connection,
    question_round
):

    require_transaction(connection)

    session_id = question_round["session_id"]

    question_id = question_round["question_id"]

    round_number = question_round["round_number"]

    presentation = question_round[
        "presentation_snapshot"
    ]

    rows = connection.execute("""
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
        decode_event(row)
        for row in rows
    ]

    presentations = [
        event for event in events
        if event["event_type"] == "QUESTION_PRESENTED"
    ]

    responses = [
        event for event in events
        if event["event_type"] == "RESPONSE_SUBMITTED"
    ]

    completions = [
        event for event in events
        if event["event_type"] == "QUESTION_COMPLETED"
    ]

    require_consistency(
        len(presentations) == 1
        and len(completions) == 1
        and len(responses) > 0,
        "Incomplete historical round evidence"
    )

    presented = presentations[0]

    completed = completions[0]

    require_consistency(
        presented["event_id"] ==
            question_round["presentation_event_id"]
        and completed["event_id"] ==
            question_round["completion_event_id"],
        "Historical evidence association mismatch"
    )

    require_consistency(
        presented["source"] == "SYSTEM"
        and completed["source"] == "SYSTEM",
        "Invalid historical evidence source"
    )

    expected_presentation_payload = {
        "sequence_number": round_number,

        "activity_type":
            presentation["activity_type"],

        "achievement_code":
            presentation["achievement_code"],

        "instruction":
            presentation["instruction"],

        "target_answer":
            presentation["target_answer"],

        "presented_choices":
            presentation["presented_choices"],

        "presentation_context": {
            **presentation["presentation_context"],

            "question":
                presentation["question"],

            "round_number":
                round_number,

            "first_attempt_required":
                question_round["first_attempt_required"],

            "correct_index":
                presentation["correct_index"],
        },
    }

    require_consistency(
        presented["payload"] ==
            expected_presentation_payload,
        "Historical presentation payload mismatch"
    )

    attempt_count = 0

    selected_alternatives = []

    final_decision = None

    attempt_ids = set()

    for event in responses:

        require_consistency(
            event["source"] == "SYSTEM",
            "Invalid historical response source"
        )

        require_consistency(
            presented["sequence_number"]
            < event["sequence_number"]
            < completed["sequence_number"],
            "Invalid historical response ordering"
        )

        attempt_id = event["attempt_id"]

        require_consistency(
            isinstance(attempt_id, str)
            and bool(attempt_id)
            and attempt_id not in attempt_ids,
            "Invalid or duplicate attempt identity"
        )

        attempt_ids.add(attempt_id)

        if final_decision is not None:

            require_consistency(
                final_decision["evaluation"] !=
                    "CORRECT",
                "Response recorded after correct answer"
            )

        payload = event["payload"]

        decision = evaluate_response(
            presentation=presentation,

            round_number=round_number,

            previous_attempt_count=attempt_count,

            previously_selected_alternatives=
                selected_alternatives,

            selected_position=payload[
                "selected_position"
            ],
        )

        require_consistency(
            payload["attempt_number"] ==
                decision["attempt_number"],
            "Historical attempt number mismatch"
        )

        require_consistency(
            payload["evaluation"] ==
                decision["evaluation"],
            "Historical response evaluation mismatch"
        )

        require_consistency(
            payload["response"] ==
                presentation["presented_choices"][
                    decision["selected_position"]
                ],
            "Historical response content mismatch"
        )

        require_consistency(
            payload.get("progression_decision") ==
                decision,
            "Historical progression decision mismatch"
        )

        attempt_count = decision["attempt_number"]

        selected_alternatives = decision[
            "selected_alternatives"
        ]

        final_decision = decision

    require_consistency(
        attempt_count ==
            question_round["attempt_count"]
        and selected_alternatives ==
            question_round["selected_alternatives"],
        "Historical round progress mismatch"
    )

    require_consistency(
        final_decision["evaluation"] == "CORRECT",
        "Historical round has no correct response"
    )

    require_consistency(
        final_decision["round_status"] ==
            question_round["status"],
        "Historical round outcome mismatch"
    )

    completion_payload = completed["payload"]

    require_consistency(
        completion_payload["outcome"] == "CORRECT"
        and completion_payload.get("round_number") ==
            round_number
        and completion_payload.get("response_event_id") ==
            responses[-1]["event_id"]
        and completion_payload.get("decision_reason") ==
            final_decision["decision_reason"]
        and completion_payload.get(
            "completion_authorized"
        ) is final_decision["completion_authorized"],
        "Historical completion payload mismatch"
    )

    return {
        "question_id": question_id,
        "round_number": round_number,
        "attempt_count": attempt_count,

        "presentation_sequence":
            presented["sequence_number"],

        "completion_sequence":
            completed["sequence_number"],

        "completion_event_id":
            completed["event_id"],

        "decision_reason":
            final_decision["decision_reason"],

        "next_action":
            final_decision["next_action"],

        "completion_authorized":
            final_decision["completion_authorized"],
    }


def verify_execution_history(
    connection,
    session_id
):

    require_transaction(connection)

    presentation_evidence = (
        verify_presentation_history(
            connection,
            session_id
        )
    )

    session_id = presentation_evidence["session_id"]

    rows = connection.execute("""
        SELECT *
        FROM activity_execution_rounds
        WHERE session_id = ?
        ORDER BY round_number
    """, (session_id,)).fetchall()

    round_evidence = []

    previous_completion_sequence = 0

    total_attempts = 0

    for index, row in enumerate(rows):

        question_round = decode_execution_round(row)

        evidence = verify_round_progression(
            connection,
            question_round
        )

        require_consistency(
            evidence["presentation_sequence"] >
                previous_completion_sequence,
            "Historical question rounds overlap"
        )

        is_final_round = index == len(rows) - 1

        if is_final_round:

            require_consistency(
                evidence["completion_authorized"]
                    is True
                and evidence["next_action"] ==
                    "AUTHORIZE_COMPLETION",
                "Final round does not authorize completion"
            )

        else:

            require_consistency(
                evidence["completion_authorized"]
                    is False
                and evidence["next_action"] == "REPEAT",
                "Historical repetition was not justified"
            )

        previous_completion_sequence = evidence[
            "completion_sequence"
        ]

        total_attempts += evidence["attempt_count"]

        round_evidence.append(evidence)

    # Reject question events that have no corresponding
    # persistent execution round.

    unmatched = connection.execute("""
        SELECT COUNT(*) AS event_count
        FROM performance_events AS e

        LEFT JOIN activity_execution_rounds AS r
          ON r.question_id = e.question_id
         AND r.session_id = e.session_id

        WHERE e.session_id = ?
          AND e.question_id IS NOT NULL
          AND r.question_id IS NULL
    """, (session_id,)).fetchone()

    require_consistency(
        unmatched["event_count"] == 0,
        "Unassociated historical question events"
    )

    return {
        "verified": True,
        "session_id": session_id,

        "round_count":
            presentation_evidence["round_count"],

        "repetition_count":
            presentation_evidence["repetition_count"],

        "total_attempts": total_attempts,

        "final_question_id":
            round_evidence[-1]["question_id"],

        "completion_event_id":
            round_evidence[-1]["completion_event_id"],

        "round_evidence": round_evidence,
    }
