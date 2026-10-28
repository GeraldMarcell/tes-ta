# Analisis per kelas evaluasi recognition ECUSTFD

Analisis ini memakai classification report, confusion matrix, metrics JSON, serta manifest validation yang sudah tersedia. Tidak ada training atau inferensi ulang, tidak ada akses ke test split, dan artefak sumber tidak diubah. Nilai per kelas disalin dari laporan evaluasi tersimpan; ringkasan macro/weighted memakai definisi yang sama seperti evaluator.

## Validasi bukti dan definisi metrik

Checkpoint pada metrics JSON dan metadata berkas sudah dicocokkan: MobileNetV2 `recognition_mobilenet_v2_pilot_best.pt` (best epoch 1), EfficientNet-B0 `recognition_efficientnet_b0_pilot_best.pt` (best epoch 1), dan ResNet-50 `recognition_resnet50_pilot_best.pt` (best epoch 3). Ketiga model memakai 350 baris validation yang sama, urutan 19 kelas yang sama, dan confusion matrix berjumlah 350; jumlah support per baris matriks cocok dengan support manifest.

Precision, recall, dan F1 per kelas menggunakan confusion matrix dengan baris = kelas aktual dan kolom = prediksi. `zero_division=0` dipakai untuk kelas ber-support positif yang tidak pernah diprediksi. Macro average adalah rata-rata tanpa bobot atas 17 kelas dengan support positif; weighted average membobot metrik kelas dengan support aktual. Grape dan lemon ber-support nol sehingga skor per kelas N/A dan dikecualikan dari kedua average tersebut. Karena itu, prediksi ke kelas tanpa support tidak langsung mengurangi precision/F1 macro atau weighted, walaupun memengaruhi accuracy.

## Classification report per model

### MobileNetV2

| Kelas | Support aktual | Precision | Recall | F1-score |
|---|---:|---:|---:|---:|
| apple | 34 | 0.872 | 1.000 | 0.932 |
| banana | 24 | 0.920 | 0.958 | 0.939 |
| bread | 16 | 1.000 | 0.938 | 0.968 |
| bun | 8 | 0.750 | 0.750 | 0.750 |
| doughnut | 6 | 0.462 | 1.000 | 0.632 |
| egg | 18 | 0.857 | 1.000 | 0.923 |
| fired_dough_twist | 20 | 1.000 | 0.800 | 0.889 |
| grape | 0 | N/A | N/A | N/A |
| lemon | 0 | N/A | N/A | N/A |
| litchi | 14 | 1.000 | 1.000 | 1.000 |
| mango | 13 | 0.786 | 0.846 | 0.815 |
| mooncake | 32 | 0.941 | 1.000 | 0.970 |
| orange | 12 | 1.000 | 0.667 | 0.800 |
| peach | 16 | 0.448 | 0.812 | 0.578 |
| pear | 40 | 0.966 | 0.700 | 0.812 |
| plum | 44 | 1.000 | 0.682 | 0.811 |
| qiwi | 9 | 1.000 | 0.889 | 0.941 |
| sachima | 24 | 0.857 | 1.000 | 0.923 |
| tomato | 20 | 1.000 | 0.950 | 0.974 |

### EfficientNet-B0

| Kelas | Support aktual | Precision | Recall | F1-score |
|---|---:|---:|---:|---:|
| apple | 34 | 0.971 | 1.000 | 0.986 |
| banana | 24 | 0.957 | 0.917 | 0.936 |
| bread | 16 | 0.941 | 1.000 | 0.970 |
| bun | 8 | 0.636 | 0.875 | 0.737 |
| doughnut | 6 | 1.000 | 1.000 | 1.000 |
| egg | 18 | 0.947 | 1.000 | 0.973 |
| fired_dough_twist | 20 | 1.000 | 0.950 | 0.974 |
| grape | 0 | N/A | N/A | N/A |
| lemon | 0 | N/A | N/A | N/A |
| litchi | 14 | 0.933 | 1.000 | 0.966 |
| mango | 13 | 1.000 | 1.000 | 1.000 |
| mooncake | 32 | 1.000 | 1.000 | 1.000 |
| orange | 12 | 1.000 | 1.000 | 1.000 |
| peach | 16 | 0.938 | 0.938 | 0.938 |
| pear | 40 | 1.000 | 0.925 | 0.961 |
| plum | 44 | 1.000 | 0.977 | 0.989 |
| qiwi | 9 | 1.000 | 0.889 | 0.941 |
| sachima | 24 | 1.000 | 1.000 | 1.000 |
| tomato | 20 | 0.950 | 0.950 | 0.950 |

