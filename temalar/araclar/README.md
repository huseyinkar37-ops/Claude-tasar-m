# Araçlar Puzzle – Tema 01

İki katmanlı eğitici çocuk puzzle'ı. Bitmiş ölçü **320 × 180 mm**, dış köşeler 8 mm yuvarlatılmış. 9 araç parçası, üç "dünya" şeridine yerleştirilmiştir — çocuk hem araçları hem nerede gittiklerini öğrenir:

| Şerit | Parçalar |
|---|---|
| Gökyüzü | sıcak hava balonu, uçak, helikopter |
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

- `UST_KATMAN_KESIM` (kırmızı): dış çerçeve + 9 araç konturu. Araçları dış çizgisinden keser; parçalar **ve** cepler aynı kesimden çıkar.
- `ALT_KATMAN_KESIM` (mavi): düz taban panosu (yalnız dış çerçeve).
- `YAZI` (gri): etiketler — **kesilmez**, lazer yazılımında kapatın.

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
