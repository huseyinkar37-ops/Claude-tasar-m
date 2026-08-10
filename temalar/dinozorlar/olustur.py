# -*- coding: utf-8 -*-
"""
İki katmanlı "Dinozorlar" puzzle üretim dosyalarını oluşturur (315 x 210 mm).

Bu tema, yeniden çizim YAPMAZ: kaynak illüstrasyonun (varlik/dinozor_sahne.jpg)
kendisi üst katman baskısıdır. Parça konturları görselin içinden segmentasyonla
çıkarılır, böylece kesim ile baskı birebir örtüşür.

Boru hattı
----------
1. maskeler()   – ad plakaları "opak duvar" sayılarak koyu konturlarla çevrili
                  bölgeler bulunur; birbirine değen nesneler morfolojik açma +
                  en yakın işaretçiye atama (watershed) ile en dar boğazdan ayrılır.
2. konturlar()  – maskeler marching-squares ile poligona, oradan mm'ye çevrilir;
                  4 mm altı çıkıntılar ahşap dayanımı için budanır.
3. paylari_ac() – kaynak kompozisyonda parçalar birbirine çok yakın; temas
                  bölgelerinde her iki parçadan eşit miktar traşlanarak
                  parçalar arası >= 7,5 mm, kenara >= 6 mm sağlanır.
4. Çıktılar: UV kalıp PDF, UV baskı PDF (2 mm taşmalı), alt gölge PDF, lazer DXF.

Çalıştırma:  python3 olustur.py
"""
import base64
import math
import os

import numpy as np
from PIL import Image
from scipy import ndimage as ndi
from skimage import measure

from shapely.geometry import Point, Polygon, box as s_kutu
from shapely.ops import unary_union

# ---------------------------------------------------------------- temel ölçüler
W, H = 315.0, 210.0          # bitmiş pano (kaynak görsel 3:2 -> kırpma yok)
BLEED = 2.0
CORNER_R = 8.0
MIN_GAP = 7.5                # parçalar arası en az duvar
MIN_EDGE = 6.0               # parça -> dış kenar
MIN_DETAY = 4.0              # en ince kesilebilir ayrıntı (ahşap dayanımı)
YUVA_R = 5.5                 # parmak yuvası hilali yarıçapı
YUVA_ACIKLIK = 4.0           # yuva -> diğer parça / kenar

KLASOR = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(KLASOR, "cikti")
KAYNAK = os.path.join(KLASOR, "varlik", "dinozor_sahne.jpg")
TEMA = "dinozorlar"

# tohum noktaları (kaynak görsel pikselinde, her dinozorun gövdesinde bir nokta)
TOHUM = {
    "trex":         (250, 430),
    "pteranodon":   (560, 140),
    "triceratops":  (600, 520),
    "brakiyozor":   (980, 480),
    "stegosaurus":  (1270, 450),
    "spinosaurus":  (300, 760),
    "velosiraptor": (890, 730),
}
ADLAR = {                                  # görselde basılı TR / EN adlar
    "trex":         ("T-Rex", "T-Rex"),
    "pteranodon":   ("Pteranodon", "Pteranodon"),
    "triceratops":  ("Triceratops", "Triceratops"),
    "brakiyozor":   ("Brakiyozor", "Brachiosaurus"),
    "stegosaurus":  ("Stegosaurus", "Stegosaurus"),
    "spinosaurus":  ("Spinosaurus", "Spinosaurus"),
    "velosiraptor": ("Velosiraptor", "Velociraptor"),
}


# Kaynak illüstrasyonda T-Rex'in kuyruk konturu ile soldaki eğrelti otunun
# yaprakları arasında ayırıcı çizgi yok; ikisi ~9 mm genişliğinde birleşiyor.
# Morfolojik ayırma bu genişlikte çalışmadığından kuyruk hattının hemen dışından
# elle bir kesme çizgisi geçiyoruz (kaynak piksel koordinatı, T-Rex'e girmez).
KESIKLER = [
    ([(0, 515), (35, 490), (62, 470), (92, 449), (122, 430), (152, 414),
      (185, 399), (208, 388)], 5),
]


def disk(r):
    y, x = np.ogrid[-r:r + 1, -r:r + 1]
    return x * x + y * y <= r * r


def _kesik_maskesi(sekil):
    from PIL import ImageDraw
    im = Image.new("1", (sekil[1], sekil[0]), 0)
    d = ImageDraw.Draw(im)
    for noktalar, kalinlik in KESIKLER:
        d.line(noktalar, fill=1, width=kalinlik, joint="curve")
    return np.asarray(im, dtype=bool)


