# Araçlar Puzzle – Tema 01

İki katmanlı eğitici çocuk puzzle'ı. Bitmiş ölçü **320 × 180 mm**, dış köşeler 8 mm yuvarlatılmış. 8 araç parçası, üç "dünya" şeridine yerleştirilmiştir — çocuk hem araçları hem nerede gittiklerini öğrenir:

| Şerit | Parçalar |
|---|---|
| Gökyüzü | sıcak hava balonu, uçak |
| Kara / yol | traktör, itfaiye, araba, otobüs |
| Deniz | yelkenli, feribot |

## Üretim dosyaları (`cikti/`)

| Dosya | Amaç | Ölçü |
|---|---|---|
| `araclar_uv_kalip.pdf` | UV baskı hizalama kalıbı — **yalnız dış çerçeve konturu** (kırmızı, 1:1) | 320 × 180 mm |
| `araclar_uv_baski.pdf` | ÜST katman baskı deseni — **her kenardan 2 mm taşmalı** | 324 × 184 mm |
| `araclar_alt_golge.pdf` | ALT katman gölge baskısı — cep tabanlarında parça gölgeleri, 2 mm taşmalı | 324 × 184 mm |
| `araclar_lazer_kesim.dxf` | Lazer kesim (mm, R2010) | iki pano yan yana |
| `araclar_onizleme.png` | Ekran önizlemesi | ~170 dpi |

Beyaz mürekkep (alt zemin) dosyası bu üretimde **kullanılmıyor** — UV makine ayarı gerektirmiyor. Gölge baskısındaki siluetler cep duvarından taşmasın diye 0,4 mm içeri alınmıştır.

### DXF katmanları

- `UST_KATMAN_KESIM` (kırmızı): dış çerçeve + 8 araç konturu + **8 parmak yuvası hilali**. Araçları dış çizgisinden keser; parçalar **ve** cepler aynı kesimden çıkar. Hilaller (R 5,5 mm yarım ay, her cebin açık tarafında) ayrı kapalı kesimlerdir: küçük hilal parçası fire olur, cep kenarında parmak yuvası kalır — parça şekli değişmez.
- `ALT_KATMAN_KESIM` (mavi): düz taban panosu (yalnız dış çerçeve).
- `YAZI` (gri): etiketler — **kesilmez**, lazer yazılımında kapatın.
- `HIZA` (sarı): **kesilmez** — baskı↔kesim hizası için dört köşe register haçı. Aynı haçlar baskı ve kalıp PDF'inde de aynı yerdedir (yuvarlatılmış çerçevenin dışında, köşe fire alanında; kesince atılır, oyuncakta görünmez).

### Baskı–kesim hizası (register)

**Kalıp SABİT 320 × 180 mm'dir** — ürünün yerleştirildiği fiziksel jigdir, boyu değişmez. Baskı **324 × 184 mm**'dir ve tasarım tam ortalıdır (tasarım merkezi = sayfa merkezi = 162 × 92). Baskıyı **kalıbın merkezine** ortalayınca tasarım dört kenardan **eşit 2'şer mm taşar** (bleed). Ek güvence için baskı, kalıp ve DXF'in `HIZA` katmanında **aynı koordinatta dört köşe hiza haçı** vardır (yuvarlatılmış çerçeve dışı fire alanı, kesince atılır); operatör baskıyı kalıba ortalarken bu dört haçın çakıştığını kontrol edebilir. "Baskı kalıba göre kayık" sorunu neredeyse her zaman baskının yanlış ölçek/konumda basılmasından kaynaklanır (dosya geometrisi zaten tek 320 × 180 merkeze oturur); baskıyı %100 ölçekte basıp kalıp merkezine ortalamak bunu giderir.

### Marka logosu

Baskının sağ üst köşesinde **zoziva** logosu yer alır. Kaynak: `varlik/zoziva_logo.png` (şeffaf zeminli, marka rengi #573720) — `olustur.py` bu dosyayı baskıya otomatik gömer; dosya yoksa uyarı basıp logosuz üretir.

### Baskıdaki isim etiketleri

Üst katman baskısında her parçanın yanında **Türkçe • İngilizce** adı yazar (BALON • BALLOON, UÇAK • AIRPLANE, TRAKTÖR • TRACTOR, İTFAİYE • FIRE TRUCK, ARABA • CAR, OTOBÜS • BUS, YELKENLİ • SAILBOAT, FERİBOT • FERRY). Etiket konumları parmak yuvalarıyla çakışmaz. Yuvalar yalnız önizleme PNG'sinde gösterilir; baskı PDF'lerine kesim izi girmez.

## Üretim notları

- **İş sırası:** üst katman levhasına `araclar_uv_baski.pdf`, alt katman levhasına `araclar_alt_golge.pdf` UV basılır → kalıp dosyasıyla hizalanır → lazerde iki pano da kesilir → üst katman (cepli) alt katmana yapıştırılır. Gölgeler ceplerin içinden görünür; çocuk parçanın yerini gölgeden bulur.
- Kerf telafisi eklenmedi; tipik 0,15–0,3 mm kerf, parçaların cebe rahat oturmasını sağlar (çocuklar için istenen gevşek geçme).
- Levha kalınlığı serbesttir (DXF 2 boyutludur); iki katman için genellikle 3–4 mm MDF/kontrplak kullanılır.
- Parça aralık kuralları kodda doğrulanır: parçalar arası ≥ 7,5 mm duvar, dış kenara ≥ 6 mm pay.

## Yeniden üretme

```bash
pip install ezdxf cairosvg shapely
python3 olustur.py
```

Tüm geometri `olustur.py` içinde milimetre cinsinden tanımlıdır. Her araç konturu, basit şekillerin (kutu/elips/kapsül/çokgen) **birleşiminden** oluşturulur; `birlesim()` köşeleri yumuşatır ve lazer için tek kapalı dış çizgi üretir. Bir aracı değiştirmek için ilgili `kontur_*` fonksiyonundaki parçaları düzenleyip betiği yeniden çalıştırın — baskı ve DXF aynı konturdan türediği için asla ayrışmaz. Yerleşim kuralları (gerçek çokgen mesafeleriyle) ihlal edilirse betik uyarı basar.
