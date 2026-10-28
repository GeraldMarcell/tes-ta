# Audit dataset FoodBD untuk pipeline food computer vision

Tanggal audit: 2026-10-27. Lokasi yang diperiksa: `C:\TA\data\raw\FoodBD`. Audit bersifat read-only untuk data asli; tidak ada training/evaluasi model, file manifest baru, atau perubahan pada ECUSTFD maupun artefak recognition. Satu visual inspeksi turunan disimpan di reports, bukan di raw dataset.

## Ringkasan status lokal

FoodBD **tersedia lokal**. Gambar dan label poligon memiliki pasangan basename di split train/valid/test. Polygon dapat dirasterisasi sebagai mask; satu contoh visual berhasil dibuat. Data mendukung recognition multi-label, semantic segmentation, dan estimasi nutrisi tingkat hidangan, dengan batasan serta temuan yang perlu diselesaikan di bawah. **Dataset belum siap dipakai untuk eksperimen yang hasilnya dapat dipercaya** sampai perbedaan jumlah anotasi, ID yang muncul lintas split, dan pemetaan empat baris nutrisi diperiksa.

## Isi dan struktur yang ditemukan

```text
FoodBD/
  data.yaml
  MealNutrition1837_All.csv
  train/{images,labels}/
  valid/{images,labels}/
  test/{images,labels}/
```

| Split | Gambar JPG 1024x1024 | Label TXT pasangan | Instance polygon |
|---|---:|---:|---:|
| Train | 2.473 | 2.473 | 9.364 |
| Validation (`valid`) | 697 | 697 | 2.748 |
| Test | 353 | 353 | 1.373 |
| Total | 3.523 | 3.523 | 13.485 |

Semua gambar yang diinventarisasi terbaca sebagai JPEG dan memiliki dimensi 1024 x 1024; tidak ditemukan label TXT orphan atau gambar tanpa TXT. Terdapat 1 sampai 15 polygon per gambar; 3.373 gambar memuat lebih dari satu objek dan hanya 150 yang memiliki satu anotasi. Jadi satu gambar sering berisi sejumlah kelas sekaligus, bukan satu label kelas tunggal.

`data.yaml` mendefinisikan 67 kelas. Label TXT berisi ID kelas 0-66 diikuti pasangan koordinat polygon; pemeriksaan seluruh 13.485 baris tidak menemukan koordinat non-numerik, koordinat di luar rentang 0..1, atau jumlah koordinat ganjil/kurang dari tiga vertex. Semua 67 kelas ada di train dan validation; kelas `egg` tidak memiliki instance di official test. Distribusi objek tidak seimbang: `rice` 1.536 instance, `ruti` 1.098, `chicken` 818, `cucumber` 776; `mango` dan `roll` masing-masing 20, `guava` 23.

Nama 67 kelas dari YAML: `achar`, `apple`, `badam`, `banana`, `beef`, `begun-vaji`, `beguni`, `biriyani`, `bread`, `burinda`, `cabbage`, `carrot`, `cauliflower`, `cha`, `chichinga-vaji`, `chicken`, `chola`, `chomchom`, `chop-alu`, `cucumber`, `daal`, `dates`, `dundol`, `egg`, `egg-boiled`, `egg-poached`, `fish`, `grapes`, `green-pea`, `guava`, `jilapi`, `juice`, `kabab`, `khichuri`, `kochu`, `korola-vaji`, `kumra-vaji`, `lal-shak`, `lau`, `lemon`, `mango`, `milk`, `noodles`, `okra`, `orange`, `papaya`, `payesh`, `peyaju`, `pineapple`, `piyaju`, `potato`, `potato-mashed`, `potol`, `puffed-rice`, `puri`, `rice`, `roll`, `ruti`, `salad`, `shak`, `shim`, `sweets`, `tomato`, `vaji`, `vegetable`, `vorta`, `watermelon`.

### Polygon-to-mask check

TXT coordinates berada pada rentang ternormalisasi dan mengikuti struktur class-ID plus vertex pairs. Rasterisasi sampel dengan mengalikan x oleh lebar gambar, y oleh tinggi, lalu mengisi polygon menghasilkan mask binary berukuran 1024 x 1024. Overlay memperlihatkan polygon berada pada objek makanan di gambar contoh. Ini memverifikasi bahwa anotasi lokal dapat dirender sebagai mask pada contoh; bukan audit visual manual atas setiap polygon.

Contoh `train/images/FoodBD-0003.jpg` memiliki enam polygon, kelas `banana`, `carrot`, `chicken`, `cucumber`, `lau`, dan `ruti`. Mask union yang divisualisasikan mencakup sekitar 31,5% piksel. Artefak terdiri dari panel gambar asli, polygon overlay, dan binary union mask: [foodbd_polygon_mask_example.png](foodbd_polygon_mask_example.png). Visual ini adalah konversi inspeksi dari anotasi asli, bukan mask sintetis yang dimasukkan ke raw data.

