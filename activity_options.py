"""
Digit-choice generation for MAT1.1.1.

This module generates candidate answers only.
It does not approve or assign activities to students.
"""

import random


def generate_digit_options(
    target_digit,
    option_count=4,
    seed=None,
):
    if type(target_digit) is not int or not 0 <= target_digit <= 9:
        raise ValueError("Target digit must be an integer between 0 and 9")

    if type(option_count) is not int or not 2 <= option_count <= 10:
        raise ValueError("Option count must be between 2 and 10")

    if seed is not None and type(seed) is not int:
        raise ValueError("Seed must be an integer or None")

    rng = random.Random(seed)

    distractor_pool = [
        digit for digit in range(10)
        if digit != target_digit
    ]

    distractors = rng.sample(
        distractor_pool,
        option_count - 1,
    )

    options = [target_digit] + distractors
    rng.shuffle(options)

    return {
        "target_digit": target_digit,
        "options": options,
        "correct_index": options.index(target_digit),
    }


def validate_digit_options(target_digit, options):
    """
    Validate teacher-edited digit choices.

    Returns a normalized result with the correct answer index.
    """
    if type(target_digit) is not int or not 0 <= target_digit <= 9:
        raise ValueError("Target digit must be an integer between 0 and 9")

    if not isinstance(options, list):
        raise ValueError("Options must be a list")

    if not 2 <= len(options) <= 10:
        raise ValueError("Option count must be between 2 and 10")

    if any(type(digit) is not int or not 0 <= digit <= 9 for digit in options):
        raise ValueError("Options must contain digits between 0 and 9")

    if len(set(options)) != len(options):
        raise ValueError("Duplicate digits are not allowed")

    if options.count(target_digit) != 1:
        raise ValueError("Target digit must appear exactly once")

    return {
        "target_digit": target_digit,
        "options": list(options),
        "correct_index": options.index(target_digit),
    }
