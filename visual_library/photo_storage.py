"""Storage for teacher-reviewed photographic visual assets."""

import hashlib
import io
import json
import os
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageOps, UnidentifiedImageError

BASE = Path(__file__).resolve().parent
UPLOADS = BASE / "uploads"
PENDING = BASE / "pending"
CATALOG = BASE.parent / "data" / "visual_assets.json"

MAX_BYTES = 10 * 1024 * 1024
MAX_PIXELS = 20_000_000

FORMATS = {
    "PNG": "png",
    "JPEG": "jpg",
    "WEBP": "webp",
}


def _load_catalog():
    if not CATALOG.exists():
        return {"assets": []}
    data = json.loads(CATALOG.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get("assets"), list):
        raise ValueError("Invalid visual asset catalog")
    return data


def _save_catalog(data):
    CATALOG.parent.mkdir(parents=True, exist_ok=True)
    fd, temp = tempfile.mkstemp(dir=CATALOG.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(data, stream, ensure_ascii=False, indent=2)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp, CATALOG)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)


def prepare_upload(file, metadata=None):
    """Validate and normalize an uploaded image for teacher review."""
    if file is None:
        raise ValueError("Görsel dosyası seçilmedi.")

    raw = file.read(MAX_BYTES + 1)
    if not raw:
        raise ValueError("Dosya boş.")
    if len(raw) > MAX_BYTES:
        raise ValueError("Dosya 10 MB sınırını aşıyor.")

    try:
        with Image.open(io.BytesIO(raw)) as source:
            if source.format not in FORMATS:
                raise ValueError("Yalnızca PNG, JPEG ve WebP desteklenir.")

            if source.width * source.height > MAX_PIXELS:
                raise ValueError("Görsel boyutları çok büyük.")

            image = ImageOps.exif_transpose(source)
            image.load()
            image = image.convert("RGBA" if "A" in image.getbands() else "RGB")

    except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as exc:
        raise ValueError("Geçersiz veya desteklenmeyen görsel.") from exc

    # Normalize to PNG to remove embedded metadata.
    output = io.BytesIO()
    image.save(output, format="PNG", optimize=True)
    content = output.getvalue()

    PENDING.mkdir(parents=True, exist_ok=True)
    token = uuid.uuid4().hex
    metadata = dict(metadata or {})
    source_type = metadata.get("source", "teacher_upload")

    if source_type not in ("teacher_upload", "ai_generated"):
        raise ValueError("Geçersiz görsel kaynağı.")

    pending_metadata = {"source": source_type}

    if source_type == "ai_generated":
        for key in ("model", "prompt"):
            value = metadata.get(key)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"Eksik görsel üretim bilgisi: {key}")
            pending_metadata[key] = value.strip()

    image_path = PENDING / f"{token}.png"
    metadata_path = PENDING / f"{token}.json"

    try:
        image_path.write_bytes(content)
        metadata_path.write_text(
            json.dumps(
                pending_metadata,
                ensure_ascii=False,
                indent=2
            ),
            encoding="utf-8"
        )
    except Exception:
        image_path.unlink(missing_ok=True)
        metadata_path.unlink(missing_ok=True)
        raise

    return {
        "token": token,
        "width": image.width,
        "height": image.height,
        "preview_url": f"/visual-library/pending/{token}",
    }


def approve_upload(token, name):
    """Approve a pending image and register one master copy."""
    if not isinstance(token, str) or len(token) != 32:
        raise ValueError("Geçersiz görsel kimliği.")

    try:
        int(token, 16)
    except ValueError as exc:
        raise ValueError("Geçersiz görsel kimliği.") from exc

    if not isinstance(name, str) or not name.strip():
        raise ValueError("Görsel adı gerekli.")

    name = name.strip()[:120]
    pending = PENDING / f"{token}.png"

    if not pending.is_file():
        raise ValueError("Onay bekleyen görsel bulunamadı.")

    metadata_path = PENDING / f"{token}.json"

    if metadata_path.is_file():
        metadata = json.loads(
            metadata_path.read_text(encoding="utf-8")
        )
    else:
        metadata = {"source": "teacher_upload"}

    if not isinstance(metadata, dict):
        raise ValueError("Geçersiz görsel kaynak bilgisi.")

    source_type = metadata.get("source")

    if source_type not in ("teacher_upload", "ai_generated"):
        raise ValueError("Geçersiz görsel kaynağı.")

    generation_metadata = {}

    if source_type == "ai_generated":
        for key in ("model", "prompt"):
            value = metadata.get(key)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"Eksik görsel üretim bilgisi: {key}")
            generation_metadata[key] = value

    content = pending.read_bytes()
    digest = hashlib.sha256(content).hexdigest()

    UPLOADS.mkdir(parents=True, exist_ok=True)
    destination = UPLOADS / f"{digest}.png"

    catalog = _load_catalog()

    for asset in catalog["assets"]:
        if asset["sha256"] == digest:
            pending.unlink(missing_ok=True)
            metadata_path.unlink(missing_ok=True)
            return {**asset, "duplicate": True}

    if not destination.exists():
        destination.write_bytes(content)

    asset = {
        "id": uuid.uuid4().hex,
        "name": name,
        "filename": destination.name,
        "sha256": digest,
        "format": "PNG",
        "source": source_type,
        **generation_metadata,
        "teacher_approved": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    catalog["assets"].append(asset)
    _save_catalog(catalog)
    pending.unlink(missing_ok=True)
    metadata_path.unlink(missing_ok=True)

    return {**asset, "duplicate": False}


def list_approved_images():
    return [
        asset for asset in _load_catalog()["assets"]
        if asset.get("teacher_approved") is True
    ]
