"""
Parametrik SVG futbol topu çizimi.

Şematik panel düzeni:
- Merkezde beşgen
- Çevrede çokgen paneller
- Değiştirilebilir renkler ve çizgi kalınlığı
"""

import math
from pathlib import Path

from .pencil import validate_color


def draw_soccer_ball(
    panel_color="#303030",
    background_color="#FFFFFF",
    line_color="#303030",
    line_width=3,
    width=240,
    height=240,
):
    """
    Parametrik futbol topu SVG'si üretir.
    """

    for name, color in {
        "panel_color": panel_color,
        "background_color": background_color,
        "line_color": line_color,
    }.items():
        validate_color(color, name)

    for name, value in {
        "line_width": line_width,
        "width": width,
        "height": height,
    }.items():
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
        ):
            raise ValueError(f"{name}: Geçersiz sayı.")

    if not 1 <= line_width <= 12:
        raise ValueError("Çizgi kalınlığı 1–12 arasında olmalıdır.")

    if not 1 <= width <= 4096 or not 1 <= height <= 4096:
        raise ValueError("Boyutlar 1–4096 arasında olmalıdır.")

    return f'''<svg
xmlns="http://www.w3.org/2000/svg"
width="{width:g}"
height="{height:g}"
viewBox="0 0 200 200"
role="img"
aria-label="Futbol topu">

<defs>
    <clipPath id="soccer-ball-clip">
        <circle cx="100" cy="100" r="85"/>
    </clipPath>
</defs>

<!-- Ana top yüzeyi -->
<circle
cx="100"
cy="100"
r="85"
fill="{background_color}"
stroke="{line_color}"
stroke-width="{line_width:g}"/>

<!-- Panel çizgileri -->
<g
clip-path="url(#soccer-ball-clip)"
stroke="{line_color}"
stroke-width="{line_width:g}"
stroke-linejoin="round">

<!-- Merkez beşgen -->
<path
d="M100 64L135 89L122 130L78 130L65 89Z"
fill="{panel_color}"/>

<!-- Alt panel -->
<path
d="M78 130L55 151L72 190L111 193L122 130"
fill="{background_color}"/>

<!-- Sağ panel -->
<path
d="M135 89L165 73L193 104L170 144L122 130"
fill="{background_color}"/>

<!-- Sol panel -->
<path
d="M65 89L34 73L8 104L31 144L78 130"
fill="{background_color}"/>

<!-- Üst sağ panel -->
<path
d="M100 64L100 27L139 6L165 73L135 89"
fill="{background_color}"/>

<!-- Üst sol panel -->
<path
d="M100 64L100 27L61 6L34 73L65 89"
fill="{background_color}"/>

<!-- Kenar panelleri -->
<path
d="M100 27L83 -7L117 -7Z"
fill="{panel_color}"/>

<path
d="M31 144L9 164L45 193L72 190Z"
fill="{panel_color}"/>

<path
d="M170 144L191 164L155 193L111 193Z"
fill="{panel_color}"/>

</g>
</svg>'''


if __name__ == "__main__":

    output = Path(
        "/tmp/autism_soccer_ball_preview.svg"
    )

    output.write_text(
        draw_soccer_ball(),
        encoding="utf-8"
    )

    print("SVG oluşturuldu:", output)
    print(
        "Dosya boyutu:",
        output.stat().st_size,
        "bayt"
    )
