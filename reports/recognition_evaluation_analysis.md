# Analisis kualitas evaluasi klasifikasi ECUSTFD

## Cakupan dan validasi artefak

Audit ini menggunakan laporan dan confusion matrix/classification report yang telah ada. Tidak ada training, inferensi ulang, penggunaan test set, atau perubahan manifest/checkpoint.

Ketiga confusion matrix berukuran 19×19 dan masing-masing berjumlah 350, sesuai jumlah validation crop. Tiap classification report memiliki 19 kelas serta macro dan weighted average. Urutan label adalah urutan kelas checkpoint yang konsisten. Kelas `grape` dan `lemon` memiliki dukungan nol; skor per kelas dibiarkan kosong/N/A, bukan dianggap nol.

Perhitungan macro dan weighted average diverifikasi ulang dari nilai per kelas yang tersimpan. Macro merata-ratakan 17 kelas dengan dukungan positif; weighted average membobot nilai tiap kelas tersebut dengan jumlah sampelnya. Nilainya cocok dengan laporan:

| Model | Macro P / R / F1 | Weighted P / R / F1 |
|---|---|---|
| MobileNetV2 | 0.9030 / 0.9048 / 0.8887 | 0.9164 / 0.8657 / 0.8700 |
| EfficientNet-B0 | 0.9573 / 0.9659 / 0.9600 | 0.9722 / 0.9686 / 0.9695 |
| ResNet-50 | 0.7553 / 0.7110 / 0.6869 | 0.8054 / 0.7029 / 0.7064 |

**Keterbatasan metrik kelas tak terdukung:** MobileNetV2 memprediksi satu sampel sebagai `lemon`, sedangkan tidak ada label lemon sebenarnya; ResNet-50 memprediksi lemon empat kali. Semua skor per kelas lemon tetap N/A sesuai kebijakan evaluasi. Namun, karena kelas tanpa dukungan dikeluarkan dari macro dan weighted average, false positive ke lemon tidak menurunkan precision/F1 average tersebut secara langsung. Kesalahan itu tetap memengaruhi accuracy (sampel sebenarnya dihitung salah). Jumlah prediksi kelas kosong sebaiknya disajikan eksplisit atau protokol skor nol-kelas disepakati sebelum evaluasi lanjutan.

## Kelas lemah dan kebingungan

Skor di bawah merujuk hanya pada kelas dengan dukungan validation positif. Kelas berdukungan kecil menghasilkan estimasi yang tidak stabil.

- **MobileNetV2 (47 salah dari 350):** precision/F1 terendah pada peach (0.429 / 0.588); recall terendah pada plum (0.500), lalu pear (0.750). Kebingungan terbesar adalah plum→apple (13), plum→peach (8), dan pear→peach (7). Mango juga sering tertukar ke peach (2).
- **EfficientNet-B0 (11 salah):** bun terlemah (precision 0.636, recall 0.875, F1 0.737); recall qiwi 0.889. Kebingungan terbesar pear→bun (2). Sisanya tersebar satu sampel per pasangan, termasuk tomato→bun, qiwi→bun, peach→apple, dan fired_dough_twist→litchi.
- **ResNet-50 (104 salah):** doughnut terlemah (precision 0.062, recall 0.167, F1 0.091); litchi recall 0.286 dan bread recall 0.375. Kebingungan terbesar plum→apple (22), pear→bun (13), mooncake→doughnut (13), serta sachima→fired_dough_twist (6).

## Pemeriksaan split dan risiko kebocoran

Manifest berisi 942 crop train pada 62 grup dan 350 crop validation pada 20 grup. Audit menemukan nol `group_id` yang muncul di kedua split, nol `image_id` overlap, dan semua crop dari sebuah image berada dalam split yang sama.

