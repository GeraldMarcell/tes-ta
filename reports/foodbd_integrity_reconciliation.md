# Rekonsiliasi integritas dataset FoodBD

Tanggal: 2026-10-27. Pemeriksaan bersifat baca-saja terhadap dataset asli. Tidak ada file di `data/raw/FoodBD` atau ECUSTFD yang diubah/dihapus; tidak ada manifest final dibuat; tidak ada training dijalankan; checkpoint dan laporan eksperimen recognition tidak disentuh.

## 1. Sumber hitungan 13.485 polygon

Anotasi berasal dari seluruh file `*.txt` pada:

- `data/raw/FoodBD/train/labels/`
- `data/raw/FoodBD/valid/labels/`
- `data/raw/FoodBD/test/labels/`

Setiap baris non-kosong berisi `class_id` diikuti pasangan koordinat polygon. Tidak ada ID anotasi/instance eksplisit; nomor baris di TXT hanya posisi lokal, bukan ID stabil. Hitungan yang diperoleh:

| Split | Gambar | TXT berpasangan | Baris polygon |
|---|---:|---:|---:|
| train | 2.473 | 2.473 | 9.364 |
| valid | 697 | 697 | 2.748 |
| test | 353 | 353 | 1.373 |
| total | 3.523 | 3.523 | 13.485 |

Nama gambar mengikuti pola `FoodBD-####.jpg`; TXT pasangan menggunakan basename sama. `data.yaml` berisi 67 nama kelas dengan ID 0-66. Semua basename di setiap split punya TXT dan tidak ditemukan TXT tanpa gambar. Seluruh 13.485 baris yang diparse memiliki class ID valid, nilai koordinat finite dalam 0..1, jumlah koordinat genap dengan sedikitnya tiga vertex, dan luas poligon shoelace bukan nol.

Pemeriksaan geometri menemukan tiga kasus yang perlu ditinjau, tanpa mengubah anotasi:

| ID gambar | File dan baris TXT | Temuan |
|---|---|---|
| `FoodBD-1633` | `test/labels/FoodBD-1633.txt`, baris 2 dan 4 | Polygon `fish` (class 26) bergeometri identik; kedua baris TXT identik mentah. |
| `FoodBD-1652` | `test/labels/FoodBD-1652.txt`, baris 2 dan 4 | Polygon `potato` (class 50) bergeometri identik; kedua baris TXT identik mentah. |
| `FoodBD-1533` | `train/labels/FoodBD-1533.txt`, baris 4 dan 6 | Geometri polygon identik tetapi kelas berbeda: `vaji` (63) dan `vegetable` (64). Belum diketahui apakah anotasi umum/spesifik yang disengaja atau duplikasi salah. |

Kasus disimpan di [polygon_anomalies.csv](foodbd_integrity_diagnostics/polygon_anomalies.csv). Jangan menghapus atau menggabungkan polygon sebelum dibandingkan dengan anotasi sumber dan aturan label.

