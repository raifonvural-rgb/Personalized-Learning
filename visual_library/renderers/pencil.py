"""
Parametrik SVG kurşun kalem çizimi.

Bileşenler:
- Silgi
- Metal silgi tutucu
- Kalem gövdesi
- Açılmış ahşap uç
- Grafit uç
"""

import re
from html import escape


HEX_COLOR = re.compile(r"^#[0-9a-fA-F]{6}$")


def validate_color(value, name):
    if not isinstance(value, str) or not HEX_COLOR.fullmatch(value):
        raise ValueError(
            f"{name} için #RRGGBB biçiminde renk belirtilmelidir."
        )
    return value


def draw_pencil(
    body_color="#E8C94E",
    eraser_color="#ED9CB4",
    wood_color="#E5B983",
    graphite_color="#30343B",
    metal_color="#B5BDC9",
    outline_color="#35455C",
    width=340,
    height=110,
):
    """
    Silgili ve açılmış kurşun kalem SVG'si üretir.

    Bütün renkler parametriktir.
    SVG, 340x110 koordinat sisteminde çizilir.
    """

    colors = {
        "body_color": body_color,
        "eraser_color": eraser_color,
        "wood_color": wood_color,
        "graphite_color": graphite_color,
        "metal_color": metal_color,
        "outline_color": outline_color,
    }

    for name, value in colors.items():
        validate_color(value, name)

    if (
        isinstance(width, bool)
        or isinstance(height, bool)
        or not isinstance(width, (int, float))
        or not isinstance(height, (int, float))
        or not 1 <= width <= 4096
        or not 1 <= height <= 4096
    ):
        raise ValueError("SVG boyutları 1 ile 4096 arasında olmalıdır.")

    return f'''<svg
xmlns="http://www.w3.org/2000/svg"
width="{width:g}"
height="{height:g}"
viewBox="0 0 340 110"
role="img"
aria-label="Silgili, ucu açılmış kurşun kalem">

<g transform="translate(12 12)">

<!-- Silgi -->
<rect
x="8" y="25"
width="43" height="40"
rx="9"
fill="{escape(eraser_color)}"
stroke="{escape(outline_color)}"
stroke-width="2"/>

<!-- Metal tutucu -->
<rect
x="43" y="24"
width="20" height="42"
fill="{escape(metal_color)}"
stroke="{escape(outline_color)}"
stroke-width="2"/>

<!-- Kalem gövdesi -->
<rect
x="63" y="25"
width="201" height="40"
fill="{escape(body_color)}"
stroke="{escape(outline_color)}"
stroke-width="2"/>

<!-- Gövde ışık çizgisi -->
<path
d="M63 34H264"
fill="none"
stroke="{escape(outline_color)}"
stroke-opacity="0.18"
stroke-width="2"/>

<!-- Gövde alt çizgisi -->
<path
d="M63 55H264"
fill="none"
stroke="{escape(outline_color)}"
stroke-opacity="0.3"
stroke-width="2"/>

<!-- Açılmış ahşap uç -->
<path
d="M264 25L308 45L264 65Z"
fill="{escape(wood_color)}"
stroke="{escape(outline_color)}"
stroke-width="2"/>

<!-- Grafit uç -->
<path
d="M294 38L308 45L294 52Z"
fill="{escape(graphite_color)}"/>

</g>
</svg>'''


if __name__ == "__main__":
    from pathlib import Path

    output = Path("/tmp/autism_pencil_preview.svg")

    output.write_text(
        draw_pencil(),
        encoding="utf-8"
    )

    print("SVG oluşturuldu:", output)
    print("Dosya boyutu:", output.stat().st_size, "bayt")