Kode membentuk grup lewat regex `^(.+?\d+)[ST]\(\d+\)$`: akhiran view `S`/`T` dan nomor frame dibuang sehingga citra seperti `apple001S(1)` dan `apple001T(1)` berbagi grup `apple001`. Ini mencegah kebocoran antar-view/shot untuk prefix yang sama. Jaminannya tetap bergantung pada konvensi nama file: manifest tidak membuktikan bahwa prefix berbeda selalu berarti objek fisik berbeda, dan split validation kecil ini tidak membuktikan generalisasi ke objek atau kondisi pengambilan baru. Split dibuat dari trainval; test resmi tidak dibaca atau dipakai.

## Waktu inference

Waktu yang dilaporkan evaluator adalah waktu satu lintasan atas 350 crop pada RTX 3060, diukur dengan `perf_counter`, sinkronisasi CUDA sebelum dan sesudah, serta mencakup pembacaan gambar, crop PIL, resize/normalisasi, transfer batch, dan forward pass. Loader memakai urutan tetap, batch 16, `num_workers=0`, dan ketiga model memakai perangkat/proses yang sama. Catatan hasil: MobileNetV2 2.01 s, EfficientNet-B0 1.96 s, ResNet-50 2.54 s.

Ini membandingkan **latensi pipeline end-to-end pada run tersebut**, bukan throughput inferensi murni arsitektur. Hanya ada satu pengukuran; tidak ada warm-up eksplisit. Startup CUDA dapat membebani model yang dievaluasi pertama, sementara decoding/preprocessing CPU dapat mendominasi atau menambah variasi. Karena itu selisih kecil MobileNetV2 dan EfficientNet-B0 tidak cukup untuk klaim kecepatan. Perbandingan latensi yang lebih kuat perlu warm-up identik, beberapa pengulangan, sinkronisasi, dan pemisahan waktu preprocessing dari forward pass.

## Status checkpoint MobileNetV2

File yang tersedia hanya `recognition_mobilenet_v2_pilot.pt`. Isinya menyimpan state dict, kelas, seed, konfigurasi dasar, dan riwayat metrik, tetapi tidak menyimpan nomor epoch, jenis checkpoint, optimizer state, atau state dict per epoch. Riwayat mencatat validation accuracy epoch 1 = 0.8829, epoch 2 = 0.8943, dan epoch 3 = 0.8657. Kode training saat itu menyimpan model setelah loop berakhir, sehingga state dict yang ada adalah bobot akhir epoch 3. Bobot epoch 2 tidak dapat dipulihkan dari metrik saja. Evaluasi MobileNetV2 yang tersedia karenanya bukan evaluasi checkpoint terbaik.

## Rekomendasi tahap berikutnya

1. Jangan tetapkan model final dari pilot tiga epoch atau validation set kecil ini. Pertahankan hasil sebagai smoke-test komparatif.
2. Sebelum eksperimen baru, tetapkan protokol agar setiap epoch menyimpan bobot best beserta epoch, konfigurasi lengkap, dan optimizer state bila pemulihan diperlukan. Jangan menimpa artefak saat ini.
3. Untuk MobileNetV2 best, hanya gunakan checkpoint epoch 2 jika artefak bobot epoch tersebut ditemukan secara lokal dan dapat diverifikasi; jika tidak ada, evaluasi final-state yang ada sebagai hasilnya dan rencanakan run baru hanya setelah persetujuan eksperimen.
4. Tinjau prediksi salah plum/apple/peach dan pear/bun/mooncake/doughnut dengan sampel validation terkait, tanpa memindahkan sampel atau memilih model berdasarkan test.
5. Untuk membandingkan waktu secara adil, lakukan pengukuran terpisah setelah evaluasi akurasi disepakati: warm-up, beberapa lintasan, dan laporkan latensi model serta pipeline end-to-end secara terpisah.
6. Perlakukan hasil grape dan lemon sebagai belum terukur. Jangan menyimpulkan performa kelas tersebut tanpa sampel validation yang representatif; perubahan split harus menjadi eksperimen baru dan bukan edit pada manifest ini.

Tidak ada model yang ditetapkan sebagai model final dalam analisis ini.
