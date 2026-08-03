# Deniz Canlıları Puzzle – Tema 02

İki katmanlı eğitici çocuk puzzle'ı. Bitmiş ölçü **320 × 180 mm**, dış köşeler 8 mm yuvarlatılmış, 8 canlı parçası.

Bu tema, çizimleri kodla üretmez. Görseller `varlik/kaynak/` altındaki hazır çizimlerden gelir; kod bunlardan üretime uygun siluet ve kesim konturu çıkarır. Kodla çizim denemesinin sonucu ve neden bırakıldığı `arastirma/gercekcilik-pilotu/` altındadır.

## Boru hattı

| Adım | Dosya | İş |
|---|---|---|
| 1 | `siluet.py` | Kaynak görselden siluet maskesi çıkarır, mm ölçeğine getirir, imalat uygunluğunu ölçer |
| 2 | `kesim.py` | Siluetten üretime uygun kesim konturu üretir (budama yöntemi) |
| 3 | `olustur.py` | Yerleşimi kurar, doğrular ve dört üretim dosyasını yazar |

### Zemin ayırma

Beyaz zemin, görsel kenarından taşırma (flood fill) ile ayrılır. Böylece gövde **içinde** kalan kapalı beyaz bölgeler (denizatının kuyruk halkasının ortası gibi) siluetin parçası kalır — lazer zaten yalnız dış konturu keser, iç delik açılmaz.

### Kesim konturu: budama

Kaynak çizimlerdeki ince uzuvlar (tentakül, bacak, kıvrım ucu) 3 mm kontrplakta kırılır. Kesim konturu şöyle üretilir:

```
kesim = genislet(acma(siluet, 2.1 mm), 1.0 mm)
```

Yani `MIN_KALINLIK`'tan ince olan her şey kesimden düşer, kalan biçim 1 mm dışa ötelenir. Bu öteleme aynı zamanda baskıda **beyaz sticker kenarı** üretir — kaynak çizimlerin diline uyar.

Denenip elenen iki yaklaşım:

- **Boşluk köprüleme** (morfolojik kapama): girintileri de doldurduğu için parçalar dikdörtgene dönüştü.
- **İnce bölgeleri kalınlaştırma**: büyüme çevredeki boşluğa taşıp yumru yaptı, alanı %34–85 şişirdi.

Budama şekli korur, 4 mm altı detay bırakmaz, alan değişimini %-15…+19 aralığında tutar.

### Ölçekleme

`siluet.HEDEF_BOY` kaynak görselin hedef yüksekliğidir; budama uzuv kestiği için nihai parça bundan kısa çıkar. Kaybı büyük olanlar (yengeç, denizanası) buradan büyütülerek parça boyu 25–40 mm bandında tutulur. Nihai parça ölçüleri ve budama oranları `python3 olustur.py` çıktısında listelenir.

## Üretim dosyaları (`cikti/`)

| Dosya | Amaç | Ölçü |
|---|---|---|
| `deniz_canlilari_uv_kalip.pdf` | UV hizalama kalıbı — **yalnız dış çerçeve konturu** (1:1) | 320 × 180 mm |
| `deniz_canlilari_uv_baski.pdf` | ÜST katman baskısı — her kenardan 2 mm taşmalı | 324 × 184 mm |
| `deniz_canlilari_alt_golge.pdf` | ALT katman gölge baskısı — cep tabanlarında siluetler | 324 × 184 mm |
| `deniz_canlilari_lazer_kesim.dxf` | Lazer kesim (mm, R2010) | iki pano yan yana |
| `deniz_canlilari_onizleme.png` | Ekran önizlemesi (yuvalar görünür) | ~190 dpi |

Beyaz mürekkep dosyası kullanılmıyor. Gölge siluetleri 0,4 mm içeri alınmıştır.

### DXF katmanları

- `UST_KATMAN_KESIM`: dış çerçeve + 8 canlı konturu + **8 parmak yuvası hilali** (R 5,5 mm, her cebin açık tarafında).
- `ALT_KATMAN_KESIM`: düz taban panosu.
- `YAZI`: etiketler — kesilmez, lazer yazılımında kapatın.

### Baskı içeriği

- Parça yüzü: kaynak çizim + dışında beyaz sticker payı.
- Her parçanın altında **Türkçe • İngilizce** ad plakası. Konumlar parmak yuvalarıyla ve komşu parçalarla çakışmaz (kod doğrular).
- Sağ üst köşede **zoziva** logosu (`varlik/zoziva_logo.png`).
- Dekor: su gradyanı, yüzeyden inen ışık huzmeleri, kabarcıklar, uzakta balık sürüsü, kumlu taban, yosun ve mercan öbekleri. Hiçbir dekor ögesi parça ya da etiket alanına girmez.

## Bilinen kısıt

Denizanası (%15), ahtapot (%17), yengeç (%18) ve denizatında (%11) kaynak çizimin bir bölümü budamayla kesimden düşüyor. Bunu sıfıra indirmenin yolu kaynak görselleri kalın uzuvlu üretmektir: hiçbir uzuv, uzunluğunun dörtte birinden ince olmamalı.

## Yeniden üretme

```bash
pip install ezdxf cairosvg shapely numpy scipy scikit-image pillow
python3 olustur.py
```