Untuk semantic segmentation multiclass, mask dapat memakai background=0 dan kelas 1-67. Kebijakan untuk piksel yang terkena beberapa polygon harus ditetapkan dan diperiksa sebelum training (misalnya tandai ignore dan ukur jumlahnya; jangan menimpa kelas secara diam-diam). Binary food-vs-background union juga dapat dievaluasi, tetapi membuang informasi kelas.

## Hubungan split, duplikasi, dan kebocoran

Split lokal berjumlah 70,2% train, 19,8% validation, dan 10,0% test; `data.yaml` memetakan `val` ke folder `valid`. Pemeriksaan SHA-256 menemukan nol file identik byte-per-byte. Namun empat basename terulang lintas split:

| Basename | Split yang ditemukan | SHA sama? | MAE grayscale 32x32 setelah resize (skala 0-255)* |
|---|---|---|---:|
| `FoodBD-0888.jpg` | train, valid | tidak | 0,086 |
| `FoodBD-1103.jpg` | train, valid | tidak | 0,094 |
| `FoodBD-1217.jpg` | train, valid | tidak | 0,099 |
| `FoodBD-3083.jpg` | valid, test | tidak | 0,050 |

\*MAE adalah selisih rata-rata nilai pixel grayscale uint8 setelah kedua gambar di-resize ke 32 x 32, tanpa normalisasi; ini pemeriksaan kasar, bukan bukti definitif duplikasi. Nama ID yang sama lintas split merupakan collision terverifikasi. Kandidat sangat mirip ini harus diperlakukan sebagai satu grup konservatif sampai asal file diklarifikasi. Khususnya, `FoodBD-3083` membuat validation dan test berbagi ID serta mengaburkan gambar mana yang dirujuk oleh satu baris nutrisi.

File lokal tidak menyertakan `FoodBD_Meta_data.csv` yang disebut dalam publikasi, sehingga tidak tersedia metadata lokasi/pengambilan/perangkat untuk mendeteksi kelompok terkait lainnya. Sebelum pemilihan model apa pun, buat manifest turunan group-aware yang menempatkan seluruh gambar dengan ID dasar yang sama dalam satu split; jangan mengubah folder sumber. Pertahankan test tertutup dan jangan gunakan test untuk pemilihan model. Verifikasi juga kemungkinan kelompok dari metadata resmi jika file itu dapat diperoleh.

## Nutrisi dan portion/weight

`MealNutrition1837_All.csv` berisi 1.837 baris dan 1.837 `FoodImage` unik. Kolomnya: `FoodImage`, `CHO`, `Protein`, `Fat`, `Fiber`, `Calorie`, `GL`. Tidak ada nilai kosong, record duplikat, atau nilai non-numerik pada kolom target. `CHO` berarti carbohydrate menurut dokumentasi; header lokal tidak menyertakan unit eksplisit. Nilai numerik lokal berkisar: CHO 0-168,85; protein 0-52,45; fat 0-52,5; fiber 0-20,7335; calorie 31,6-1.023; GL 0-953,664.

Join exact basename ke gambar menemukan 1.832 baris yang memetakan satu-ke-satu, satu baris (`FoodBD-3083.jpg`) yang memetakan ke dua salinan berbeda pada validation dan test, serta empat baris tanpa gambar lokal: `FoodBD-2282.jpg`, `FoodBD-2383.jpg`, `FoodBD-3381.jpg`, `FoodBD-3508.jpg`. Dengan demikian, hanya 1.832 pasangan nutrisi-gambar yang saat ini memiliki pemetaan satu-ke-satu yang tidak ambigu. Semua enam field numerik tersedia pada baris tersebut, tetapi satu baris yang bertabrakan dan empat yang tidak cocok tidak boleh dipaksakan ke gambar tertentu.

Dokumentasi publik menyebut 1.837 gambar memiliki label nutrisi dan menjelaskan bahwa ahli gizi memperkirakan portion/berat bahan dari panduan porsi, kemudian mengagregasi CHO, protein, fat, fiber, dan calorie per gambar/hidangan. `GL` dihitung memakai estimasi berat; publikasi menyatakan berat bukan hasil timbang aktual. CSV lokal hanya punya satu key `FoodImage` per hidangan, tidak punya kolom `Weight`, tidak mengidentifikasi objek/polygon, dan tidak menyediakan nutrisi per objek. Karena itu:

- **Nutrisi tingkat hidangan:** tersedia sebagai target estimasi untuk CHO, protein, fat, fiber, calorie, GL pada subset yang berhasil dijoin; target mereproduksi estimasi ahli, bukan pengukuran asupan aktual. Setelah mapping dibersihkan, laporan dapat memakai MAE/RMSE per nutrien. Evaluasi tidak boleh disebut validasi terhadap hasil timbang laboratorium.
- **Portion/berat regresi:** belum didukung sebagai target teramati. Tidak ada kolom berat eksplisit atau berat aktual per gambar/objek. Jangan menurunkan berat dari GL atau membagi nutrisi hidangan ke polygon.
- **Multi-objek:** label polygon adalah tingkat objek; nutrisi adalah tingkat gambar/hidangan yang diagregasi. CSV tidak memungkinkan target makro per objek.