### ResNet-50

| Kelas | Support aktual | Precision | Recall | F1-score |
|---|---:|---:|---:|---:|
| apple | 34 | 0.540 | 1.000 | 0.701 |
| banana | 24 | 0.913 | 0.875 | 0.894 |
| bread | 16 | 0.750 | 0.375 | 0.500 |
| bun | 8 | 0.333 | 1.000 | 0.500 |
| doughnut | 6 | 0.062 | 0.167 | 0.091 |
| egg | 18 | 0.900 | 1.000 | 0.947 |
| fired_dough_twist | 20 | 0.714 | 1.000 | 0.833 |
| grape | 0 | N/A | N/A | N/A |
| lemon | 0 | N/A | N/A | N/A |
| litchi | 14 | 1.000 | 0.286 | 0.444 |
| mango | 13 | 0.714 | 0.769 | 0.741 |
| mooncake | 32 | 0.857 | 0.562 | 0.679 |
| orange | 12 | 1.000 | 1.000 | 1.000 |
| peach | 16 | 0.706 | 0.750 | 0.727 |
| pear | 40 | 0.781 | 0.625 | 0.694 |
| plum | 44 | 1.000 | 0.409 | 0.581 |
| qiwi | 9 | 0.778 | 0.778 | 0.778 |
| sachima | 24 | 1.000 | 0.542 | 0.703 |
| tomato | 20 | 0.792 | 0.950 | 0.864 |

## Jumlah kesalahan menurut kelas aktual

Jumlah kesalahan = total baris confusion matrix dikurangi nilai diagonal untuk kelas aktual tersebut. Angka nol pada grape/lemon berarti tidak ada sampel aktual, bukan bukti bahwa kelas itu berhasil dikenali.

| Kelas aktual | Support | MobileNetV2 | EfficientNet-B0 | ResNet-50 |
|---|---:|---:|---:|---:|
| apple | 34 | 0 | 0 | 0 |
| banana | 24 | 1 | 2 | 3 |
| bread | 16 | 1 | 0 | 10 |
| bun | 8 | 2 | 1 | 0 |
| doughnut | 6 | 0 | 0 | 5 |
| egg | 18 | 0 | 0 | 0 |
| fired_dough_twist | 20 | 4 | 1 | 0 |
| grape | 0 | 0 (N/A) | 0 (N/A) | 0 (N/A) |
| lemon | 0 | 0 (N/A) | 0 (N/A) | 0 (N/A) |
| litchi | 14 | 0 | 0 | 10 |
| mango | 13 | 2 | 0 | 3 |
| mooncake | 32 | 0 | 0 | 14 |
| orange | 12 | 4 | 0 | 0 |
| peach | 16 | 3 | 1 | 4 |
| pear | 40 | 12 | 3 | 15 |
| plum | 44 | 14 | 1 | 26 |
| qiwi | 9 | 1 | 1 | 2 |
| sachima | 24 | 0 | 0 | 11 |
| tomato | 20 | 1 | 1 | 1 |

## Analisis confusion matrix

Pasangan dihitung sebagai kelas tak berurutan dengan menjumlahkan dua arah. `A->B` berarti label sebenarnya A diprediksi sebagai B. Pasangan dua arah hanya dinyatakan bila kedua sel off-diagonal bernilai positif; selain itu kesalahannya satu arah.

### MobileNetV2

- Recall terendah: **orange** = 0.667 (support 12). F1 terendah: **peach** = 0.578 (support 16).
- Pasangan dengan jumlah salah tertinggi:
  - **peach / pear: 8** (satu arah: pear->peach 8).
  - **doughnut / plum: 7** (satu arah: plum->doughnut 7).
  - **fired_dough_twist / sachima: 4** (satu arah: fired_dough_twist->sachima 4).
  - **peach / plum: 4** (satu arah: plum->peach 4).
  - **apple / plum: 3** (satu arah: plum->apple 3).
- Tidak ada pasangan dua arah (kedua arah positif) pada matriks ini.

### EfficientNet-B0

- Recall terendah: **bun** = 0.875 (support 8). F1 terendah: **bun** = 0.737 (support 8).
- Pasangan dengan jumlah salah tertinggi:
  - **bun / pear: 2** (satu arah: pear->bun 2).
  - **apple / peach: 1** (satu arah: peach->apple 1).
  - **banana / bread: 1** (satu arah: banana->bread 1).
  - **banana / bun: 1** (satu arah: bun->banana 1).
  - **banana / peach: 1** (satu arah: banana->peach 1).
