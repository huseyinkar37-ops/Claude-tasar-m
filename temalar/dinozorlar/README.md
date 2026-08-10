# Dinozorlar Puzzle – Tema 03

İki katmanlı eğitici çocuk puzzle'ı. **Diğer temalardan farkı: sahne yeniden
çizilmez.** Kaynak illüstrasyonun (`varlik/dinozor_sahne.jpg`) kendisi üst katman
baskısıdır; parça konturları görselin içinden segmentasyonla çıkarılır, böylece
kesim ile baskı birebir örtüşür.

Bitmiş ölçü **315 × 210 mm**, dış köşeler 8 mm yuvarlatılmış. 7 dinozor parçası:
Pteranodon, Brakiyozor, T-Rex, Triceratops, Stegosaurus, Spinosaurus,
Velosiraptor.

> **Ölçü neden 320 × 180 değil?** Kaynak görsel 1536 × 1024 px, yani 3:2.
> 320 × 180 (16:9) panoya sığdırmak için görselin %16'sını kırpmak gerekirdi;
> kırpma alt kenardaki ad plakalarını, zoziva logosunu ve spinosaurusun
> ayaklarını kesiyordu. Görseli bozmamak için pano kaynağın en–boy oranına
> getirildi. Panoyu 320 × 180'de tutmak isterseniz `olustur.py` içindeki
> `W, H` sabitini değiştirmek yeterli; kırpma/ölçekleme kendiliğinden uyar.

## Üretim dosyaları (`cikti/`)

| Dosya | Amaç | Ölçü |
|---|---|---|
| `dinozorlar_uv_kalip.pdf` | UV hizalama kalıbı — **yalnız dış çerçeve konturu** (1:1) | 315 × 210 mm |
| `dinozorlar_uv_baski.pdf` | ÜST katman baskısı — kaynak görsel, her kenardan 2 mm taşmalı | 319 × 214 mm |
| `dinozorlar_alt_golge.pdf` | ALT katman gölge baskısı — cep tabanlarında siluetler | 319 × 214 mm |
| `dinozorlar_lazer_kesim.dxf` | Lazer kesim (mm, R2010) | iki pano yan yana |
| `dinozorlar_onizleme.png` | Kesim çizgileri + parmak yuvaları görünür kontrol baskısı | ~175 dpi |

Beyaz mürekkep dosyası kullanılmıyor. Gölge siluetleri 0,4 mm içeri alınmıştır.
Taşma payı, kaynak görselin taşma kutusunu tam dolduracak şekilde ölçeklenmesiyle
elde edilir (uydurma kenar dokusu yok, kenardan ~%1,3 gerçek görsel feda edilir).

### DXF katmanları

- `UST_KATMAN_KESIM` (kırmızı): dış çerçeve + 7 dinozor konturu + 7 parmak yuvası
  hilali (R 5,5 mm).
- `ALT_KATMAN_KESIM` (mavi): düz taban panosu.
- `YAZI` (gri): etiketler — kesilmez, lazer yazılımında kapatın.

### Baskı içeriği

Kaynak illüstrasyonda **zaten basılı** olan her şey korunur: Türkçe / İngilizce ad
plakaları, zoziva logosu, yanardağ, orman, gölet ve kum patikası. Ayrıca çizim
eklenmez. Parça konturları hiçbir ad plakasını kesmez (kod bunu denetler).

## ⚠ Üretim öncesi bilinmesi gerekenler

1. **Baskı çözünürlüğü 124 dpi.** Kaynak 1536 × 1024 px olduğundan 315 mm
   genişlikte etkin çözünürlük 124 dpi'dır; UV baskıda alışılmış alt sınır
   150 dpi'dır. Kol mesafesinden bakılan bir oyuncakta kabul edilebilir, ancak
   keskin sonuç isteniyorsa aynı sahnenin **en az 1900 × 1270 px** (150 dpi) ya da
   3720 × 2480 px (300 dpi) sürümü `varlik/dinozor_sahne.jpg` ile değiştirilmeli;
   betik başka değişiklik gerektirmez.
2. **Kaynak kompozisyonda parçalar birbirine çok yakındı.** Ham konturlar arası
   ölçülen en küçük aralıklar: brakiyozor–stegosaurus 2,9 mm, T-Rex–spinosaurus
   3,5 mm, triceratops–spinosaurus 5,2 mm, T-Rex–triceratops 7,4 mm; T-Rex'in
   kuyruğu dış kenara 3,0 mm. Kural ≥ 7,5 mm (kenara ≥ 6 mm). `paylari_ac()`
   temas bölgelerinde **her iki parçadan eşit miktar traşlayarak** kuralı sağlar
   (en fazla ~2,3 mm). Pratik sonuç: brakiyozorun kuyruk ucu ve T-Rex'in
   kuyruk/ayak ucu basılı çizgiden birkaç mm önce biter. Alternatif isteniyorsa
   yakın duran hayvanların birbirinden ayrıldığı bir sahne çizimi gerekir.
3. **4 mm altı ayrıntılar budanır.** Stegosaurusun kuyruk dikenleri, triceratops
   boynuzları gibi ince uçlar ahşap dayanımı için körleştirilir; kesim o
   noktalarda basılı çizgiyi birebir izlemez.

## Nasıl çalışır (`olustur.py`)

1. `maskeler()` – ad plakaları (beyaz, dolu dikdörtgenler) bulunup **opak duvar**
   sayılır; koyu konturlarla çevrelenen bölgeler kenardan taşma-doldurma ile
   ayrıştırılır. Birbirine değen nesneler **morfolojik açma → işaretçi → en yakın
   işaretçiye atama (watershed)** ile en dar boğazdan bölünür; böylece ince
   kuyruk/boynuz uçları korunurken bitki öbekleri ayrılır.
   Tek istisna `KESIKLER`: T-Rex'in kuyruk konturu ile soldaki eğrelti otu
   kaynakta ~9 mm genişliğinde ayırıcı çizgisiz birleştiği için oraya elle bir
   kesme çizgisi konur.
2. `konturlar()` – maskeler marching-squares ile poligona, oradan mm'ye çevrilir.
3. `paylari_ac()` – yukarıdaki aralık düzeltmesi (yakınsayana dek yinelenir).
4. `yuvalar_yerlestir()` – her parçanın **en ferah** kenarına, basılı ad
   plakasına değmeyen bir R 5,5 mm hilal otomatik yerleştirilir.
5. `dogrula()` – aralık, kenar payı ve yuva açıklıkları gerçek poligon
   mesafeleriyle denetlenir; ihlal varsa uyarı basar.

## Yeniden üretme

```bash
pip install ezdxf cairosvg shapely numpy scipy scikit-image pillow
python3 olustur.py
```

Çalışma süresi ~30 sn (segmentasyon dahil). Kaynak görsel değişirse `TOHUM`
sözlüğündeki tohum noktalarının hâlâ ilgili hayvanın gövdesine düştüğü
doğrulanmalıdır.
