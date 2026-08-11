# Dinozorlar Puzzle — Tema 03

İki katmanlı eğitici çocuk puzzle'ı. **450 × 250 mm**, 6 parça. Üretim
`../_ortak/puzzle_motoru.py` ile; bu klasörde yalnız config ve varlıklar var.

| Parça | Türkçe / İngilizce | Ölçü | Sıra |
|---|---|---|---|
| `trex` | T-Rex / T-Rex | 88,5 × 74,8 mm | arka |
| `triceratops` | Triceratops / Triceratops | 88,3 × 57,8 mm | arka |
| `stegosaurus` | Stegosaurus / Stegosaurus | 87,1 × 55,9 mm | arka |
| `brontozor` | Brontozor / Brontosaurus | 103,4 × 86,2 mm | ön |
| `velosiraptor` | Velosiraptor / Velociraptor | 101,9 × 71,8 mm | ön |
| `parasaurolophus` | Parasaurolophus / Parasaurolophus | 103,1 × 78,6 mm | ön |

Ön sıra derinlik hissi için biraz daha iri. Arka sıra ayakları y≈132 mm'ye
(kum düzlüğünün başladığı yer), ön sıra y≈236 mm'ye basar.

## Varlıklar (`varlik/`)

- `sahne.png` — parçasız arka plan (yanardağ, palmiyeler, kum düzlüğü, şelale)
- `parca_*.png` — her dinozor, magenta zeminden ayrılmış RGBA

Parçalar ChatGPT'den **tek sayfada** geldi; `../_ortak/sayfa_bol.py` ile bölündü:

```bash
python3 ../_ortak/sayfa_bol.py <sayfa.jpg> varlik \
    trex brontozor triceratops stegosaurus velosiraptor parasaurolophus
```

Bacak araları PNG'de **saydam** bırakılır: baskıda arka plan görünür, kesim
konturunu motor ahşap dayanımı için köprüler.

## Üretim

```bash
pip install ezdxf cairosvg shapely numpy scipy scikit-image pillow
python3 olustur.py
```

Çıktılar `cikti/`: `dinozorlar_uv_baski.pdf` (454 × 254 mm taşmalı),
`dinozorlar_uv_kalip.pdf`, `dinozorlar_lazer_kesim.dxf`,
`dinozorlar_onizleme.png`.

## ⚠ Üretim öncesi

**Baskı çözünürlüğü düşük.** Parçalar tek sayfada geldiği için her birine az
piksel düştü:

| Varlık | dpi | |
|---|---|---|
| sahne | 86 | ↓ |
| parasaurolophus | 121 | ↓ |
| velosiraptor | 124 | ↓ |
| brontozor | 128 | ↓ |
| trex | 139 | ↓ |
| triceratops | 152 | ✓ |
| stegosaurus | 159 | ✓ |

UV baskıda alışılmış alt sınır 150 dpi. Deneme baskısı için yeterli; seri
üretim öncesi:

1. Her dinozoru **ayrı ayrı** 1024 × 1024 üret (tek sayfa yerine) → ~200 dpi
2. Sahneyi 2× yükselt (3072 × 2048) → ~172 dpi
3. İkisini birden yaparsan 250–300 dpi'a çıkar

Varlıkları değiştirmek yeterli; `olustur.py` aynı kalır. Motor kompozit
çözünürlüğünü en iyi varlığa göre kendisi seçer (şu an 199 dpi).

**Adlandırma notu:** mavi uzun boyunlu için "Brontozor / Brontosaurus" seçildi;
gövde oranları Apatosaurus/Brontosaurus'a daha yakın (Brachiosaurus'un ön
bacakları arkadan uzun ve boynu çok daha diktir). Başka bir ad tercih edersen
`olustur.py` içinde tek satır.

## Lazer atölyesi talimatı

- `UST_KATMAN_KESIM`: **kerf 0,3 mm, çizgi üzerinde kes.** Cep de parça da aynı
  konturdan çıkar; oturma boşluğunu kerf verir.
- `ALT_KATMAN_GRAVUR`: **kesme, çiz** (gravür). Parça konturları 0,5 mm içeri.
- `ALT_KATMAN_KESIM`: düz taban dış hattı.
- `YAZI`: talimat metni, kesilmez — kapatın.
