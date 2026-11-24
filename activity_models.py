"""
Reusable activity definitions for digits 0-9.

This module defines and validates activity configurations.
It does not store student data or approve activities.
"""

from dataclasses import dataclass, field
from typing import Optional


ACHIEVEMENTS = {
    "MAT1.1.1": "Rakamları gösterir",
    "MAT1.1.2": "Gösterilen rakamı söyler",
    "MAT1.1.3": "İstenen rakamı yazar",
}

ACTIVITY_TYPES = {
    "find_digit": "Rakamı bul",
    "say_digit": "Rakamı söyle",
    "trace_digit": "Rakamın üzerinden çiz",
    "write_digit": "Rakamı yaz",
}

ALLOWED_ACTIVITIES = {
    "MAT1.1.1": {"find_digit"},
    "MAT1.1.2": {"say_digit"},
    "MAT1.1.3": {"trace_digit", "write_digit"},
}


@dataclass
class ActivityConfig:
    achievement_code: str
    target_digit: int
    activity_type: str

    visual_id: Optional[str] = None

    audio_enabled: bool = True
    drawing_enabled: bool = False
    celebration_enabled: bool = True
    quantity_animation_enabled: bool = False

    settings: dict = field(default_factory=dict)

    def validate(self):
        if self.achievement_code not in ACHIEVEMENTS:
            raise ValueError("Unknown achievement code")

        if type(self.target_digit) is not int:
            raise ValueError("Target digit must be an integer")

        if not 0 <= self.target_digit <= 9:
            raise ValueError("Target digit must be between 0 and 9")

        allowed = ALLOWED_ACTIVITIES[self.achievement_code]

        if self.activity_type not in allowed:
            raise ValueError(
                "Activity type is not compatible with achievement"
            )

        if type(self.audio_enabled) is not bool:
            raise ValueError("audio_enabled must be boolean")

        if type(self.drawing_enabled) is not bool:
            raise ValueError("drawing_enabled must be boolean")

        if type(self.quantity_animation_enabled) is not bool:
            raise ValueError("quantity_animation_enabled must be boolean")

        if type(self.celebration_enabled) is not bool:
            raise ValueError("celebration_enabled must be boolean")

        if self.activity_type in {"trace_digit", "write_digit"}:
            if not self.drawing_enabled:
                raise ValueError(
                    "Drawing must be enabled for writing activities"
                )

        if self.visual_id is not None:
            if not isinstance(self.visual_id, str) or not self.visual_id.strip():
                raise ValueError("visual_id must be a nonempty string")

            from visual_library.routes import OBJECTS
            from visual_library.photo_storage import list_approved_images

            if self.visual_id.startswith("photo:"):
                photo_id = self.visual_id.removeprefix("photo:")
                approved_ids = {
                    asset["id"]
                    for asset in list_approved_images()
                    if asset.get("teacher_approved") is True
                }

                if photo_id not in approved_ids:
                    raise ValueError(
                        f"Unknown or unapproved photo: {photo_id}"
                    )

            elif self.visual_id not in OBJECTS:
                raise ValueError(
                    f"Unknown visual library object: {self.visual_id}"
                )

        if not isinstance(self.settings, dict):
            raise ValueError("settings must be a dictionary")

        if self.activity_type == "find_digit":
            from activity_layouts import get_find_digit_layout

            layout_id = self.settings.get("layout_id")

            if layout_id is not None:
                if not isinstance(layout_id, str):
                    raise ValueError("layout_id must be a string")

                layout = get_find_digit_layout(layout_id)

                if layout["uses_visual_library"] and self.visual_id is None:
                    raise ValueError(
                        "Selected layout requires a visual library object"
                    )

                if not layout["uses_visual_library"] and self.visual_id is not None:
                    raise ValueError(
                        "Selected layout does not use a visual library object"
                    )

        return True
