INTENT_CLASSIFICATION_PROMPT = """Klasifikasikan pertanyaan tourist ke SATU angka kategori (1-7). Jawab HANYA angka, tanpa titik/teks lain.

Kategori:
1 = deskripsi tempat (apa itu tempat ini, sejarah, ciri-ciri umum)
2 = lokasi/alamat/cara ke sana (dari luar lokasi menuju ke sana)
3 = fasilitas yang tersedia (toilet, parkir, warung, mushola, dll)
4 = denah/peta area DI DALAM lokasi wisata (rute jalan setelah sampai di lokasi)
5 = jam operasional (buka/tutup, jam terakhir masuk)
6 = harga tiket masuk (HTM, diskon)
7 = kontak (telepon/WA/Instagram/medsos pengelola)

Jika pertanyaan tidak jelas cocok ke kategori manapun, pilih kategori yang paling mendekati maksudnya.

Q: "{user_question}" ->"""