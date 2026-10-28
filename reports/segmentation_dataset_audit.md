# Audit dataset segmentasi makanan

Tanggal pemeriksaan: 2026-10-27. Pemeriksaan file lokal bersifat baca-saja. Tidak ada dataset, anotasi, manifest, checkpoint, atau eksperimen recognition yang diubah; tidak ada training atau unduhan dataset/weights.

## Temuan pada `C:\TA\data`

Di `data/raw` terdapat `ECUSTFD` dan `processed`. `processed` kosong. Pencarian rekursif di `data` tidak menemukan direktori UNIMIB2016, folder mask/segmentation, atau dataset gambar lain. Tidak ada file anotasi raster `.png`, `.tif/.tiff`, `.bmp`, atau `.gif` di ECUSTFD.

ECUSTFD lokal berisi 2.978 JPG, 2.978 XML, empat file split TXT, `density.xls`, dan `density_export.csv`. Semua 2.978 XML berhasil diparse; setiap root memiliki `<segmented>0`, dan tidak ada elemen mask, segmentation, polygon, atau RLE. Label objek mencakup 19 kelas makanan serta `coin`. Ukuran yang tercatat paling banyak 816 x 612 x 3 (2.803 gambar); berikutnya 504 x 378 x 3 (154) dan 612 x 612 x 3 (16). Tiga ukuran lain tercatat pada lima gambar sisanya. XML menyediakan bounding box, bukan ground truth piksel. Oleh karena itu, anotasi ini tidak mendukung supervised segmentation.

## UNIMIB2016: apa yang diketahui dan belum diketahui

**Terverifikasi dari file lokal:** UNIMIB2016 tidak ditemukan di `C:\TA\data`; jumlah gambar, struktur file, format mask aktual, kelas, ukuran gambar, dan duplikatnya tidak dapat diperiksa pada mesin ini.

**Informasi publikasi, bukan verifikasi atas salinan lokal:** sebuah paper computer-vision melaporkan UNIMIB2016 berisi 1.027 gambar dengan 73 kategori dan ground-truth food mask yang dibuat manual dengan poligon. Mask-nya menggabungkan seluruh makanan menjadi satu kelas, bukan memberi label kelas pada setiap piksel makanan. Dengan demikian, target yang didukung anotasi tersebut adalah **binary semantic segmentation: food vs background**, bukan multiclass food segmentation. Lihat [paper CVPR tentang benchmark food segmentation](https://computer-vision-the-wild.github.io/cvpr-2023/static/cvpr2023/accepted_papers/18/CameraReady/CVinW2023_FoodSeg_CR.pdf), bagian 2.1 dan Tabel 1.

Informasi publikasi membuat UNIMIB2016 kandidat yang masuk akal untuk eksperimen binary segmentation, tetapi anotasi encoding, lisensi, pemetaan file gambar-mask, kelengkapan mask, kelas di mask, serta ketersediaan split/provenance harus dicek ulang terhadap salinan yang benar-benar diperoleh. Gambar tray dan makanan campuran juga berbeda dari gambar objek tunggal ECUSTFD; keberhasilan pada dataset tersebut tidak dengan sendirinya membuktikan kinerja pada domain ECUSTFD. Karena UNIMIB belum tersedia lokal, semua detail implementasi di atas belum diverifikasi pada file dataset.

## Rekomendasi kandidat dan baseline

- **Dataset kandidat:** UNIMIB2016, bila tujuannya adalah baseline segmentasi **makanan-vs-latar** dan mask binary-nya dapat diverifikasi secara lokal. Kandidat ini punya anotasi segmentasi yang disebut dalam literatur, tetapi domain tray merupakan batas generalisasi untuk ECUSTFD.
- **Baseline:** U-Net binary segmentation dengan satu kanal logit, sigmoid/BCE-with-logits (atau Dice+BCE yang ditetapkan sebelum eksperimen), dan mask target bernilai 1 untuk area makanan serta 0 untuk latar. Pertahankan ukuran/crop dan transformasi geometris identik untuk gambar dan mask. Jangan mulai implementasi/training sebelum pasangan gambar-mask dan encoding target diperiksa. DeepLabV3+ dapat menjadi pembanding setelah baseline dan data pipeline terverifikasi.
- **Evaluasi:** laporkan IoU/Jaccard dan Dice pada mask binary, dihitung per gambar lalu diringkas dengan macro mean; sertakan juga agregat pixel-level bila berguna. Tetapkan eksplisit cara menangani mask kosong dan ambang prediksi, dan jangan menganggap pixel sebagai sampel independen untuk split.

Untuk ECUSTFD saat ini, binary-vs-multiclass **tidak dapat ditentukan dari anotasi mask karena mask tidak ada**. Bounding box dapat mendukung deteksi atau lokalisasi, tetapi mengubahnya menjadi filled rectangles tidak menghasilkan ground truth segmentation dan tidak boleh dipakai sebagai label mask.

## Split dan risiko kebocoran

Mask/dataset UNIMIB tidak tersedia, jadi duplikasi atau relasi gambar di dalamnya belum dapat diuji. Saat dataset didapat, buat split hanya setelah memeriksa ID/provenance untuk tray, pengambilan, atau kelompok terkait; semua gambar dalam kelompok yang sama harus berada di satu split. Hash SHA-256 mendeteksi duplikat byte-identik. Pemeriksaan perceptual hash/embedding hanya dapat menandai kandidat near-duplicate untuk tinjauan; kesamaan visual atau kelas saja tidak membuktikan identitas objek/sesi.

Untuk ECUSTFD, audit recognition yang sudah ada melaporkan 1.245 gambar trainval dengan 1.245 hash berbeda, 82 prefix provisional dan nol overlap prefix pada manifest train/validation saat ini. Prefix menggabungkan urutan filename S/T; metadata lokal tidak membuktikan apakah prefix berbeda bisa berasal dari objek/sesi yang sama. Ini split provisional untuk classification crops, bukan split segmentasi berbasis mask. Official train dan val dilaporkan memiliki 77 prefix yang sama jika digunakan terpisah; jangan menggabungkannya tanpa grouping ulang. Rujukan lokal: `reports/recognition_group_audit.md` dan `reports/dataset_inspection.md`.

## Hambatan dan langkah berikutnya

Belum ada dataset lokal yang menyediakan mask terverifikasi, jadi belum ada ground truth untuk eksperimen segmentasi dan belum tepat membuat script training. Langkah selanjutnya adalah memperoleh dataset segmentasi melalui saluran yang diizinkan, menaruhnya di lokasi data proyek, lalu melakukan inspeksi lokal atas dokumentasi/lisensi, pasangan gambar-mask, encoding dan kelas, ukuran, split, serta duplikat/kelompok terkait. Jika dipilih UNIMIB2016 dan mask-nya sesuai laporan publikasi, mulai dengan U-Net binary food/background dan evaluasi IoU serta Dice. Jika tujuan akhirnya adalah segmentasi 19 kelas ECUSTFD, dibutuhkan anotasi piksel multiclass yang sesuai atau pelabelan manusia yang tervalidasi; bounding box ECUSTFD tidak mencukupi.