# ---------------------------------------------------------------- 1. segmentasyon
def maskeler():
    """Kaynak görselden 7 dinozorun piksel maskesini ve ad plakalarını döndürür."""
    im = Image.open(KAYNAK).convert("RGB")
    rgb = np.asarray(im).astype(np.float32)
    lum = 0.299 * rgb[..., 0] + 0.587 * rgb[..., 1] + 0.114 * rgb[..., 2]
    yh, yw = lum.shape
    pxmm = yw / W

    # -- ad plakaları: beyaz, bbox'ını iyi dolduran yatık dikdörtgenler
    beyaz = ndi.binary_closing(rgb.min(axis=2) > 222, structure=disk(4))
    lb, nb = ndi.label(beyaz)
    plaka = np.zeros((yh, yw), bool)
    for i in range(1, nb + 1):
        m = lb == i
        if m.sum() < 4000:
            continue
        ys, xs = np.nonzero(m)
        w, h = xs.max() - xs.min() + 1, ys.max() - ys.min() + 1
        if m.sum() / (w * h) > 0.80 and 1.6 < w / h < 5.0 and h < 130:
            plaka |= m
    plaka_ic = plaka.copy()
    plaka = ndi.binary_dilation(plaka, structure=disk(8))   # kenarlık çizgisi dahil

    # -- koyu konturlarla çevrelenmiş bölgeler (plaka opak engel)
    koyu = ndi.binary_closing(lum < 60, structure=np.ones((3, 3)), iterations=2)
    koyu = ndi.binary_dilation(koyu, structure=np.ones((3, 3)))
    et, _ = ndi.label(~(koyu | plaka))
    kenar = set(et[0, :]) | set(et[-1, :]) | set(et[:, 0]) | set(et[:, -1])
    kenar.discard(0)
    nesne = (~np.isin(et, list(kenar))) & ~plaka
    nesne &= ~_kesik_maskesi(lum.shape)          # elle ayırma çizgileri

    # -- değen nesneleri en dar boğazdan ayır (açma -> işaretçi -> en yakın atama)
    isaret, _ = ndi.label(ndi.binary_opening(nesne, structure=disk(6)))
    _, (iy, ix) = ndi.distance_transform_edt(isaret == 0, return_indices=True)
    atama = np.where(nesne, isaret[iy, ix], 0)

    # 4 mm altı çıkıntıları buda (kesilemezler); sonra köşeleri yumuşat
    r_ac = max(2, int(round(MIN_DETAY * pxmm / 2)))
    r_kapa = max(2, int(round(1.2 * pxmm)))

    cikti = {}
    for ad, (sx, sy) in TOHUM.items():
        k = atama[sy, sx]
        if not k:
            raise RuntimeError(f"{ad}: tohum ({sx},{sy}) hiçbir nesneye düşmedi")
        m = ndi.binary_fill_holes(atama == k)
        l, _ = ndi.label(m)
        m = l == l[sy, sx]
        # plakanın örttüğü yeri köprüle (plaka arkası görünmüyor)
        m = ndi.binary_fill_holes(m | (ndi.binary_closing(m, structure=disk(30)) & plaka))
        # açma komşu bitkileri koparır; kapama onları GERİ köprülemesin diye
        # bileşen seçimi araya girer
        m = ndi.binary_opening(m, structure=disk(r_ac))
        l, _ = ndi.label(m)
        if l.max() == 0 or not l[sy, sx]:
            raise RuntimeError(f"{ad}: temizlik sonrası maske kayboldu")
        m = l == l[sy, sx]
        m = ndi.binary_closing(m, structure=disk(r_kapa))
        cikti[ad] = ndi.binary_fill_holes(m)
    return cikti, plaka_ic, (yw, yh), pxmm


# ---------------------------------------------------------------- 2. mm poligonları
def _maske_poligon(maske, pxmm, sadelik=0.22):
    """İkili maskenin dış sınırını mm cinsinden tek kapalı poligona çevirir."""
    pad = np.pad(maske, 1)
    izler = measure.find_contours(pad.astype(float), 0.5)
    if not izler:
        raise RuntimeError("kontur bulunamadı")
    iz = max(izler, key=len)                       # en uzun = dış sınır
    pts = [((c - 1) / pxmm, (r - 1) / pxmm) for r, c in iz]
    p = Polygon(pts)
    if not p.is_valid:
        p = p.buffer(0)
        if p.geom_type == "MultiPolygon":
            p = max(p.geoms, key=lambda g: g.area)
    return Polygon(p.exterior).simplify(sadelik, preserve_topology=True)


