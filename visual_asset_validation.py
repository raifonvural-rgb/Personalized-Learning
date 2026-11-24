"""Shared visual library asset verification."""


def validate_visual_asset(visual_id):
    if visual_id is not None:
        if not isinstance(visual_id, str) or not visual_id.strip():
            raise ValueError("visual_id must be a nonempty string")

        from visual_library.routes import OBJECTS
        from visual_library.photo_storage import list_approved_images

        if visual_id.startswith("photo:"):
            photo_id = visual_id.removeprefix("photo:")
            approved_ids = {
                asset["id"]
                for asset in list_approved_images()
                if asset.get("teacher_approved") is True
            }

            if photo_id not in approved_ids:
                raise ValueError(
                    f"Unknown or unapproved photo: {photo_id}"
                )

        elif visual_id not in OBJECTS:
            raise ValueError(
                f"Unknown visual library object: {visual_id}"
            )
