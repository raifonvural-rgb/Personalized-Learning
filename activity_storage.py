"""
Persistent storage for teacher-created activity drafts.

This module does not approve or assign activities.
All newly saved activities remain drafts.
"""

import copy
import fcntl
import json
import os
import tempfile
import uuid

from datetime import datetime, timezone
from pathlib import Path

from profile_storage import get_profile


DATA_DIR = Path(__file__).resolve().parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

ACTIVITIES_FILE = DATA_DIR / "activities.json"
LOCK_FILE = DATA_DIR / "activities.lock"


def current_time():
    return datetime.now(timezone.utc).isoformat()


def load_activities():
    if not ACTIVITIES_FILE.exists():
        return []

    with ACTIVITIES_FILE.open("r", encoding="utf-8") as file:
        activities = json.load(file)

    if not isinstance(activities, list):
        raise ValueError("Invalid activity storage format")

    return activities


def write_activities(activities):
    temp_path = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=DATA_DIR,
            delete=False,
        ) as file:
            temp_path = file.name

            json.dump(
                activities,
                file,
                ensure_ascii=False,
                indent=4,
            )

            file.flush()
            os.fsync(file.fileno())

        os.replace(temp_path, ACTIVITIES_FILE)

    finally:
        if temp_path and os.path.exists(temp_path):
            os.unlink(temp_path)


def get_activity(activity_id):
    for activity in load_activities():
        if activity["id"] == activity_id:
            return copy.deepcopy(activity)

    return None


def list_student_activities(student_id):
    return [
        copy.deepcopy(activity)
        for activity in load_activities()
        if activity["student_id"] == student_id
    ]


def save_activity_draft(student_id, draft, copied_from=None):
    if not isinstance(student_id, str) or not student_id:
        raise ValueError("Student ID is required")

    if get_profile(student_id) is None:
        raise ValueError("Student does not exist")

    if not isinstance(draft, dict):
        raise ValueError("Activity draft must be an object")

    if draft.get("status") != "draft":
        raise ValueError("Only drafts can be saved")

    if draft.get("teacher_approved") is not False:
        raise ValueError("Draft must not be teacher-approved")

    required = {
        "achievement_code",
        "activity_type",
        "target_digit",
        "layout_id",
        "options",
        "correct_index",
    }

    if not required.issubset(draft):
        raise ValueError("Activity draft is incomplete")

    if copied_from is not None and not isinstance(copied_from, str):
        raise ValueError("Invalid source activity ID")

    from activity_models import ActivityConfig
    from activity_builder import build_find_digit_draft

    config = ActivityConfig(
        achievement_code=draft.get("achievement_code"),
        target_digit=draft.get("target_digit"),
        activity_type=draft.get("activity_type"),
        visual_id=draft.get("visual_id"),
        audio_enabled=draft.get("audio_enabled"),
        celebration_enabled=draft.get("celebration_enabled"),
        quantity_animation_enabled=draft.get("quantity_animation_enabled", False),
        settings={"layout_id": draft.get("layout_id")},
    )

    validated = build_find_digit_draft(
        config,
        options=draft.get("options"),
    )

    if draft != {k: v for k, v in validated.items() if k in draft}:
        raise ValueError(
            "Draft does not match the validated activity configuration"
        )

    now = current_time()

    activity = {
        "id": str(uuid.uuid4()),
        "student_id": student_id,
        "config": copy.deepcopy(draft),
        "status": "draft",
        "validation": None,
        "approval": None,
        "copied_from": copied_from,
        "created_at": now,
        "updated_at": now,
    }

    with LOCK_FILE.open("a", encoding="utf-8") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)

        try:
            activities = load_activities()
            activities.append(activity)
            write_activities(activities)

        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)

    return copy.deepcopy(activity)


def validate_saved_activity(activity_id):
    """
    Validate a saved draft against its current student profile.

    Does not approve or publish the activity.
    """
    from activity_validation_record import (
        create_validation_record,
        check_validation_freshness,
    )

    if not isinstance(activity_id, str) or not activity_id:
        raise ValueError("Activity ID is required")

    with LOCK_FILE.open("a", encoding="utf-8") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)

        try:
            activities = load_activities()

            activity = next(
                (item for item in activities
                 if item.get("id") == activity_id),
                None,
            )

            if activity is None:
                raise ValueError("Activity not found")

            if activity.get("status") != "draft":
                raise ValueError("Only drafts can be validated")

            if activity.get("approval") is not None:
                raise ValueError("Approved activity cannot be revalidated")

            student_id = activity.get("student_id")
            profile = get_profile(student_id)

            if profile is None:
                raise ValueError("Student profile not found")

            draft = copy.deepcopy(activity["config"])
            record = create_validation_record(draft, profile)

            current_profile = get_profile(student_id)

            if current_profile is None:
                raise ValueError("Student profile disappeared")

            freshness = check_validation_freshness(
                record, activity["config"], current_profile
            )

            if not freshness["current"]:
                raise ValueError(
                    "Activity or student profile changed during validation"
                )

            activity["validation"] = record
            activity["updated_at"] = current_time()

            write_activities(activities)

            return copy.deepcopy(activity)

        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)

def approve_saved_activity(activity_id, acknowledge_issues=False):
    """
    Approve a validated activity following explicit teacher review.

    This function does not itself authenticate the teacher.
    """
    from activity_validation_record import check_validation_freshness

    if not isinstance(activity_id, str) or not activity_id:
        raise ValueError("Activity ID is required")

    if type(acknowledge_issues) is not bool:
        raise ValueError("Acknowledgement must be a boolean")

    with LOCK_FILE.open("a", encoding="utf-8") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)

        try:
            activities = load_activities()

            activity = next(
                (item for item in activities if item.get("id") == activity_id),
                None,
            )

            if activity is None:
                raise ValueError("Activity not found")

            if activity.get("status") != "draft":
                raise ValueError("Only drafts can be approved")

            if activity.get("approval") is not None:
                raise ValueError("Activity already approved")

            validation = activity.get("validation")

            if not isinstance(validation, dict):
                raise ValueError("Activity must be validated first")

            profile = get_profile(activity["student_id"])

            if profile is None:
                raise ValueError("Student profile not found")

            freshness = check_validation_freshness(
                validation, activity["config"], profile
            )

            if not freshness["current"]:
                raise ValueError(freshness["reason"])

            result = validation.get("result")

            if not isinstance(result, dict):
                raise ValueError("Invalid validation result")

            checks = result.get("checks")

            if not isinstance(checks, list) or not checks:
                raise ValueError("Validation checks are missing")

            if any(
                not isinstance(check, dict)
                or check.get("status") not in ("ok", "warning", "review")
                for check in checks
            ):
                raise ValueError("Invalid validation checks")

            has_issues = any(
                check["status"] in ("warning", "review")
                for check in checks
            )

            if has_issues and not acknowledge_issues:
                raise ValueError(
                    "Teacher must acknowledge warnings and review items"
                )

            now = current_time()

            activity["status"] = "approved"
            activity["approval"] = {
                "approved_at": now,
                "issues_acknowledged": acknowledge_issues,
                "validation_activity_hash": validation["activity_hash"],
                "validation_profile_hash": validation["profile_hash"],
            }
            activity["updated_at"] = now

            write_activities(activities)

            return copy.deepcopy(activity)

        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)
