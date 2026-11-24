"""
Etkinlik doğrulama sonuçlarını içerik özetleriyle ilişkilendirir.

Bu modül kalıcı kayıt oluşturmaz ve öğretmen onayı vermez.
"""

from datetime import datetime, timezone

from activity_fingerprint import activity_hash, profile_hash
from activity_validation import validate_activity_for_student


def create_validation_record(draft, profile):
    result = validate_activity_for_student(draft, profile)

    return {
        "activity_hash": activity_hash(draft),
        "profile_hash": profile_hash(profile),
        "validated_at": datetime.now(timezone.utc).isoformat(),
        "result": result,
    }


def check_validation_freshness(record, draft, profile):
    if not isinstance(record, dict):
        return {
            "current": False,
            "reason": "Doğrulama kaydı geçersiz.",
        }

    if record.get("activity_hash") != activity_hash(draft):
        return {
            "current": False,
            "reason": "Etkinlik doğrulamadan sonra değişmiş.",
        }

    if record.get("profile_hash") != profile_hash(profile):
        return {
            "current": False,
            "reason": "Öğrenci profili doğrulamadan sonra değişmiş.",
        }

    if not isinstance(record.get("result"), dict):
        return {
            "current": False,
            "reason": "Doğrulama sonucu eksik.",
        }

    return {
        "current": True,
        "reason": "Etkinlik ve öğrenci profili doğrulanan içerikle eşleşiyor.",
    }
