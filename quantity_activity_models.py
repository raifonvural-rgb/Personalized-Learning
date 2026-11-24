"""Configuration models for quantity representation activities."""

from dataclasses import dataclass, field
from visual_asset_validation import validate_visual_asset


QUANTITY_ACTIVITY_TYPES = frozenset({
    "number_to_quantity",
    "quantity_to_number",
})

QUANTITY_ARRANGEMENTS = frozenset({
    "grid",
    "horizontal",
    "vertical",
})


@dataclass
class QuantityActivityConfig:
    activity_type: str
    target_quantity: int
    visual_id: str

    min_quantity: int = 0
    max_quantity: int = 9

    options: list[int] = field(default_factory=list)
    arrangement: str = "grid"

    audio_enabled: bool = True
    spoken_counting_enabled: bool = False
    quantity_animation_enabled: bool = False
    celebration_enabled: bool = True


def validate_quantity_config(
    config: QuantityActivityConfig,
) -> None:
    """Raise ValueError if the configuration is invalid."""

    if not isinstance(config, QuantityActivityConfig):
        raise ValueError("Invalid quantity activity configuration")

    if config.activity_type not in QUANTITY_ACTIVITY_TYPES:
        raise ValueError("Unsupported quantity activity type")

    for name in (
        "target_quantity",
        "min_quantity",
        "max_quantity",
    ):
        if type(getattr(config, name)) is not int:
            raise ValueError(f"{name} must be an integer")

    if not 0 <= config.min_quantity < config.max_quantity <= 9:
        raise ValueError("Invalid quantity range")

    if not (
        config.min_quantity
        <= config.target_quantity
        <= config.max_quantity
    ):
        raise ValueError("Target quantity is outside the range")

    if (
        not isinstance(config.visual_id, str)
        or not config.visual_id.strip()
    ):
        raise ValueError("A visual asset must be selected")

    validate_visual_asset(config.visual_id)

    if config.arrangement not in QUANTITY_ARRANGEMENTS:
        raise ValueError("Unsupported object arrangement")

    if not isinstance(config.options, list):
        raise ValueError("Options must be a list")

    if not 2 <= len(config.options) <= 10:
        raise ValueError("Between 2 and 10 options are required")

    for option in config.options:
        if type(option) is not int:
            raise ValueError("Options must be integers")

        if not config.min_quantity <= option <= config.max_quantity:
            raise ValueError("Option is outside the quantity range")

    if len(set(config.options)) != len(config.options):
        raise ValueError("Options must be unique")

    if config.options.count(config.target_quantity) != 1:
        raise ValueError(
            "Target quantity must appear exactly once"
        )

    for name in (
        "audio_enabled",
        "spoken_counting_enabled",
        "quantity_animation_enabled",
        "celebration_enabled",
    ):
        if type(getattr(config, name)) is not bool:
            raise ValueError(f"{name} must be a boolean")
