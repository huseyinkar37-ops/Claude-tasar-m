# Dinozorlar Puzzle – Tema 03

İki katmanlı eğitici çocuk puzzle'ı. Bitmiş ölçü **320 × 180 mm**, dış köşeler 8 mm yuvarlatılmış. Referans görseldeki 7 dinozor, beslenme biçimlerine göre üç gruba ayrılmıştır — çocuk hem dinozorları hem ne yediklerini öğrenir:

| Grup | Parçalar |
|---|---|
| Uçan sürüngen | pteranodon |
| Otçul | brakiyozor, triceratops, stegosaurus |
| Etçil | T-Rex, spinosaurus, velosiraptor |

## Üretim dosyaları (`cikti/`)

| Dosya | Amaç | Ölçü |
|---|---|---|
| `dinozorlar_uv_kalip.pdf` | UV hizalama kalıbı — **yalnız dış çerçeve konturu** (1:1) | 320 × 180 mm |
| `dinozorlar_uv_baski.pdf` | ÜST katman baskısı — her kenardan 2 mm taşmalı | 324 × 184 mm |
| `dinozorlar_alt_golge.pdf` | ALT katman gölge baskısı — cep tabanlarında siluetler | 324 × 184 mm |
| `dinozorlar_lazer_kesim.dxf` | Lazer kesim (mm, R2010) | iki pano yan yana |
| `dinozorlar_onizleme.png` | Ekran önizlemesi (yuvalar görünür) | ~170 dpi |

Beyaz mürekkep dosyası kullanılmıyor. Gölge siluetleri 0,4 mm içeri alınmıştır.

### DXF katmanları

- `UST_KATMAN_KESIM` (kırmızı): dış çerçeve + 7 dinozor konturu + **7 parmak yuvası hilali** (R 5,5 mm, her cebin açık tarafında).
- `ALT_KATMAN_KESIM` (mavi): düz taban panosu.
- `YAZI` (gri): etiketler — kesilmez, lazer yazılımında kapatın.

### Baskı içeriği

- Çizim stili: masal kitabı (kalın koyu konturlar, iri parlak gözler, doygun renkler) — diğer temalarla aynı dil.
- Her parçanın yanında **Türkçe / İngilizce** ad plakası (İngilizce mavi renkte): Pteranodon / Pteranodon, Brakiyozor / Brachiosaurus, T-Rex / T-Rex, Triceratops / Triceratops, Stegosaurus / Stegosaurus, Spinosaurus / Spinosaurus, Velosiraptor / Velociraptor. Konumlar parmak yuvalarıyla çakışmaz.
- Sağ üst köşede **zoziva** logosu (`varlik/zoziva_logo.png`).
- Dekor: gökyüzü ve bulutlar, karlı uzak dağlar, duman tüten **yanardağ**, yuvarlak tropik orman kanopisi, palmiyeler, çimen zemin, sol altta **gölet** (nilüferli, spinosaurus suda yürür), sağ altta **kum patikası** (dinozor ayak izleriyle), kayalar, eğrelti otları ve çalılar. Tüm dekor öğeleri parça sınır kutularının dışındadır.

## Üretim notları

- İş sırası ve toleranslar `temalar/araclar/README.md` ile aynıdır (kerf telafisi yok, parçalar arası ≥ 7,5 mm, kenara ≥ 6 mm; kod doğrular).
- **Kaynaşan bacaklar bilinçlidir:** ahşap dayanımı için bacak araları kapatılmıştır (2,6 mm altı boşluklar köprülenir); bacak ayrımları yalnız baskıda koyu çizgilerle gösterilir. Aynı sebeple pteranodonun ibiği ile T-Rex / spinosaurus / velosiraptorun ön kolları silüette değil, baskıda çizilir.

## Yeniden üretme

```bash
pip install ezdxf cairosvg shapely
python3 olustur.py
```
