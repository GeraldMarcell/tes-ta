# Audit sampel salah klasifikasi recognition ECUSTFD

## Metode dan validasi reproduksi

Prediksi terdahulu tidak menyimpan ID sampel atau confidence, jadi inferensi validation direproduksi dari checkpoint best yang sama memakai manifest, crop VOC ter-clamp, resize 224×224, normalisasi ImageNet, urutan batch 16, dan evaluasi tanpa gradien. Confusion matrix hasil reproduksi **identik** dengan CSV evaluasi untuk masing-masing model. Checkpoint yang digunakan: MobileNetV2 best epoch 1, EfficientNet-B0 best epoch 1, dan ResNet-50 best epoch 3. Setiap model memproses 350 baris validation; tidak ada test set yang dibaca.

Confidence di CSV adalah nilai softmax maksimum untuk prediksi kelas model; ini bukan ukuran kalibrasi. CSV mencatat ID gambar, label aktual/prediksi, confidence, lokasi relatif dan absolut, `group_id`, object index, XML, koordinat asli dan crop, ukuran gambar, serta pemeriksaan konsistensi. Contact sheet menampilkan gambar sumber dengan kotak merah dan crop yang diberikan ke classifier.

## Sampel yang diekspor

- **MobileNetV2, pear→peach:** 8 kesalahan, seluruhnya gambar ber-prefix `pear002` (`group_id=pear002`), pada view T yang berbeda. Jadi ini 8 crop validation tetapi hanya satu grup prefix provisional, bukan 8 objek independen yang terverifikasi.
- **EfficientNet-B0:** 9 kesalahan yang menyangkut target prioritas: 2 pear→bun; 2 false negative banana (banana→peach dan banana→bread); bun→banana; qiwi→bun; fired_dough_twist→litchi; tomato→bun; dan plum→tomato. Untuk empat kelas F1 lebih rendah, ini mencakup false negative dan false positive yang relevan.
- **ResNet-50, plum→apple:** 22 kesalahan, seluruhnya ber-prefix `plum001` (`group_id=plum001`) pada view S/T. Jumlah ini juga berasal dari satu grup prefix provisional, tidak 22 objek independen yang terverifikasi.

Daftar lengkap dan confidence per sampel: `outputs/evaluation/recognition_misclassified_samples.csv`.

## Pemeriksaan gambar, XML, dan bounding box

Semua 39 gambar yang dipilih dapat dibaca. Pada seluruh baris, filename XML cocok dengan gambar, ukuran XML cocok dengan ukuran dekode, label dan object index XML cocok dengan manifest, koordinat manifest cocok dengan XML, kotak crop tidak kosong, berada di dalam batas gambar, dan tidak perlu clipping. Syarat geometris ini tidak menjamin kotak melingkupi objek yang disebut labelnya.

### Masalah anotasi yang terverifikasi

Pada **`tomato001S(4)`**, validation label/XML menyatakan object 0 sebagai tomato. Namun, box VOC-nya `xmin=119, ymin=373, xmax=178, ymax=434` (gambar 816x612) memotong area koin dan meja di kiri bawah, bukan tomat merah di tengah gambar. Crop berukuran 60x62 piksel (sekitar 0.74% area gambar). XML juga berisi object 1 `coin` dengan box `87,347,153,409`, yang berada di area sama dan bertumpang tindih dengan box tomato. Contact sheet menunjukkan ketidakcocokan lokasi ini secara langsung. Label kelas XML `tomato` sama dengan manifest, tetapi lokalisasi box untuk object tersebut salah secara semantik. Sampel ini diprediksi EfficientNet-B0 sebagai bun (confidence 0.189) dan merupakan satu false negative tomato.

Anotasi mentah tidak diubah dan tidak dibuat koordinat koreksi. Karena inferensi validation memakai crop dari manifest, prediksi dan skor yang melibatkan baris ini tidak merepresentasikan crop tomat yang benar. Error ini perlu dikecualikan atau dianotasi ulang melalui perubahan dataset/split yang terdokumentasi sebelum memakai sampel tersebut dalam analisis model lanjutan.

