"""Deterministic builder for quantity representation activities."""

from dataclasses import asdict

from quantity_activity_models import (
    QuantityActivityConfig,
    validate_quantity_config,
)


def build_object_group(quantity: int, visual_id: str) -> dict:
    """Represent a quantity using repeated instances of one asset."""

    if type(quantity) is not int or not 0 <= quantity <= 9:
        raise ValueError("Invalid object quantity")

    if not isinstance(visual_id, str) or not visual_id.strip():
        raise ValueError("Invalid visual asset")

    return {
        "quantity": quantity,
        "objects": [
            {
                "instance_id": index + 1,
                "visual_id": visual_id,
            }
            for index in range(quantity)
        ],
    }


def build_quantity_activity_draft(
    config: QuantityActivityConfig,
) -> dict:
    """Build a deterministic, unapproved quantity activity draft."""

    validate_quantity_config(config)

    draft = asdict(config)

    draft["correct_index"] = config.options.index(
        config.target_quantity
    )

    if config.activity_type == "number_to_quantity":
        draft["question"] = {
            "type": "numeral",
            "value": config.target_quantity,
        }

        draft["answer_choices"] = [
            {
                "type": "object_group",
                **build_object_group(quantity, config.visual_id),
            }
            for quantity in config.options
        ]

    elif config.activity_type == "quantity_to_number":
        draft["question"] = {
            "type": "object_group",
            **build_object_group(
                config.target_quantity,
                config.visual_id,
            ),
        }

        draft["answer_choices"] = [
            {
                "type": "numeral",
                "value": quantity,
            }
            for quantity in config.options
        ]

    draft["status"] = "draft"
    draft["teacher_approved"] = False

    return draft
