"""Student-specific validation for quantity representation activities."""

import math
from copy import deepcopy

from quantity_activity_integrity import (
    validate_quantity_draft_integrity,
)

from student_activity_validation import (
    validate_common_student_requirements,
)


def validate_quantity_activity_for_student(draft, profile):
    """Validate a quantity activity without approving or saving it."""

    validate_quantity_draft_integrity(draft)

    result = deepcopy(
        validate_common_student_requirements(draft, profile)
    )

    checks = result["checks"]

    def add(rule, status, message):
        checks.append({
            "rule": rule,
            "status": status,
            "message": message,
        })

    visual = profile.get("visual") or {}
    auditory = profile.get("auditory") or {}

    # 1. Simultaneous object count

    if draft["activity_type"] == "number_to_quantity":
        object_count = sum(draft["options"])
    else:
        object_count = draft["target_quantity"]

    max_objects = visual.get("max_objects")

    if (
        type(max_objects) in (int, float)
        and math.isfinite(max_objects)
        and max_objects >= 0
        and max_objects == int(max_objects)
    ):
        if object_count > max_objects:
            add(
                "max_objects",
                "warning",
                f"Ekrandaki nesne sayısı ({object_count}) "
                f"öğrencinin belirlenen sınırını "
                f"({max_objects}) aşıyor."
            )
        else:
            add(
                "max_objects",
                "ok",
                f"Ekrandaki nesne sayısı ({object_count}) "
                "belirlenen sınır içinde."
            )
    else:
        add(
            "max_objects",
            "review",
            "Öğrencinin eşzamanlı nesne sınırı belirtilmemiş "
            "veya geçersiz."
        )

    # 2. Animation and moving image tolerance

    for field, label in (
        ("animation", "Animasyon"),
        ("moving_images", "Hareketli görsel"),
    ):
        if not draft["quantity_animation_enabled"]:
            add(
                field,
                "ok",
                f"Nesne animasyonu kapsamında {label.lower()} "
                "kullanımı kapalı."
            )
            continue

        tolerance = visual.get(field)

        if tolerance == "Uygun değil":
            add(
                field,
                "warning",
                f"{label} kullanımı öğrenci için uygun değil."
            )
        elif tolerance == "Uygun":
            add(
                field,
                "ok",
                f"{label} kullanımı profil tercihiyle uyumlu."
            )
        elif tolerance == "Sınırlı kullanım":
            add(
                field,
                "review",
                f"{label} kullanımı sınırlı olmalı."
            )
        else:
            add(
                field,
                "review",
                f"{label} kullanımına uygunluk belirtilmemiş."
            )

    # 3. Spoken counting

    if draft["spoken_counting_enabled"]:
        if auditory.get("spoken_instructions") == "Uygun değil":
            add(
                "spoken_counting",
                "warning",
                "Sesli sayma öğrencinin işitsel tercihiyle "
                "çelişebilir."
            )
        else:
            add(
                "spoken_counting",
                "review",
                "Sesli saymanın uygunluğu ve zamanlaması "
                "öğretmen tarafından değerlendirilmelidir."
            )
    else:
        add(
            "spoken_counting",
            "ok",
            "Sesli sayma kapalı."
        )

    # 4. Requirements not yet automatically verifiable

    add(
        "quantity_arrangement",
        "review",
        "Nesnelerin yerleşimi öğrenciye uygunluk açısından "
        "öğretmen tarafından incelenmelidir."
    )

    add(
        "visual_complexity",
        "review",
        "Etkinliğin görsel karmaşıklığı öğretmen tarafından "
        "değerlendirilmelidir."
    )

    if draft["celebration_enabled"]:
        add(
            "celebration_suitability",
            "review",
            "Kutlama ve pekiştirme biçiminin öğrenciye "
            "uygunluğu öğretmen tarafından incelenmelidir."
        )

    add(
        "academic_suitability",
        "review",
        "Hedef miktar ve seçenekler öğrencinin mevcut "
        "becerileri ve öğrenme hedefleri açısından "
        "değerlendirilmelidir."
    )

    # 5. Recalculate the combined validation result

    warnings = sum(
        c["status"] == "warning" for c in checks
    )

    reviews = sum(
        c["status"] == "review" for c in checks
    )

    result["warning_count"] = warnings
    result["review_count"] = reviews

    result["overall_status"] = (
        "warning" if warnings else
        "review" if reviews else
        "ok"
    )

    result["teacher_approval_required"] = True

    return result
