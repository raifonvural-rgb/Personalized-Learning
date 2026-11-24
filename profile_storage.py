"""
Öğrenci profillerinin kalıcı olarak saklanması,
okunması, doğrulanması ve güncellenmesi.
"""

import json
import os
import tempfile
import uuid
import fcntl

from pathlib import Path
from datetime import datetime, timezone
from student_profiles import PROFILE_SCHEMA


DATA_DIR = Path(__file__).resolve().parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

PROFILES_FILE = DATA_DIR / "students.json"
LOCK_FILE = DATA_DIR / "students.lock"


def current_time():
    return datetime.now(timezone.utc).isoformat()


def empty_value(field):
    if field["type"] == "multiselect":
        return []

    if field["type"] == "number":
        return None

    return ""


def create_empty_profile():

    profile = {
        "id": str(uuid.uuid4()),
        "created_at": current_time(),
        "updated_at": current_time()
    }

    for section in PROFILE_SCHEMA:

        key = section["key"]

        if section.get("repeatable"):
            profile[key] = []
        else:
            profile[key] = {
                field["key"]: empty_value(field)
                for field in section["fields"]
            }

    return profile


def load_profiles():

    if not PROFILES_FILE.exists():
        return []

    with PROFILES_FILE.open(
        "r", encoding="utf-8"
    ) as file:

        profiles = json.load(file)

    if not isinstance(profiles, list):
        raise ValueError(
            "Öğrenci profil dosyasının biçimi geçersiz."
        )

    return profiles


def write_profiles(profiles):

    temp_path = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=DATA_DIR,
            delete=False
        ) as file:

            temp_path = file.name

            json.dump(
                profiles,
                file,
                ensure_ascii=False,
                indent=4
            )

            file.flush()
            os.fsync(file.fileno())

        os.replace(temp_path, PROFILES_FILE)

    finally:
        if temp_path and os.path.exists(temp_path):
            os.unlink(temp_path)


def list_students():

    students = [
        {
            "id": profile["id"],
            "name": profile["general"]["name"]
        }
        for profile in load_profiles()
    ]

    return sorted(
        students,
        key=lambda student: student["name"].casefold()
    )


def get_profile(student_id):

    for profile in load_profiles():

        if profile["id"] == student_id:
            return profile

    return None


def validate_fields(values, fields, section_title):

    if not isinstance(values, dict):
        raise ValueError(
            f"{section_title}: Geçersiz bölüm biçimi."
        )

    allowed_keys = {
        field["key"] for field in fields
    }

    if set(values) - allowed_keys:
        raise ValueError(
            f"{section_title}: Bilinmeyen alan."
        )

    for field in fields:

        value = values.get(
            field["key"], empty_value(field)
        )

        label = field["label"]
        kind = field["type"]
        options = field["options"]

        if field["required"]:

            if not isinstance(value, str) or not value.strip():
                raise ValueError(
                    f"{label} zorunludur."
                )

        if kind == "number":

            if value not in (None, ""):

                if (
                    type(value) not in (int, float)
                    or value < 0
                    or not __import__("math").isfinite(value)
                ):
                    raise ValueError(
                        f"{label}: Geçersiz sayısal değer."
                    )

        elif kind == "multiselect":

            if not isinstance(value, list):
                raise ValueError(
                    f"{label}: Liste bekleniyor."
                )

            if any(item not in options for item in value):
                raise ValueError(
                    f"{label}: Geçersiz seçim."
                )

        elif kind == "select":

            if value != "" and value not in options:
                raise ValueError(
                    f"{label}: Geçersiz seçim."
                )

        else:

            if not isinstance(value, str):
                raise ValueError(
                    f"{label}: Metin bekleniyor."
                )


def validate_profile(profile):

    if not isinstance(profile, dict):
        raise ValueError("Geçersiz öğrenci profili.")

    for section in PROFILE_SCHEMA:

        key = section["key"]
        title = section["title"]
        fields = section["fields"]

        if section.get("repeatable"):

            items = profile.get(key, [])

            if not isinstance(items, list):
                raise ValueError(
                    f"{title}: Liste bekleniyor."
                )

            for item in items:

                validate_fields(item, fields, title)

                if not item.get("name", "").strip():
                    raise ValueError(
                        "Ek gereksinim adı boş bırakılamaz."
                    )

                if not item.get("description", "").strip():
                    raise ValueError(
                        "Ek gereksinim açıklaması boş bırakılamaz."
                    )

                if not item.get("priority"):
                    raise ValueError(
                        "Ek gereksinim önceliği seçilmelidir."
                    )

        else:

            validate_fields(
                profile.get(key, {}),
                fields,
                title
            )

    return True


def save_profile(profile):

    validate_profile(profile)

    with LOCK_FILE.open("a", encoding="utf-8") as lock:

        fcntl.flock(lock, fcntl.LOCK_EX)

        try:

            profiles = load_profiles()

            student_id = profile.get("id")

            existing_index = next(
                (
                    index
                    for index, item in enumerate(profiles)
                    if item["id"] == student_id
                ),
                None
            )

            normalized = create_empty_profile()

            for section in PROFILE_SCHEMA:

                key = section["key"]

                if key not in profile:
                    continue

                if section.get("repeatable"):
                    normalized[key] = profile[key]
                else:
                    normalized[key].update(profile[key])

            normalized["general"]["name"] = (
                normalized["general"]["name"].strip()
            )

            if existing_index is not None:

                existing = profiles[existing_index]

                normalized["id"] = existing["id"]
                normalized["created_at"] = existing["created_at"]

                profiles[existing_index] = normalized

            else:

                if student_id:
                    raise ValueError(
                        "Güncellenecek öğrenci bulunamadı."
                    )

                profiles.append(normalized)

            normalized["updated_at"] = current_time()

            write_profiles(profiles)

            return normalized

        finally:

            fcntl.flock(lock, fcntl.LOCK_UN)


if __name__ == "__main__":

    profile = create_empty_profile()

    print("Profil saklama modülü başarıyla yüklendi.")
    print("Veri klasörü:", DATA_DIR)
    print("Profil dosyası:", PROFILES_FILE)
    print("Oluşturulan örnek profil ID:", profile["id"])
    print("Profil bölümü sayısı:", len(PROFILE_SCHEMA))
    print("Kayıtlı öğrenci sayısı:", len(load_profiles()))

    try:

        validate_profile(profile)

    except ValueError as error:

        print("Beklenen doğrulama sonucu:", error)

    print("Test tamamlandı. Öğrenci kaydı yapılmadı.")