### Sampel lain

Inspeksi contact sheet tidak menemukan box kosong, terpotong batas, gambar gagal dibaca, atau ketidakcocokan teks label XML-manifest lain di antara sampel terpilih. Crop pear berlabel pear dan crop plum berlabel plum berada pada buah yang tampak di tengah box. Sebagian gambar pear berbentuk bulat dan terang, tetapi itu saja tidak membuktikan labelnya salah atau memastikan alasan classifier memilih peach/bun. Pada seri plum, beberapa view tampak serupa; label plum sesuai XML dan box mencakup buah. Tidak ada dasar dari contact sheet untuk mengubah label atau menyimpulkan penyebab visual tertentu.

CSV dan sheet adalah sampel salah yang diprioritaskan sesuai permintaan, bukan audit semantik seluruh 350 validation crop. Pemeriksaan tambahan terhadap semua box bisa diperlukan sebelum klaim kualitas anotasi yang menyeluruh.

## Implikasi pada empat kelas EfficientNet-B0

- **banana (F1 0.936):** dua sampel aktual terlewat dan satu false positive dari bun. Crop terpilih tampak sesuai lokasi objek; tidak terverifikasi ada masalah anotasi pada sampel ini.
- **bun (F1 0.737, support 8):** satu sampel bun diprediksi banana dan empat false positive masuk ke bun; dua berasal dari pear002, satu dari qiwi, dan satu dari crop tomato001S(4) yang salah lokasi. Sampel pear/qiwi perlu ditafsirkan sebagai prediksi pada crop yang diberikan, bukan bukti penyebab.
- **litchi (F1 0.966):** recall 1.0; satu false positive datang dari fired_dough_twist. Box dan label pada gambar yang ditinjau sesuai, tetapi kebingungan ini sendiri tidak membuktikan kemiripan visual sebagai penyebab.
- **tomato (F1 0.950):** ada satu false negative dari `tomato001S(4)` dengan box salah lokasi, serta satu false positive plum→tomato. Nilai F1 ini dipengaruhi minimal oleh satu contoh validation yang crop-nya bukan objek berlabel tomato.

## Kesimpulan dan batas pengaruh terhadap pemilihan model

Ada **satu masalah konkret** pada anotasi lokalisasi: bounding box object tomato pada `tomato001S(4)` mengarah ke koin/meja. Tidak ada masalah file yang tidak terbaca atau koordinat di luar batas pada 39 sampel terpilih lainnya. Kesalahan ini cukup untuk menandai evaluasi kelas tomato EfficientNet sebagai terkontaminasi dan tidak layak dipakai tanpa catatan; jangan mengoreksi skor secara spekulatif karena prediksi untuk crop tomat yang benar belum diketahui.

Error MobileNet pear dan ResNet plum terkumpul dalam satu prefix group masing-masing. Ini bukan bukti leakage lintas train/validation, tetapi berarti 8 dan 22 kesalahan tersebut tidak independen pada tingkat grup provisional. Audit grup terdahulu juga belum dapat memastikan identitas fisik objek lintas prefix.

Temuan tomato dapat memengaruhi perbandingan kelas tomato dan perlu ditangani sebelum keputusan berbasis metrik kelas. Satu sampel tidak cukup untuk menjelaskan selisih accuracy keseluruhan model atau menetapkan model final. Hasil tetap pilot validation, dengan kelas grape/lemon tidak terukur karena support nol. Tidak ada perubahan checkpoint, anotasi, manifest, atau artefak evaluasi terdahulu.

## Artefak

- CSV: `outputs/evaluation/recognition_misclassified_samples.csv`
- Contact sheet MobileNetV2: `outputs/evaluation/misclassification_contact_sheet_mobilenet_v2.png`
- Contact sheet EfficientNet-B0: `outputs/evaluation/misclassification_contact_sheet_efficientnet_b0.png`
- Contact sheet ResNet-50: `outputs/evaluation/misclassification_contact_sheet_resnet50.png`
