"""
Reusable visual layouts for digit-finding activities.

Layouts define presentation structure, not SVG objects.
"""

FIND_DIGIT_LAYOUTS = {
    "balloons": {
        "name": "Balonlar",
        "description": "Rakamlar balonların üzerinde gösterilir.",
        "uses_visual_library": False,
    },
    "flower_petals": {
        "name": "Çiçek Yaprakları",
        "description": "Rakamlar çiçeğin yapraklarında gösterilir.",
        "uses_visual_library": False,
    },
    "object_cards": {
        "name": "Nesne Kartları",
        "description": "Rakamlar seçilen görsel nesnelerle birlikte gösterilir.",
        "uses_visual_library": True,
    },
}


def get_find_digit_layout(layout_id):
    if layout_id not in FIND_DIGIT_LAYOUTS:
        raise ValueError(f"Unknown activity layout: {layout_id}")
    return FIND_DIGIT_LAYOUTS[layout_id]