## Kesesuaian pipeline dan metrik

| Pipeline | Dukungan yang ditemukan | Rancangan target dan metrik | Status |
|---|---|---|---|
| Food recognition | Kelas per polygon tersedia pada seluruh 3.523 gambar; gambar umumnya multi-label. | EfficientNet-B0 dengan 67 logit sigmoid untuk label kelas-presence per gambar, `BCEWithLogitsLoss`; accuracy sebagai exact-match/subset accuracy dan macro F1 per kelas. Alternatif crop per polygon memberi single-label object recognition, tetapi itu tugas berbeda. | Label ada; tangani split collision dan class imbalance. Existing 19-class checkpoint bukan head/data configuration FoodBD. |
| Food segmentation | Polygon per objek dengan class ID tersedia; contoh rasterisasi terlihat benar. | U-Net semantic segmentation dengan 68 kelas termasuk background; CE atau CE+Dice; mean IoU dan Dice macro per foreground class. Laporkan binary food union sebagai metrik sekunder jika dibutuhkan. | Didukung oleh format lokal, tetapi audit visual seluruh mask dan overlap policy masih perlu. |
| Portion/berat | Tidak ada nilai berat eksplisit; berat porsi hanya disebut sebagai estimasi perantara untuk GL. | MAE/RMSE berat memerlukan label gram langsung yang dapat dipetakan ke gambar/objek dan provenance pengukuran yang diketahui. | **Belum didukung.** Perlu subset label berat terukur atau estimasi berat eksplisit yang dapat dipasangkan. |
| Nutrisi | 1.832 join satu-ke-satu; target CSV berada pada level meal/image, berdasarkan estimasi ahli. | Model image-level multi-output; MAE/RMSE terpisah untuk CHO, protein, dan fat; calorie/fiber/GL dapat dianalisis sebagai target tambahan. | Didukung secara terbatas setelah 5 masalah join diselesaikan dan split bebas konflik. |

Untuk seluruh tahap, pisahkan train/validation/test berdasar grup gambar terkait dan identitas basename; tetap simpan test hanya untuk evaluasi akhir. Gunakan data test sekali setelah konfigurasi model dipilih dengan validation. Jangan memakai test untuk tuning, early stopping, atau pemilihan checkpoint.

## Perbedaan terhadap publikasi dan risiko provenance

Mendeley Data versi 2 mencatat FoodBD sebagai 3.523 gambar, 67 kategori, polygon segmentation, nutrisi pada 1.837 gambar, estimasi ahli, dan lisensi CC BY 4.0. [Halaman dataset resmi Mendeley](https://data.mendeley.com/datasets/xh3ghf3jbg/2). Artikel data mendeskripsikan TXT sebagai class ID diikuti koordinat polygon, 12.575 anotasi, split 70/20/10, file metadata `FoodBD_Meta_data.csv`, dan nutrisi per image yang diturunkan dari estimasi portion; [artikel peer-reviewed](https://pmc.ncbi.nlm.nih.gov/articles/PMC12801922/).

**Temuan discrepancy:** parser lokal menemukan 13.485 baris instance polygon, 910 lebih banyak daripada 12.575 anotasi yang dilaporkan artikel. Jumlah gambar/split lokal cocok dengan 3.523, tetapi ini belum membuktikan kesamaan versi atau integritas. Root lokal tidak memiliki metadata CSV dan provenance/versi/checksum. Cocokkan salinan ini dengan rilis Mendeley v2 dan protokol anotasinya sebelum menyatakan seluruh anotasi tervalidasi.

## Kesimpulan dan langkah berikutnya

FoodBD lokal menyediakan gambar, 67 label kategori, polygon yang dapat dirasterisasi, dan label nutrisi agregat untuk sebagian gambar. Food recognition full-image seharusnya diperlakukan sebagai multi-label. U-Net multiclass dapat memakai polygon setelah konflik dan discrepancy anotasi ditinjau. Nutrisi dapat diuji hanya pada join image-level yang tidak ambigu dan harus dilaporkan sebagai prediksi terhadap estimasi ahli. Portion/berat langsung belum memiliki target yang tersedia. Estimasi 3D tidak termasuk cakupan.

Sebelum training: verifikasi versi/provenance dan checksum terhadap rilis resmi; selidiki selisih 910 polygon serta empat image ID lintas split; peroleh metadata jika tersedia; pulihkan/konfirmasi empat gambar nutrisi yang hilang; selesaikan join `FoodBD-3083`; buat manifest grup train/validation/test tanpa overlap dan bekukan test; lalu audit visual sampel anotasi dan kelas-mask raster. Sampai itu selesai, dataset **belum siap untuk training/pelaporan hasil yang final**. ECUSTFD serta checkpoint, manifest, dan laporan recognition yang ada tidak diubah.
