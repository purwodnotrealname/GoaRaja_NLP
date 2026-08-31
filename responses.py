import json
import logging
from pathlib import Path

from deep_translator import GoogleTranslator

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent
DATA_PATH = BASE_DIR / "data.json"

with open(DATA_PATH, "r", encoding="utf-8") as f:
    _data = json.load(f)

# Cache terjemahan Indonesia -> Inggris. Key: teks asli (id), Value: hasil translate (en).
# Diisi lazy oleh _t(), supaya string yang sama tidak di-translate berulang kali
# dan supaya kegagalan translate (mis. tidak ada internet) hanya terjadi sekali
# per string, bukan setiap kali user chat.
_translation_cache: dict[str, str] = {}
_translator = GoogleTranslator(source="id", target="en")


def _t(text: str, lang: str) -> str:
    """Translate teks id -> en kalau lang == 'en', pakai cache. Kalau gagal, kembalikan teks asli."""
    if lang != "en" or not text:
        return text

    if text in _translation_cache:
        return _translation_cache[text]

    try:
        translated = _translator.translate(text)
        if not translated:
            translated = text
    except Exception as e:
        logger.warning(f"Translate gagal untuk teks '{text[:50]}...': {e}")
        translated = text

    _translation_cache[text] = translated
    return translated


def get_data() -> dict:
    return _data


def reload_data() -> None:
    global _data
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        _data = json.load(f)
    _translation_cache.clear()
    logger.info("data.json berhasil di-reload ke memory, translation cache direset.")


def _format_foto() -> str | None:
    """Return path foto sapaan untuk command /start, atau None kalau tidak ada.

    Dipanggil langsung oleh start() di bot.py, di luar alur intent
    classification. Berbeda dari _format_denah(), fungsi ini hanya
    mengembalikan path (bukan tuple) karena caption-nya sudah didefinisikan
    sendiri oleh start().
    """
    foto = _data.get("foto", [])
    if not foto:
        return None

    photo_path = BASE_DIR / foto[0]
    if not photo_path.is_file():
        logger.warning(f"File foto sapaan tidak ditemukan di '{photo_path}'.")
        return None

    return str(photo_path)


def _format_tarif(lang: str = "id") -> str:
    tarif = _data.get("tarif", {})
    dewasa = tarif.get("dewasa", 0)
    anak = tarif.get("anak", 0)
    catatan = tarif.get("catatan", "")

    label_dewasa = "Adult" if lang == "en" else "Dewasa"
    label_anak = "Child" if lang == "en" else "Anak"

    if dewasa or anak:
        parts = []
        if dewasa:
            parts.append(f"{label_dewasa}: Rp{dewasa:,}".replace(",", "."))
        if anak:
            parts.append(f"{label_anak}: Rp{anak:,}".replace(",", "."))
        harga = "\n".join(parts)
    elif catatan:
        # "catatan" bisa berupa harga polos ("Rp.25000") atau kalimat bebas.
        # Angka/harga tidak perlu di-translate; hanya diberi label sesuai bahasa.
        label = "Entrance fee" if lang == "en" else "Harga tiket masuk"
        harga = f"{label}: {catatan}"
    else:
        harga = "Ticket price information is not yet available." if lang == "en" else "Informasi harga belum tersedia."

    return harga


def _format_jam_operasional(lang: str = "id") -> str:
    jam = _data.get("jam_operasional", {})
    if not jam:
        return "Operating hours information is not yet available." if lang == "en" else "Informasi jam operasional belum tersedia."

    _HARI_EN = {
        "senin": "Monday", "selasa": "Tuesday", "rabu": "Wednesday",
        "kamis": "Thursday", "jumat": "Friday", "sabtu": "Saturday", "minggu": "Sunday",
    }

    lines = []
    for hari, waktu in jam.items():
        if lang == "en":
            # Terjemahkan tiap segmen nama hari (mis. "senin_jumat" -> "Monday-Friday")
            segmen = [_HARI_EN.get(h, h.title()) for h in hari.split("_")]
            label_hari = "-".join(segmen)
        else:
            label_hari = hari.replace("_", "-").title()
        lines.append(f"{label_hari}: {waktu}")

    return "\n".join(lines)


