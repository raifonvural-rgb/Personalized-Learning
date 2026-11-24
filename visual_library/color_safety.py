"""
SVG renklerinin öğrenci profiline göre ön denetimi.

Bu sınıflandırma sezgiseldir; pedagojik uygunluk kararı değildir.
Belirsizlikler öğretmen incelemesine yönlendirilir.
"""

import colorsys
import re

COLOR_NAMES = {
    "Kırmızı": "red",
    "Turuncu": "orange",
    "Sarı": "yellow",
    "Yeşil": "green",
    "Mavi": "blue",
    "Mor": "purple",
    "Pembe": "pink",
    "Beyaz": "white",
    "Siyah": "black",
    "Gri": "gray",
    "Kahverengi": "brown",
}

def classify_color(hex_color):
    if not isinstance(hex_color, str) or not re.fullmatch(
        r"#[0-9a-fA-F]{6}", hex_color
    ):
        return {
            "status": "review",
            "family": None,
            "possible_families": [],
            "reason": "Geçersiz renk kodu"
        }

    r, g, b = (
        int(hex_color[i:i+2], 16) / 255
        for i in (1, 3, 5)
    )

    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    hue = h * 360

    if v < 0.15:
        family = "black"
    elif s < 0.12 and v > 0.88:
        family = "white"
    elif s < 0.15:
        family = "gray"
    elif 12 <= hue <= 45 and v < 0.65:
        family = "brown"
    elif 290 <= hue < 345:
        family = "purple" if v < 0.75 else "pink"
    elif hue >= 345 or hue < 12:
        family = "pink" if s < 0.45 and v > 0.75 else "red"
    elif hue < 45:
        family = "orange"
    elif hue < 70:
        family = "yellow"
    elif hue < 165:
        family = "green"
    elif hue < 255:
        family = "blue"
    else:
        family = "purple"

    possible = {family}

    boundaries = [
        (12, "red", "orange"),
        (45, "orange", "yellow"),
        (70, "yellow", "green"),
        (165, "green", "blue"),
        (255, "blue", "purple"),
        (290, "purple", "pink"),
        (345, "pink", "red"),
    ]

    if s >= 0.15:
        for boundary, left, right in boundaries:
            if abs(hue - boundary) < 5:
                possible.update((left, right))

    if family in {"red", "pink"} and v > 0.7:
        if 0.25 <= s <= 0.65:
            possible.update(("red", "pink"))

    if family in {"purple", "pink"} and 285 <= hue <= 345:
        if 0.65 <= v <= 0.85:
            possible.update(("purple", "pink"))

    uncertain = len(possible) > 1

    return {
        "status": "review" if uncertain else "classified",
        "family": family,
        "possible_families": sorted(possible),
        "reason": (
            "Birden fazla renk ailesi olası"
            if uncertain else "Renk ailesi belirlendi"
        )
    }


def check_avoided_colors(colors, avoided_colors):
    avoided = {
        COLOR_NAMES[name]
        for name in avoided_colors
        if name in COLOR_NAMES
    }

    results = []

    for parameter, hex_color in colors.items():
        classification = classify_color(hex_color)
        possible = set(classification["possible_families"])
        overlap = possible & avoided

        if classification["status"] == "review":
            status = "review"
        elif overlap:
            status = "warning"
        else:
            status = "ok"

        results.append({
            "parameter": parameter,
            "color": hex_color,
            "family": classification["family"],
            "possible_families": sorted(possible),
            "status": status,
            "matched_avoided_colors": sorted(overlap),
            "reason": classification["reason"]
        })

    return results
