# -*- coding: utf-8 -*-
"""
Kaynak görselin siluetinden üretime uygun kesim konturu üretir.

Denenen ve elenen yaklaşımlar:
  * Boşluk köprüleme (morfolojik kapama): girintileri de doldurduğu için
    parçalar dikdörtgene dönüştü.
  * İnce bölgeleri kalınlaştırma: büyüme çevredeki boşluğa taşıp yumru yaptı,
    alan %34-85 arttı.

Kullanılan yöntem — budama (ahşap oyuncak standardı):
    kesim = genislet(acma(siluet, r), geri)
Yani MIN_KALINLIK'tan ince olan her şey kesimden düşer, kalan biçim sticker
payı kadar dışa ötelenir. Şekil korunur, kırılgan uzuv kalmaz, alan değişimi
%-15..+19 aralığında.

Sonuç: çizimde olup ahşapta olmayan bölgeler `budanan()` ile raporlanır —
bunlar baskıda da görünmez, çünkü baskı kesim konturuna kırpılır.

python3 kesim.py    -> cikti/kesim_onizleme.png
"""
import os

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

import siluet

CIKTI = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cikti")

BUDAMA_R = 2.1     # bundan ince uzuvlar kesimden düşer (yarıçap, mm)
STICKER = 1.0      # kesim konturunun çizim siluetinden dışa payı (mm)


def kesim_maskesi(m, mm_px, budama_r=BUDAMA_R, sticker=STICKER):
    k = siluet.acma(m, budama_r / mm_px)
    k = siluet.genislet(k, sticker / mm_px)
    return ndimage.binary_fill_holes(k)


def budanan(m, kesim):
    """Çizimde olup kesimde kalmayan bölge."""
    return m & ~kesim


def ince_pay(m, mm_px, esik=siluet.MIN_KALINLIK):
    kalin = siluet.acma(m, (esik / 2.0) / mm_px)
    return float((m & ~kalin).sum() / max(1, m.sum()))


def isle(ad):
    r = siluet.isle(ad)
    m, mm_px = r["maske"], r["mm_px"]
    k = kesim_maskesi(m, mm_px)
    r["kesim"] = k
    r["kesim_kontur"] = siluet.maske_kontur(k, mm_px)
    r["budanan_pay"] = float(budanan(m, k).sum() / m.sum())
    r["ince_pay_sonra"] = ince_pay(k, mm_px)
    r["alan_degisim"] = k.sum() / m.sum() - 1
    return r


def main():
    print(f"{'canlı':14} {'<4mm sonra':>11} {'alan değişimi':>14} "
          f"{'budanan':>9}  durum")
    print("-" * 62)
    kartlar = []
    for ad in siluet.HEDEF_BOY:
        r = isle(ad)
        bud = r["budanan_pay"]
        durum = ("TAMAM" if bud < 0.03 else
                 "kabul edilebilir" if bud < 0.08 else "UZUV KAYBI")
        print(f"{ad:14} {100*r['ince_pay_sonra']:10.1f}% "
              f"{100*r['alan_degisim']:13.0f}% {100*bud:8.1f}%  {durum}")
        m, k = r["maske"], r["kesim"]
        h, w = m.shape
        px = np.zeros((h, w, 3), np.uint8) + 255
        px[k] = (255, 208, 90)
        px[m & k] = (110, 160, 205)
        px[m & ~k] = (226, 60, 60)
        im = Image.fromarray(px)
        im.thumbnail((300, 300), Image.LANCZOS)
        kartlar.append((ad, im, bud))

    gw = max(i.size[0] for _, i, _ in kartlar) + 20
    gh = max(i.size[1] for _, i, _ in kartlar) + 40
    tv = Image.new("RGB", (gw * 4, gh * 2), "#FFFFFF")
    dr = ImageDraw.Draw(tv)
    for i, (ad, im, bud) in enumerate(kartlar):
        x, y = (i % 4) * gw, (i // 4) * gh
        tv.paste(im, (x + 10, y + 30))
        dr.text((x + 10, y + 8), f"{ad}  budanan %{100*bud:.1f}",
                fill="#B00000" if bud >= 0.08 else "#116611")
    os.makedirs(CIKTI, exist_ok=True)
    yol = os.path.join(CIKTI, "kesim_onizleme.png")
    tv.save(yol)
    print("\nmavi = ahşapta kalan, kırmızı = budanan, sarı = sticker payı")
    print("yazildi:", yol)


if __name__ == "__main__":
    main()
