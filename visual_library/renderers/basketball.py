"""
Parametrik SVG basketbol topu.
"""

import math
from html import escape
from pathlib import Path

from .pencil import validate_color


def draw_basketball(
    ball_color="#E67E22",
    line_color="#303030",
    line_width=4,
    width=240,
    height=240,
):
    """
    Basketbol topu SVG'si üretir.

    Değiştirilebilir özellikler:
    - Top rengi
    - Çizgi rengi
    - Çizgi kalınlığı
    - SVG boyutları
    """

    validate_color(ball_color, "ball_color")
    validate_color(line_color, "line_color")

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
            raise ValueError(f"{name}: Geçersiz sayısal değer.")

    if not 1 <= line_width <= 12:
        raise ValueError(
            "Çizgi kalınlığı 1 ile 12 arasında olmalıdır."
        )

    if not 1 <= width <= 4096 or not 1 <= height <= 4096:
        raise ValueError(
            "SVG boyutları 1 ile 4096 arasında olmalıdır."
        )

    return f'''<svg
xmlns="http://www.w3.org/2000/svg"
width="{width:g}"
height="{height:g}"
viewBox="0 0 200 200"
role="img"
aria-label="Basketbol topu">

<defs>
    <clipPath id="basketball-clip">
        <circle cx="100" cy="100" r="83"/>
    </clipPath>
</defs>

<!-- Topun ana gövdesi -->
<circle
cx="100"
cy="100"
r="83"
fill="{escape(ball_color)}"
stroke="{escape(line_color)}"
stroke-width="{line_width:g}"/>

<!-- Basketbol topu çizgileri -->
<g
clip-path="url(#basketball-clip)"
fill="none"
stroke="{escape(line_color)}"
stroke-width="{line_width:g}">

    <path d="M100 17V183"/>
    <path d="M17 100H183"/>

    <path
    d="M50 32C108 65 108 135 50 168"/>

    <path
    d="M150 32C92 65 92 135 150 168"/>

</g>

</svg>'''


if __name__ == "__main__":

    output = Path(
        "/tmp/autism_basketball_preview.svg"
    )

    output.write_text(
        draw_basketball(),
        encoding="utf-8"
    )

    print("SVG oluşturuldu:", output)
    print(
        "Dosya boyutu:",
        output.stat().st_size,
        "bayt"
    )
