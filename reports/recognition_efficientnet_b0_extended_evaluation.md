# EfficientNet-B0 extended-best validation evaluation

## Prosedur dan verifikasi

Checkpoint `outputs/checkpoints/recognition_efficientnet_b0_extended_best.pt` dimuat dengan `weights_only=True`; metadata menyatakan `checkpoint_kind=best`, epoch 6, 19 kelas. Bobot dimuat strict ke arsitektur EfficientNet-B0. Evaluasi memakai manifest tetap `data/splits/recognition_train_val.csv`, hanya baris `val`, dengan crop XML VOC 1-based yang dipotong ke batas gambar, RGB, resize 224x224, dan normalisasi ImageNet yang sama dengan training/evaluator terdahulu. Urutan kelas mengikuti checkpoint. Model berada pada `eval()` dan inferensi memakai `torch.inference_mode()`.

| Pemeriksaan | Hasil |
|---|---:|
| Baris validation / prediksi | 350 / 350 |
| Dimensi confusion matrix | 19 x 19 |
| Jumlah seluruh sel confusion matrix | 350 |
| Sampel benar / salah | 347 / 3 |
| Device | CUDA, NVIDIA GeForce RTX 3060 |
| Waktu satu lintasan evaluasi | 2.95 s (termasuk pembacaan crop dan preprocessing) |

## Metrik

Metrik per kelas dan confusion matrix lengkap disimpan sebagai CSV. Grape dan lemon memiliki support nol dan metrik per kelas kosong/N/A. Seperti evaluator sebelumnya, macro dan weighted average dihitung atas 17 kelas dengan support positif. Untuk kelas yang memiliki support tetapi tidak memiliki prediksi, aturan zero-division adalah 0. Lemon tetap mendapat satu prediksi false positive dari sampel mango; metrik lemon N/A karena tidak ada label aktual lemon, sementara kesalahan tersebut tetap tercermin dalam accuracy dan baris mango.

| Metrik | Extended-best (epoch 6) | Pilot-best (epoch 1) | Selisih |
|---|---:|---:|---:|
| Accuracy | 0.991429 (347/350) | 0.968571 (339/350) | +0.022857 (+8 benar) |
| Macro precision | 0.994040 | 0.957276 | +0.036764 |
| Macro recall | 0.985998 | 0.965902 | +0.020096 |
| Macro F1 | 0.989780 | 0.959958 | +0.029822 |
| Weighted precision | 0.994355 | 0.972155 | +0.022201 |
| Weighted recall | 0.991429 | 0.968571 | +0.022857 |
| Weighted F1 | 0.992754 | 0.969456 | +0.023298 |

Pilot-best berasal dari artefak evaluasi terdahulu `outputs/evaluation/efficientnet_b0_metrics.json` (checkpoint best epoch 1), bukan hasil training atau evaluasi ulang dalam tahap ini. Kedua checkpoint terbaik dipilih berdasarkan validation set yang sama dan hasil di atas dihitung pada set yang sama; karena itu perbandingan bersifat deskriptif dan validation accuracy bukan estimasi independen. Hasil ini tidak menetapkan model final.

## Prediksi yang salah

Confidence adalah probabilitas softmax kelas prediksi tertinggi. Grup adalah prefix filename provisional dari manifest.

| ID gambar | Label aktual | Prediksi | Confidence | Grup |
|---|---|---|---:|---|
| `mix003S(3)` (object 1) | qiwi | pear | 0.6475 | `mix003` |
| `mix005T(6)` (object 0) | mango | lemon | 0.7961 | `mix005` |
| `tomato001S(4)` (object 0) | tomato | mango | 0.5427 | `tomato001` |

Daftar lengkap beserta path gambar ada di `outputs/evaluation/efficientnet_b0_extended_best/misclassified_samples.csv`. Untuk `tomato001S(4)`, label di manifest/XML adalah tomato dan model memprediksi mango. Audit misclassification terdahulu (`reports/recognition_misclassification_audit.md`) telah menemukan bahwa bounding box tomato pada gambar ini berada di area koin/meja, tumpang tindih dengan box coin, bukan pada tomat. Evaluasi ini menggunakan crop tersebut apa adanya. Jadi kesalahan ini terverifikasi pada pipeline yang diuji, tetapi tidak dapat ditafsirkan sebagai kegagalan mengklasifikasikan crop tomat yang benar; skor kelas tomato ikut dipengaruhi anotasi lokalisasi bermasalah ini.

## Artefak

Semua output baru disimpan di `outputs/evaluation/efficientnet_b0_extended_best/`:

- `metrics.json` - metrik agregat, metadata checkpoint, dukungan kelas, dan verifikasi jumlah.
- `classification_report.csv` - precision, recall, F1, dan support per kelas serta macro/weighted average.
- `confusion_matrix.csv` dan `confusion_matrix.png` - confusion matrix 19 x 19.
- `misclassified_samples.csv` - ketiga kesalahan dengan ID, kelas, confidence, grup, dan path sumber.

Script evaluasi yang dapat dijalankan ulang: `src/evaluate_efficientnet_extended.py`. Tidak ada training, akses test set, atau perubahan terhadap dataset, manifest, anotasi, maupun checkpoint pada tahap evaluasi ini.

## Batasan dan langkah berikutnya

Validation hanya memiliki 350 crop dari 17 kelas; grape dan lemon sama sekali belum terukur. Checkpoint extended-best dipilih pada validation set ini setelah melihat beberapa epoch, sehingga metriknya rentan optimisme akibat pemilihan checkpoint. Satu kesalahan pada tomato berasal dari crop dengan bounding box yang sudah diketahui salah secara semantik. Pertahankan anotasi dan skor saat ini sebagai rekaman eksperimen; sebelum menyimpulkan generalisasi atau memilih model, gunakan evaluasi pada data independen dengan anotasi crop tervalidasi, terutama untuk tomato, serta dukungan sampel untuk seluruh kelas. Jangan gunakan test set untuk pemilihan checkpoint.