def cerceve_poly():
    return s_kutu(CORNER_R, CORNER_R, W - CORNER_R,
                  H - CORNER_R).buffer(CORNER_R, quad_segs=16)


def _tek(g):
    if g.is_empty:
        return g
    if g.geom_type == "MultiPolygon":
        g = max(g.geoms, key=lambda x: x.area)
    return Polygon(g.exterior)


def konturlar(mask_dict, pxmm):
    return {ad: _maske_poligon(m, pxmm) for ad, m in mask_dict.items()}


# ---------------------------------------------------------------- 3. paylar
def paylari_ac(P):
    """Kaynak kompozisyonda parçalar çok yakın; temas bölgelerinde eşit traşla
    parçalar arası >= MIN_GAP, kenara >= MIN_EDGE sağlanır."""
    rapor = []
    ic_alan = cerceve_poly().buffer(-MIN_EDGE)
    for ad in P:
        d = P[ad].distance(cerceve_poly().exterior)
        if d < MIN_EDGE:
            P[ad] = _tek(P[ad].intersection(ic_alan))
            rapor.append(f"{ad}: dış kenar payı {d:.1f} -> {MIN_EDGE:.1f} mm "
                         f"(kenarda traşlandı)")

    adlar = list(P)
    basla = {a: P[a].distance(P[b]) for i, a in enumerate(adlar)
             for b in adlar[i + 1:]}
    ilk_aralik = {}
    for i, a in enumerate(adlar):
        for b in adlar[i + 1:]:
            ilk_aralik[(a, b)] = P[a].distance(P[b])

    # nokta–yüzey geometrisinde traş simetrik eklenmediğinden yakınsayana dek yinele
    for tur in range(24):
        anlik = dict(P)
        kotu = [(a, b, anlik[a].distance(anlik[b]))
                for i, a in enumerate(adlar) for b in adlar[i + 1:]
                if anlik[a].distance(anlik[b]) < MIN_GAP - 0.02]
        if not kotu:
            break
        for a, b, g in kotu:
            pay = (MIN_GAP - g) / 2 + 0.05
            P[a] = _tek(P[a].difference(anlik[b].buffer(g + pay)))
            P[b] = _tek(P[b].difference(anlik[a].buffer(g + pay)))
        for ad in P:                              # traş artığı ince payandaları at
            P[ad] = _tek(P[ad].buffer(-MIN_DETAY / 2).buffer(MIN_DETAY / 2))
    else:
        rapor.append("UYARI: aralıklar 24 turda yakınsamadı")

    for (a, b), g in ilk_aralik.items():
        if g < MIN_GAP:
            yeni = P[a].distance(P[b])
            rapor.append(f"{a}–{b}: aralık {g:.1f} -> {yeni:.1f} mm "
                         f"({tur + 1} turda, her parçadan traş)")
    return rapor


# ---------------------------------------------------------------- parmak yuvaları
def yuvalar_yerlestir(P, plaka_poly):
    """Her parçanın en ferah kenarına, baskılı ad plakasına değmeyen bir
    R=YUVA_R hilal yerleştirir."""
    sonuc, rapor = {}, []
    kenar = cerceve_poly().exterior
    for ad, poly in P.items():
        digerleri = unary_union([q for a, q in P.items() if a != ad])
        cevre = poly.exterior
        n = max(120, int(cevre.length / 1.5))
        en_iyi, en_iyi_skor = None, -1e9
        for t in range(n):
            c = cevre.interpolate(t / n, normalized=True)
            hilal = Point(c.x, c.y).buffer(YUVA_R, quad_segs=24).difference(poly)
            if hilal.is_empty:
                continue
            hilal = _tek(hilal)
            if hilal.area < 12.0:
                continue
            skor = min(hilal.distance(digerleri), hilal.distance(kenar))
            if plaka_poly is not None and hilal.intersects(plaka_poly):
                skor -= 100                        # basılı adı kesme
            if skor > en_iyi_skor:
                en_iyi_skor, en_iyi = skor, hilal
        if en_iyi is None or en_iyi_skor < YUVA_ACIKLIK:
            rapor.append(f"{ad}: uygun parmak yuvası bulunamadı "
                         f"(en iyi açıklık {en_iyi_skor:.1f} mm)")
        if en_iyi is not None:
            sonuc[ad] = en_iyi.simplify(0.05, preserve_topology=True)
    return sonuc, rapor


