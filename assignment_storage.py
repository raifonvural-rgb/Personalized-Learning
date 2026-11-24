"""
Persistent storage for teacher-controlled activity assignments.

Each student can have only one active assignment.
Assignment does not modify the approved activity.
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
from activity_storage import get_activity


DATA_DIR = Path(__file__).resolve().parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

ASSIGNMENTS_FILE = DATA_DIR / "assignments.json"
LOCK_FILE = DATA_DIR / "assignments.lock"


def load_assignments():
    if not ASSIGNMENTS_FILE.exists():
        return {}

    with ASSIGNMENTS_FILE.open(
        "r", encoding="utf-8"
    ) as file:
        assignments = json.load(file)

    if not isinstance(assignments, dict):
        raise ValueError("Invalid assignment storage format")

    return assignments


def write_assignments(assignments):
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
                assignments,
                file,
                ensure_ascii=False,
                indent=4,
            )

            file.flush()
            os.fsync(file.fileno())

        os.replace(temp_path, ASSIGNMENTS_FILE)

    finally:
        if temp_path and os.path.exists(temp_path):
            os.unlink(temp_path)


def get_assignment(student_id):
    assignment = load_assignments().get(student_id)

    return copy.deepcopy(assignment)


def assign_activity(student_id, activity_id):

    if not isinstance(student_id, str) or not student_id:
        raise ValueError("Student ID is required")

    if not isinstance(activity_id, str) or not activity_id:
        raise ValueError("Activity ID is required")

    if get_profile(student_id) is None:
        raise ValueError("Student does not exist")

    activity = get_activity(activity_id)

    if activity is None:
        raise ValueError("Activity does not exist")

    if activity.get("student_id") != student_id:
        raise ValueError("Activity belongs to another student")

    if activity.get("status") != "approved":
        raise ValueError("Only approved activities can be assigned")

    assignment = {
        "id": str(uuid.uuid4()),
        "student_id": student_id,
        "activity_id": activity_id,
        "assigned_at": datetime.now(timezone.utc).isoformat(),
    }

    with LOCK_FILE.open("a", encoding="utf-8") as lock:

        fcntl.flock(lock, fcntl.LOCK_EX)

        try:
            assignments = load_assignments()

            assignments[student_id] = assignment

            write_assignments(assignments)

        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)

    return copy.deepcopy(assignment)


def clear_assignment(student_id, assignment_id):

    with LOCK_FILE.open("a", encoding="utf-8") as lock:

        fcntl.flock(lock, fcntl.LOCK_EX)

        try:
            assignments = load_assignments()

            current = assignments.get(student_id)

            if current is None:
                return False

            if current.get("id") != assignment_id:
                return False

            del assignments[student_id]

            write_assignments(assignments)

            return True

        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)
