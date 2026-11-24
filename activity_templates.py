"""
Reusable activity templates for teaching digits 0-9.

Templates describe teaching interactions independently of
the target digit, student, and selected visual object.
"""

ACTIVITY_TEMPLATES = {
    "find_digit": {
        "name": "Rakamı Bul",
        "achievement_code": "MAT1.1.1",
        "interaction": "select",
        "supports_visual_library": True,
        "supports_audio": True,
        "requires_drawing": False,
        "teacher_evaluation": True,
    },
    "say_digit": {
        "name": "Rakamı Söyle",
        "achievement_code": "MAT1.1.2",
        "interaction": "speak",
        "supports_visual_library": False,
        "supports_audio": True,
        "requires_drawing": False,
        "teacher_evaluation": True,
    },
    "trace_digit": {
        "name": "Rakamın Üzerinden Çiz",
        "achievement_code": "MAT1.1.3",
        "interaction": "trace",
        "supports_visual_library": False,
        "supports_audio": True,
        "requires_drawing": True,
        "teacher_evaluation": True,
    },
    "write_digit": {
        "name": "Rakamı Yaz",
        "achievement_code": "MAT1.1.3",
        "interaction": "write",
        "supports_visual_library": False,
        "supports_audio": True,
        "requires_drawing": True,
        "teacher_evaluation": True,
    },
}


def get_templates_for_achievement(achievement_code):
    return {
        template_id: template
        for template_id, template in ACTIVITY_TEMPLATES.items()
        if template["achievement_code"] == achievement_code
    }