- Tidak ada pasangan dua arah (kedua arah positif) pada matriks ini.

### ResNet-50

- Recall terendah: **doughnut** = 0.167 (support 6). F1 terendah: **doughnut** = 0.091 (support 6).
- Pasangan dengan jumlah salah tertinggi:
  - **apple / plum: 22** (satu arah: plum->apple 22).
  - **bun / pear: 13** (satu arah: pear->bun 13).
  - **doughnut / mooncake: 13** (satu arah: mooncake->doughnut 13).
  - **fired_dough_twist / sachima: 6** (satu arah: sachima->fired_dough_twist 6).
  - **apple / litchi: 4** (satu arah: litchi->apple 4).
- Pasangan dua arah yang teramati: doughnut->mango 1 dan mango->doughnut 2.

## Perbandingan model

| Model (checkpoint best) | Accuracy | Macro F1 | Weighted F1 | Kelas ber-support | Performa kelas terendah (F1) | Pasangan tertukar terbanyak |
|---|---:|---:|---:|---:|---|---|
| MobileNetV2 (epoch 1) | 0.8714 | 0.8621 | 0.8760 | 17/19 | peach (0.578) | peach/pear (pear->peach 8, 8 total) |
| EfficientNet-B0 (epoch 1) | 0.9686 | 0.9600 | 0.9695 | 17/19 | bun (0.737) | bun/pear (pear->bun 2, 2 total) |
| ResNet-50 (epoch 3) | 0.7029 | 0.6869 | 0.7064 | 17/19 | doughnut (0.091) | apple/plum (plum->apple 22, 22 total) |

EfficientNet-B0 memiliki F1 tertinggi secara unik pada 11 dari 17 kelas dan berbagi F1 tertinggi pada 2 kelas (orange dengan ResNet-50; qiwi dengan MobileNetV2). Pada 4 kelas lain, F1-nya di bawah model lain: banana (0.936 vs MobileNetV2 0.939), bun (0.737 vs 0.750), litchi (0.966 vs 1.000), tomato (0.950 vs 0.974). F1 EfficientNet-B0 setidaknya 0.90 pada 16/17 kelas; pengecualian utamanya bun (support 8). Dengan demikian keunggulannya tampak luas, bukan hanya berasal dari beberapa kelas, tetapi tidak seragam dan bukan yang tertinggi di semua kelas.

Dari pasangan kesalahan, EfficientNet-B0 hanya memiliki satu pasangan dengan lebih dari satu kesalahan gabungan (pear->bun, 2); pasangan teratas model lain mencapai 8 (pear->peach, MobileNetV2) dan 22 (plum->apple, ResNet-50). Perbandingan hitungan mentah ini dipengaruhi support tiap kelas dan tidak menerangkan penyebab kesalahan.

## Keterbatasan dan interpretasi

Grape dan lemon tidak mempunyai sampel validation, sehingga performanya belum diketahui. Pada checkpoint best yang dievaluasi, confusion matrix menunjukkan MobileNetV2 dan EfficientNet-B0 tidak mengeluarkan prediksi grape/lemon; ResNet-50 mengeluarkan empat prediksi lemon. Nilai N/A grape/lemon tetap tidak boleh ditafsirkan sebagai skor nol atau keberhasilan.

Laporan `recognition_evaluation_analysis.md` mendahului evaluasi ulang MobileNetV2 dan membahas checkpoint MobileNet lama/final. Rinciannya mengenai skor serta pasangan kesalahan MobileNetV2 tidak berlaku untuk laporan ini; tabel di atas memakai artefak evaluasi checkpoint best terbaru. Audit grup tetap menyebut split provisional berbasis prefix: tidak ada overlap prefix yang terukur, namun identitas objek fisik lintas prefix tidak dapat dipastikan dari metadata dataset.

Validation hanya berisi 350 crop dari split grup provisional dan sejumlah kelas memiliki dukungan kecil (misalnya doughnut 6, bun 8, qiwi 9). Hasil adalah analisis validation pilot, bukan estimasi generalisasi final. Tidak ada bukti pada matriks tentang kemiripan visual sebagai penyebab kebingungan; laporan ini hanya mencatat pasangan prediksi yang salah.

Tidak ada training, evaluasi test, perubahan checkpoint, dataset, manifest, ataupun laporan lama dalam tahap ini.