# ---------------------------------------------------------------- doğrulama
def dogrula(P, Y):
    h = []
    kenar = cerceve_poly().exterior
    for ad, poly in P.items():
        d = poly.distance(kenar)
        if d < MIN_EDGE - 0.05:
            h.append(f"{ad}: dış kenara {d:.2f} mm (en az {MIN_EDGE})")
    adlar = list(P)
    for i in range(len(adlar)):
        for j in range(i + 1, len(adlar)):
            a, b = adlar[i], adlar[j]
            d = P[a].distance(P[b])
            if d <= 0:
                h.append(f"{a} ile {b} ÇAKIŞIYOR")
            elif d < MIN_GAP - 0.05:
                h.append(f"{a}–{b} arası {d:.2f} mm (en az {MIN_GAP})")
    for ad, hilal in Y.items():
        if hilal.area < 12:
            h.append(f"{ad} yuvası çok küçük ({hilal.area:.1f} mm²)")
        if P[ad].distance(hilal) > 0.2:
            h.append(f"{ad} yuvası kontura bitişik değil")
        if hilal.distance(kenar) < YUVA_ACIKLIK - 0.05:
            h.append(f"{ad} yuvası dış kenara {hilal.distance(kenar):.2f} mm")
        for n, p in P.items():
            if n != ad and hilal.distance(p) < YUVA_ACIKLIK - 0.05:
                h.append(f"{ad} yuvası {n} parçasına {hilal.distance(p):.2f} mm")
    for ad in P:
        if ad not in Y:
            h.append(f"{ad}: parmak yuvası yok")
    return h


# ---------------------------------------------------------------- SVG
def _yol(poly):
    pts = list(poly.exterior.coords)[:-1]
    return (f"M {pts[0][0]:.3f} {pts[0][1]:.3f} "
            + " ".join(f"L {x:.3f} {y:.3f}" for x, y in pts[1:]) + " Z")


def _gorsel_b64():
    veri = open(KAYNAK, "rb").read()
    return "data:image/jpeg;base64," + base64.b64encode(veri).decode()


def svg_belge(w, h, icerik):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" '
            f'xmlns:xlink="http://www.w3.org/1999/xlink" '
            f'width="{w}mm" height="{h}mm" viewBox="0 0 {w} {h}">'
            + "\n".join(icerik) + "</svg>")


def uret_baski_svg(P=None, Y=None):
    """Taşma payı, kaynak görselin taşma kutusunu tam dolduracak şekilde
    ölçeklenmesiyle sağlanır (gerçek görsel içeriği, uydurma kenar yok)."""
    tw, th = W + 2 * BLEED, H + 2 * BLEED
    ic = [f'<image x="0" y="0" width="{tw}" height="{th}" '
          f'preserveAspectRatio="none" xlink:href="{_gorsel_b64()}"/>']
    if P:
        ic.append(f'<g transform="translate({BLEED},{BLEED})">')
        for poly in P.values():
            ic.append(f'<path d="{_yol(poly)}" fill="none" stroke="#FF1744" '
                      f'stroke-width="0.6"/>')
        for hilal in (Y or {}).values():
            ic.append(f'<path d="{_yol(hilal)}" fill="#FFFFFF" fill-opacity="0.75" '
                      f'stroke="#FF1744" stroke-width="0.4"/>')
        ic.append(f'<path d="{_yol(cerceve_poly())}" fill="none" stroke="#2979FF" '
                  f'stroke-width="0.6"/>')
        ic.append("</g>")
    return svg_belge(tw, th, ic)


def uret_kalip_svg():
    ic = [f'<path d="{_yol(cerceve_poly())}" fill="none" stroke="#FF0000" '
          f'stroke-width="0.25"/>',
          f'<text x="6" y="{H - 4:.1f}" fill="#888888" font-size="3" '
          f'font-family="sans-serif">DINOZORLAR PUZZLE {W:.0f}x{H:.0f} '
          f'- UV KALIP (1:1)</text>']
    return svg_belge(W, H, ic)


def uret_golge_svg(P):
    tw, th = W + 2 * BLEED, H + 2 * BLEED
    ic = [f'<rect x="0" y="0" width="{tw}" height="{th}" fill="#DCEEF8"/>',
          f'<g transform="translate({BLEED},{BLEED})">']
    for poly in P.values():
        for iceri, op in ((-0.15, 0.4), (-0.55, 1.0)):
            g = poly.buffer(iceri, quad_segs=8)
            if g.is_empty:
                continue
            for gg in (g.geoms if g.geom_type == "MultiPolygon" else [g]):
                ic.append(f'<path d="{_yol(gg)}" fill="#54677A" fill-opacity="{op}"/>')
    ic.append("</g>")
    return svg_belge(tw, th, ic)


