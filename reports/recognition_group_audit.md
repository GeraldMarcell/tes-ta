# Audit grup dan potensi kebocoran recognition ECUSTFD

## Ruang lingkup

Pemeriksaan baca-saja ini mencakup struktur `data/raw/ECUSTFD`, XML dan gambar yang dirujuk manifest train/validation, kode pembentukan grup, serta laporan audit evaluasi sebelumnya. Tidak ada gambar test yang dibaca untuk analisis model, dan tidak ada dataset, manifest, checkpoint, atau laporan lama yang diubah. Hash SHA-256 dihitung untuk 1.245 file gambar unik yang terdaftar di manifest (train dan validation saja).

## Temuan terverifikasi

- Struktur raw berisi `JPEGImages`, `Annotations`, `ImageSets`, `density.xls`, dan `density_export.csv`. Masing-masing `JPEGImages` dan `Annotations` memiliki 2.978 file; `ImageSets/Main` memiliki `train.txt`, `val.txt`, `trainval.txt`, dan `test.txt`. Isi test split tidak dibaca.
- Seluruh 1.245 ID pada daftar resmi `trainval.txt` memiliki pasangan gambar dan XML; tidak ada ID berulang pada daftar itu. Nama dasarnya memakai pola seperti `apple001S(1).JPG` dengan XML `apple001S(1).xml` yang bersesuaian.
- Semua 1.245 ID trainval cocok dengan pola `^(.+?\d+)[ST]\(\d+\)$`. Ada 82 prefix grup; nama mengandung kelas dan nomor sampel, lalu penanda `S`/`T` dan nomor urut dalam tanda kurung. Di trainval terdapat 627 gambar berpenanda S dan 618 berpenanda T.
- XML mengulang nama file dan menyediakan ukuran gambar, objek/kelas, bounding box, serta elemen `segmented=0`. Field `source` tersedia pada semua XML yang diperiksa; nilainya generik (`database=My Database`, `annotation=VOC2007`, `image=flickr`, `flickrid=NULL`). Tidak ditemukan path pengambilan, ID sesi, waktu, atau ID objek fisik tambahan. Ukuran paling umum 816×612; tidak ada gambar dengan EXIF pada file yang dicek.
- SHA-256: 1.245 file gambar manifest menghasilkan 1.245 hash berbeda. Tidak ditemukan duplikasi byte identik, baik lintas train/validation maupun lintas prefix.
- Manifest saat ini menghasilkan 62 grup train dan 20 grup validation, tanpa `group_id` overlap dan tanpa `image_id` overlap. Seluruh crop dari satu gambar tetap berada di split yang sama.

## Interpretasi dan batas bukti

Penamaan mendukung pengelompokan konservatif berdasarkan prefix: variasi S/T dan nomor urut pada prefix yang sama disatukan oleh regex di `src/recognition.py`. Ini merupakan indikasi kuat bahwa frame/view dalam satu seri filename tidak tersebar antar split pada manifest sekarang.

Namun, metadata lokal tidak membuktikan secara independen bahwa `S` dan `T` adalah sesi, sudut pandang, atau urutan tertentu, dan tidak menyatakan secara eksplisit bahwa tiga digit setelah nama kelas adalah ID objek fisik. Lebih penting, metadata tidak dapat memastikan apakah dua prefix berbeda menunjuk objek fisik yang benar-benar berbeda atau sesi pemotretan berbeda. Tidak adanya hash identik tidak membuktikan tidak adanya foto nyaris sama atau pengambilan ulang objek yang sama. Tidak dilakukan pemeriksaan kemiripan visual karena kemiripan tampilan sendiri tidak dapat menetapkan identitas fisik tanpa provenance yang dapat dipercaya.

Dengan bukti yang tersedia, **tidak ada bukti konkret duplikasi gambar eksak atau kebocoran grup yang teramati** antara train dan validation. Tetapi kebocoran objek fisik lintas prefix tidak dapat disingkirkan atau dibuktikan dari data lokal ini. Ini adalah keterbatasan metadata, bukan bukti bahwa kebocoran tersebut terjadi.

## Kelayakan manifest dan rekomendasi

Manifest layak dipakai untuk eksperimen lanjutan yang konsisten dengan pilot sebagai **split provisional berbasis prefix**: struktur grouping dan pemisahan train/validation yang ditetapkan berjalan tanpa overlap terukur. Hasilnya sebaiknya tidak diklaim sebagai evaluasi generalisasi antar-objek fisik yang sepenuhnya terjamin.

Untuk klaim lebih kuat, perlu provenance resmi yang menjelaskan makna prefix/S/T/nomor frame atau tabel ID objek/sesi yang otoritatif. Jika provenance tersebut tersedia, evaluasi leakage perlu dilakukan sebagai eksperimen split baru yang terdokumentasi; jangan mengedit manifest saat ini diam-diam. Hash/kemiripan visual hanya dapat menandai kandidat duplikat, bukan membuktikan identitas dua objek.

Tidak ada training, pemilihan model, ataupun evaluasi pada test set dalam audit ini.
