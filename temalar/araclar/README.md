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
| `araclar_uv_kalip.pdf` | UV baskı hizalama kalıbı — yalnız kesim konturları (kırmızı, 1:1) | 320 × 180 mm |
| `araclar_uv_baski.pdf` | UV baskı deseni — **her kenardan 2 mm taşmalı** | 324 × 184 mm |
| `araclar_lazer_kesim.dxf` | Lazer kesim (mm, R2010) | iki pano yan yana |
| `araclar_onizleme.png` | Ekran önizlemesi | ~150 dpi |

### DXF katmanları

- `UST_KATMAN_KESIM` (kırmızı): dış çerçeve + 9 araç konturu. Araçları dış çizgisinden keser; parçalar **ve** cepler aynı kesimden çıkar.
- `ALT_KATMAN_KESIM` (mavi): düz taban panosu (yalnız dış çerçeve).
- `YAZI` (gri): etiketler — **kesilmez**, lazer yazılımında kapatın.

## Üretim notları

- **İş sırası:** üst katman levhasına deseni UV bas → kalıp dosyasıyla hizala → lazerde konturları kes → üst katmanı düz tabana yapıştır.
- Kerf telafisi eklenmedi; tipik 0,15–0,3 mm kerf, parçaların cebe rahat oturmasını sağlar (çocuklar için istenen gevşek geçme).
- Levha kalınlığı serbesttir (DXF 2 boyutludur); iki katman için genellikle 3–4 mm MDF/kontrplak kullanılır.
- Parça aralık kuralları kodda doğrulanır: parçalar arası ≥ 7,5 mm duvar, dış kenara ≥ 6 mm pay.

## Yeniden üretme

```bash
pip install ezdxf cairosvg
python3 olustur.py
```

Tüm geometri `olustur.py` içinde milimetre cinsinden tanımlıdır; bir aracı taşımak/yeniden çizmek için ilgili `kontur_*` fonksiyonunu düzenleyip betiği yeniden çalıştırın. Yerleşim kuralları ihlal edilirse betik uyarı basar.
