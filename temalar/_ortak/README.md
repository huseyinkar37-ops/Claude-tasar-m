# Ortak Puzzle Motoru

`puzzle_motoru.py`, katmanlı varlıklardan (sahne + ayrı parça görselleri) eksiksiz
üretim dosyası çıkaran ortak motordur. Yeni temalar bunu kullanır; her tema yalnızca
kendi `olustur.py` config dosyasını yazar.

## Tasarım kuralları (tüm temalar)

| Konu | Kural |
|---|---|
| Bütünlük | Parçalar yerindeyken sahne eksiksiz bir bütündür. |
| Eğitim | Parçalar temaya uygun; her parçanın Türkçe / İngilizce adı basılır. |
| ALT katman | Düz levha. Parça yerlerine kontur **gravür** olarak, 0,5 mm küçültülerek çizilir — hem ipucu hem boşken görsel değer. |
| ÜST katman | Cepler kesilir. DXF'te parça başına **tek kapalı kontur**; 0,3 mm oturma payı lazer kerfiyle sağlanır. |
| Parça çıkarma | Her cebin en ferah kenarında **Ø12 mm yarım ay**; ad plakasına asla değmez (kod denetler). |
| Ahşap dayanımı | 4 mm'den ince kesilebilir ayrıntı yok — ince uçlar otomatik budanır. |
| Paylar | Parçalar arası ≥ 7,5 mm duvar, dış kenara ≥ 6 mm. |
| Pano | 320 × 180 mm, dış köşeler 8 mm yuvarlatılmış, her kenardan 2 mm taşma. |

> **Lazer atölyesine talimat:** *"Kerf 0,3 mm, çizgi üzerinde kes."* Cep de parça da
> aynı konturdan çıkar; oturma boşluğunu kerf verir. DXF'te ayrı parça yolu yoktur.

## Üretim dosyaları (`cikti/`)

| Dosya | Amaç |
|---|---|
| `<tema>_uv_baski.pdf` | ÜST katman baskısı (sahne + parçalar + ad plakaları), 324 × 184 mm taşmalı |
| `<tema>_uv_kalip.pdf` | UV hizalama kalıbı — yalnız dış çerçeve, 1:1 |
| `<tema>_lazer_kesim.dxf` | ÜST ve ALT panolar yan yana |
| `<tema>_onizleme.png` | Kesim çizgileri + yarım aylar görünür kontrol baskısı |

Beyaz mürekkep dosyası yok. Alt katman gölge **baskısı** da yok — yerini gravür aldı.

### DXF katmanları

- `UST_KATMAN_KESIM` (kırmızı) — dış çerçeve + parça cepleri + yarım aylar
- `ALT_KATMAN_KESIM` (mavi) — düz taban panosu
- `ALT_KATMAN_GRAVUR` (yeşil) — **kesme, çiz**: 0,5 mm içeri alınmış parça konturları
- `YAZI` (gri) — talimat metinleri, kesilmez

## Yeni tema açma

```
temalar/<tema>/
  olustur.py            # yalnız config (aşağıdaki şablon)
  varlik/
    sahne.png           # parçasız arka plan, YAZISIZ
    parca_<anahtar>.png # her parça, magenta (#FF00FF) zeminde, YAZISIZ
  cikti/                # üretilen dosyalar
```

```python
# -*- coding: utf-8 -*-
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "_ortak"))
from puzzle_motoru import Parca, Tema, uret

T = Tema(
    ad="dinozorlar", baslik="DINOZORLAR PUZZLE",
    klasor=os.path.dirname(os.path.abspath(__file__)),
    parcalar=[
        # merkez: yaklaşık hedef konum (mm). Motor payları kendisi düzeltir.
        Parca("trex", "T-Rex", "T-Rex", merkez=(60, 60), genislik=78),
        Parca("stego", "Stegosaurus", "Stegosaurus", merkez=(180, 58), genislik=82),
        # ...
    ])
uret(T)
```

