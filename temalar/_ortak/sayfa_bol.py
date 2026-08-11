# -*- coding: utf-8 -*-
"""
Magenta zeminli TEK sayfada gelen parçaları ayrı PNG'lere böler.

ChatGPT çoğu zaman parçaları tek karede döndürür. Bu araç magentayı anahtarlar,
konuları soldan sağa / yukarıdan aşağıya sıralar ve `parca_<anahtar>.png` olarak
yazar. Motor bunları olduğu gibi okur.

Kullanım:
    python3 sayfa_bol.py <sayfa.jpg> <hedef_klasor> anahtar1 anahtar2 ...
    python3 sayfa_bol.py <sayfa.jpg> <hedef_klasor>          # yalnız rapor
"""
import os
import sys

import numpy as np
from PIL import Image
from scipy import ndimage as ndi


def disk(r):
    y, x = np.ogrid[-r:r + 1, -r:r + 1]
    return x * x + y * y <= r * r


def konulari_bul(yol, en_az_alan=8000):
    """Magenta zeminden konuları ayırır; (maske, bbox) listesi döndürür."""
    im = Image.open(yol).convert("RGB")
    a = np.asarray(im).astype(np.int16)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    zemin = (r > 150) & (b > 150) & (g < 120)
    konu = ~zemin
    # JPEG saçaklarını temizle, gövde içindeki magenta-benzeri lekeleri doldur
    konu = ndi.binary_opening(konu, structure=disk(3))
    konu = ndi.binary_closing(konu, structure=disk(3))
    etiket, n = ndi.label(konu)
    bulunan = []
    for i in range(1, n + 1):
        m = etiket == i
        if m.sum() < en_az_alan:
            continue
        # DELİKLERİ DOLDURMA: bacak araları saydam kalmalı ki baskıda arka plan
        # görünsün. Kesim konturunu motor kendisi köprüler (ahşap dayanımı).
        ys, xs = np.nonzero(ndi.binary_fill_holes(m))
        bulunan.append((m, (xs.min(), ys.min(), xs.max() + 1, ys.max() + 1)))
    # satır satır sırala: önce üst satır, her satırda soldan sağa
    if bulunan:
        yuk = np.median([b[3] - b[1] for _, b in bulunan])
        bulunan.sort(key=lambda t: (int(t[1][1] / (yuk * 0.6)), t[1][0]))
    return im, bulunan


def bol(yol, hedef, anahtarlar=None, kenar_pay=12):
    im, bulunan = konulari_bul(yol)
    print(f"{os.path.basename(yol)}: {len(bulunan)} konu bulundu")
    os.makedirs(hedef, exist_ok=True)
    for i, (m, (x0, y0, x1, y1)) in enumerate(bulunan):
        ad = anahtarlar[i] if anahtarlar and i < len(anahtarlar) else f"konu{i+1}"
        x0p, y0p = max(0, x0 - kenar_pay), max(0, y0 - kenar_pay)
        x1p, y1p = min(im.width, x1 + kenar_pay), min(im.height, y1 + kenar_pay)
        kirp = im.crop((x0p, y0p, x1p, y1p)).convert("RGBA")
        alfa = np.where(m[y0p:y1p, x0p:x1p], 255, 0).astype(np.uint8)
        d = np.asarray(kirp).copy()
        d[..., 3] = alfa
        d[alfa == 0] = (255, 0, 255, 0)          # zemini temiz magentaya sabitle
        if anahtarlar and i < len(anahtarlar):
            cikti = os.path.join(hedef, f"parca_{ad}.png")
        else:
            cikti = os.path.join(hedef, f"konu_{i+1}.png")
        Image.fromarray(d, "RGBA").save(cikti)
        print(f"  {i+1}. {ad:<18} {x1-x0:4d} x {y1-y0:4d} px  -> "
              f"{os.path.basename(cikti)}")
    return bulunan


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    bol(sys.argv[1], sys.argv[2], sys.argv[3:] or None)
