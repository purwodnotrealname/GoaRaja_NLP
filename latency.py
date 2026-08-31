import time
from intent_classifier import classify_intent

try:
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

test_cases = [
    # --- Kategori 1: info umum/deskripsi tempat ---
    ("apa itu goa raja?", 1, "info_umum"),
    ("goa raja adalah wisata apa?", 1, "info_umum"),
    ("deskripsikan goa raja", 1, "info_umum"),
    ("ceritakan tentang goa raja dong", 1, "info_umum"),
    ("sejarah singkat goa raja", 1, "info_umum"),
    ("kenapa dinamain goa raja?", 1, "info_umum"),
    ("ini tempat wisata alam atau buatan manusia?", 1, "info_umum"),
    ("objek wisata ini seperti apa sih", 1, "info_umum"),
    ("goa raja itu terkenal karena apa", 1, "info_umum"),
    ("boleh jelasin sedikit soal tempat ini", 1, "info_umum"),
    ("goa raja termasuk situs bersejarah bukan?", 1, "info_umum"),
    ("info umum tentang goa raja", 1, "info_umum"),
    ("apa keunikan dari goa raja?", 1, "info_umum"),

    # --- Kategori 2: lokasi/alamat/cara ke sana ---
    ("di mana lokasi dari tempat wisata?", 2, "lokasi"),
    ("titik lokasi di google maps apa?", 2, "lokasi"),
    ("tunjukkan alamat goa raja", 2, "lokasi"),
    ("rute menuju goa raja", 2, "lokasi"),
    ("goa raja ada di mana?", 2, "lokasi"),
    ("gimana cara ke sana dari desa jehem", 2, "lokasi"),
    ("koordinat google mapsnya ada?", 2, "lokasi"),
    ("dmn lokasinya kak", 2, "lokasi"),
    ("dari denpasar berapa jam ke sana", 2, "lokasi"),
    ("alamat lengkapnya apa", 2, "lokasi"),
    ("dimana?", 2, "lokasi"),
    ("alamat dimana", 2, "lokasi"),
    ("kalau naik motor dari ubud berapa lama sampai sana", 2, "lokasi"),

    # --- Kategori 3: fasilitas yang tersedia ---
    ("fasilitas apa saja yang disediakan di sana?", 3, "fasilitas"),
    ("bisa sewa loker ga di sana", 3, "fasilitas"),
    ("apakah ada toilet di sana?", 3, "fasilitas"),
    ("fasilitas wisata apa saja yang ada?", 3, "fasilitas"),
    ("apakah ada restoran di dalam?", 3, "fasilitas"),
    ("di sana ada toilet ga?", 3, "fasilitas"),
    ("ada tempat parkir?", 3, "fasilitas"),
    ("ada warung atau tempat makan ga di sana", 3, "fasilitas"),
    ("kalo mau sholat ada mushola?", 3, "fasilitas"),
    ("ada tempat sampah ga di area wisata", 3, "fasilitas"),
    ("apakah tersedia gazebo buat istirahat", 3, "fasilitas"),
    ("ada penyewaan alat snorkeling atau camping?", 3, "fasilitas"),
    ("fasilitas untuk difabel ada ga", 3, "fasilitas"),

    # --- Kategori 4: denah/peta area di dalam lokasi wisata ---
    ("boleh minta denah lokasinya", 4, "denah_dalam"),
    ("peta area dalam goa raja gimana", 4, "denah_dalam"),
    ("layout tempatnya kaya gimana", 4, "denah_dalam"),
    ("ada denah biar ga nyasar di dalam", 4, "denah_dalam"),
    ("gambar rute jalan di area wisatanya ada?", 4, "denah_dalam"),
    ("dari pintu masuk ke goa nya jalan ke arah mana", 4, "denah_dalam"),
    ("ada denah jalur trekking di dalam kawasan?", 4, "denah_dalam"),
    ("tolong kirim peta lokasi wisata bagian dalamnya", 4, "denah_dalam"),
    ("posisi mushola di dalam area itu di mana ya, ada petanya?", 4, "denah_dalam"),
    ("susunan area dalam goa raja kaya gimana, ada gambarnya?", 4, "denah_dalam"),
    ("jalur dari parkiran ke goa lewat mana aja", 4, "denah_dalam"),

    # --- Kategori 5: jam operasional ---
    ("Goa Raja buka jam berapa?", 5, "jam_operasional"),
    ("kapan goa raja dibuka untuk umum?", 5, "jam_operasional"),
    ("jam operasional hari minggu", 5, "jam_operasional"),
    ("jam tutup goa raja", 5, "jam_operasional"),
    ("buka jam berapa?", 5, "jam_operasional"),
    ("hari senin buka ga?", 5, "jam_operasional"),
    ("jam berapa terakhir masuk", 5, "jam_operasional"),
    ("weekend buka jam berapaan", 5, "jam_operasional"),
    ("libur nasional tetap buka ga?", 5, "jam_operasional"),
    ("jam berapa paling pagi bisa masuk", 5, "jam_operasional"),
    ("operasionalnya setiap hari atau ada hari tutup?", 5, "jam_operasional"),
    ("malem masih buka ga tempatnya", 5, "jam_operasional"),

    # --- Kategori 6: harga tiket masuk ---
    ("saya ingin tahu harga masuk goa raja", 6, "harga_tiket"),
    ("tiket masuknya berapa?", 6, "harga_tiket"),
    ("berapakah biaya parkir dan tiket masuk?", 6, "harga_tiket"),
    ("harga tiket anak-anak", 6, "harga_tiket"),
    ("harga masuknya berapa?", 6, "harga_tiket"),
    ("tiket buat anak-anak berapa?", 6, "harga_tiket"),
    ("berapaan sih HTMnya", 6, "harga_tiket"),
    ("ada diskon rombongan ga", 6, "harga_tiket"),
    ("turis asing bayar berapa buat masuk", 6, "harga_tiket"),
    ("biaya masuk weekend beda ga sama weekday", 6, "harga_tiket"),
    ("kalau bawa kamera ada tambahan biaya ga", 6, "harga_tiket"),
    ("berapa harga tiket terusan kalau mau ke goa lain juga", 6, "harga_tiket"),

    # --- Kategori 7: kontak (telepon/WA/Instagram/medsos) ---
    ("apakah ada nomor yang bisa dihubungi?", 7, "kontak"),
    ("ada kontak pengelola yang bisa ditelpon?", 7, "kontak"),
    ("berapa nomor telponnya?", 7, "kontak"),
    ("kontak whatsapp pengelola", 7, "kontak"),
    ("email atau nomor telepon", 7, "kontak"),
    ("ada instagram resmi?", 7, "kontak"),
    ("medsosnya apa aja", 7, "kontak"),
    ("ada nomor wa yang bisa dihubungi?", 7, "kontak"),
    ("kontak pengelola gimana", 7, "kontak"),
    ("boleh telpon ga buat nanya-nanya", 7, "kontak"),
    ("kalau mau booking rombongan hubungi siapa ya", 7, "kontak"),
    ("ada facebook atau twitter resmi ga", 7, "kontak"),

    ("what is goa raja?", 1, "general_info"),
    ("what kind of tourist spot is goa raja?", 1, "general_info"),
    ("describe goa raja", 1, "general_info"),
    ("tell me about goa raja", 1, "general_info"),
    ("brief history of goa raja", 1, "general_info"),
    ("why is it called goa raja?", 1, "general_info"),
    ("is this a natural or man-made attraction?", 1, "general_info"),
    ("what is this tourist attraction like", 1, "general_info"),
    ("what is goa raja famous for", 1, "general_info"),
    ("can you explain a bit about this place", 1, "general_info"),
    ("is goa raja a historical site?", 1, "general_info"),
    ("general info about goa raja", 1, "general_info"),
    ("what makes goa raja unique?", 1, "general_info"),
 
    # --- Category 2: location/address/how to get there ---
    ("where is the tourist attraction located?", 2, "location"),
    ("what's the google maps pin?", 2, "location"),
    ("show me the address of goa raja", 2, "location"),
    ("route to goa raja", 2, "location"),
    ("where is goa raja located?", 2, "location"),
    ("how do i get there from jehem village", 2, "location"),
    ("is there a google maps coordinate?", 2, "location"),
    ("where's it located", 2, "location"),
    ("how many hours from denpasar to get there", 2, "location"),
    ("what's the full address", 2, "location"),
    ("where is it?", 2, "location"),
    ("what's the address", 2, "location"),
    ("how long by motorbike from ubud to get there", 2, "location"),
 
    # --- Category 3: available facilities ---
    ("what facilities are provided there?", 3, "facilities"),
    ("can you rent a locker there", 3, "facilities"),
    ("is there a restroom there?", 3, "facilities"),
    ("what tourist facilities are available?", 3, "facilities"),
    ("is there a restaurant inside?", 3, "facilities"),
    ("is there a toilet there?", 3, "facilities"),
    ("is there a parking area?", 3, "facilities"),
    ("is there a food stall or eatery there", 3, "facilities"),
    ("is there a prayer room if i want to pray", 3, "facilities"),
    ("is there a trash bin in the tourist area", 3, "facilities"),
    ("is there a gazebo available to rest", 3, "facilities"),
    ("is there snorkeling or camping gear rental?", 3, "facilities"),
    ("are there facilities for people with disabilities", 3, "facilities"),
 
    # --- Category 4: site map/layout inside the location ---
    ("can i get a site map", 4, "site_map"),
    ("what's the internal area map of goa raja like", 4, "site_map"),
    ("what's the layout of the place like", 4, "site_map"),
    ("is there a map so i don't get lost inside", 4, "site_map"),
    ("is there a route map of the tourist area?", 4, "site_map"),
    ("which direction from the entrance to the cave", 4, "site_map"),
    ("is there a trekking trail map within the area?", 4, "site_map"),
    ("please send the interior site map", 4, "site_map"),
    ("where is the prayer room inside the area, is there a map?", 4, "site_map"),
    ("what's the layout of goa raja's interior, any pictures?", 4, "site_map"),
    ("which path goes from the parking lot to the cave", 4, "site_map"),
 
    # --- Category 5: opening hours ---
    ("what time does goa raja open?", 5, "opening_hours"),
    ("when does goa raja open to the public?", 5, "opening_hours"),
    ("operating hours on sunday", 5, "opening_hours"),
    ("what time does goa raja close", 5, "opening_hours"),
    ("what time does it open?", 5, "opening_hours"),
    ("is it open on mondays?", 5, "opening_hours"),
    ("what time is the last entry", 5, "opening_hours"),
    ("what time does it open on weekends", 5, "opening_hours"),
    ("is it still open on national holidays?", 5, "opening_hours"),
    ("what's the earliest time i can enter", 5, "opening_hours"),
    ("is it open every day or are there closed days?", 5, "opening_hours"),
    ("is the place still open at night", 5, "opening_hours"),
 
    # --- Category 6: entrance ticket price ---
    ("i want to know the entrance fee for goa raja", 6, "ticket_price"),
    ("how much is the entrance ticket?", 6, "ticket_price"),
    ("how much are parking and entrance fees?", 6, "ticket_price"),
    ("ticket price for children", 6, "ticket_price"),
    ("how much is the entrance fee?", 6, "ticket_price"),
    ("how much is a ticket for kids?", 6, "ticket_price"),
    ("how much is the entrance ticket price", 6, "ticket_price"),
    ("is there a group discount", 6, "ticket_price"),
    ("how much do foreign tourists pay to enter", 6, "ticket_price"),
    ("is the weekend entrance fee different from weekdays", 6, "ticket_price"),
    ("is there an extra charge for bringing a camera", 6, "ticket_price"),
    ("how much is a combo ticket to visit other caves too", 6, "ticket_price"),
 
    # --- Category 7: contact (phone/WA/Instagram/social media) ---
    ("is there a number i can contact?", 7, "contact"),
    ("is there a manager's contact i can call?", 7, "contact"),
    ("what's the phone number?", 7, "contact"),
    ("whatsapp contact for the management", 7, "contact"),
    ("email or phone number", 7, "contact"),
    ("is there an official instagram?", 7, "contact"),
    ("what social media accounts are there", 7, "contact"),
    ("is there a whatsapp number i can contact?", 7, "contact"),
    ("how do i contact the management", 7, "contact"),
    ("can i call to ask some questions", 7, "contact"),
    ("who do i contact to book for a group", 7, "contact"),
    ("is there an official facebook or twitter", 7, "contact"),
]


