"""
Build standardized question presentations from
approved activity configuration snapshots.

This module does not persist data or evaluate
student performance.
"""

from copy import deepcopy

from activity_integrity import (
    validate_activity_draft_integrity,
)


SUPPORTED_ACTIVITY_TYPES = {
    "find_digit",
    "number_to_quantity",
    "quantity_to_number",
}


def build_question_presentation(configuration):

    if not isinstance(configuration, dict):

        raise ValueError(
            "Activity configuration must be a dictionary"
        )

    validate_activity_draft_integrity(
        configuration
    )

    activity_type = configuration.get(
        "activity_type"
    )

    if activity_type not in SUPPORTED_ACTIVITY_TYPES:

        raise ValueError(
            "Unsupported activity type"
        )

    if activity_type == "find_digit":

        target_answer = configuration["target_digit"]

        question = {
            "type": "digit_recognition",
            "target_digit": target_answer,
        }

        instruction = (
            f"{target_answer} rakamını bul."
        )

        choices = [
            {
                "type": "numeral",
                "value": digit,
            }
            for digit in configuration["options"]
        ]

    elif activity_type == "number_to_quantity":

        target_answer = configuration["target_quantity"]

        question = deepcopy(
            configuration["question"]
        )

        instruction = (
            "Verilen sayıya uygun nesne grubunu seç."
        )

        choices = deepcopy(
            configuration["answer_choices"]
        )

    else:

        target_answer = configuration["target_quantity"]

        question = deepcopy(
            configuration["question"]
        )

        instruction = (
            "Nesneleri say ve doğru sayıyı seç."
        )

        choices = deepcopy(
            configuration["answer_choices"]
        )

    correct_index = configuration["correct_index"]

    if len(choices) < 2:

        raise ValueError(
            "At least two alternatives are required"
        )

    if (
        type(correct_index) is not int
        or not 0 <= correct_index < len(choices)
    ):

        raise ValueError(
            "Invalid correct alternative position"
        )

    achievement_code = configuration.get(
        "achievement_code"
    )

    if not isinstance(achievement_code, str):
        achievement_code = None

    presentation_context = {
        key: deepcopy(value)

        for key, value in configuration.items()

        if key not in {
            "options",
            "answer_choices",
            "correct_index",
            "question",
            "status",
            "teacher_approved",
        }
    }

    return {
        "activity_type": activity_type,
        "achievement_code": achievement_code,
        "question": question,
        "instruction": instruction,
        "target_answer": target_answer,
        "presented_choices": choices,
        "correct_index": correct_index,
        "presentation_context": presentation_context,
    }


def get_student_presentation(presentation):
    """
    Return presentation data without explicit
    answer-evaluation metadata.
    """

    context = deepcopy(
        presentation["presentation_context"]
    )

    context.pop("target_digit", None)
    context.pop("target_quantity", None)

    return {
        "activity_type":
            presentation["activity_type"],

        "question":
            deepcopy(presentation["question"]),

        "instruction":
            presentation["instruction"],

        "presented_choices":
            deepcopy(presentation["presented_choices"]),

        "presentation_context":
            context,
    }
