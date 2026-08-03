# -*- coding: utf-8 -*-
"""
Kaynak görsellerden üretim siluetlerini çıkarır ve imalat uygunluğunu ölçer.

Akış:
  1. Beyaz zemini kenardan taşırma (flood fill) ile ayır — böylece gövde
     içinde kalan kapalı beyaz bölgeler (denizatının kuyruk halkası gibi)
     siluetin parçası kalır; lazer yalnız dış konturu keser.
  2. Delikleri doldur, en büyük bileşeni al -> tek kapalı siluet.
  3. mm ölçeğine getir, kontur çıkar, sadeleştir.
  4. İmalat kontrolü: mesafe dönüşümü ile en dar yeri ölç; MIN_KALINLIK
     altındaki uzuvları raporla.

Tek başına çalıştırılabilir:  python3 siluet.py
"""
import json
import os

import numpy as np
from PIL import Image
from scipy import ndimage
from shapely.geometry import Polygon
from skimage import measure

KLASOR = os.path.dirname(os.path.abspath(__file__))
KAYNAK = os.path.join(KLASOR, "varlik", "kaynak")

MIN_KALINLIK = 4.0        # ahşap dayanımı: hiçbir kesim detayı bundan ince olamaz
ZEMIN_ESIK = 236          # bu değerin üstü beyaz zemin sayılır

# Kaynak görselin hedef yüksekliği (mm). Budama uzuvları kestiği için nihai
# parça bundan kısa çıkar; kaybı büyük olanlar (yengeç, denizanası) buradan
# büyütülerek parça boyu 25-40 mm bandında tutulur.
HEDEF_BOY = {
    "yunus":        32.0,
    "denizanasi":   45.0,
    "denizati":     40.0,
    "kaplumbaga":   34.0,
    "balik":        32.0,
    "ahtapot":      36.0,
    "yengec":       46.0,
    "denizyildizi": 34.0,
}


def maske_cikar(yol, rgb_de=False):
    """Görselden dolu siluet maskesi (bool) üretir."""
    im = Image.open(yol).convert("RGB")
    a = np.asarray(im).astype(np.int16)
    rgb = np.asarray(im).copy()
    # beyaza yakınlık: hem parlak hem renksiz olmalı (sarı/pembe gövdeyi yeme)
    parlak = a.min(axis=2) >= ZEMIN_ESIK
    renksiz = (a.max(axis=2) - a.min(axis=2)) <= 18
    zemin_aday = parlak & renksiz

    # kenardan taşır: yalnız dışarıya bağlı beyaz bölgeler gerçek zemin
    etiket, _ = ndimage.label(zemin_aday)
    kenar = np.concatenate([etiket[0, :], etiket[-1, :],
                            etiket[:, 0], etiket[:, -1]])
    dis = set(int(v) for v in np.unique(kenar) if v)
    zemin = np.isin(etiket, list(dis)) if dis else np.zeros_like(zemin_aday)

    maske = ~zemin
    maske = ndimage.binary_fill_holes(maske)
    # en büyük bileşen (kaynaktaki kopuk lekeleri at)
    et, n = ndimage.label(maske)
    if n > 1:
        boyut = ndimage.sum(maske, et, range(1, n + 1))
        maske = et == (int(np.argmax(boyut)) + 1)
    # 1 px tırtıkları temizle
    maske = ndimage.binary_opening(maske, np.ones((3, 3)))
    maske = ndimage.binary_fill_holes(maske)
    return (maske, rgb) if rgb_de else maske


def maske_kontur(maske, mm_px, sadelik=0.35):
    """Maskeden mm cinsinden tek kapalı dış kontur."""
    dolgu = np.pad(maske, 2, constant_values=False)
    izler = measure.find_contours(dolgu.astype(float), 0.5)
    iz = max(izler, key=len)
    pts = [((c - 2) * mm_px, (r - 2) * mm_px) for r, c in iz]
    p = Polygon(pts).buffer(0)
    if p.geom_type == "MultiPolygon":
        p = max(p.geoms, key=lambda g: g.area)
    return Polygon(p.exterior).simplify(sadelik, preserve_topology=True)


