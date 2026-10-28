# Audit metadata sumber FoodBD v2

Tanggal: 2026-10-27. Baca-saja. Tidak ada training, manifest, perubahan dataset, ataupun perubahan pada eksperimen ECUSTFD.

## Sumber yang tersedia lokal

Arsip v2 dan ekstraknya tersedia:

- `C:\Users\user\Downloads\FoodBD A Polygon-Annotated Meal Image Dataset of B (1).zip` (345.368.652 byte; 7.054 entri)
- `C:\TA\data\source_archives\FoodBD_v2\root\`

Arsip berisi kedua CSV yang disebut publikasi: `FoodBD_Meta_data.csv` dan `FoodBD/MealNutrition1837_All.csv`, serta `FoodBD/data.yaml` dan lima gambar dokumentasi: `Class_Distribution_Chart.png`, `Dataset_Folder_Structure.png`, `Data_Collection_Pipeline.png`, `Original_vs_Annotated_Images.png`, dan `Single_Meal_Annotation_File.png`. Tidak ditemukan README, changelog, daftar/checksum rilis, manifest gambar dengan stable ID, atau file anotasi alternatif. Nama direktori lokal `FoodBD_v2` saja tidak menetapkan nomor revisi/provenance resmi.

Ada ZIP lain yang lebih lama dengan 7.049 entri. Seluruh 7.049 file yang sama pada kedua ZIP identik byte-per-byte; ZIP yang lebih baru menambahkan tepat lima PNG dokumentasi di atas. Jadi tidak ditemukan revisi CSV, gambar, label, atau YAML di antara dua arsip lokal tersebut.

Dalam arsip/ekstrak v2 terdapat 3.523 JPG dan 3.523 TXT. Semua JPG dan TXT hasil ekstrak v2 cocok byte-per-byte dengan `C:\TA\data\raw\FoodBD`; `data.yaml` dan CSV nutrisi juga cocok byte-per-byte. Sumber anotasi tetap file TXT split lokal, bukan dataset alternatif pada arsip v2.

## Perbandingan kedua CSV

| File | Isi sumber v2 | Salinan proyek | Hasil |
|---|---|---|---|
| `FoodBD_Meta_data.csv` | 3.523 baris data; kolom `filename`, `instances`, `Environmental conditions`, `preprocessing `, `types` | Tidak ada salinan file ini di root FoodBD proyek; versi yang ada di paket sumber cocok byte-per-byte dengan versi ZIP lama | 2.473 train, 697 valid, 353 test. Kolom `instances` berisi nama kelas pada level gambar, bukan ID objek/polygon. Tidak ada versi, stable image ID, annotation ID, sesi, atau crosswalk nutrisi. |
| `MealNutrition1837_All.csv` | 1.837 baris; 1.837 nilai `FoodImage` unik; kolom `FoodImage`, `CHO`, `Protein`, `Fat`, `Fiber`, `Calorie`, `GL` | `C:\TA\data\raw\FoodBD\MealNutrition1837_All.csv` | Byte-identik (SHA-256 `a03e6a22c9aff5edb29dcf0a8aff839c7e060147c7f53217df2495dbe223524d`); tidak ada perubahan ID, nama gambar, kolom, urutan, atau nilai yang dapat memulihkan baris unmatched. |

Metadata menyebut preprocessing `resized to 1024x1024`, kondisi `indoor`. Gambar folder dataset menunjukkan pasangan image/label per split. Diagram pipeline lokal menyatakan rasio split 70/20/10 dan alur pengumpulan meal nutrition; tidak mencatat pengecualian ID, aturan canonical filename, atau relasi nutrisi ke polygon. Diagram format label menunjukkan baris `class_id` dan pasangan koordinat, sejalan dengan TXT, namun bukan daftar instance sumber dengan ID stabil.

## Selisih 13.485 polygon vs 12.575

Arsip v2 tidak menyediakan TXT alternatif: hitungan proyek tetap 9.364 train + 2.748 valid + 1.373 test = **13.485 baris polygon**. Namun paket ini menambahkan `Class_Distribution_Chart.png`, dengan 67 angka per kelas. Jumlah angka yang tercetak pada chart adalah **12.575**—sama dengan jumlah anotasi yang dirujuk laporan publikasi sebelumnya.

Perbandingan angka chart dengan hitungan class ID dari seluruh TXT menghasilkan:

| Kelas | Hitungan chart sumber | TXT lokal | TXT lokal dikurangi chart |
|---|---:|---:|---:|
| `ruti` | 198 | 1.098 | +900 |
| `cauliflower` | 105 | 106 | +1 |
| `daal` | 517 | 519 | +2 |
| `dates` | 399 | 400 | +1 |
| `fish` | 587 | 589 | +2 |
| `mango` | 21 | 20 | -1 |
| `potato` | 452 | 454 | +2 |
| `rice` | 1.535 | 1.536 | +1 |
| `shim` | 63 | 64 | +1 |
| `tomato` | 79 | 80 | +1 |
| 57 kelas lain | Sama per kelas | Sama | 0 |
| **Total** | **12.575** | **13.485** | **+910** |

Jadi paket v2 memberikan bukti sumber tambahan bahwa agregat kelas yang didokumentasikan berjumlah 12.575. Selisih lokal dapat direkonsiliasi secara aritmetika: 900 berasal dari perbedaan hitungan `ruti`, dan net 10 dari sembilan kelas lain di tabel (satu kelas lebih rendah satu, delapan kelas lebih tinggi; net +10). Tetapi chart tidak mengidentifikasi file atau baris polygon yang membentuk hitungan tersebut, tidak menjelaskan cara chart dihitung, dan tidak mengatakan apakah data TXT atau chart berasal dari revisi berbeda. **Belum dapat dipastikan apakah 900 baris `ruti` adalah anotasi yang sah, duplikasi, atau perbedaan ekspor. Tidak ada baris dihapus atau diubah.** Bukti yang diperlukan: ekspor anotasi sumber/canonical per-image, revisi dataset yang menghasilkan chart, dan definisi hitungan `ruti`/protokol anotasinya.

## Konflik split dan nutrisi

| Kasus | Bukti sumber v2 | Rekonsiliasi terhadap file proyek | Status |
|---|---|---|---|
| `FoodBD-0888` | Metadata memiliki dua row filename: train dan valid; keduanya mencantumkan `kumra-vaji,rice` | Nama split collision memang ada di metadata sumber, bukan hanya akibat penggabungan folder lokal. Dua JPG berbeda byte, TXT persis sama. Metadata tidak punya stable ID atau relasi antara kedua gambar. | **Partly resolved**: provenance split overlap terbukti; identitas/relasi gambar unresolved. Perlu canonical image IDs atau capture/source mapping. |
| `FoodBD-1103` | Dua row: train dan valid; keduanya mencantumkan `carrot,cucumber,daal,potol,rice` | Sama: split overlap dinyatakan oleh metadata; gambar byte berbeda dan TXT sama persis. | **Partly resolved**; perlu identitas/provenance sumber. |
| `FoodBD-1217` | Dua row: train dan valid; keduanya mencantumkan `banana,carrot,chicken,ruti` | Sama: split overlap dinyatakan metadata; belum dapat ditentukan apakah foto terkait atau referensi ID dipakai ulang. | **Partly resolved**; perlu identitas/provenance sumber. |
| `FoodBD-3083` | Satu row metadata: valid, `beef,ruti`; satu row nutrisi `FoodBD-3083.jpg` | Folder lokal berisi JPG valid dan test berbeda byte, TXT sama. Metadata tidak mencatat file test. CSV nutrisi hanya key basename, sehingga pemilihan file tidak otomatis terjustifikasi. | **Partly resolved**: row valid didukung metadata; file test dan kandidat persis yang ditautkan ke nutrisi masih unresolved. Perlu canonical ID/file mapping. |
| `FoodBD-2282.jpg` | Tidak ada entry di metadata gambar | Ada satu row di CSV nutrisi, tetapi tidak ada basename JPG di split lokal. Metadata sumber tidak memberikan kandidat pengganti. | **Unresolved**; perlu file gambar atau correction/crosswalk resmi. |
| `FoodBD-2383.jpg` | Tidak ada entry di metadata gambar | Satu row nutrisi, tanpa JPG cocok; tidak ada pemetaan alternatif. | **Unresolved**; perlu file gambar atau correction/crosswalk resmi. |
| `FoodBD-3381.jpg` | Tidak ada entry di metadata gambar | Satu row nutrisi, tanpa JPG cocok; tidak ada pemetaan alternatif. | **Unresolved**; perlu file gambar atau correction/crosswalk resmi. |
| `FoodBD-3508.jpg` | Tidak ada entry di metadata gambar | Satu row nutrisi, tanpa JPG cocok; tidak ada pemetaan alternatif. | **Unresolved**; perlu file gambar atau correction/crosswalk resmi. |

Sumber v2 tidak menambahkan ID objek atau hubungan antara kolom nutrisi dengan polygon. Nutrisi tetap merupakan row ber-key `FoodImage`; tidak dapat diturunkan menjadi label per objek. Header dan nilai tidak ditransformasikan.

## Rekonsiliasi filename metadata

Metadata sumber juga memuat mismatch basename yang ditemukan sebelumnya. Untuk train, metadata-only: `FoodBD-3301.rf.7f3254b2c7fbe0861f40fa4be65c3cbd.jpg.jpg`, `FoodBD-8003jpg`, `FoodBD-8114jpg`, `FoodBD-8543jpg`; folder-only: `FoodBD-8003.jpg`, `FoodBD-8114.jpg`, `FoodBD-8301.jpg`, `FoodBD-8543.jpg`. Untuk test, metadata-only: `FoodBD-8083.jpg`, `FoodBD-8652.jpg`; folder-only: `FoodBD-1652.jpg`, `FoodBD-3083.jpg`. Valid tidak memiliki mismatch exact basename.

Dua arsip dan metadata v2 mengulang nama yang sama; tidak ada correction map atau ID stabil yang mengonfirmasi bahwa filename yang mirip adalah pasangan. Mismatch tetap **unresolved** dan tidak dinormalisasi secara spekulatif.

## Tabel status akhir

| Kasus | Bukti sumber | Hasil rekonsiliasi | Status |
|---|---|---|---|
| Kedua CSV sumber tersedia | Ada di arsip dan ekstrak v2; header/row counts terukur | Nutrition CSV byte-identik dengan proyek; metadata split/category tersedia di paket, tanpa ID objek atau revisi | **Resolved** untuk ketersediaan/isi file; provenance versi penuh belum ada |
| Polygon total | Chart 67 kelas menjumlah tepat 12.575; TXT berjumlah 13.485 | Selisih +910 terlokalisasi agregat pada ruti +900 dan net +10 kelas lain, tetapi tidak ada crosswalk baris/file | **Unresolved**; butuh ekspor anotasi canonical dan dokumentasi revisi/hitungan |
| 3 collision train/valid | Metadata mencatat ID dan kelas yang sama pada kedua split | Mengonfirmasi collision ada pada metadata sumber; tidak menetapkan identitas dua JPG | **Partly resolved**, perlu stable capture/image IDs |
| Collision `3083` + nutrition join | Metadata hanya menyebut valid; nutrisi CSV memakai basename tunggal | Valid didukung; test tidak tercatat; data tidak memilih kandidat gambar untuk nutrition record secara formal | **Partly resolved**, perlu crosswalk resmi |
| Empat nutrition key yatim | Tidak ada pada metadata; ada masing-masing satu row CSV nutrisi | Tidak ada candidate image atau alias resmi | **Unresolved**, perlu file/correction map |
| Filename mismatch | Nama metadata dan folder berbeda persis pada daftar di atas | Tidak ada correction table; dua ZIP setuju pada isi yang sama | **Unresolved**, perlu mapping canonical filenames |
| README/checksum/manifest versi | Tidak ada di ZIP; chart dan diagram bukan manifest | Label `FoodBD_v2` tidak menetapkan checksum/revisi file yang dipakai | **Requires source metadata** |

## Kesimpulan dan bukti tambahan yang diperlukan

CSV pendukung memang tersedia di arsip v2 dan sama dengan data yang dipakai proyek; arsip terbaru hanya menambahkan lima gambar dokumentasi, bukan revisi label/CSV. Chart distribusi kelas memberi bukti bahwa sumber mendokumentasikan total 12.575, dan menjelaskan secara agregat bahwa perbedaan dengan TXT lokal terutama berada pada `ruti`. Chart tersebut **tidak** menyelesaikan identitas anotasi yang berbeda maupun menetapkan data mana yang canonical. Metadata menyelesaikan fakta bahwa tiga ID dicatat pada dua split, tetapi tidak menjelaskan relasi fotonya. Metadata tidak menyelesaikan `3083` test atau empat key nutrisi yang tidak cocok.

Sebelum membuat manifest training, minta/unduh manual dari sumber FoodBD: (1) file anotasi canonical yang memetakan setiap polygon ke image ID dan class ID beserta revision; (2) versi/checksum dan catatan pembuatan `Class_Distribution_Chart`; (3) stable image/capture IDs dan correction map untuk split serta filename collision; dan (4) crosswalk CSV nutrition ke canonical image ID, termasuk empat ID yatim dan pemilihan file `3083`. Jangan menghapus polygon, memasangkan file dari kemiripan nama, atau menyusun manifest final sebelum informasi ini cocok dengan file lokal.
