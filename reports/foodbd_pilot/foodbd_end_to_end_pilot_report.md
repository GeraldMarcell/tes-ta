# FoodBD end-to-end pilot report

Status: pilot eksploratif, bukan hasil final TA. Semua data dibaca dari salinan lokal. Dataset FoodBD dan ECUSTFD, manifest/checkpoint recognition lama, serta output lama tidak diubah. Tidak ada unduhan.

## Data, split, dan eksklusi

Folder official `train/valid/test` dipertahankan; file tidak dipindah. Group key adalah basename image ID. Empat ID lintas-split (`FoodBD-0888`, `1103`, `1217`, `3083`) dikeluarkan seluruh kemunculannya. Enam image yang tidak memiliki entry metadata exact `(split, filename)` dikeluarkan. SHA-256 tidak menemukan exact duplicate lintas split. Skrining dHash 64-bit menemukan 28 pasangan lintas-split dengan jarak <=2; seluruh endpoint dikeluarkan sebagai langkah konservatif. Kandidat dHash bukan bukti bahwa pasangan adalah foto/objek sama.

| Tahap | Train | Validation | Test | Kelas dengan data |
|---|---:|---:|---:|---:|
| Recognition | 2.442 | 678 | 343 | 67 train/val, 66 test (egg support 0) |
| Segmentation | 2.442 | 678 | 343 | Binary food/background |
| Nutrisi | 1.273 | 353 | 174 | Join gambar satu-ke-satu |

Recognition/segmentation manifest memakai 3.463 gambar eligible. Nutrisi memakai 1.800 dari 1.837 baris CSV: empat ID tidak punya gambar, satu ID `FoodBD-3083.jpg` memiliki dua kandidat, dan 32 one-to-one rows terkait gambar yang dikecualikan. `excluded_samples.csv` berisi 107 alasan eksklusi; karena beberapa sampel memiliki lebih dari satu alasan, terdapat 60 path gambar unik yang dikeluarkan.

Target recognition adalah multi-hot dari ID kelas unik pada TXT. Segmentation merasterisasi union seluruh polygon menjadi mask biner; overlap dan duplikasi tidak menggandakan mask. Tidak ada anotasi yang diubah atau dihapus. Ketidaksesuaian geometri `FoodBD-1633`, `FoodBD-1652`, dan `FoodBD-1533` tetap dipertahankan; `1652` dikeluarkan karena metadata split tidak cocok.

Detail distribusi kelas/split: `outputs/foodbd_pilot/manifests/split_summary.json`. Manifest: `recognition_manifest.csv`, `segmentation_manifest.csv`, `nutrition_manifest.csv`, `excluded_samples.csv`.

## Konfigurasi dan training

| Tahap | Model/initialization | Maks./selesai; best epoch | Optimizer dan loss | Training time |
|---|---|---:|---|---:|
| Recognition | EfficientNet-B0; ImageNet weights dari cache lokal, strict load | 8/8; 8 | AdamW 1e-4; BCEWithLogits | 423,3 s |
| Segmentation | U-Net base=16; inisialisasi acak | 8/8; 8 | AdamW 5e-4; BCE + soft Dice | 412,6 s |
| Nutrisi | EfficientNet-B0; ImageNet weights lokal, output 3 target | 10/6; 3 | AdamW 1e-4; SmoothL1 pada target yang distandardisasi dari train | 159,7 s |

Seed 42, ImageNet RGB mean/std, tanpa augmentasi, cuDNN deterministic. Input 224x224 untuk recognition/nutrisi dan 160x160 untuk segmentation; batch size 16/16/12. Hardware/runtime: RTX 3060, PyTorch 2.5.1+cu121, torchvision 0.20.1+cu121. Best checkpoint dipilih berdasarkan validation loss terendah. Recognition threshold per kelas dipilih dari validation F1 pada grid 0,05–0,95; jika dukungan positif/negatif validation tidak cukup, fallback 0,5. Test tidak digunakan untuk pemilihan checkpoint atau threshold.

### Loss per epoch

| Epoch | Recognition train | Recognition val | Segmentation train | Segmentation val | Nutrition train | Nutrition val |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 0,27987 | 0,14137 | 0,72248 | 0,49037 | 0,31573 | 0,24252 |
| 2 | 0,12809 | 0,11207 | 0,44591 | 0,38590 | 0,22253 | 0,22176 |
| 3 | 0,10863 | 0,09967 | 0,34298 | 0,32298 | 0,17188 | 0,21824 |
| 4 | 0,09656 | 0,09092 | 0,29753 | 0,27419 | 0,14153 | 0,22695 |
| 5 | 0,08794 | 0,08494 | 0,26174 | 0,26713 | 0,11571 | 0,22266 |
| 6 | 0,07898 | 0,08077 | 0,25755 | 0,22660 | 0,10887 | 0,22472 |
| 7 | 0,07224 | 0,07680 | 0,22625 | 0,21722 | — | — |
| 8 | 0,06645 | 0,07459 | 0,21163 | 0,20692 | — | — |

Nutrisi berhenti setelah tiga epoch berturut-turut tanpa perbaikan validation loss; best epoch 3. Recognition dan segmentation menyelesaikan batas pilot 8 epoch.

## Evaluasi test (dijalankan sekali setelah semua training)

### Recognition