# ---------------------------------------------------------------- DXF
def uret_dxf(dosya, P, Y):
    import ezdxf

    doc = ezdxf.new("R2010", setup=True)
    doc.header["$INSUNITS"] = 4
    msp = doc.modelspace()
    doc.layers.add("UST_KATMAN_KESIM", color=1)
    doc.layers.add("ALT_KATMAN_KESIM", color=5)
    doc.layers.add("YAZI", color=8)

    def poli(poly, dx, katman):
        pts, son = [], None
        for (x, y) in list(poly.exterior.coords)[:-1]:
            q = (round(x + dx, 3), round(H - y, 3))
            if q != son:
                pts.append(q)
                son = q
        if pts[0] == pts[-1]:
            pts.pop()
        msp.add_lwpolyline(pts, close=True, dxfattribs={"layer": katman})

    poli(cerceve_poly(), 0, "UST_KATMAN_KESIM")
    for poly in P.values():
        poli(poly, 0, "UST_KATMAN_KESIM")
    for hilal in Y.values():
        poli(hilal, 0, "UST_KATMAN_KESIM")
    dx_alt = W + 15
    poli(cerceve_poly(), dx_alt, "ALT_KATMAN_KESIM")
    msp.add_text(f"UST KATMAN - dinozorlar + cepler ({W:.0f}x{H:.0f})",
                 dxfattribs={"layer": "YAZI", "height": 6}).set_placement((0, H + 6))
    msp.add_text(f"ALT KATMAN - duz taban ({W:.0f}x{H:.0f})",
                 dxfattribs={"layer": "YAZI", "height": 6}).set_placement((dx_alt, H + 6))
    doc.saveas(dosya)


# ---------------------------------------------------------------- ana akış
def main():
    print(f"Kaynak: {os.path.relpath(KAYNAK, KLASOR)}")
    mask_dict, plaka_maskesi, (pw, ph), pxmm = maskeler()
    print(f"Görsel {pw}x{ph} px -> pano {W:.0f}x{H:.0f} mm "
          f"({pxmm:.2f} px/mm = {pxmm * 25.4:.0f} dpi)")

    P = konturlar(mask_dict, pxmm)
    plaka_poly = unary_union(
        [_maske_poligon(m, pxmm, 0.3)
         for m in [ndi.label(plaka_maskesi)[0] == i
                   for i in range(1, ndi.label(plaka_maskesi)[1] + 1)]])

    print("\nKaynak kompozisyondan gelen paylar düzeltiliyor:")
    for satir in paylari_ac(P) or ["  (düzeltme gerekmedi)"]:
        print("  •", satir)

    Y, y_rapor = yuvalar_yerlestir(P, plaka_poly)
    for satir in y_rapor:
        print("  !", satir)

    hatalar = dogrula(P, Y)
    print()
    if hatalar:
        print("UYARI – yerleşim sorunları:")
        for hh in hatalar:
            print("  •", hh)
    else:
        print("Yerleşim doğrulandı: tüm parçalar aralık kurallarına uygun.")

    kesilen = [ad for ad, poly in P.items() if poly.intersects(plaka_poly)]
    if kesilen:
        print("Not: basılı ad plakası parça konturuyla kesişiyor ->",
              ", ".join(kesilen))

    os.makedirs(OUT, exist_ok=True)
    import cairosvg
    cairosvg.svg2pdf(bytestring=uret_baski_svg().encode(),
                     write_to=f"{OUT}/{TEMA}_uv_baski.pdf")
    cairosvg.svg2pdf(bytestring=uret_kalip_svg().encode(),
                     write_to=f"{OUT}/{TEMA}_uv_kalip.pdf")
    cairosvg.svg2pdf(bytestring=uret_golge_svg(P).encode(),
                     write_to=f"{OUT}/{TEMA}_alt_golge.pdf")
    cairosvg.svg2png(bytestring=uret_baski_svg(P, Y).encode(),
                     write_to=f"{OUT}/{TEMA}_onizleme.png", output_width=2200)
    cairosvg.svg2png(bytestring=uret_golge_svg(P).encode(),
                     write_to=f"{OUT}/{TEMA}_alt_golge_onizleme.png", output_width=1920)
    uret_dxf(f"{OUT}/{TEMA}_lazer_kesim.dxf", P, Y)

    print("\nparçalar:")
    for ad, poly in P.items():
        x0, y0, x1, y1 = poly.bounds
        tr, en = ADLAR[ad]
        print(f"  {tr:<13} ({en:<14}) {x1-x0:6.1f} x {y1-y0:6.1f} mm  "
              f"alan {poly.area:6.0f} mm²")
    print("Tamamlandı ->", OUT)


if __name__ == "__main__":
    main()
