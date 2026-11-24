"""
Deterministic fingerprints for activity and student profile content.
"""

import hashlib
import json


def content_hash(data):
    serialized = json.dumps(
        data,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )

    return hashlib.sha256(
        serialized.encode("utf-8")
    ).hexdigest()


def activity_hash(draft):
    if not isinstance(draft, dict):
        raise ValueError("Activity must be a dictionary")

    return content_hash(draft)


def profile_hash(profile):
    if not isinstance(profile, dict):
        raise ValueError("Profile must be a dictionary")

    return content_hash(profile)