| Metrik | Hasil |
|---|---:|
| Subset accuracy | 0,2391 |
| Micro precision / recall / F1 | 0,6816 / 0,7504 / 0,7143 |
| Macro precision / recall / F1 (66 kelas bersupport) | 0,4739 / 0,5248 / 0,4597 |
| Weighted precision / recall / F1 | 0,7684 / 0,7504 / 0,7448 |
| mAP (66 kelas bersupport) | 0,5123 |
| Test images | 343 |

Per-class report dan support: `outputs/foodbd_pilot/metrics/foodbd_recognition_test_per_class.csv`. Kelas egg memiliki support 0; seluruh skornya N/A dan kelas itu tidak masuk macro/mAP. Precision zero-division untuk kelas bersupport tetapi tanpa positive prediction ditetapkan 0. Prediksi per image: `predictions/recognition_test.csv`.

### Binary segmentation

| Metrik | Hasil |
|---|---:|
| Mean IoU per image | 0,8690 |
| Mean Dice per image | 0,9263 |
| Global pixel IoU / Dice | 0,8750 / 0,9333 |
| Pixel precision / recall | 0,9248 / 0,9400 |
| Test images | 343 |

Tugas hanya food-vs-background; bukan segmentasi per kelas. Threshold prediksi 0,5. Predicted masks dan ground-truth masks (masing-masing 343 PNG), metrik per-image, dan visual input/GT/prediction ada di `outputs/foodbd_pilot/predictions/segmentation/` dan `outputs/foodbd_pilot/visualizations/segmentation_test_examples.png`. Ground-truth masks adalah rasterisasi sementara dari polygon TXT sumber; file anotasi sumber tidak diubah.

### Estimasi nutrisi hidangan

| Target CSV | MAE | RMSE | R² | Median-train baseline MAE / RMSE |
|---|---:|---:|---:|---:|
| CHO | 9,690 | 13,233 | 0,703 | 16,188 / 24,850 |
| Protein | 2,941 | 4,663 | 0,207 | 3,699 / 5,247 |
| Fat | 3,093 | 4,215 | 0,296 | 4,095 / 5,029 |

Test berisi 174 meal/image pairs. Header asli dipertahankan; unit tidak dinyatakan di header CSV. Target adalah estimasi ahli pada tingkat hidangan/gambar, bukan pengukuran laboratorium atau label polygon. Encoder segmentation tidak dipakai sebagai fitur nutrisi; model menggunakan gambar saja. Prediksi: `outputs/foodbd_pilot/predictions/nutrition_test.csv`.

## Porsi/berat

Tidak dilatih atau dievaluasi. FoodBD lokal tidak menyediakan target berat aktual terverifikasi yang terhubung ke gambar; tidak dibuat target pengganti.

## Integrasi teknis

`src/infer_foodbd_pilot.py` berhasil memuat ketiga checkpoint best dan menjalankan recognition → U-Net binary mask → regresi nutrisi. Demo memakai `train/images/FoodBD-0888.jpg`, yang dikeluarkan dari training karena collision ID (bukan gambar test). Input copy, kategori/score, mask, overlay, prediksi nutrisi, dan JSON tersimpan di `outputs/foodbd_pilot/predictions/integrated_demo/`. Ini membuktikan jalur eksekusi teknis, bukan akurasi end-to-end. Berat ditandai `not_available`.

## Keterbatasan dan error implementasi

TXT lokal berisi 13.485 polygon, sementara chart sumber menjumlah 12.575; `ruti` berbeda +900. Arsip tidak memiliki anotasi alternatif per object; chart aggregate juga tidak memetakan baris per gambar. Pilot memakai TXT lokal apa adanya dan tidak menyatakan revisi mana canonical. dHash screening bisa false-positive; kandidatnya dikeluarkan untuk mengurangi risiko leakage. Kemungkinan hubungan gambar lain di luar exact/dHash screening belum dapat dikesampingkan. Test kelas egg tidak didukung. Nutrisi hanya 174 test samples dan target tidak memiliki unit pada header.

Run recognition pertama menyelesaikan 8 epoch tetapi gagal saat menyimpan artefak dengan `NameError: name 'Path' is not defined`. Error dicatat di `outputs/foodbd_pilot/metrics/recognition_artifact_save_error.json`; import diperbaiki dan run recognition final dilakukan ulang. Hanya checkpoint run final yang dipakai untuk evaluasi.

Secara teknis recognition, binary segmentation, dan estimasi nutrisi berhasil dilatih, checkpoint best/last diverifikasi dapat dimuat, serta evaluasi test selesai. Estimasi berat terblokir oleh target yang tidak tersedia. Sebelum hasil dapat dipertimbangkan untuk TA, perlukan provenance/crosswalk anotasi per-instance untuk selisih polygon, file/split collision dan filename mismatch; tinjau grup near-duplicate; bekukan split group-aware baru; pastikan unit/provenance target nutrisi; lalu lakukan eksperimen terkontrol dan evaluasi independen. Tidak ada model final yang dipilih.

## File utama

Scripts: `src/foodbd_pilot_common.py`, `src/prepare_foodbd_pilot.py`, `src/train_foodbd_pilot.py`, `src/evaluate_foodbd_pilot.py`, `src/infer_foodbd_pilot.py`.

Artefak terpisah berada di `outputs/foodbd_pilot/{manifests,checkpoints,metrics,predictions,visualizations}/`. Checkpoint: `foodbd_{recognition,segmentation,nutrition}_{best,last}.pt`; masing-masing tahap juga memiliki JSON konfigurasi dan metrik. Kurva training loss: `outputs/foodbd_pilot/visualizations/training_loss_curves.png`.
