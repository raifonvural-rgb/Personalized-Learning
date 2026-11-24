"""
Öğretmen kontrollü bireyselleştirilmiş öğrenme materyalleri.

Öğrenci profili merkezi alan şeması.
Tanımlanmamış özellikler hakkında varsayım yapılmaz.
"""

def field(key, label, kind="text", options=None, required=False):
    return {
        "key": key,
        "label": label,
        "type": kind,
        "options": options or [],
        "required": required
    }


ABILITY = [
    "Bağımsız yapabilir",
    "Kısmi destekle yapabilir",
    "Yoğun destekle yapabilir",
    "Henüz yapamıyor"
]

YES_NO = ["Evet", "Hayır"]

SUPPORT = [
    "Gerekmiyor",
    "Bazen gerekiyor",
    "Sıklıkla gerekiyor",
    "Her zaman gerekiyor"
]

TOLERANCE = [
    "Uygun",
    "Sınırlı kullanım",
    "Uygun değil"
]

SIZE = [
    "Küçük",
    "Orta",
    "Büyük",
    "Çok büyük"
]

DIGITS = [str(n) for n in range(10)]

COLORS = [
    "Kırmızı", "Mavi", "Yeşil", "Sarı",
    "Turuncu", "Mor", "Pembe", "Beyaz",
    "Siyah", "Gri", "Kahverengi"
]

FEEDBACK = [
    "Yazılı", "Sesli", "Görsel"
]