Publikasi FoodBD melaporkan 12.575 anotasi. Hitungan lokal 13.485 lebih banyak 910 polygon. Tidak ada `FoodBD_Meta_data.csv`, README rilis, checksum, atau metadata anotasi di root lokal untuk menerangkan selisih. Karena itu penyebab selisih belum dapat ditentukan; tidak ada polygon yang dibuang untuk menyamakan angka. Publikasi juga menjelaskan file TXT sebagai class ID diikuti koordinat polygon dan menyebut file metadata yang semestinya menyertai data. [Artikel data FoodBD](https://pmc.ncbi.nlm.nih.gov/articles/PMC12801922/).

Contoh rendering asli tetap tersedia di [foodbd_polygon_mask_example.png](foodbd_polygon_mask_example.png); contoh itu menunjukkan format dapat dirasterisasi, tetapi bukan validasi visual semua instance.

## 2. Audit empat ID lintas split

Terdapat empat basename yang muncul di lebih dari satu direktori split. Tidak ada gambar dengan SHA-256 identik di seluruh 3.523 file. Pada setiap pasangan di bawah, label TXT **identik persis** antar-split, sedangkan bytes gambar berbeda. MAE 32x32 adalah selisih grayscale kasar pada skala intensitas 0-255, hanya indikator kandidat kemiripan dan bukan bukti identitas.

| ID | Lokasi | Byte gambar (split A / B) | TXT identik | Kelas dan jumlah anotasi di kedua TXT | MAE grayscale 32x32 |
|---|---|---:|---|---|---:|
| `FoodBD-0888` | train / valid | 49.834 / 48.192 | ya | `kumra-vaji` x1, `rice` x1 | 0,086 |
| `FoodBD-1103` | train / valid | 73.593 / 74.431 | ya | `carrot`, `cucumber`, `daal`, `potol`, `rice` masing-masing x1 | 0,094 |
| `FoodBD-1217` | train / valid | 63.704 / 64.571 | ya | `banana`, `carrot`, `chicken`, `ruti` masing-masing x1 | 0,099 |
| `FoodBD-3083` | valid / test | 93.264 / 93.177 | ya | `beef` x1, `ruti` x1 | 0,050 |

Detail path dan SHA-256 penuh berada di [split_id_collisions.csv](foodbd_integrity_diagnostics/split_id_collisions.csv). Folder dan `data.yaml` membuktikan salinan lokal menempatkan ID yang sama pada split berbeda. Hash membuktikan bytes tidak identik; basename dan TXT yang identik serta selisih grayscale kecil menjadikannya kandidat salinan gambar terkait yang kuat. **Penyebab asalnya belum dapat dipastikan**: file lokal tidak cukup untuk membedakan split resmi yang keliru, ekspor/penyalinan ganda, atau referensi basename yang dipakai ulang untuk gambar terkait. Jangan memindah gambar atau memilih salah satu salinan tanpa sumber/provenance.

Tidak ada ID yang berulang dua kali dalam direktori split yang sama. Empat ID terulang pada split berbeda; khusus `FoodBD-3083`, satu key CSV nutrisi juga cocok dengan dua file berbeda (valid dan test).

## 3. Rekonsiliasi CSV nutrisi

`MealNutrition1837_All.csv` memiliki tepat 1.837 baris, 1.837 nilai `FoodImage` unik, tidak ada sel kosong, dan keenam kolom target terbaca numerik. Join dilakukan hanya dengan basename persis; tidak ada pencocokan berdasarkan kelas atau tebakan.

| Status join | Jumlah baris | ID/keterangan |
|---|---:|---|
| Satu gambar yang cocok | 1.832 | Pemetaan basename satu-ke-satu. |
| Ambigu | 1 | `FoodBD-3083.jpg` cocok dengan `valid/images/FoodBD-3083.jpg` dan `test/images/FoodBD-3083.jpg`. Kedua file berbeda SHA tetapi label TXT-nya sama. Tidak dipilih salah satunya. |
| Tidak ada gambar cocok | 4 | `FoodBD-2282.jpg`, `FoodBD-2383.jpg`, `FoodBD-3381.jpg`, `FoodBD-3508.jpg`; tidak ditemukan basename tersebut di direktori image train/valid/test. |

Setiap field asli dipertahankan pada [nutrition_join_audit.csv](foodbd_integrity_diagnostics/nutrition_join_audit.csv) bersama status, path kandidat, dan alasan join.

Nama kolom tidak diubah: `FoodImage`, `CHO`, `Protein`, `Fat`, `Fiber`, `Calorie`, `GL`. CSV tidak memiliki unit di nama/header kolom; unit tidak ditambahkan atau diasumsikan. CSV hanya memiliki key gambar, tidak ada object/instance ID, sehingga nilai numerik ditautkan ke **gambar/hidangan**, bukan polygon individual. Dokumentasi publik menyebut nilai nutrisi per gambar sebagai total hidangan hasil estimasi ahli, tetapi tidak ada dokumentasi tersebut dalam paket lokal; artikel menyatakan ahli memperkirakan porsi/berat bahan dan mengagregasi nutrisi per image. Itu berarti label bukan pengukuran berat aktual. CSV lokal tidak mempunyai field `Weight` atau berat aktual. Jangan membagi nutrisi meal-level ke polygon atau menurunkan label berat dari `GL`. [Artikel data FoodBD](https://pmc.ncbi.nlm.nih.gov/articles/PMC12801922/).

## 4. Split baru yang direkomendasikan (belum dibuat)

Jangan gunakan direktori split apa adanya untuk evaluasi yang mengasumsikan independensi: ID yang sama melintasi train/validation dan validation/test. Jangan memindahkan file sumber. Setelah identitas/provenance diselesaikan:

1. Pertahankan direktori dan split asli sebagai bukti sumber yang immutable.
2. Buat manifest turunan yang merekam path relatif file aktual, basename, seluruh kelas/polygon, hash, grup, dan split; satu basename/grup tidak boleh muncul di lebih dari satu split.
3. Gunakan metadata asli untuk mengelompokkan gambar terkait berdasarkan identitas hidangan/pengambilan/sesi bila tersedia. Gabungkan juga SHA duplikat exact. Near-duplicate candidates harus diklarifikasi; kesamaan visual saja bukan bukti final.
4. Buat group-aware train/validation/test baru dengan proporsi sedekat mungkin 70/20/10 setelah grup terbentuk dan class/macro-label balance ditinjau. Tidak ada manifest final sampai konflik terpecahkan.
5. Bekukan test untuk evaluasi final satu kali; jangan gunakan test untuk pemilihan model, early stopping, atau tuning. Nutrisi dan label multi-class harus mengikuti grup split yang sama.

## 5. Checklist sebelum training

### Recognition multi-label

- [ ] Cocokkan `data.yaml` class ID/name dengan anotasi sumber; pertahankan seluruh 67 label.
- [ ] Bentuk target multi-hot per gambar dari set class ID pada semua polygon; jangan pakai softmax/top-1 single-label untuk hidangan multi-objek.
- [ ] Selesaikan/kelompokkan empat collision ID dan metadata relasi gambar sebelum manifest.
- [ ] Tinjau dukungan long-tail per split; kelas `egg` tidak muncul di test lokal.
- [ ] Kandidat EfficientNet-B0 memerlukan head 67 sigmoid outputs dan loss multi-label seperti BCE-with-logits. Checkpoint 19 kelas ECUSTFD tidak langsung menjadi head FoodBD.
- [ ] Laporkan exact-match/subset accuracy dan macro F1 per kelas (serta support); test hanya setelah keputusan model dibekukan.

### U-Net segmentation

- [ ] Cocokkan jumlah polygon lokal dengan rilis/protokol sumber dan klarifikasi selisih 910.
- [ ] Tinjau duplikasi geometri `FoodBD-1633`, `FoodBD-1652`, dan geometri lintas-kelas `FoodBD-1533`; jangan hapus otomatis.
- [ ] Verifikasi transformasi koordinat dan rasterisasi terhadap overlay sampel yang representatif dan edge cases.
- [ ] Tentukan semantic mask 68 nilai (background + 67 class) atau binary union sebelum run; jika mask multiclass, ukur piksel overlap dan tetapkan aturan ignore/priority yang terdokumentasi.
- [ ] Sinkronkan semua transformasi spasial image/mask; periksa ukuran, nilai unik, mask kosong, dan preview overlay seluruh kelompok sampel.
- [ ] Laporkan foreground macro mIoU dan Dice; nyatakan kebijakan kelas tanpa support dan piksel ignore.

### Regresi nutrisi hidangan

- [ ] Pulihkan/konfirmasi empat gambar tidak cocok dan identitas tunggal `FoodBD-3083` melalui metadata sumber; jangan menebak join.
- [ ] Pastikan units dan definisi setiap kolom dari sumber lokal/dokumentasi rilis; simpan nama asli `CHO`, `Protein`, `Fat`, `Fiber`, `Calorie`, `GL`.
- [ ] Nyatakan target sebagai nilai image/meal-level estimasi ahli, bukan berat terukur atau label per objek.
- [ ] Jangan mulai portion/weight regression tanpa field gram target yang eksplisit dan terpetakan; validasi terpisah diperlukan untuk measured weight.
- [ ] Join nutrition subset ke manifest group-aware yang sama, hanya gunakan train/validation untuk pengembangan, simpan test sampai evaluasi final.
- [ ] Laporkan MAE dan RMSE terpisah per `CHO`, `Protein`, dan `Fat`; calorie/fiber/GL dapat menjadi target tambahan yang ditetapkan sebelumnya.

## Status masalah

Status hanya menandai bukti yang saat ini ada; `resolved` pada pemeriksaan struktural tidak berarti kualitas semantik semua polygon telah disetujui.

| Masalah | Status | Alasan |
|---|---|---|
| Sumber 13.485 baris polygon | **resolved** | Dihitung langsung dari seluruh TXT: 9.364 train, 2.748 valid, 1.373 test. |
| Semua JPG punya TXT, kelas/koordinat valid, polygon degenerate | **resolved** untuk validasi struktural | Tidak ditemukan pasangan hilang, class ID di luar 0-66, koordinat di luar [0,1], atau luas nol. Ini bukan audit visual penuh. |
| Selisih 13.485 lokal vs 12.575 publikasi | **requires source metadata** | Metadata, README versi, dan checksum rilis tidak tersedia lokal. Penyebab belum dapat dijelaskan. |
| ID lintas split `0888`, `1103`, `1217`, `3083` | **requires source metadata** | Collision split, byte image berbeda, TXT identik; sumber tidak menerangkan apakah duplicate export, variasi foto, atau salah split. |
| Geometri duplikat di `1633`/`1652` dan lintas-kelas di `1533` | **unresolved** | Perlu konfirmasi manual terhadap anotasi asli/protokol sebelum menyatakan salah; tidak ada penghapusan. |
| 1.832 pasangan nutrisi satu-ke-satu | **resolved** | Exact basename join unik ditemukan. |
| CSV `FoodBD-3083.jpg` ambigu | **requires source metadata** | Dua kandidat file di split berbeda. |
| Empat baris nutrisi tanpa image | **requires source metadata** | Empat basename tidak ada di folder image lokal. |
| Tingkat label nutrisi | **resolved** sebagai image-keyed | CSV memiliki satu row per `FoodImage`, tanpa instance ID; semantik agregasi hidangan didukung dokumentasi artikel, bukan README lokal. |
| Target berat aktual | **resolved**: tidak tersedia | Tidak ada kolom berat di CSV lokal; hanya estimasi porsi/berat yang dijelaskan sumber publik. |
| Manifest final leak-safe dan kesiapan training | **unresolved** | Tunggu rekonsiliasi provenance, empat ID split, selisih anotasi, polygon anomaly, dan nutrition join. |

## Diagnostik yang dibuat

Disimpan di `reports/foodbd_integrity_diagnostics/` tanpa menulis ke data asli:

- `annotation_source_summary.csv` - hitungan gambar, TXT, baris polygon, file label hilang, dan baris anotasi struktural invalid per split.
- `split_id_collisions.csv` - empat kasus dengan path, ukuran, SHA-256, class counts, identitas TXT, dan similarity heuristic.
- `nutrition_join_audit.csv` - 1.837 row asli dengan kolom asli plus status/patokan join.
- `polygon_anomalies.csv` - polygon duplikat/geometri lintas kelas yang perlu review.

**Kesimpulan:** FoodBD memiliki dukungan data yang kuat untuk recognition multi-label dan segmentation berbasis polygon; nutrition regression tingkat hidangan tersedia secara terbatas dan memakai estimasi ahli. Regresi berat/porsi terukur belum tersedia. Dataset belum siap untuk training yang hasilnya dapat dipercaya sampai konflik split, perbedaan versi/anotasi, dan join nutrisi di atas diselesaikan.