Konumları göz kararı ver; `yerlesimi_duzelt()` parçaları birbirinden ve kenardan
iterek payları **garantiye alır** ve ne kadar kaydırdığını raporlar. Etiket bir
parçayı örtüyorsa `etiket_yon="ust"` ya da `etiket_kaydir=(dx, dy)` kullan.

```bash
pip install ezdxf cairosvg shapely numpy scipy scikit-image pillow
cd temalar/<tema> && python3 olustur.py
```

Üretilen `*_onizleme.png` her seferinde gözle kontrol edilmeli: kod payları
doğrular, estetiği doğrulamaz.

---

## ChatGPT görsel promptları

Görselleri **tek sohbette, arka arkaya** üret — stil tutarlılığı böyle sağlanır.
Önce sahne, sonra parçalar.

### 1) Sahne (parçasız)

```
Create a children's educational puzzle BACKGROUND illustration.

THEME: {TEMA — e.g. "prehistoric jungle with a smoking volcano, palm forest,
a river and scattered rocks"}

STYLE
- Flat vector children's-book illustration. Bold, uniform dark outlines (#1A1A1A).
- Saturated but soft colours, simple cel shading. No photorealism, no 3D render.
- Even ambient lighting, no dramatic cast shadows.

COMPOSITION
- 3:2 landscape, 1536x1024, highest quality. Fill the canvas edge to edge.
- BACKGROUND ONLY: do NOT draw any {PARÇA TÜRÜ — e.g. dinosaurs}.
- Leave {N} clearly open, uncluttered "landing areas" spread across the scene where
  subjects will be placed later: {e.g. left foreground, centre, right middle, sky}.
  These areas must be simple and low-detail — plain ground or plain sky, no busy
  foliage or rocks there.
- Keep all important content inside a centred 16:9 safe area; the top and bottom
  12% may be cropped.
- Keep background contrast low so subjects placed on top stay readable.

STRICT
- NO text, NO letters, NO numbers, NO labels, NO watermark, NO logo, NO signature.
- NO frame, NO border, NO vignette.
```

### 2) Her parça için

```
Same illustration style as the previous background image (flat vector children's-book,
bold uniform dark outline #1A1A1A, saturated soft colours, simple cel shading,
even ambient lighting).

Draw ONE {PARÇA ADI — e.g. Stegosaurus} — full body, side view, facing {left/right},
calm neutral pose.

STRICT
- Centred and complete, nothing cropped. Leave ~10% empty margin on all sides.
- Background: solid uniform pure magenta #FF00FF, perfectly flat. No gradient,
  no ground, no shadow, no props. Magenta must not appear anywhere in the subject.
- Chunky toy-like proportions: no body part narrower than 1/15 of the subject's
  total width. Thicken thin tails, legs, horns, spikes, wings.
- Keep limbs slightly separated from the body; no gap narrower than 1/15 of the width.
- NO text, NO watermark, NO frame, NO shadow.
- 1024x1024 (or 1536x1024 if the subject is wide), highest quality.
```

**Neden böyle:**

- *Magenta zemin* — konturu piksel hassasiyetinde ayırmayı sağlar. Beyaz zemin
  isteme; diş, göz, boynuz beyazıyla karışır.
- *Yazısız* — adları motor vektör metin olarak koyar: Türkçe karakterler garanti
  doğru, düşük dpi'da bile keskin ve yarım ayın yazıya değmediği denetlenebilir.
- *1/15 kalınlık kuralı* — ahşapta kırılacak ince uçları en baştan engeller.
- *Ayrı parça görselleri* — tek birleşik sahneden kontur çıkarmak kırılgandır
  (konular arka plana değer, aralıklar kuralları ihlal eder). Ayrı üretilince her
  parça 250–320 dpi olur; birleşik sahnede aynı parça ~120 dpi'da kalır.