PROFILE_SCHEMA = [

    {
        "key": "general",
        "title": "Genel Bilgiler",
        "icon": "user",
        "fields": [
            field("name", "Öğrencinin adı ve soyadı",
                  required=True),
            field("age", "Yaşı", "number"),
            field("grade", "Sınıfı / eğitim düzeyi"),
            field("interests", "İlgi alanları", "textarea"),
            field("favorite_objects", "Sevdiği nesneler, hayvanlar ve karakterler", "textarea"),
            field("dislikes", "Sevmediği nesneler ve durumlar", "textarea"),
            field("strengths", "Güçlü yönleri", "textarea"),
            field("observations", "Öğretmenin genel gözlemleri", "textarea")
        ]
    },

    {
        "key": "educational_diagnoses",
        "title": "Eğitsel Tanılar",
        "icon": "clipboard",
        "fields": [
            field(
                "diagnoses",
                "Eğitsel tanılar",
                "multiselect",
                [
                    "Ağır Düzey Zihinsel Yetersizlik (ADZY)",
                    "Bedensel Yetersizlik",
                    "Birden Fazla Yetersizlik",
                    "Dikkat Eksikliği ve Hiperaktivite Bozukluğu (DEHB)",
                    "Dil Konuşma Güçlüğü (DKG)",
                    "Down Sendromu",
                    "Duygusal Davranış Bozukluğu (DDB)",
                    "Epilepsi",
                    "Gelişim Geriliği",
                    "Görme Yetersizliği",
                    "Hafif Düzey Zihinsel Yetersizlik",
                    "Hafif Otizm",
                    "Normal",
                    "Orta Ağır Otizm",
                    "Orta Düzey Zihinsel Yetersizlik (ODZY)",
                    "Serebral Palsi (CP)",
                    "Yaygın Gelişimsel Bozukluk (OTİZM)",
                    "Çok Ağır Düzey Zihinsel Yetersizlik (CADZY)",
                    "Özel Öğrenme Güçlüğü",
                    "Üstün Yetenekli Birey (ÜYB)",
                    "İşitme Yetersizliği"
                ]
            )
        ]
    },

    {
        "key": "visual",
        "title": "Görsel Özellikler",
        "icon": "eye",
        "fields": [
            field("preferred_colors", "Tercih ettiği renkler", "multiselect", COLORS),
            field("avoided_colors", "Rahatsız olduğu renkler", "multiselect", COLORS),
            field("background_color", "Tercih edilen arka plan rengi", "color"),
            field("text_size", "Yazı ve rakam büyüklüğü", "select", SIZE),
            field("complexity", "Görsel karmaşıklık", "select",
                  ["Sade", "Orta", "Ayrıntılı"]),
            field("max_objects", "Ekranda aynı anda sunulabilecek nesne sayısı", "number"),
            field("moving_images", "Hareketli görsellere toleransı", "select", TOLERANCE),
            field("animation", "Animasyon kullanımına uygunluk", "select", TOLERANCE),
            field("image_types", "Tercih edilen görsel türleri", "multiselect",
                  ["Fotoğraf", "Çizim", "Sembol", "Piktogram"]),
            field("contrast", "Işık ve kontrast hassasiyeti", "textarea"),
            field("other", "Diğer görsel gereksinimler", "textarea")
        ]
    },

    {
        "key": "auditory",
        "title": "İşitsel Özellikler",
        "icon": "volume",
        "fields": [
            field("spoken_instructions", "Sesli yönerge kullanımına uygunluk", "select", TOLERANCE),
            field("volume", "Tercih edilen ses düzeyi", "select",
                  ["Düşük", "Orta", "Yüksek"]),
            field("speech_rate", "Konuşma hızı", "select",
                  ["Çok yavaş", "Yavaş", "Normal", "Hızlı"]),
            field("voice", "Ses tercihi", "select",
                  ["Kadın", "Erkek", "Fark etmez"]),
            field("instruction_repetition", "Yönergelerin tekrarlanma gereksinimi", "select", SUPPORT),
            field("music", "Müzik kullanımına uygunluk", "select", TOLERANCE),
            field("sound_effects", "Ses efektlerine toleransı", "select", TOLERANCE),
            field("loud_sounds", "Ani ve yüksek seslere hassasiyeti", "select", YES_NO),
            field("avoided_sounds", "Rahatsız olduğu sesler", "textarea"),
            field("other", "Diğer işitsel gereksinimler", "textarea")
        ]
    },

    {
        "key": "motor",
        "title": "Motor Beceriler",
        "icon": "hand",
        "fields": [
            field("dominant_hand", "Tercih ettiği el", "select",
                  ["Sağ", "Sol", "Her ikisi"]),
            field("right_hand", "Sağ elini kullanabilme düzeyi", "select", ABILITY),
            field("left_hand", "Sol elini kullanabilme düzeyi", "select", ABILITY),
            field("mouse", "Fare kullanabilme becerisi", "select", ABILITY),
            field("touchscreen", "Dokunmatik ekran kullanabilme becerisi", "select", ABILITY),
            field("keyboard", "Klavye kullanabilme becerisi", "select", ABILITY),
            field("drag_drop", "Sürükle-bırak yapabilme becerisi", "select", ABILITY),
            field("pencil", "Kalem kullanabilme becerisi", "select", ABILITY),
            field("tracing", "Çizgi ve nokta takip edebilme becerisi", "select", ABILITY),
            field("button_size", "Tercih edilen düğme büyüklüğü", "select", SIZE),
            field("interaction_position", "Etkileşim alanlarının konumu", "select",
                  ["Sağ", "Sol", "Orta", "Fark etmez"]),
            field("other", "Diğer fiziksel gereksinimler", "textarea")
        ]
    },

    {
        "key": "communication",
        "title": "Dil ve İletişim",
        "icon": "message",
        "fields": [
            field("verbal", "Sözel iletişim becerisi", "select", ABILITY),
            field("spoken_comprehension", "Sözel yönergeleri anlama becerisi", "select", ABILITY),
            field("written_comprehension", "Yazılı yönergeleri anlama becerisi", "select", ABILITY),
            field("visual_comprehension", "Görsel yönergeleri anlama becerisi", "select", ABILITY),
            field("reading", "Okuma becerisi", "select", ABILITY),
            field("writing", "Yazma becerisi", "select", ABILITY),
            field("communication_methods", "Tercih edilen iletişim yöntemleri", "multiselect",
                  ["Konuşma", "Yazı", "Görsel", "İşaret", "Sembol", "Destekleyici iletişim"]),
            field("assistive_tools", "Alternatif ve destekleyici iletişim araçları", "textarea"),
            field("language_complexity", "Yönergelerde kullanılacak dil", "select",
                  ["Çok basit", "Basit", "Orta", "Ayrıntılı"]),
            field("instruction_steps", "Yönerge yapısı", "select",
                  ["Tek aşamalı", "İki aşamalı", "Çok aşamalı"]),
            field("response_time", "Yanıt vermek için ihtiyaç duyduğu süre", "text"),
            field("other", "Diğer iletişim gereksinimleri", "textarea")
        ]
    },

    {
        "key": "learning",
        "title": "Dikkat ve Öğrenme",
        "icon": "brain",
        "fields": [
            field("attention_minutes", "Tahmini dikkat süresi (dakika)", "number"),
            field("activity_minutes", "Tercih edilen etkinlik süresi (dakika)", "number"),
            field("breaks", "Mola gereksinimi", "select", SUPPORT),
            field("break_minutes", "Tercih edilen mola süresi (dakika)", "number"),
            field("repetition", "Tekrar gereksinimi", "select", SUPPORT),
            field("max_choices", "Aynı anda sunulabilecek seçenek sayısı", "number"),
            field("demonstration", "Örnek gösterilerek öğrenme tercihi", "select", YES_NO),
            field("visual_model", "Görsel model kullanımına uygunluk", "select", TOLERANCE),
            field("video_model", "Video model kullanımına uygunluk", "select", TOLERANCE),
            field("prompts", "İpucu gereksinimi", "select", SUPPORT),
            field("prompt_fading", "İpuçlarının aşamalı azaltılması", "select", YES_NO),
            field("transition_support", "Yeni etkinliklere geçişte destek gereksinimi", "select", SUPPORT),
            field("distractions", "Dikkatini dağıtan unsurlar", "textarea"),
            field("learning_facilitators", "Öğrenmeyi kolaylaştıran unsurlar", "textarea")
        ]
    },

    {
        "key": "motivation",
        "title": "Motivasyon ve Geri Bildirim",
        "icon": "star",
        "fields": [
            field("reinforcers", "Tercih edilen olumlu pekiştireçler", "textarea"),
            field("rewards", "Sevdiği ödüller", "textarea"),
            field("feedback_types", "Olumlu geri bildirim biçimleri", "multiselect", FEEDBACK),
            field("positive_messages", "Olumlu geri bildirim ifadeleri", "textarea"),
            field("retry_messages", "Yanlış cevapta kullanılacak ifadeler", "textarea"),
            field("retry_preference", "Yanlış cevapta yeniden deneme tercihi", "select", YES_NO),
            field("attempts_before_hint", "İpucu verilmeden önceki deneme sayısı", "number"),
            field("applause", "Alkış sesi kullanımına uygunluk", "select", TOLERANCE),
            field("visual_rewards", "Yıldız ve rozet kullanımına uygunluk", "select", TOLERANCE),
            field("avoided_feedback", "Kaçınılması gereken geri bildirimler", "textarea")
        ]
    },

    {
        "key": "sensory_emotional",
        "title": "Duyusal ve Duygusal Gereksinimler",
        "icon": "heart",
        "fields": [
            field("anxiety_triggers", "Kaygıya neden olan durumlar", "textarea"),
            field("uncomfortable_stimuli", "Rahatsızlık yaratan uyaranlar", "textarea"),
            field("calming_factors", "Sakinleşmesini sağlayan unsurlar", "textarea"),
            field("time_limits", "Zaman sınırlamasına toleransı", "select", TOLERANCE),
            field("unexpected_changes", "Beklenmedik ekran değişikliklerine toleransı", "select", TOLERANCE),
            field("transition_warning", "Etkinlik geçişlerinin önceden bildirilmesi", "select", YES_NO),
            field("failure_support", "Başarısızlık durumunda destek gereksinimi", "textarea"),
            field("stop_conditions", "Etkinliğe ara verilmesini gerektiren durumlar", "textarea"),
            field("other", "Diğer duyusal ve duygusal gereksinimler", "textarea")
        ]
    },

    {
        "key": "academic",
        "title": "Akademik Beceriler",
        "icon": "book",
        "fields": [
            field("recognized_digits", "Tanıyabildiği rakamlar", "multiselect", DIGITS),
            field("spoken_digits", "Söyleyebildiği rakamlar", "multiselect", DIGITS),
            field("written_digits", "Yazabildiği rakamlar", "multiselect", DIGITS),
            field("recognized_number_range", "Tanıyabildiği sayı aralığı"),
            field("spoken_number_range", "Söyleyebildiği sayı aralığı"),
            field("written_number_range", "Yazabildiği sayı aralığı"),
            field("independent_activities", "Bağımsız yapabildiği etkinlikler", "textarea"),
            field("supported_activities", "Yardımla yapabildiği etkinlikler", "textarea"),
            field("difficult_activities", "Zorlandığı etkinlikler", "textarea"),
            field("learning_goals", "Öncelikli öğrenme hedefleri", "textarea")
        ]
    },

    {
        "key": "custom_requirements",
        "title": "Ek Bireysel Gereksinimler",
        "icon": "plus",
        "repeatable": True,
        "fields": [
            field("name", "Özellik / gereksinim adı"),
            field("description", "Ayrıntılı açıklama", "textarea"),
            field("priority", "Uygulama önceliği", "select",
                  [
                      "Zorunlu gereksinim",
                      "Tercih edilen özellik",
                      "Genel gözlem"
                  ])
        ]
    }

]


if __name__ == "__main__":
    print("Öğrenci profili şeması başarıyla oluşturuldu.")
    print("-" * 65)

    total = 0

    for index, section in enumerate(PROFILE_SCHEMA, start=1):
        count = len(section["fields"])
        total += count
        print(f"{index:2}. {section['title']}: {count} alan")

    print("-" * 65)
    print(f"Toplam bölüm: {len(PROFILE_SCHEMA)}")
    print(f"Toplam alan tanımı: {total}")