def print_confusion_matrix(actual_labels, predicted_labels, labels=None):
    if labels is None:
        labels = sorted(set(actual_labels) | set(predicted_labels))

    label_to_index = {label: idx for idx, label in enumerate(labels)}
    matrix = [[0 for _ in labels] for _ in labels]

    for actual, predicted in zip(actual_labels, predicted_labels):
        matrix[label_to_index[actual]][label_to_index[predicted]] += 1

    width = max(5, max(len(str(label)) for label in labels) + 2)
    header = "".rjust(width) + "".join(str(label).rjust(width) for label in labels)
    print("\n=== Confusion Matrix (actual rows, predicted cols) ===")
    print(header)
    for label, row in zip(labels, matrix):
        print(str(label).rjust(width) + "".join(str(value).rjust(width) for value in row))


def plot_confusion_matrix(actual_labels, predicted_labels, labels=None, filename="confusion_matrix.png"):
    if not HAS_MATPLOTLIB:
        print("Matplotlib belum terpasang. Visual confusion matrix tidak dapat dibuat.")
        return

    if labels is None:
        labels = sorted(set(actual_labels) | set(predicted_labels))

    label_to_index = {label: idx for idx, label in enumerate(labels)}
    matrix = [[0 for _ in labels] for _ in labels]
    for actual, predicted in zip(actual_labels, predicted_labels):
        matrix[label_to_index[actual]][label_to_index[predicted]] += 1

    fig, ax = plt.subplots(figsize=(8, 6))
    heatmap = ax.imshow(matrix, cmap="Blues", interpolation="nearest")

    ax.set_xticks(range(len(labels)))
    ax.set_yticks(range(len(labels)))
    ax.set_xticklabels(labels)
    ax.set_yticklabels(labels)
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Actual")
    ax.set_title("Confusion Matrix")

    for i in range(len(labels)):
        for j in range(len(labels)):
            ax.text(j, i, matrix[i][j], ha="center", va="center", color="black")

    fig.colorbar(heatmap, ax=ax)
    plt.tight_layout()
    fig.savefig(filename, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Visual confusion matrix disimpan ke {filename}")


def print_classification_report(actual_labels, predicted_labels, labels=None, label_names=None):
    if not actual_labels:
        print("\n=== Classification Report (precision / recall / F1 per kategori) ===")
        print("Tidak ada data untuk dilaporkan.")
        return

    if labels is None:
        labels = sorted(set(actual_labels) | set(predicted_labels))

    label_to_index = {label: idx for idx, label in enumerate(labels)}
    n = len(labels)
    matrix = [[0 for _ in labels] for _ in labels]
    for actual, predicted in zip(actual_labels, predicted_labels):
        matrix[label_to_index[actual]][label_to_index[predicted]] += 1

    per_class = []
    for idx, label in enumerate(labels):
        tp = matrix[idx][idx]
        support = sum(matrix[idx])
        predicted_as_label = sum(matrix[r][idx] for r in range(n))

        precision = tp / predicted_as_label if predicted_as_label else 0.0
        recall = tp / support if support else 0.0
        f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0

        per_class.append({
            "label": label,
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "support": support,
        })

    total_support = sum(row["support"] for row in per_class)
    macro_precision = sum(row["precision"] for row in per_class) / n if n else 0.0
    macro_recall = sum(row["recall"] for row in per_class) / n if n else 0.0
    macro_f1 = sum(row["f1"] for row in per_class) / n if n else 0.0
    weighted_precision = sum(row["precision"] * row["support"] for row in per_class) / total_support if total_support else 0.0
    weighted_recall = sum(row["recall"] * row["support"] for row in per_class) / total_support if total_support else 0.0
    weighted_f1 = sum(row["f1"] * row["support"] for row in per_class) / total_support if total_support else 0.0
    accuracy = (
        sum(1 for a, p in zip(actual_labels, predicted_labels) if a == p) / len(actual_labels)
        if actual_labels else 0.0
    )

    def display(label):
        if label_names and label in label_names:
            return f"{label} ({label_names[label]})"
        return str(label)

    name_width = max(10, max(len(display(row["label"])) for row in per_class) + 2)
    col_width = 11

    print("\n=== Classification Report (precision / recall / F1 per kategori) ===")
    header = "Kategori".ljust(name_width) + "".join(
        col.rjust(col_width) for col in ["precision", "recall", "f1-score", "support"]
    )
    print(header)
    for row in per_class:
        print(
            display(row["label"]).ljust(name_width)
            + f"{row['precision']:.2f}".rjust(col_width)
            + f"{row['recall']:.2f}".rjust(col_width)
            + f"{row['f1']:.2f}".rjust(col_width)
            + f"{row['support']}".rjust(col_width)
        )
    print()
    print("accuracy".ljust(name_width) + "".rjust(col_width * 2) + f"{accuracy:.2f}".rjust(col_width) + f"{total_support}".rjust(col_width))
    print(
        "macro avg".ljust(name_width)
        + f"{macro_precision:.2f}".rjust(col_width)
        + f"{macro_recall:.2f}".rjust(col_width)
        + f"{macro_f1:.2f}".rjust(col_width)
        + f"{total_support}".rjust(col_width)
    )
    print(
        "weighted avg".ljust(name_width)
        + f"{weighted_precision:.2f}".rjust(col_width)
        + f"{weighted_recall:.2f}".rjust(col_width)
        + f"{weighted_f1:.2f}".rjust(col_width)
        + f"{total_support}".rjust(col_width)
    )


print("=== Stress Test: Akurasi Intent Classification (kasus menantang) ===\n")

correct = 0
results_by_category = {}
exact_actuals = []
exact_predictions = []
ambiguous_cases = 0

for i, (question, expected, category) in enumerate(test_cases, 1):
    start = time.time()
    intent = classify_intent(question)
    elapsed = time.time() - start

    if isinstance(expected, list):
        is_correct = intent in expected
        expected_display = f"salah satu dari {expected}"
        ambiguous_cases += 1
    else:
        is_correct = intent == expected
        expected_display = str(expected)
        exact_actuals.append(expected)
        exact_predictions.append(intent)

    status = "BENAR" if is_correct else "SALAH"
    if is_correct:
        correct += 1

    results_by_category.setdefault(category, {"correct": 0, "total": 0})
    results_by_category[category]["total"] += 1
    if is_correct:
        results_by_category[category]["correct"] += 1

    print(f"Test {i} [{category}]: \"{question}\"")
    print(f"  -> Intent: {intent} (expected: {expected_display}) [{status}]")
    print(f"  -> Waktu: {elapsed:.2f} detik\n")

print(f"=== Total Akurasi: {correct}/{len(test_cases)} ({correct/len(test_cases)*100:.0f}%) ===\n")
print("=== Breakdown per Kategori ===")
for category, stats in results_by_category.items():
    pct = stats["correct"] / stats["total"] * 100
    print(f"  {category}: {stats['correct']}/{stats['total']} ({pct:.0f}%)")

if exact_actuals:
    print_confusion_matrix(exact_actuals, exact_predictions)
    plot_confusion_matrix(exact_actuals, exact_predictions)

    label_names = {}
    for _, expected, category in test_cases:
        if not isinstance(expected, list) and expected not in label_names:
            label_names[expected] = category
    print_classification_report(exact_actuals, exact_predictions, label_names=label_names)

    if ambiguous_cases:
        print(f"\nCatatan: {ambiguous_cases} kasus ambigu dilewati dalam confusion matrix karena label expected berisi beberapa kemungkinan.")