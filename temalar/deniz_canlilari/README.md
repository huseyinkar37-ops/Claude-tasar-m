# Deniz Canlıları Puzzle – Tema 02

İki katmanlı eğitici çocuk puzzle'ı. Bitmiş ölçü **320 × 180 mm**, dış köşeler 8 mm yuvarlatılmış. 8 canlı parçası, üç derinlik kuşağına yerleştirilmiştir — çocuk hem canlıları hem nerede yaşadıklarını öğrenir:

| Kuşak | Parçalar |
|---|---|
| Yüzeye yakın | yunus, denizanası |
| Orta su | denizatı, kaplumbağa, balık (palyaço) |
| Deniz tabanı | ahtapot, yengeç, denizyıldızı |

## Üretim dosyaları (`cikti/`)

| Dosya | Amaç | Ölçü |
|---|---|---|
| `deniz_canlilari_uv_kalip.pdf` | UV hizalama kalıbı — **yalnız dış çerçeve konturu** (1:1) | 320 × 180 mm |
| `deniz_canlilari_uv_baski.pdf` | ÜST katman baskısı — her kenardan 2 mm taşmalı | 324 × 184 mm |
| `deniz_canlilari_alt_golge.pdf` | ALT katman gölge baskısı — cep tabanlarında siluetler | 324 × 184 mm |
| `deniz_canlilari_lazer_kesim.dxf` | Lazer kesim (mm, R2010) | iki pano yan yana |
| `deniz_canlilari_onizleme.png` | Ekran önizlemesi (yuvalar görünür) | ~170 dpi |

Beyaz mürekkep dosyası kullanılmıyor. Gölge siluetleri 0,4 mm içeri alınmıştır.

### DXF katmanları

- `UST_KATMAN_KESIM` (kırmızı): dış çerçeve + 8 canlı konturu + **8 parmak yuvası hilali** (R 5,5 mm, her cebin açık tarafında).
- `ALT_KATMAN_KESIM` (mavi): düz taban panosu.
- `YAZI` (gri): etiketler — kesilmez, lazer yazılımında kapatın.

### Baskı içeriği

- Her parçanın yanında **Türkçe • İngilizce** ad plakası (YUNUS • DOLPHIN, DENİZANASI • JELLYFISH, DENİZATI • SEAHORSE, KAPLUMBAĞA • SEA TURTLE, BALIK • FISH, AHTAPOT • OCTOPUS, YENGEÇ • CRAB, DENİZYILDIZI • STARFISH). Konumlar parmak yuvalarıyla çakışmaz.
- Sağ üst köşede **zoziva** logosu (`varlik/zoziva_logo.png`).
- Dekor: su yüzeyi, ışık hüzmeleri, kabarcıklar, balık sürüleri, kumlu taban, yosunlar, mercan, kayalar, deniz kabukları.

## Üretim notları

- İş sırası ve toleranslar `temalar/araclar/README.md` ile aynıdır (kerf telafisi yok, parçalar arası ≥ 7,5 mm, kenara ≥ 6 mm; kod doğrular).

## Yeniden üretme

```bash
pip install ezdxf cairosvg shapely
python3 olustur.py
```
