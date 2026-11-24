"""
Öğrenci profili yönetimi için Flask API.

Merkezi profil şeması, öğrenci listesi,
profil okuma ve profil kaydetme işlemleri.
"""

from flask import Blueprint, jsonify, request, current_app

from student_profiles import PROFILE_SCHEMA

from profile_storage import (
    list_students,
    get_profile,
    save_profile
)


profile_api = Blueprint(
    "profile_api",
    __name__,
    url_prefix="/api/student-profiles"
)


# ==========================================
# 1. MERKEZİ PROFİL ŞEMASI
# ==========================================

@profile_api.get("/schema")
def get_schema():

    return jsonify({
        "schema": PROFILE_SCHEMA
    })


# ==========================================
# 2. ÖĞRENCİ LİSTESİ
# ==========================================

@profile_api.get("")
def get_students():

    try:

        students = list_students()

        return jsonify({
            "students": students
        })

    except Exception:

        current_app.logger.exception(
            "Öğrenci listesi okunamadı."
        )

        return jsonify({
            "error": "Öğrenci listesi yüklenemedi."
        }), 500


# ==========================================
# 3. ÖĞRENCİ PROFİLİ OKUMA
# ==========================================

@profile_api.get("/<student_id>")
def get_student(student_id):

    try:

        profile = get_profile(student_id)

        if profile is None:

            return jsonify({
                "error": "Öğrenci profili bulunamadı."
            }), 404

        return jsonify({
            "profile": profile
        })

    except Exception:

        current_app.logger.exception(
            "Öğrenci profili okunamadı."
        )

        return jsonify({
            "error": "Öğrenci profili yüklenemedi."
        }), 500


# ==========================================
# 4. ÖĞRENCİ PROFİLİ KAYDETME
# ==========================================

@profile_api.post("/save")
def save_student():

    if not request.is_json:

        return jsonify({
            "error": "JSON biçiminde veri gönderilmelidir."
        }), 415

    profile = request.get_json(silent=True)

    if not isinstance(profile, dict):

        return jsonify({
            "error": "Geçersiz öğrenci profili."
        }), 400

    try:

        is_new = not profile.get("id")

        saved_profile = save_profile(profile)

        return jsonify({
            "success": True,
            "message": "Öğrenci profili başarıyla kaydedildi.",
            "profile": saved_profile
        }), 201 if is_new else 200

    except ValueError as error:

        return jsonify({
            "error": str(error)
        }), 400

    except Exception:

        current_app.logger.exception(
            "Öğrenci profili kaydedilemedi."
        )

        return jsonify({
            "error": "Profil kaydedilirken sunucu hatası oluştu."
        }), 500


# ==========================================
# 5. PROFİL VERİLERİNİN ÖNBELLEK KONTROLÜ
# ==========================================

@profile_api.after_request
def disable_profile_cache(response):

    response.headers["Cache-Control"] = (
        "no-store, max-age=0"
    )

    return response
