"""Deterministic integrity verification for quantity activity drafts."""

import json
from dataclasses import fields

from quantity_activity_models import QuantityActivityConfig
from quantity_activity_builder import build_quantity_activity_draft


def canonical_json(value) -> str:
    """Preserve JSON data types during comparison."""

    return json.dumps(
        value,
        sort_keys=True,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
    )


def validate_quantity_draft_integrity(draft: dict) -> None:
    """Reject drafts inconsistent with their configuration."""

    if not isinstance(draft, dict):
        raise ValueError("Activity draft must be a dictionary")

    config_fields = {
        field.name for field in fields(QuantityActivityConfig)
    }

    missing = config_fields - draft.keys()

    if missing:
        raise ValueError(
            f"Missing configuration fields: {sorted(missing)}"
        )

    try:
        config = QuantityActivityConfig(
            **{
                name: draft[name]
                for name in config_fields
            }
        )

        expected = build_quantity_activity_draft(config)

        if canonical_json(draft) != canonical_json(expected):
            raise ValueError(
                "Activity draft does not match its configuration"
            )

    except TypeError as exc:
        raise ValueError("Invalid activity draft data") from exc
