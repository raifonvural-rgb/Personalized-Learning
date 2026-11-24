"""Independent AI image generation provider."""

import os
import base64
import binascii

from openai import OpenAI, OpenAIError


DEFAULT_MODEL = "gpt-image-1-mini"
DEFAULT_SIZE = "1024x1024"
DEFAULT_QUALITY = "medium"
MAX_PROMPT_LENGTH = 2000


class ImageGenerationError(Exception):
    """Safe image generation error for the application."""


def generate_image(description):
    """Generate one educational image and return bytes and metadata."""

    if not isinstance(description, str) or not description.strip():
        raise ValueError("Görsel açıklaması gerekli.")

    description = description.strip()

    if len(description) > MAX_PROMPT_LENGTH:
        raise ValueError("Görsel açıklaması çok uzun.")

    model = os.environ.get("OPENAI_IMAGE_MODEL", DEFAULT_MODEL)

    prompt = (
        "Create a clear educational image suitable for children. "
        "Use a simple, distraction-free composition. "
        "Avoid unnecessary decorative elements. "
        "Do not include text or numbers unless explicitly requested. "
        "Follow the teacher's description carefully. "
        "Teacher description: " + description
    )

    if not os.environ.get("OPENAI_API_KEY"):
        raise ImageGenerationError(
            "Görsel üretim servisi yapılandırılmamış."
        )

    try:
        client = OpenAI(
            timeout=180.0,
            max_retries=0
        )

        result = client.images.generate(
            model=model,
            prompt=prompt,
            size=DEFAULT_SIZE,
            quality=DEFAULT_QUALITY,
            n=1
        )

    except OpenAIError as exc:
        raise ImageGenerationError(
            "Görsel üretimi başarısız oldu. "
            "Lütfen daha sonra tekrar deneyin."
        ) from exc

    if not result.data or not result.data[0].b64_json:
        raise ImageGenerationError(
            "Görsel üretim servisi boş sonuç döndürdü."
        )

    try:
        content = base64.b64decode(
            result.data[0].b64_json,
            validate=True
        )
    except (ValueError, binascii.Error) as exc:
        raise ImageGenerationError(
            "Üretilen görsel verisi geçersiz."
        ) from exc

    if not content:
        raise ImageGenerationError("Üretilen görsel boş.")

    return {
        "content": content,
        "metadata": {
            "source": "ai_generated",
            "model": model,
            "prompt": prompt
        }
    }
