# İş Makineleri Puzzle – Tema 03

İki katmanlı eğitici çocuk puzzle'ı. Bitmiş ölçü **320 × 180 mm**, dış köşeler 8 mm yuvarlatılmış. 8 iş makinesi parçası, üç şantiye kuşağına yerleştirilmiştir:

| Kuşak | Parçalar |
|---|---|
| Kazı | ekskavatör, buldozer, kepçe (yükleyici) |
| Taşıma | damperli kamyon, vinç, beton mikseri, forklift |
| Yol yapımı | yol silindiri |

## Üretim dosyaları (`cikti/`)

| Dosya | Amaç | Ölçü |
|---|---|---|
| `is_makineleri_uv_kalip.pdf` | UV hizalama kalıbı — **yalnız dış çerçeve konturu** (1:1) | 320 × 180 mm |
| `is_makineleri_uv_baski.pdf` | ÜST katman baskısı — her kenardan 2 mm taşmalı | 324 × 184 mm |
| `is_makineleri_alt_golge.pdf` | ALT katman gölge baskısı — cep tabanlarında siluetler | 324 × 184 mm |
| `is_makineleri_lazer_kesim.dxf` | Lazer kesim (mm, R2010) | iki pano yan yana |
| `is_makineleri_onizleme.png` | Ekran önizlemesi (yuvalar görünür) | ~170 dpi |

Beyaz mürekkep dosyası kullanılmıyor. Gölge siluetleri 0,4 mm içeri alınmıştır.

### DXF katmanları

- `UST_KATMAN_KESIM` (kırmızı): dış çerçeve + 8 makine konturu + **8 parmak yuvası hilali** (R 5,5 mm, her cebin açık tarafında).
- `ALT_KATMAN_KESIM` (mavi): düz taban panosu.
- `YAZI` (gri): etiketler — kesilmez, lazer yazılımında kapatın.
- `HIZA` (sarı): **kesilmez** — baskı↔kesim hizası için dört köşe register haçı (aynı haçlar baskı ve kalıp PDF'inde de var; köşe fire alanında, kesince atılır). Operatör baskılı tahtayı bu dört noktadan kesime çakıştırır; konum + açı + ölçek sabitlenir. Kalıp PDF'i baskıyla birebir çakışsın diye 324 × 184 mm'dir.

### Baskı içeriği

- Parçalar **elle vektör çizilir** (araclar temasıyla aynı yaklaşım): her makine basit şekillerin (kutu/elips/kapsül/çokgen) birleşimidir; `birlesim()` köşeleri yumuşatıp lazer için tek kapalı dış kontur üretir. Aynı kontur hem SVG çizimini hem DXF polyline'ını besler — baskı ve kesim asla ayrışmaz.
- Her parçanın yanında **Türkçe • İngilizce** ad plakası: Ekskavatör • Excavator, Damperli Kamyon • Dump Truck, Vinç • Crane, Buldozer • Bulldozer, Beton Mikseri • Mixer, Forklift • Forklift, Yol Silindiri • Road Roller, Kepçe • Wheel Loader. Konumlar parmak yuvalarıyla çakışmaz.
- Sağ üst köşede **zoziva** logosu (`varlik/zoziva_logo.png`).
- Dekor: gökyüzü + güneş + bulutlar, şantiye toprağı ve çakıl, toprak yığınları, trafik konileri, sarı-siyah bariyerler.
- Detaylar: paletli tabanlar (track), gerçekçi tekerlekler (lastik/jant/bijon), camlar, sarı-siyah uyarı şeritleri, kepçe/bıçak/tambur/çatal gibi makineye özgü parçalar.

### Yerleşim / düzenleme

- Konum `olustur.py` içindeki `YERLESIM` tablosundan ayarlanır: `(ad, merkez_x, merkez_y, sınıf, kontur_fonksiyonu)`. Her makine kendi `(cx, cy)` merkezine göre çizilir; makineyi taşımak için tablodaki merkezi değiştirmek yeter.
- Bir makinenin şeklini değiştirmek: ilgili `kontur_*` fonksiyonundaki parçaları ve `is_detaylari()` içindeki detay bloğunu düzenleyin.

## Üretim notları

- İş sırası ve toleranslar `temalar/araclar/README.md` ile aynıdır (kerf telafisi yok, parçalar arası ≥ 7,5 mm, kenara ≥ 6 mm; kod doğrular).
- İnce çıkıntılar (ekskavatör bomu, vinç kolu, forklift direği/çatalı) ahşap dayanımı için `birlesim()`'in `kapa` parametresiyle tıknazlaştırılır.

## Yeniden üretme

```bash
pip install ezdxf cairosvg shapely
python3 olustur.py
```