def genislet(maske, r_px):
    """Disk ile genişletme — mesafe dönüşümü üzerinden (büyük r'de hızlı)."""
    if r_px <= 0:
        return maske
    return ndimage.distance_transform_edt(~maske) <= r_px


def daralt(maske, r_px):
    if r_px <= 0:
        return maske
    return ndimage.distance_transform_edt(maske) >= r_px


def acma(maske, r_px):
    """Açma = daralt sonra genişlet; r_px'ten dar uzuvlar kaybolur."""
    return genislet(daralt(maske, r_px), r_px)


def incelik_raporu(maske, mm_px):
    """MIN_KALINLIK'tan ince bölgeleri bulur."""
    d = ndimage.distance_transform_edt(maske) * mm_px
    kalin = acma(maske, (MIN_KALINLIK / 2.0) / mm_px)
    ince = maske & ~kalin
    return {
        "en_dar_mm": float(2 * d[maske].max()) if maske.any() else 0.0,
        "ince_alan_pay": float(ince.sum() / maske.sum()),
        "ince_maske": ince,
    }


PAY_MM = 4.0        # kırpma payı: kesim genişletmesi dizi sınırında kesilmesin


def isle(ad):
    yol = os.path.join(KAYNAK, f"{ad}.png")
    maske, rgb = maske_cikar(yol, rgb_de=True)
    sat = np.where(maske.any(axis=1))[0]
    sut = np.where(maske.any(axis=0))[0]
    mm_px = HEDEF_BOY[ad] / (sat[-1] - sat[0] + 1)
    p = int(round(PAY_MM / mm_px))
    r0, r1 = sat[0] - p, sat[-1] + 1 + p
    c0, c1 = sut[0] - p, sut[-1] + 1 + p

    def _kirp(a, dolgu):
        h, w = maske.shape
        ust, alt = max(0, -r0), max(0, r1 - h)
        sol, sag = max(0, -c0), max(0, c1 - w)
        kes = a[max(0, r0):min(h, r1), max(0, c0):min(w, c1)]
        gen = [(ust, alt), (sol, sag)] + [(0, 0)] * (a.ndim - 2)
        return np.pad(kes, gen, constant_values=dolgu)

    kirp = _kirp(maske, False)
    kirp_rgb = _kirp(rgb, 255)
    kontur = maske_kontur(kirp, mm_px)
    rapor = incelik_raporu(kirp, mm_px)
    x0, y0, x1, y1 = kontur.bounds
    return {
        "ad": ad,
        "px": kirp.shape,
        "mm_px": mm_px,
        "en_mm": x1 - x0,
        "boy_mm": y1 - y0,
        "alan_mm2": kontur.area,
        "dpi": 25.4 / mm_px,
        "ince_pay": rapor["ince_alan_pay"],
        "kontur": kontur,
        "maske": kirp,
        "rgb": kirp_rgb,
        "ince_maske": rapor["ince_maske"],
    }


def main():
    print(f"{'canlı':14} {'en×boy mm':>14} {'alan mm²':>9} {'dpi':>6} "
          f"{'<4mm alan':>10}  durum")
    print("-" * 68)
    sonuc = {}
    for ad in HEDEF_BOY:
        r = isle(ad)
        sonuc[ad] = r
        durum = "TAMAM" if r["ince_pay"] < 0.02 else (
            "DÜZELTME GEREKLİ" if r["ince_pay"] < 0.15 else "CİDDİ SORUN")
        print(f"{ad:14} {r['en_mm']:6.1f}×{r['boy_mm']:5.1f} "
              f"{r['alan_mm2']:9.0f} {r['dpi']:6.0f} "
              f"{100 * r['ince_pay']:9.1f}%  {durum}")
    return sonuc


if __name__ == "__main__":
    main()