def _format_fasilitas(lang: str = "id") -> str:
    fasilitas = _data.get("fasilitas", [])
    if not fasilitas:
        return "Facilities information is not yet available." if lang == "en" else "Informasi fasilitas belum tersedia."

    judul = "Available facilities:" if lang == "en" else "Fasilitas yang tersedia:"
    items = "\n".join(f"- {_t(f, lang)}" for f in fasilitas)
    return f"{judul}\n{items}"


def _format_lokasi(lang: str = "id") -> str:
    lokasi = _data.get("lokasi", {})
    default_alamat = "Address not yet available." if lang == "en" else "Alamat belum tersedia."
    alamat = lokasi.get("alamat", default_alamat)
    maps = lokasi.get("maps", "")

    label = "Location" if lang == "en" else "Lokasi"
    teks = f"{label}: {alamat}"
    if maps:
        teks += f"\nGoogle Maps: {maps}"
    return teks


def _format_denah(lang: str = "id") -> tuple[str, str | None]:
    denah = _data.get("Denah", [])
    fallback_text = "Site map information is not yet available." if lang == "en" else "Informasi denah belum tersedia."
    if not denah:
        return fallback_text, None

    photo_path = BASE_DIR / denah[0]
    if not photo_path.is_file():
        logger.warning(f"File denah tidak ditemukan di '{photo_path}'.")
        return fallback_text, None

    caption = "Here is the site map of Goa Raja Waterfall:" if lang == "en" else "Berikut denah lokasi Air Terjun Goa Raja:"
    return caption, str(photo_path)


def _format_overview(lang: str = "id") -> str:
    info = _data.get("info_umum", {})
    nama = info.get("nama", "")
    deskripsi = info.get("deskripsi", [])

    if deskripsi:
        teks_deskripsi = "\n\n".join(_t(d, lang) for d in deskripsi)
    else:
        teks_deskripsi = "Description not yet available." if lang == "en" else "Deskripsi belum tersedia."

    if nama:
        return f"{nama}\n\n{teks_deskripsi}"
    return teks_deskripsi


def _format_kontak_sosial(lang: str = "id") -> str:
    kontak = _data.get("kontak", {})
    ig = kontak.get("Instagram", "")
    if not ig:
        return "Social media information is not yet available." if lang == "en" else "Informasi media sosial belum tersedia."

    nama = kontak.get("nama", "")
    telepon = kontak.get("telepon", "")

    if not telepon:
        if lang == "en":
            pengelola = _t(nama, lang) if nama else "the management"
            return (
                f"Phone contact for {pengelola} is not yet available. "
                "Please reach out via our official Instagram."
            )
        return (
            f"Untuk saat ini kontak telepon {nama or 'pengelola'} belum tersedia. "
            "Silakan hubungi melalui Instagram resmi kami."
        )

    if lang == "en":
        pengelola = _t(nama, lang) if nama else nama
        return f"Instagram: {ig}\nContact {pengelola}:\nPhone/WA: {telepon}"
    return f"Instagram: {ig} Kontak {nama}:\nTelepon/WA: {telepon}"


_INTENT_HANDLERS = {
    1: _format_overview,
    2: _format_lokasi,
    3: _format_fasilitas,
    4: _format_denah,
    5: _format_jam_operasional,
    6: _format_tarif,
    7: _format_kontak_sosial,
}

_FALLBACK_RESPONSE = {
    "id": (
        "Maaf, saya belum bisa memahami pertanyaan Anda. "
        "Silakan tanyakan seputar lokasi, tarif, jam operasional, fasilitas, "
        "denah, atau kontak Goa Raja."
    ),
    "en": (
        "Sorry, I couldn't understand your question. "
        "Feel free to ask about Goa Raja's location, ticket prices, operating hours, "
        "facilities, site map, or contact info."
    ),
}


def get_static_response(intent: int, lang: str = "id") -> tuple[str, str | None]:
    """Return (text, photo_path). photo_path is None for text-only intents.

    lang: "id" (default) atau "en". Nilai lain diperlakukan sebagai "id".
    """
    if lang not in ("id", "en"):
        lang = "id"

    handler = _INTENT_HANDLERS.get(intent)
    if handler is None:
        logger.warning(f"Intent {intent} tidak memiliki handler, menggunakan fallback.")
        return _FALLBACK_RESPONSE[lang], None

    try:
        result = handler(lang)
        if isinstance(result, tuple):
            return result
        return result, None
    except Exception as e:
        logger.error(f"Gagal memformat respons untuk intent {intent} (lang={lang}): {e}")
        return _FALLBACK_RESPONSE[lang], None